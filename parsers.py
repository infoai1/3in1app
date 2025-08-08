from docx import Document
import fitz
import re

def parse_file_advanced(uploaded_file, font_settings):
    text = ""
    structure = []
    footnotes = {}
    
    body_threshold = font_settings['body_threshold']
    header1_threshold = font_settings['header1_threshold']
    header2_threshold = font_settings['header2_threshold'] 
    header3_threshold = font_settings['header3_threshold']
    enable_header1 = font_settings['enable_header1']
    enable_header2 = font_settings['enable_header2']
    enable_header3 = font_settings['enable_header3']
    enable_centered = font_settings['enable_centered']

    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                if not block_text:
                    continue
                    
                font_size = block[3] - block[1]
                is_bold = "bold" in block[4].lower()
                is_centered = abs(block - block[2]) < 100
                word_count = len(block_text.split())
                
                structure_type = classify_text_simple(
                    block_text, font_size, is_bold, is_centered, word_count,
                    body_threshold, header1_threshold, header2_threshold, header3_threshold,
                    enable_header1, enable_header2, enable_header3, enable_centered
                )
                
                if re.match(r"^\[\d+\]", block_text):
                    num = re.findall(r"\d+", block_text)
                    footnotes[num] = block_text
                else:
                    structure.append({"type": structure_type, "text": block_text})

    else:  # DOCX
        doc = Document(uploaded_file)
        
        for para in doc.paragraphs:
            para_text = para.text.strip()
            if not para_text:
                continue
                
            # Simple font detection
            is_bold = any(run.bold for run in para.runs if run.bold is not None)
            
            # Get font sizes - use a simpler approach
            font_sizes = []
            for run in para.runs:
                if run.font.size is not None:
                    font_sizes.append(run.font.size.pt)
            
            # Use max font size if available, otherwise assume body text
            if font_sizes:
                max_font_size = max(font_sizes)
            else:
                max_font_size = body_threshold  # Default to body
            
            # Check if it's a heading style
            style_name = para.style.name.lower()
            is_heading_style = 'heading' in style_name or 'title' in style_name
            
            is_centered = para.alignment == 1
            word_count = len(para_text.split())
            
            # Simple classification
            structure_type = classify_text_simple(
                para_text, max_font_size, is_bold, is_centered, word_count,
                body_threshold, header1_threshold, header2_threshold, header3_threshold,
                enable_header1, enable_header2, enable_header3, enable_centered,
                is_heading_style
            )
            
            if re.match(r"^\[\d+\]", para_text):
                num = re.findall(r"\d+", para_text)[0]
                footnotes[num] = para_text
            else:
                structure.append({"type": structure_type, "text": para_text})

    text = " ".join([item["text"] for item in structure])
    
    # Link footnotes to structure
    for item in structure:
        for num, ref in footnotes.items():
            if f"[{num}]" in item.get("text", ""):
                item["footnote"] = ref

    return text, structure

def classify_text_simple(text, font_size, is_bold, is_centered, word_count, 
                        body_threshold, header1_threshold, header2_threshold, header3_threshold,
                        enable_header1, enable_header2, enable_header3, enable_centered,
                        is_heading_style=False):
    """MUCH SIMPLER classification - easier to debug"""
    
    # Common header patterns (very obvious ones)
    obvious_headers = [
        r'^[A-Z\s]{10,}$',  # Long ALL CAPS text
        r'^FROM\s+THE\s+',  # FROM THE EDITOR, etc.
        r'^Chapter\s+\d+',  # Chapter 1, etc.
        r'^CHAPTER\s+',     # CHAPTER anything
        r'^\d+\.\s+[A-Z]',  # 1. Something
        r'^[A-Z]{3,}\s+[A-Z]{3,}',  # Multiple caps words
    ]
    
    is_obvious_header = any(re.match(pattern, text) for pattern in obvious_headers)
    
    # Very simple rules - if ANY of these is true, it's a header
    possible_header = (
        is_obvious_header or
        is_heading_style or
        font_size > body_threshold + 2 or  # Even slightly bigger font
        (is_bold and word_count <= 15) or  # Bold and short
        (is_centered and enable_centered and word_count <= 12) or  # Centered and short
        text.isupper() and len(text) > 10  # All caps and long enough
    )
    
    if not possible_header:
        return "body"
    
    # Determine header level based on font size (if enabled)
    if enable_header1 and font_size >= header1_threshold:
        return "header1"
    elif enable_header2 and font_size >= header2_threshold:
        return "header2"
    elif enable_header3 and font_size >= header3_threshold:
        return "header3"
    elif enable_header1:  # Default to header1 if enabled
        return "header1"
    elif enable_header2:  # Default to header2 if enabled
        return "header2"
    elif enable_header3:  # Default to header3 if enabled
        return "header3"
    else:
        return "body"  # If no headers enabled, treat as body

# Keep the old function for backward compatibility
def parse_file(uploaded_file, body_threshold=12, heading_threshold=14):
    font_settings = {
        'body_threshold': body_threshold,
        'header1_threshold': heading_threshold + 4,
        'header2_threshold': heading_threshold + 2,
        'header3_threshold': heading_threshold,
        'enable_header1': True,
        'enable_header2': True,
        'enable_header3': True,
        'enable_centered': True
    }
    return parse_file_advanced(uploaded_file, font_settings)
