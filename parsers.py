from docx import Document
import fitz
import re

def parse_file(uploaded_file, body_threshold=12, heading_threshold=14):
    text = ""
    structure = []  # List with types and text
    footnotes = {}  # Dict for endnotes

    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                font_size = block[3] - block[1]  # Approx size
                is_bold = "bold" in block[5]  # Check font flags
                is_centered = abs(block[0] - block[2]) < 100  # Rough centering
                if (font_size > heading_threshold or is_bold or is_centered or len(block_text.split()) < 20 or re.match(r"Chapter|Section", block_text)):
                    structure_type = "chapter" if "Chapter" in block_text else "subchapter" if re.match(r"\d+\.\d+", block_text) else "heading"
                    structure.append({"type": structure_type, "text": block_text})
                elif re.match(r"^\[\d+\]", block_text):  # Footnote detection
                    num = re.findall(r"\d+", block_text)[0]
                    footnotes[num] = block_text
                elif font_size <= body_threshold:
                    structure.append({"type": "body", "text": block_text})
        text = " ".join([item["text"] for item in structure])
    
    else:  # DOCX
        doc = Document(uploaded_file)
        current_chapter = ""
        for para in doc.paragraphs:
            is_bold = any(run.bold for run in para.runs)
            font_size = max((run.font.size.pt for run in para.runs if run.font.size), default=12)
            is_centered = para.alignment == 1  # WD_ALIGN_PARAGRAPH.CENTER
            if para.style.name.startswith("Heading") or (is_bold and font_size > heading_threshold) or len(para.text.split()) < 20:
                if "Chapter" in para.text:
                    current_chapter = para.text
                    structure.append({"type": "chapter", "text": para.text})
                else:
                    structure.append({"type": "subchapter", "text": para.text, "parent": current_chapter})
            elif re.match(r"^\[\d+\]", para.text):  # Footnote
                num = re.findall(r"\d+", para.text)[0]
                footnotes[num] = para.text
            elif font_size <= body_threshold:
                structure.append({"type": "body", "text": para.text, "parent": current_chapter})
        text = " ".join([item["text"] for item in structure])
    
    # Link footnotes to structure
    for item in structure:
        for num, ref in footnotes.items():
            if f"[{num}]" in item.get("text", ""):
                item["footnote"] = ref
    
    return text, structure
