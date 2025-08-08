import streamlit as st
import pandas as pd
from parsers import parse_file_advanced
from chunker import improved_chunk_text_sentences

st.title("Advanced Islamic Book Chunking App")

# Font size controls
st.sidebar.header("📏 Font Size Settings")
body_font_size = st.sidebar.slider("Body Text Font Size", 2, 40, 12)
header1_font_size = st.sidebar.slider("Header 1 Font Size", 2, 40, 16)  # Lower default
header2_font_size = st.sidebar.slider("Header 2 Font Size", 2, 40, 14)  # Lower default
header3_font_size = st.sidebar.slider("Header 3 Font Size", 2, 40, 13)  # Lower default

# Header Detection Controls
st.sidebar.header("🎯 Header Detection Settings")
enable_header1 = st.sidebar.checkbox("Enable Header 1 Detection", value=True)
enable_header2 = st.sidebar.checkbox("Enable Header 2 Detection", value=True)
enable_header3 = st.sidebar.checkbox("Enable Header 3 Detection", value=True)
enable_centered = st.sidebar.checkbox("Detect Centered Text as Headers", value=True)

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
            'header3_threshold': header3_font_size,
            'enable_header1': enable_header1,
            'enable_header2': enable_header2,
            'enable_header3': enable_header3,
            'enable_centered': enable_centered
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
        
        # DEBUG: Show all detected headers
        if st.checkbox("🔍 Show ALL detected headers"):
            st.write("**All Headers Found:**")
            for item in structure:
                if item['type'] in ['header1', 'header2', 'header3']:
                    st.write(f"**{item['type'].upper()}:** {item['text']}")
        
        # Show structure preview
        if st.checkbox("📋 Show document structure (first 20 items)"):
            for i, item in enumerate(structure[:20]):
                if item['type'] == 'header1':
                    st.write(f"{i+1}. **H1:** {item['text'][:80]}...")
                elif item['type'] == 'header2':
                    st.write(f"{i+1}. **H2:** {item['text'][:80]}...")
                elif item['type'] == 'header3':
                    st.write(f"{i+1}. **H3:** {item['text'][:80]}...")
                else:
                    st.write(f"{i+1}. Body: {item['text'][:60]}...")
        
        if st.button("🚀 Create Smart Chunks and Download CSV"):
            # Create chunks with sentence completion
            chunk_settings = {
                'chunk_min': chunk_min,
                'chunk_max': chunk_max,
                'overlap_ratio': overlap_percent / 100
            }
            
            # Only use enabled headers as chapter markers
            all_headers = []
            if enable_header1: all_headers.extend(header1s)
            if enable_header2: all_headers.extend(header2s)
            if enable_header3: all_headers.extend(header3s)
            
            st.write(f"**Using {len(all_headers)} headers as chapter boundaries**")
            
            chunks = improved_chunk_text_sentences(
                paragraphs, book_name, author_name, 
                all_headers,  # Only enabled headers as chapter markers
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
            
            # Show unique chapter names found
            unique_chapters = df['chapter_name'].unique()
            st.write(f"**Unique chapters found:** {list(unique_chapters)}")
            
            # Show chunk size distribution
            if chunks:
                word_counts = [len(chunk['text_chunk'].split()) for chunk in chunks]
                st.write(f"**Chunk sizes:** Min: {min(word_counts)}, Max: {max(word_counts)}, Avg: {sum(word_counts)//len(word_counts)}")
                
                # Show preview
                st.write("**Preview of chunks:**")
                st.dataframe(df.head())
            else:
                st.warning("⚠️ No chunks created. Try adjusting your settings.")
            
    except Exception as e:
        st.error(f"❌ Error parsing file: {str(e)}")

elif uploaded_file:
    st.warning("⚠️ Please enter both book name and author name")

# Show help
with st.expander("ℹ️ How to Fix Header Detection"):
    st.write("""
    **If headers aren't being detected:**
    
    1. **Lower the font sizes** - Try Header1=14, Header2=13, Header3=12
    2. **Check the debug info** - Use "Show ALL detected headers" to see what's found
    3. **Look at document structure** - Use "Show document structure" to see classifications
    4. **Enable all detection methods** - Check all the enable boxes
    5. **Try different font thresholds** - Experiment with the sliders
    
    **Common issues:**
    - Headers might be same font size as body text
    - Headers might not be bold or centered
    - Document might use styles instead of font formatting
    """)
