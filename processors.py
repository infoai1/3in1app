from openai import OpenAI
from sentence_transformers import SentenceTransformer
import pandas as pd

# Manually paste your DeepSeek R1 API key here
api_key = "paste_your_deepseek_r1_api_key_here"  # Replace this text with your actual API key
client = OpenAI(base_url="https://api.deepseek.com/v1", api_key=api_key)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, structure, chunk_size=250):
    paragraphs = text.split("\n\n")  # Basic split
    chunks = []
    current_chunk = ""
    current_structure = ""  # Track heading
    for para in paragraphs:
        # Respect structure: Start new chunk on chapter/subchapter change
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
    if current_chunk: chunks.append({"text": current_chunk, "structure": current_structure})
    return [chunk["text"] for chunk in chunks]  # Return list; structure in metadata later

def extract_metadata(df):
    for i, chunk in enumerate(df["chunk_text"]):
        # DeepSeek prompt for references, themes, summaries, outlines, contexts
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",  # Compatible with R1 reasoning model
                messages=[{"role": "user", "content": f"Extract references (Quran verses, Hadith, names, dates, events, quotes from other books), themes (inspiring, preventing depression, increasing God realization, importance of patience, faith building, moral lessons), and question-style summaries/outlines/contexts that clarify aspects, remove misinterpretations, and link to God's creation plan for: {chunk}"}]
            )
            extracted = response.choices[0].message.content
        except Exception as e:
            extracted = f"Error: {str(e)}"
        df.at[i, "extracted_data"] = extracted  # All in one field; parse if needed (e.g., split into refs/themes/summary)
    return df

def generate_embeddings(df):
    df["combined"] = df["chunk_text"] + " " + df["extracted_data"]
    df["embedding"] = df["combined"].apply(lambda x: embedder.encode(x))
    return df
