from openai import OpenAI
from sentence_transformers import SentenceTransformer
import pandas as pd
import os
import streamlit as st

# Use environment variable for API key (safer than hardcoding)
api_key = os.getenv("DEEPSEEK_API_KEY", "sk-112d70c0bc7f43edadef276d8251f85e")
client = OpenAI(base_url="https://api.deepseek.com/v1", api_key=api_key)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, structure, chunk_size=250):
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    current_structure = ""

    for para in paragraphs:
        for item in structure:
            if item["text"] in para:
                if current_chunk:
                    chunks.append({"text": current_chunk, "structure": current_structure})
                current_structure = item["type"] + ": " + item["text"]
                current_chunk = para
                break
        else:
            if len(current_chunk.split()) + len(para.split()) < chunk_size:
                current_chunk += " " + para
            else:
                chunks.append({"text": current_chunk, "structure": current_structure})
                current_chunk = para

    if current_chunk: 
        chunks.append({"text": current_chunk, "structure": current_structure})
    
    return [chunk["text"] for chunk in chunks]

def extract_metadata(df):
    # Handle different column names
    text_column = None
    if 'text_chunk' in df.columns:
        text_column = 'text_chunk'
    elif 'chunk_text' in df.columns:
        text_column = 'chunk_text'
    else:
        st.error("No text column found in dataframe")
        return df
    
    # Add extracted_data column if it doesn't exist
    if 'extracted_data' not in df.columns:
        df['extracted_data'] = ""
    
    progress_bar = st.progress(0)
    
    for i, chunk in enumerate(df[text_column]):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user", 
                    "content": f"Extract references (Quran verses, Hadith, names, dates, events, quotes from other books), themes (inspiring, preventing depression, increasing God realization, importance of patience, faith building, moral lessons), and question-style summaries/outlines/contexts that clarify aspects, remove misinterpretations, and link to God's creation plan for: {chunk}"
                }]
            )
            extracted = response.choices[0].message.content
        except Exception as e:
            extracted = f"Error: {str(e)}"
        
        df.at[i, "extracted_data"] = extracted
        progress_bar.progress((i + 1) / len(df))
    
    return df

def generate_embeddings(df):
    # Handle different column names
    text_column = 'text_chunk' if 'text_chunk' in df.columns else 'chunk_text'
    
    if 'extracted_data' not in df.columns:
        df['extracted_data'] = ""
    
    df["combined"] = df[text_column] + " " + df["extracted_data"]
    
    progress_bar = st.progress(0)
    embeddings = []
    
    for i, text in enumerate(df["combined"]):
        try:
            embedding = embedder.encode(text).tolist()
            embeddings.append(embedding)
        except Exception as e:
            st.error(f"Error generating embedding for row {i}: {str(e)}")
            embeddings.append([])
        
        progress_bar.progress((i + 1) / len(df))
    
    df["embedding"] = embeddings
    return df
