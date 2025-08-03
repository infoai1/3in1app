import streamlit as st
import pandas as pd
from docx import Document
import fitz
import re

st.title("App 1: Chunking and Structure Extraction")

uploaded_file = st.file_uploader("Upload DOCX/PDF (10-page batch)", type=["docx", "pdf"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")
body_font_threshold = st.slider("Body Font Threshold (pt)", 8, 16, 12)
heading_font_threshold = st.slider("Heading Font Threshold (pt)", 12, 24, 14)

def parse_file(uploaded_file, body_threshold, heading_threshold):
    paragraphs = []
    chapter_names = []
    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                font_size = block[3] - block[1]
                is_bold = "bold" in block[5]
                is_centered = abs(block[0] - block[2]) < 100
                if font_size > heading_threshold or is_bold or is_centered or len(block_text.split()) < 20 or re.match(r"Chapter|Section", block_text):
                    chapter_names.append(block_text)
                paragraphs.append(block_text)
    else:  # DOCX
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text: continue
            is_bold = any(run.bold for run in para.runs)
            font_size = max((run.font.size.pt for run in para.runs if run.font.size), default=12)
            is_centered = para.alignment == 1
            if is_bold and font_size > heading_threshold or len(text.split()) < 20:
                chapter_names.append(text)
            paragraphs.append(text)
    return paragraphs, chapter_names

def improved_chunk_text(paragraphs, book_name, author_name, chapter_names, chunk_min=200, chunk_max=250, overlap_ratio=0.2):
    results = []
    chap_idx = 0
    in_chapter = chapter_names[chap_idx] if chapter_names else ""
    buf = []
    buf_len = 0
    overlap = []
    for para in paragraphs:
        if chap_idx + 1 < len(chapter_names) and para.strip() == chapter_names[chap_idx + 1]:
            if buf:
                if overlap: buf = overlap + buf
                results.append({"book_name": book_name, "author_name": author_name, "chapter_name": in_chapter, "text_chunk": " ".join(buf)})
            chap_idx += 1
            in_chapter = chapter_names[chap_idx]
            buf = []
            buf_len = 0
            overlap = []
            continue
        words = para.split()
        num_words = len(words)
        if num_words > chunk_max:
            if buf:
                if overlap: buf = overlap + buf
                results.append({"book_name": book_name, "author_name": author_name, "chapter_name": in_chapter, "text_chunk": " ".join(buf)})
                buf = []
                buf_len = 0
                overlap = []
            results.append({"book_name": book_name, "author_name": author_name, "chapter_name": in_chapter, "text_chunk": para})
            overlap_count = int(chunk_max * overlap_ratio)
            overlap = words[-overlap_count:] if overlap_count > 0 else []
            continue
        buf += words
        buf_len += num_words
        if buf_len >= chunk_min:
            results.append({"book_name": book_name, "author_name": author_name, "chapter_name": in_chapter, "text_chunk": " ".join(buf)})
            overlap_count = int(chunk_max * overlap_ratio)
            overlap = buf[-overlap_count:] if overlap_count > 0 else []
            buf = overlap.copy()
            buf_len = len(buf)
    if buf:
        results.append({"book_name": book_name, "author_name": author_name, "chapter_name": in_chapter, "text_chunk": " ".join(buf)})
    return results

if uploaded_file and book_name and author_name:
    paragraphs, chapter_names = parse_file(uploaded_file, body_font_threshold, heading_font_threshold)
    st.write("Detected Chapters:", chapter_names)
    if st.button("Chunk and Export CSV"):
        chunks = improved_chunk_text(paragraphs, book_name, author_name, chapter_names)
        df = pd.DataFrame(chunks)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Clean Chunks CSV", csv, "clean_chunks.csv", "text/csv")
        st.dataframe(df.head())
