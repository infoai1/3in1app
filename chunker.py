import pandas as pd
import re

def improved_chunk_text_sentences(paragraphs, book_name, author_name, chapter_names, settings):
    """
    Advanced chunking with complete sentences and smart overlapping
    """
    results = []
    chunk_min = settings['chunk_min']
    chunk_max = settings['chunk_max'] 
    overlap_ratio = settings['overlap_ratio']
    
    chap_idx = 0
    in_chapter = chapter_names[chap_idx] if chapter_names else "Introduction"
    
    current_text = ""
    overlap_sentences = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Improved chapter detection - check if paragraph matches any chapter name
        chapter_found = False
        for i, chapter in enumerate(chapter_names):
            # Exact match or partial match for long chapters
            if (para == chapter or 
                (len(chapter) > 20 and para in chapter) or
                (len(para) > 20 and chapter in para)):
                
                # Save current chunk before chapter change
                if current_text:
                    if overlap_sentences:
                        final_text = " ".join(overlap_sentences) + " " + current_text
                    else:
                        final_text = current_text
                        
                    results.append({
                        "book_name": book_name,
                        "author_name": author_name,
                        "chapter_name": in_chapter,
                        "text_chunk": final_text.strip()
                    })
                
                chap_idx = i
                in_chapter = chapter
                current_text = ""
                overlap_sentences = []
                chapter_found = True
                break
        
        if chapter_found:
            continue
        
        # Split paragraph into sentences
        sentences = split_into_sentences(para)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Calculate word counts
            current_words = len(current_text.split()) if current_text else 0
            sentence_words = len(sentence.split())
            total_words = current_words + sentence_words
            
            # Check if adding this sentence exceeds max chunk size
            if total_words > chunk_max and current_words >= chunk_min:
                # Save current chunk
                if overlap_sentences:
                    final_text = " ".join(overlap_sentences) + " " + current_text
                else:
                    final_text = current_text
                    
                results.append({
                    "book_name": book_name,
                    "author_name": author_name,
                    "chapter_name": in_chapter,
                    "text_chunk": final_text.strip()
                })
                
                # Calculate overlap sentences
                all_sentences = split_into_sentences(current_text)
                overlap_count = max(1, int(len(all_sentences) * overlap_ratio))
                overlap_sentences = all_sentences[-overlap_count:] if all_sentences else []
                
                # Start new chunk with current sentence
                current_text = sentence
                
            else:
                # Add sentence to current chunk
                if current_text:
                    current_text += " " + sentence
                else:
                    current_text = sentence
    
    # Save final chunk
    if current_text:
        if overlap_sentences:
            final_text = " ".join(overlap_sentences) + " " + current_text
        else:
            final_text = current_text
            
        results.append({
            "book_name": book_name,
            "author_name": author_name,
            "chapter_name": in_chapter,
            "text_chunk": final_text.strip()
        })

    return results

def split_into_sentences(text):
    """Split text into sentences, handling Islamic text properly"""
    sentence_endings = r'[.!?؟۔]'
    
    sentences = re.split(f'({sentence_endings})', text)
    
    complete_sentences = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and re.match(sentence_endings, sentences[i + 1]):
            complete_sentences.append((sentences[i] + sentences[i + 1]).strip())
            i += 2
        else:
            if sentences[i].strip():
                complete_sentences.append(sentences[i].strip())
            i += 1
    
    complete_sentences = [s for s in complete_sentences if len(s.split()) > 3]
    
    return complete_sentences

# Keep old function for backward compatibility
def improved_chunk_text(paragraphs, book_name, author_name, chapter_names, chunk_min=200, chunk_max=250, overlap_ratio=0.2):
    settings = {
        'chunk_min': chunk_min,
        'chunk_max': chunk_max,
        'overlap_ratio': overlap_ratio
    }
    return improved_chunk_text_sentences(paragraphs, book_name, author_name, chapter_names, settings)
