import streamlit as st
import pandas as pd
from parsers import parse_file
from chunker import improved_chunk_text

st.title("Islamic Book Chunking App")

uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

if uploaded_file and book_name and author_name:
    try:
        # Parse the file (detects headers by font size, bold, center position)
        text, structure = parse_file(uploaded_file)
        
        # Extract paragraphs and chapter names from structure
        paragraphs = [item["text"] for item in structure if item["type"] == "body"]
        chapter_names = [item["text"] for item in structure if item["type"] == "chapter"]
        
        st.write("**Chapters detected:**", chapter_names)
        st.write(f"**Found {len(paragraphs)} paragraphs**")
        
        # Show structure preview
        if st.checkbox("Show document structure"):
            for item in structure[:10]:  # Show first 10 items
                st.write(f"**{item['type']}:** {item['text'][:100]}...")
        
        if st.button("Create Chunks and Download CSV"):
            # Create chunks
            chunks = improved_chunk_text(paragraphs, book_name, author_name, chapter_names)
            df = pd.DataFrame(chunks)
            
            # Show download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Chunks CSV",
                data=csv,
                file_name=f"{book_name}_chunks.csv",
                mime="text/csv"
            )
            
            # Show preview
            st.success(f"✅ Created {len(chunks)} chunks!")
            st.write("**Preview of chunks:**")
            st.dataframe(df.head())
            
    except Exception as e:
        st.error(f"❌ Error parsing file: {str(e)}")

elif uploaded_file:
    st.warning("⚠️ Please enter both book name and author name")

# Show help
with st.expander("ℹ️ How it works"):
    st.write("""
    **This app automatically detects:**
    - **Headers** based on font size, bold text, and center alignment
    - **Chapters** by looking for "Chapter" keywords
    - **Body text** for chunking
    
    **Chunking rules:**
    - Minimum chunk size: 200 words
    - Maximum chunk size: 250 words
    - 20% overlap between chunks
    - Respects chapter boundaries
    """)
