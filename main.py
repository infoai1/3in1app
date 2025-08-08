import streamlit as st
import pandas as pd
from parsers import parse_file
from chunker import improved_chunk_text
from processors import extract_metadata, generate_embeddings
from utils import export_files
import os

st.title("Islamic Book Processor App (STEP 1: Chunking)")

uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

if uploaded_file and book_name and author_name:
    try:
        # Use the correct function
        text, structure = parse_file(uploaded_file)
        
        # Extract paragraphs and chapter names from structure
        paragraphs = [item["text"] for item in structure if item["type"] == "body"]
        chapter_names = [item["text"] for item in structure if item["type"] == "chapter"]
        
        st.write("Chapters detected:", chapter_names)
        st.write(f"Found {len(paragraphs)} paragraphs")
        
        if st.button("Chunk and Save CSV"):
            chunks = improved_chunk_text(paragraphs, book_name, author_name, chapter_names)
            df = pd.DataFrame(chunks)
            st.session_state.chunk_df = df
            
            # Show download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Clean Chunks CSV",
                data=csv,
                file_name="clean_chunks.csv",
                mime="text/csv"
            )
            st.write("Preview of chunks:")
            st.write(df.head())
            
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")

elif uploaded_file:
    st.warning("Please enter both book name and author name")

st.title("STEP 2: Enrich with DeepSeek (after manual review)")

if 'chunk_df' in st.session_state:
    if st.button("Run DeepSeek Metadata Extraction"):
        try:
            enriched_df = extract_metadata(st.session_state.chunk_df.copy())
            enriched_df = generate_embeddings(enriched_df)
            
            # Show download button for enriched data
            csv = enriched_df.to_csv(index=False)
            st.download_button(
                label="Download Enriched CSV",
                data=csv,
                file_name="enriched_chunks.csv",
                mime="text/csv"
            )
            st.write("Preview of enriched data:")
            st.write(enriched_df.head())
            
        except Exception as e:
            st.error(f"Error during enrichment: {str(e)}")
