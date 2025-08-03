import streamlit as st
from parsers import parse_file
from processors import chunk_text, extract_metadata, generate_embeddings
from utils import export_files, schedule_off_peak
import pandas as pd

st.title("Islamic Book Processor App")

uploaded_file = st.file_uploader("Upload DOCX/PDF (10-page batch)", type=["docx", "pdf"])
if uploaded_file:
    text, structure = parse_file(uploaded_file)
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
    schedule_off_peak()  # Queues processing
