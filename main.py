import streamlit as st
from parsers import parse_file
from processors import chunk_text, extract_metadata, generate_embeddings
from utils import export_files, schedule_off_peak
import pandas as pd

st.title("Islamic Book Processor App")

# Font size sliders
body_font_threshold = st.slider("Body Font Threshold (pt)", 8, 16, 12)
heading_font_threshold = st.slider("Heading Font Threshold (pt)", 12, 24, 14)

uploaded_file = st.file_uploader("Upload DOCX/PDF (10-page batch)", type=["docx", "pdf"])
if uploaded_file:
    text, structure = parse_file(uploaded_file, body_font_threshold, heading_font_threshold)
    st.text_area("Preview Text with Structure", str(structure[:500]))

    if st.button("Process Chunks and Metadata (Off-Peak: 10PM-6AM IST)"):
        chunks = chunk_text(text, structure)
        df = pd.DataFrame(chunks, columns=["chunk_text"])
        df = extract_metadata(df)
        df = generate_embeddings(df)
        st.write("Processing Complete!")
        st.session_state.df = df

    if 'df' in st.session_state:
        export_files(st.session_state.df)

if st.button("Schedule for Off-Peak"):
    schedule_off_peak()

# Test section for chatbot simulation
st.header("Test Chatbot on Topic")
test_query = st.text_input("Enter query (e.g., patience preventing depression)")
if st.button("Test"):
    # Simple simulation: Search df for matches
    if 'df' in st.session_state:
        results = st.session_state.df[st.session_state.df['chunk_text'].str.contains(test_query, case=False)]
        st.write("Sample Results:", results[['chunk_text', 'themes', 'references']])
