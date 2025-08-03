import streamlit as st
import pandas as pd
from docx import Document
import fitz
import re

st.title("App 1: Chunking with Custom Heading Detection")

uploaded_file = st.file_uploader("Upload DOCX/PDF (10-page batch)", type=["docx", "pdf"])
book_name = st.text_input("Book Name")
author_name = st.text_input("Author Name")

# Custom heading controls
st.subheader("Heading Detection Settings")
col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Heading 1**")
    h1_enabled = st.checkbox("Enable Heading 1", value=True)
    h1_font_size = st.number_input("H1 Font Size", min_value=8, max_value=72, value=12)
    h1_centered = st.checkbox("H1 Centered", value=True)

with col2:
    st.write("**Heading 2**")
    h2_enabled = st.checkbox("Enable Heading 2", value=True)
    h2_font_size = st.number_input("H2 Font Size", min_value=8, max_value=72, value=22)
    h2_centered = st.checkbox("H2 Centered", value=True)

with col3:
    st.write("**Heading 3**")
    h3_enabled = st.checkbox("Enable Heading 3", value=False)
    h3_font_size = st.number_input("H3 Font Size", min_value=8, max_value=72, value=16)
    h3_centered = st.checkbox("H3 Centered", value=False)

# Body text settings
st.write("**Body Text**")
body_font_size = st.number_input("Body Font Size", min_value=8, max_value=72, value=12)

def parse_file_custom(uploaded_file, heading_settings, body_font_size):
    paragraphs = []
    structure = []
    
    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                if not block_text:
                    continue
                
                font_size = block[3] - block[1]
                is_centered = abs(block[0] - block[2]) < 100
                
                # Check against custom heading settings
                detected_heading = None
                for level, settings in heading_settings.items():
                    if not settings['enabled']:
                        continue
                    
                    font_match = abs(font_size - settings['font_size']) <= 2  # Allow 2pt tolerance
                    alignment_match = (is_centered == settings['centered'])
                    
                    if font_match and alignment_match:
                        detected_heading = level
                        break
                
                if detected_heading:
                    structure.append({"type": f"heading_{detected_heading}", "level": detected_heading, "text": block_text})
                else:
                    structure.append({"type": "body", "text": block_text})
                
                paragraphs.append(block_text)
    
    else:  # DOCX
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Check Word heading styles first
            style = para.style.name.lower()
            detected_heading = None
            
            if 'heading 1' in style and heading_settings[1]['enabled']:
                detected_heading = 1
            elif 'heading 2' in style and heading_settings[2]['enabled']:
                detected_heading = 2
            elif 'heading 3' in style and heading_settings[3]['enabled']:
                detected_heading = 3
            else:
                # Custom font-based detection
                runs_with_font = [run for run in para.runs if run.font.size]
                if runs_with_font:
                    font_size = max(run.font.size.pt for run in runs_with_font)
                else:
                    font_size = body_font_size
                
                is_centered = para.alignment == 1
                
                # Check against custom heading settings
                for level, settings in heading_settings.items():
                    if not settings['enabled']:
                        continue
                    
                    font_match = abs(font_size - settings['font_size']) <= 1  # Tighter tolerance for DOCX
                    alignment_match = (is_centered == settings['centered'])
                    
                    if font_match and alignment_match:
                        detected_heading = level
                        break
            
            if detected_heading:
                structure.append({"type": f"heading_{detected_heading}", "level": detected_heading, "text": text})
            else:
                structure.append({"type": "body", "text": text})
            
            paragraphs.append(text)
    
    return paragraphs, structure

