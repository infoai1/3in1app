import re

def improved_chunk_text_sentences(paragraphs, book_name, author_name, chapter_names, settings):
    results = []
    chunk_min = settings['chunk_min']
    chunk_max = settings['chunk_max']
    overlap_ratio = settings['overlap_ratio']
    
    in_chapter = chapter_names[0] if chapter_names else "Unknown"
    current_text = ""
    overlap_sentences = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if this para is a header (simple match)
        if any(para.lower() in ch.lower() or ch.lower() in para.lower() for ch in chapter_names):
            if current_text:
                final_text = " ".join(overlap_sentences) + " " + current_text if overlap_sentences else current_text
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": in_chapter,
                    "text_chunk": final_text.strip()
                })
            in_chapter = para
            current_text = ""
            overlap_sentences = []
            continue
        
        # Add to current chunk (sentence logic as before)
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', para)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            current_words = len(current_text.split())
            sentence_words = len(sentence.split())
            if current_words + sentence_words > chunk_max and current_words >= chunk_min:
                final_text = " ".join(overlap_sentences) + " " + current_text if overlap_sentences else current_text
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": in_chapter,
                    "text_chunk": final_text.strip()
                })
                all_sentences = current_text.split('. ')
                overlap_count = int(len(all_sentences) * overlap_ratio)
                overlap_sentences = all_sentences[-overlap_count:]
                current_text = sentence
            else:
                current_text += " " + sentence
    
    # Final chunk
    if current_text:
        final_text = " ".join(overlap_sentences) + " " + current_text if overlap_sentences else current_text
        results.append({
            "book_name": book_name,
            "author_name": author_name,
            "chapter_name": in_chapter,
            "text_chunk": final_text.strip()
        })

    return results
