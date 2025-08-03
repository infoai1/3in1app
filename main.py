import streamlit as st
import pandas as pd
from parsers import parse_docx_file
from processors import improved_chunk_text, run_deepseek_enrichment
from utils import download_csv

st.title("Islamic Book Processor App (STEP 1: Chunking)")

uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")
if uploaded_file:
    paragraphs, chapter_names = parse_docx_file(uploaded_file)
    st.write("Chapters detected:", chapter_names)
    if st.button("Chunk and Save CSV"):
        chunks = improved_chunk_text(paragraphs, book_name, author_name, chapter_names)
        df = pd.DataFrame(chunks)
        st.session_state.chunk_df = df
        download_csv(df, "clean_chunks.csv")
        st.write(df.head())

st.title("STEP 2: Enrich with DeepSeek (after manual review)")
if 'chunk_df' in st.session_state:
    if st.button("Run DeepSeek Metadata Extraction"):
        enriched_df = run_deepseek_enrichment(st.session_state.chunk_df)
        download_csv(enriched_df, "enriched_chunks.csv")
        st.write(enriched_df.head())
