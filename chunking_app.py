import streamlit as st
import pandas as pd
from parsers import parse_file_advanced
from chunker import improved_chunk_text_sentences

st.title("Advanced Islamic Book Chunking App")

# Header Detection Controls
st.sidebar.header("🎯 Detection Settings")
enable_auto_detect = st.sidebar.checkbox("Enable Auto-Detection (Recommended for subtle headers)", value=True)
enable_centered = st.sidebar.checkbox("Detect Centered Text", value=True)

# Font size controls (simplified)
st.sidebar.header("📏 Font Size Settings")
body_font_size = st.sidebar.slider("Body Text Font Size Threshold", 2, 40, 12)
header_font_size = st.sidebar.slider("Header Font Size Threshold", 2, 40, 13)  # Single slider for all headers

# Chunking controls
st.sidebar.header("✂️ Chunking Settings")
chunk_min = st.sidebar.slider("Min Chunk Size (words)", 150, 300, 200)
chunk_max = st.sidebar.slider("Max Chunk Size (words)", 200, 400, 250)
overlap_percent = st.sidebar.slider("Overlap %", 10, 30, 20)

uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

if uploaded_file and book_name and author_name:
    try:
        font_settings = {
            'body_threshold': body_font_size,
            'header_threshold': header_font_size,  # Unified for simplicity
            'enable_auto_detect': enable_auto_detect,
            'enable_centered': enable_centered
        }
        
        text, structure = parse_file_advanced(uploaded_file, font_settings)
        
        paragraphs = [item["text"] for item in structure if item["type"] == "body"]
        all_headers = [item["text"] for item in structure if item["type"].startswith("header")]
        
        # Display stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Detected Headers", len(all_headers))
        with col2:
            st.metric("Paragraphs", len(paragraphs))
        
        # Debug preview
        if st.checkbox("🔍 Show Detected Headers"):
            for h in all_headers:
                st.write(f"- {h}")
        
        if st.checkbox("📋 Show Structure Preview"):
            for item in structure[:20]:
                if item['type'].startswith("header"):
                    st.write(f"**Header:** {item['text']}")
                else:
                    st.write(f"Body: {item['text'][:100]}...")

        if st.button("🚀 Chunk and Download CSV"):
            chunk_settings = {
                'chunk_min': chunk_min,
                'chunk_max': chunk_max,
                'overlap_ratio': overlap_percent / 100
            }
            
            chunks = improved_chunk_text_sentences(
                paragraphs, book_name, author_name, 
                all_headers, chunk_settings
            )
            
            df = pd.DataFrame(chunks)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{book_name}_chunks.csv",
                mime="text/csv"
            )
            
            st.success(f"Created {len(chunks)} chunks!")
            st.write("**Unique Chapters:**", ", ".join(df['chapter_name'].unique()))
            st.dataframe(df.head())
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Help section
with st.expander("ℹ️ Quick Fix Tips"):
    st.write("""
    - **Enable Auto-Detection**: This catches subtle headers like bold/short lines.
    - **Lower Header Threshold**: Set to 12-13 if headers aren't bigger than body text.
    - **Check Previews**: Use the checkboxes to verify detection before chunking.
    - **Test with Your File**: Your DOCX has bold ALL-CAPS headers—auto-detect should catch them now.
    """)
