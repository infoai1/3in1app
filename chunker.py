import pandas as pd

def improved_chunk_text(paragraphs, book_name, author_name, chapter_names, chunk_min=200, chunk_max=250, overlap_ratio=0.2):
    results = []
    chap_idx = 0
    in_chapter = chapter_names[chap_idx] if chapter_names else ""
    buf = []  # buffer for current chunk (as a list of para texts)
    buf_len = 0
    overlap = []

    for para in paragraphs:
        # Detect chapter change
        if chap_idx + 1 < len(chapter_names) and para.strip() == chapter_names[chap_idx + 1]:
            # save last chunk before chapter change
            if buf:
                if overlap:
                    buf = overlap + buf
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": in_chapter,
                    "text_chunk": " ".join(buf)
                })
            chap_idx += 1
            in_chapter = chapter_names[chap_idx]
            buf = []
            buf_len = 0
            overlap = []
            continue  # skip the chapter title itself

        words = para.split()
        num_words = len(words)
        if num_words > chunk_max:
            # This entire para is a chunk
            if buf:
                if overlap:
                    buf = overlap + buf
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": in_chapter,
                    "text_chunk": " ".join(buf)
                })
                buf = []
                buf_len = 0
                overlap = []
            results.append({
                "book_name": book_name,
                "author_name": author_name,
                "chapter_name": in_chapter,
                "text_chunk": para
            })
            overlap_count = int(chunk_max * overlap_ratio)
            if overlap_count > 0:
                overlap = words[-overlap_count:]
            else:
                overlap = []
            continue
        buf += words
        buf_len += num_words
        if buf_len >= chunk_min:
            results.append({
                "book_name": book_name,
                "author_name": author_name,
                "chapter_name": in_chapter,
                "text_chunk": " ".join(buf)
            })
            overlap_count = int(chunk_max * overlap_ratio)
            overlap = buf[-overlap_count:] if overlap_count > 0 else []
            buf = overlap.copy()
            buf_len = len(buf)
    if buf:
        results.append({
            "book_name": book_name,
            "author_name": author_name,
            "chapter_name": in_chapter,
            "text_chunk": " ".join(buf)
        })
    return results

# ----- How to run this code -----
# 1. Parse your book file into a list of paragraphs and chapter names.
# Example variables:
book_name = "Your Book Title"
author_name = "Author Name"
# You need paragraphs as a list: [para1, para2, ...] and chapter_names as detected from your DOCX.

# 2. Call the function:
# chunks = improved_chunk_text(paragraphs, book_name, author_name, chapter_names)

# 3. Save to CSV:
# df = pd.DataFrame(chunks)
# df.to_csv("book_clean_chunks.csv", index=False)