def improved_chunk_text_custom(paragraphs, structure, book_name, author_name, chunk_min=200, chunk_max=250, overlap_ratio=0.2):
    results = []
    current_headings = {1: "", 2: "", 3: ""}
    buf = []
    buf_len = 0
    overlap = []
    
    for i, para in enumerate(paragraphs):
        struct_info = structure[i] if i < len(structure) else {"type": "body", "text": para}
        
        # Handle heading detection
        if "heading_" in struct_info["type"]:
            level = struct_info["level"]
            
            # Save current chunk before new heading
            if buf:
                if overlap:
                    buf = overlap + buf
                chapter_name = " > ".join([h for h in current_headings.values() if h])
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": chapter_name,
                    "heading_1": current_headings[1],
                    "heading_2": current_headings[2],
                    "heading_3": current_headings[3],
                    "text_chunk": " ".join(buf)
                })
            
            # Update heading hierarchy
            current_headings[level] = struct_info["text"]
            # Clear lower-level headings
            for lower_level in range(level + 1, 4):
                current_headings[lower_level] = ""
            
            buf = []
            buf_len = 0
            overlap = []
            continue
        
        # Process body text
        words = para.split()
        num_words = len(words)
        
        if num_words > chunk_max:
            # Save current buffer first
            if buf:
                if overlap:
                    buf = overlap + buf
                chapter_name = " > ".join([h for h in current_headings.values() if h])
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": chapter_name,
                    "heading_1": current_headings[1],
                    "heading_2": current_headings[2],
                    "heading_3": current_headings[3],
                    "text_chunk": " ".join(buf)
                })
                buf = []
                buf_len = 0
            
            # This para becomes its own chunk
            chapter_name = " > ".join([h for h in current_headings.values() if h])
            results.append({
                "book_name": book_name,
                "author_name": author_name,
                "chapter_name": chapter_name,
                "heading_1": current_headings[1],
                "heading_2": current_headings[2],
                "heading_3": current_headings[3],
                "text_chunk": para
            })
            
            # Set up overlap for next chunk
            overlap_count = int(chunk_max * overlap_ratio)
            overlap = words[-overlap_count:] if overlap_count > 0 else []
            continue
        
        # Add to buffer
        buf += words
        buf_len += num_words
        
        if buf_len >= chunk_min:
            # Save chunk
            chapter_name = " > ".join([h for h in current_headings.values() if h])
            results.append({
                "book_name": book_name,
                "author_name": author_name,
                "chapter_name": chapter_name,
                "heading_1": current_headings[1],
                "heading_2": current_headings[2],
                "heading_3": current_headings[3],
                "text_chunk": " ".join(buf)
            })
            
            # Set up overlap for next chunk
            overlap_count = int(chunk_max * overlap_ratio)
            overlap = buf[-overlap_count:] if overlap_count > 0 else []
            buf = overlap.copy()
            buf_len = len(buf)
    
    # Save final chunk
    if buf:
        chapter_name = " > ".join([h for h in current_headings.values() if h])
        results.append({
            "book_name": book_name,
            "author_name": author_name,
            "chapter_name": chapter_name,
            "heading_1": current_headings[1],
            "heading_2": current_headings[2],
            "heading_3": current_headings[3],
            "text_chunk": " ".join(buf)
        })
    
    return results

if uploaded_file and book_name and author_name:
    # Prepare heading settings
    heading_settings = {
        1: {"enabled": h1_enabled, "font_size": h1_font_size, "centered": h1_centered},
        2: {"enabled": h2_enabled, "font_size": h2_font_size, "centered": h2_centered},
        3: {"enabled": h3_enabled, "font_size": h3_font_size, "centered": h3_centered}
    }
    
    paragraphs, structure = parse_file_custom(uploaded_file, heading_settings, body_font_size)
    
    # Display detected structure
    st.write("**Detected Structure:**")
    headings_only = [s for s in structure if "heading" in s["type"]]
    if headings_only:
        for heading in headings_only[:15]:  # Show first 15 headings
            indent = "  " * (heading["level"] - 1)
            st.write(f"{indent}• Level {heading['level']}: {heading['text']}")
    else:
        st.warning("No headings detected with current settings. Check font sizes and alignment.")
    
    # Show settings summary
    st.write("**Current Settings:**")
    for level, settings in heading_settings.items():
        if settings['enabled']:
            alignment = "Centered" if settings['centered'] else "Left-aligned"
            st.write(f"• Heading {level}: {settings['font_size']}pt, {alignment}")
    st.write(f"• Body text: {body_font_size}pt")
    
    if st.button("Chunk and Export CSV"):
        chunks = improved_chunk_text_custom(paragraphs, structure, book_name, author_name)
        df = pd.DataFrame(chunks)
        
        # Display preview
        st.write(f"**Generated {len(chunks)} chunks**")
        st.dataframe(df.head())
        
        # Export CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Custom Chunks CSV",
            csv,
            "custom_chunks.csv",
            "text/csv"
        )
