from docx import Document
import re

def parse_file_advanced(uploaded_file, font_settings):
    structure = []
    
    body_threshold = font_settings['body_threshold']
    header_threshold = font_settings['header_threshold']
    enable_auto_detect = font_settings.get('enable_auto_detect', False)
    enable_centered = font_settings['enable_centered']

    doc = Document(uploaded_file)
    
    for para in doc.paragraphs:
        para_text = para.text.strip()
        if not para_text:
            continue
        
        is_bold = any(run.bold for run in para.runs if run.bold is not None)
        font_sizes = [run.font.size.pt for run in para.runs if run.font.size]
        max_font = max(font_sizes) if font_sizes else body_threshold
        is_centered = para.alignment == 1
        word_count = len(para_text.split())
        is_all_caps = para_text.isupper()
        
        # Simple header check
        is_header = (
            (max_font > body_threshold) or
            is_bold or
            (is_centered and enable_centered) or
            (enable_auto_detect and (is_all_caps or word_count < 10))
        )
        
        structure_type = "header" if is_header else "body"
        structure.append({"type": structure_type, "text": para_text})

    text = " ".join([item["text"] for item in structure])
    return text, structure
