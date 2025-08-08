import pandas as pd

def chunk_text(text, min_words=200, max_words=250, overlap=0.2):
    words = text.split()
    chunk_size = max_words
    step = int(chunk_size * (1 - overlap))
    chunks = []

    for i in range(0, len(words), step):
        chunk = words[i:i+chunk_size]
        if len(chunk) >= min_words:
            chunks.append(" ".join(chunk))
    return chunks

def create_csv_data(parsed_content, book_name, author_name, min_words, max_words, overlap):
    csv_rows = []
    current_header = "Introduction"
    body_buffer = []

    for item in parsed_content:
        if item["type"] == "header":
            if body_buffer:
                text_data = " ".join(body_buffer)
                for chunk in chunk_text(text_data, min_words, max_words, overlap):
                    csv_rows.append({
                        "book_name": book_name,
                        "author_name": author_name,
                        "chapter_name": current_header,
                        "text_chunk": chunk
                    })
                body_buffer = []
            current_header = item["text"]
        else:
            body_buffer.append(item["text"])

    if body_buffer:
        text_data = " ".join(body_buffer)
        for chunk in chunk_text(text_data, min_words, max_words, overlap):
            csv_rows.append({
                "book_name": book_name,
                "author_name": author_name,
                "chapter_name": current_header,
                "text_chunk": chunk
            })

    return pd.DataFrame(csv_rows)
