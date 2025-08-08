from docx import Document

def detect_headers_and_text(docx_file, font_size_threshold=13, max_header_words=15, auto_detect=True):
    doc = Document(docx_file)
    content = []
    current_type = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        is_header = False
        if auto_detect:
            run_styles = [(run.bold, run.font.size.pt if run.font.size else None) for run in para.runs]
            bold = any(b for b, _ in run_styles)
            all_caps = text.isupper()
            short_phrase = len(text.split()) <= max_header_words
            large_font = any((size and size >= font_size_threshold) for _, size in run_styles)

            if bold or all_caps or short_phrase or large_font:
                is_header = True

        if is_header:
            current_type = "header"
            content.append({"type": "header", "text": text})
        else:
            content.append({"type": "body", "text": text})

    return content
