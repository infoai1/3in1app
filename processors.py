import spacy
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import pandas as pd

nlp = spacy.load("en_core_web_sm")
# Manually paste your DeepSeek R1 API key here
api_key = "sk-112d70c0bc7f43edadef276d8251f85e"  # Replace with your copied API key
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
        # spaCy NER for references
        doc = nlp(chunk)
        refs = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "DATE", "EVENT", "WORK_OF_ART"]]  # Includes book quotes
        df.at[i, "references"] = refs
        
        # DeepSeek R1 for themes and question-style summary (using reasoning model)
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",  # Compatible with R1 reasoning tasks
                messages=[{"role": "user", "content": f"Extract themes (inspiring, preventing depression, increasing God realization, importance of patience, faith building, moral lessons) and question-style summary/outlines/contexts for: {chunk}"}]
            )
            extracted = response.choices[0].message.content
        except Exception as e:
            extracted = f"Error: {str(e)}"
        df.at[i, "themes"] = extracted  # E.g., "inspiring: Boosts faith"
        df.at[i, "summary"] = "Question-style: " + extracted
    return df

def generate_embeddings(df):
    df["combined"] = df["chunk_text"] + " " + df["themes"] + " " + df["summary"] + " " + str(df["references"])
    df["embedding"] = df["combined"].apply(lambda x: embedder.encode(x))
    return df
