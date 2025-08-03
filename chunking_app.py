import streamlit as st
import pandas as pd
from docx import Document
import fitz
import re

st.title("App 1: Chunking with Sentence-Boundary Detection")

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

# Body text and chunking settings
st.write("**Body Text & Chunking**")
body_font_size = st.number_input("Body Font Size", min_value=8, max_value=72, value=12)
chunk_min_words = st.number_input("Min Words per Chunk", min_value=100, max_value=400, value=200)
chunk_max_words = st.number_input("Max Words per Chunk", min_value=200, max_value=500, value=250)
overlap_sentences = st.number_input("Overlap Sentences", min_value=1, max_value=5, value=2)

def split_into_sentences(text):
    # Split on sentence endings (., !, ?) followed by space or end
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]

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

def chunk_by_sentences(paragraphs, structure, book_name, author_name, 
                      max_words=250, min_words=200, overlap_sentences=2):
    results = []
    current_headings = {1: "", 2: "", 3: ""}
    sentence_buffer = []
    current_word_count = 0
    
    for i, para in enumerate(paragraphs):
        struct_info = structure[i] if i < len(structure) else {"type": "body", "text": para}
        
        # Handle heading changes
        if "heading_" in struct_info.get("type", ""):
            level = struct_info["level"]
            
            # Save current chunk before heading change
            if sentence_buffer:
                chunk_text = ' '.join(sentence_buffer)
                chapter_name = " > ".join([h for h in current_headings.values() if h])
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": chapter_name,
                    "heading_1": current_headings[1],
                    "heading_2": current_headings[2],
                    "heading_3": current_headings[3],
                    "text_chunk": chunk_text
                })
            
            # Update heading hierarchy
            current_headings[level] = struct_info["text"]
            for lower_level in range(level + 1, 4):
                current_headings[lower_level] = ""
            
            sentence_buffer = []
            current_word_count = 0
            continue
        
        # Process body text by sentences
        para_sentences = split_into_sentences(para)
        
        for sentence in para_sentences:
            sentence_words = len(sentence.split())
            
            # If adding this sentence exceeds max_words and we have min_words
            if (current_word_count + sentence_words > max_words and 
                current_word_count >= min_words):
                
                # Save current chunk
                chunk_text = ' '.join(sentence_buffer)
                chapter_name = " > ".join([h for h in current_headings.values() if h])
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": chapter_name,
                    "heading_1": current_headings[1],
                    "heading_2": current_headings[2],
                    "heading_3": current_headings[3],
                    "text_chunk": chunk_text
                })
                
                # Start new chunk with overlap (last N sentences)
                if len(sentence_buffer) > overlap_sentences:
                    overlap_buffer = sentence_buffer[-overlap_sentences:]
                else:
                    overlap_buffer = sentence_buffer[:]
                
                sentence_buffer = overlap_buffer + [sentence]
                current_word_count = sum(len(s.split()) for s in sentence_buffer)
            else:
                # Add sentence to current chunk
                sentence_buffer.append(sentence)
                current_word_count += sentence_words
    
    # Save final chunk
    if sentence_buffer:
        chunk_text = ' '.join(sentence_buffer)
        chapter_name = " > ".join([h for h in current_headings.values() if h])
        results.append({
            "book_name": book_name,
            "author_name": author_name,
            "chapter_name": chapter_name,
            "heading_1": current_headings[1],
            "heading_2": current_headings[2],
            "heading_3": current_headings[3],
            "text_chunk": chunk_text
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
    st.write(f"• Chunk size: {chunk_min_words}-{chunk_max_words} words")
    st.write(f"• Sentence overlap: {overlap_sentences} sentences")
    
    if st.button("Chunk by Sentences and Export CSV"):
        chunks = chunk_by_sentences(paragraphs, structure, book_name, author_name, 
                                  chunk_max_words, chunk_min_words, overlap_sentences)
        df = pd.DataFrame(chunks)
        
        # Display preview
        st.write(f"**Generated {len(chunks)} sentence-boundary chunks**")
        st.dataframe(df.head())
        
        # Show sample chunk to verify sentence boundaries
        if len(chunks) > 0:
            st.write("**Sample Chunk (check sentence boundaries):**")
            st.write(f"'{chunks[0]['text_chunk']}'")
        
        # Export CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Sentence-Chunked CSV",
            csv,
            "sentence_chunks.csv",
            "text/csv"
        )
