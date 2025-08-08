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
                
                structure_type = classify_text_type_improved(
                    block_text, font_size, is_bold, is_centered, word_count,
                    body_threshold, header1_threshold, header2_threshold, header3_threshold,
                    enable_header1, enable_header2, enable_header3, enable_centered
                )
                
                if re.match(r"^\[\d+\]", block_text):
                    num = re.findall(r"\d+", block_text)[0]
                    footnotes[num] = block_text
                else:
                    structure.append({"type": structure_type, "text": block_text})

    else:  # DOCX
        doc = Document(uploaded_file)
        
        for para in doc.paragraphs:
            para_text = para.text.strip()
            if not para_text:
                continue
                
            # Better font detection
            is_bold = any(run.bold for run in para.runs if run.bold is not None)
            
            # Get all font sizes from runs
            font_sizes = []
            for run in para.runs:
                if run.font.size is not None:
                    font_sizes.append(run.font.size.pt)
                elif run.font.name and any(word in run.font.name.lower() for word in ['heading', 'title']):
                    font_sizes.append(16)  # Assume heading font
                else:
                    font_sizes.append(12)  # Default size
            
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
            max_font_size = max(font_sizes) if font_sizes else 12
            
            # Check paragraph style
            style_name = para.style.name.lower()
            is_heading_style = 'heading' in style_name or 'title' in style_name
            
            is_centered = para.alignment == 1
            word_count = len(para_text.split())
            
            # Use improved classification
            structure_type = classify_text_type_improved(
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

def classify_text_type_improved(text, font_size, is_bold, is_centered, word_count, 
                              body_threshold, header1_threshold, header2_threshold, header3_threshold,
                              enable_header1, enable_header2, enable_header3, enable_centered,
                              is_heading_style=False):
    """Improved classification with multiple detection methods"""
    
    # Common header patterns
    header_patterns = [
        r'^[A-Z\s]{3,}$',  # ALL CAPS (3+ chars)
        r'^Chapter\s+\d+',  # Chapter 1, Chapter 2, etc.
        r'^CHAPTER\s+[IVX]+',  # CHAPTER I, CHAPTER II, etc.
        r'^\d+\.\s*[A-Z]',  # 1. Something, 2. Something
        r'^[A-Z][a-z]+\s+\d+',  # Article 1, Section 2, etc.
        r'^FROM\s+THE\s+',  # FROM THE EDITOR, etc.
        r'^[A-Z]{2,}\s+[A-Z]{2,}',  # Multiple words in caps
    ]
    
    # Check if text matches header patterns
    is_pattern_header = any(re.match(pattern, text) for pattern in header_patterns)
    
    # Multiple criteria for header detection
    header_indicators = 0
    
    # Font-based indicators
    if font_size >= header1_threshold: header_indicators += 3
    elif font_size >= header2_threshold: header_indicators += 2
    elif font_size >= header3_threshold: header_indicators += 1
    
    # Style-based indicators
    if is_bold: header_indicators += 2
    if is_centered and enable_centered: header_indicators += 2
    if is_heading_style: header_indicators += 3
    
    # Content-based indicators
    if is_pattern_header: header_indicators += 3
    if word_count <= 10: header_indicators += 1
    if word_count <= 5: header_indicators += 2
    if text.isupper() and len(text) > 5: header_indicators += 2
    
    # Classification based on total score and enabled options
    if header_indicators >= 5:
        if enable_header1 and font_size >= header1_threshold:
            return "header1"
        elif enable_header2 and font_size >= header2_threshold:
            return "header2"
        elif enable_header3 and font_size >= header3_threshold:
            return "header3"
        elif enable_header1:
            return "header1"  # Default to header1 if enabled
        elif enable_header2:
            return "header2"
        elif enable_header3:
            return "header3"
    elif header_indicators >= 3:
        if enable_header2 and font_size >= header2_threshold:
            return "header2"
        elif enable_header3 and font_size >= header3_threshold:
            return "header3"
        elif enable_header2:
            return "header2"
        elif enable_header3:
            return "header3"
    elif header_indicators >= 2:
        if enable_header3:
            return "header3"
    
    return "body"

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
