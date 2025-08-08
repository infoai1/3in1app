import streamlit as st
import pandas as pd
from parsers import parse_file_advanced
from chunker import improved_chunk_text_sentences

st.title("Advanced Islamic Book Chunking App")

# Font size controls
st.sidebar.header("📏 Font Size Settings")
body_font_size = st.sidebar.slider("Body Text Font Size", 8, 16, 12)
header1_font_size = st.sidebar.slider("Header 1 Font Size", 14, 24, 18)
header2_font_size = st.sidebar.slider("Header 2 Font Size", 12, 20, 16)
header3_font_size = st.sidebar.slider("Header 3 Font Size", 10, 18, 14)

# Chunking controls
st.sidebar.header("✂️ Chunking Settings")
chunk_min = st.sidebar.slider("Minimum Chunk Size (words)", 150, 300, 200)
chunk_max = st.sidebar.slider("Maximum Chunk Size (words)", 200, 400, 250)
overlap_percent = st.sidebar.slider("Overlap Percentage", 10, 30, 20)

uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

if uploaded_file and book_name and author_name:
    try:
        # Parse with custom font settings
        font_settings = {
            'body_threshold': body_font_size,
            'header1_threshold': header1_font_size,
            'header2_threshold': header2_font_size,
            'header3_threshold': header3_font_size
        }
        
        text, structure = parse_file_advanced(uploaded_file, font_settings)
        
        # Extract different types
        paragraphs = [item["text"] for item in structure if item["type"] == "body"]
        header1s = [item["text"] for item in structure if item["type"] == "header1"]
        header2s = [item["text"] for item in structure if item["type"] == "header2"]
        header3s = [item["text"] for item in structure if item["type"] == "header3"]
        
        # Display structure info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Header 1", len(header1s))
        with col2:
            st.metric("Header 2", len(header2s))
        with col3:
            st.metric("Header 3", len(header3s))
        with col4:
            st.metric("Paragraphs", len(paragraphs))
        
        # Show structure preview
        if st.checkbox("🔍 Show document structure"):
            for item in structure[:15]:
                if item['type'] == 'header1':
                    st.write(f"# {item['text'][:80]}...")
                elif item['type'] == 'header2':
                    st.write(f"## {item['text'][:80]}...")
                elif item['type'] == 'header3':
                    st.write(f"### {item['text'][:80]}...")
                else:
                    st.write(f"📝 {item['text'][:100]}...")
        
        if st.button("🚀 Create Smart Chunks and Download CSV"):
            # Create chunks with sentence completion
            chunk_settings = {
                'chunk_min': chunk_min,
                'chunk_max': chunk_max,
                'overlap_ratio': overlap_percent / 100
            }
            
            chunks = improved_chunk_text_sentences(
                paragraphs, book_name, author_name, 
                header1s + header2s + header3s,  # All headers as chapter markers
                chunk_settings
            )
            
            df = pd.DataFrame(chunks)
            
            # Show download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Smart Chunks CSV",
                data=csv,
                file_name=f"{book_name}_smart_chunks.csv",
                mime="text/csv"
            )
            
            # Show stats
            st.success(f"✅ Created {len(chunks)} chunks with complete sentences!")
            
            # Show chunk size distribution
            word_counts = [len(chunk['text_chunk'].split()) for chunk in chunks]
            st.write(f"**Chunk sizes:** Min: {min(word_counts)}, Max: {max(word_counts)}, Avg: {sum(word_counts)//len(word_counts)}")
            
            # Show preview
            st.write("**Preview of chunks:**")
            st.dataframe(df.head())
            
    except Exception as e:
        st.error(f"❌ Error parsing file: {str(e)}")

elif uploaded_file:
    st.warning("⚠️ Please enter both book name and author name")

# Show help
with st.expander("ℹ️ How Smart Chunking Works"):
    st.write("""
    **Advanced Features:**
    - **Complete Sentences:** Chunks never cut off mid-sentence
    - **Multi-level Headers:** Detects Header1, Header2, Header3 by font size
    - **Adjustable Font Sizes:** Customize detection thresholds
    - **Smart Overlapping:** 20% overlap with complete sentences only
    - **Chapter Boundaries:** Respects all header levels as boundaries
    
    **Font Size Logic:**
    - Text >= Header1 size → Header 1
    - Text >= Header2 size → Header 2  
    - Text >= Header3 size → Header 3
    - Text <= Body size → Body text
    """)
