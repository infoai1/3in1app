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
                    
                font_size = block[3] - block[1]  # Approximate size
                is_bold = "bold" in block[1].lower()
                is_centered = abs(block - block[2]) < 100
                word_count = len(block_text.split())
                
                # Determine structure type based on font size and formatting
                structure_type = classify_text_type(
                    font_size, is_bold, is_centered, word_count,
                    body_threshold, header1_threshold, header2_threshold, header3_threshold,
                    enable_header1, enable_header2, enable_header3, enable_centered
                )
                
                if re.match(r"^\[\d+\]", block_text):  # Footnote
                    num = re.findall(r"\d+", block_text)[0]
                    footnotes[num] = block_text
                else:
                    structure.append({"type": structure_type, "text": block_text})

    else:  # DOCX
        doc = Document(uploaded_file)
        
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
                
            is_bold = any(run.bold for run in para.runs if run.bold is not None)
            font_sizes = [run.font.size.pt for run in para.runs if run.font.size is not None]
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
            is_centered = para.alignment == 1  # WD_ALIGN_PARAGRAPH.CENTER
            word_count = len(para.text.split())
            
            # Determine structure type
            structure_type = classify_text_type(
                avg_font_size, is_bold, is_centered, word_count,
                body_threshold, header1_threshold, header2_threshold, header3_threshold,
                enable_header1, enable_header2, enable_header3, enable_centered
            )
            
            if re.match(r"^\[\d+\]", para.text):  # Footnote
                num = re.findall(r"\d+", para.text)[0]
                footnotes[num] = para.text
            else:
                structure.append({"type": structure_type, "text": para.text})

    text = " ".join([item["text"] for item in structure])
    
    # Link footnotes to structure
    for item in structure:
        for num, ref in footnotes.items():
            if f"[{num}]" in item.get("text", ""):
                item["footnote"] = ref

    return text, structure

def classify_text_type(font_size, is_bold, is_centered, word_count, 
                      body_threshold, header1_threshold, header2_threshold, header3_threshold,
                      enable_header1, enable_header2, enable_header3, enable_centered):
    """Classify text as header1, header2, header3, or body based on formatting and enabled options"""
    
    # Short text with special formatting is likely a header
    is_header_like = (is_bold or (is_centered and enable_centered) or word_count < 15)
    
    # Check each header level if enabled
    if enable_header1 and font_size >= header1_threshold and is_header_like:
        return "header1"
    elif enable_header2 and font_size >= header2_threshold and is_header_like:
        return "header2"  
    elif enable_header3 and font_size >= header3_threshold and is_header_like:
        return "header3"
    elif font_size <= body_threshold or not is_header_like:
        return "body"
    else:
        return "body"  # Default to body if no header rules match

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
