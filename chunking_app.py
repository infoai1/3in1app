import streamlit as st
import pandas as pd
from parsers import detect_headers_and_text
from chunker import create_csv_data
from io import BytesIO

st.title("📚 DOCX to CSV Chapter Chunker")

st.write("Upload a DOCX, auto-detect headers, split into chunks, and download as CSV.")

book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

auto_detect = st.checkbox("Enable Auto-Detect Headers", value=True)
font_size_threshold = st.slider("Header Font Size Threshold", 8, 20, 13)
min_words = st.slider("Min Words per Chunk", 50, 500, 200)
max_words = st.slider("Max Words per Chunk", 100, 500, 250)
overlap = st.slider("Chunk Overlap (%)", 0, 50, 20) / 100

uploaded_file = st.file_uploader("Upload DOCX file", type=["docx"])

if uploaded_file:
    st.subheader("Step 1: Preview Detected Headers")
    parsed_content = detect_headers_and_text(
        uploaded_file,
        font_size_threshold=font_size_threshold,
        auto_detect=auto_detect
    )

    headers_preview = [item["text"] for item in parsed_content if item["type"] == "header"]
    st.write("**Detected Headers:**", headers_preview)

    if st.button("Generate CSV"):
        df = create_csv_data(parsed_content, book_name, author_name, min_words, max_words, overlap)

        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        st.download_button(
            label="Download CSV",
            data=csv_buffer,
            file_name="output.csv",
            mime="text/csv"
        )

        st.success(f"CSV generated with {len(df)} chunks.")
