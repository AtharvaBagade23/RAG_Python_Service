from typing import List, Dict, Tuple
import re

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    - Remove excessive whitespace
    - Remove page numbers
    - Remove repeated headers/footers
    - Preserve table structures
    """
    # Remove page numbers (e.g., "- 1 -", "Page 5", etc.)
    text = re.sub(r'^[-–]?\s*\d+\s*[-–]?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove excessive blank lines (keep max 2)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Normalize spaces (but preserve table alignment with tabs)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        # Don't collapse spaces in table rows
        if '|' in line or any(c in line for c in ['─', '│', '┌', '┐', '└', '┘']):
            normalized_lines.append(line)
        else:
            # For regular lines, collapse multiple spaces to single
            normalized_lines.append(re.sub(r'[ \t]+', ' ', line).strip())
    
    text = '\n'.join(normalized_lines)
    return text.strip()

def detect_section_type(text: str) -> str:
    """Detect type of section (syllabus, table, credits, objectives, etc.)"""
    text_lower = text.lower()
    
    # Check for tables
    if any(char in text for char in ['|', '─', '│', '┌']) or text.count('\t') > 3:
        return 'table'
    
    # Check for course headers
    if any(word in text_lower for word in ['course code', 'course name', 'credits', 'core course', 'f.y.', 's.y.', 't.y.']):
        return 'course_header'
    
    # Check for syllabus
    if any(word in text_lower for word in ['syllabus', 'course content', 'topics covered', 'module']):
        return 'syllabus'
    
    # Check for objectives
    if any(word in text_lower for word in ['learning objectives', 'course objectives', 'outcomes', 'learning outcomes']):
        return 'objectives'
    
    # Check for references
    if any(word in text_lower for word in ['textbook', 'reference', 'recommended', 'book', 'publication']):
        return 'references'
    
    # Check for evaluation
    if any(word in text_lower for word in ['evaluation', 'marks', 'assessment', 'grading', 'weightage', 'internal', 'end term']):
        return 'evaluation'
    
    # Check for prerequisites
    if any(word in text_lower for word in ['prerequisite', 'prior knowledge', 'pre-requisite']):
        return 'prerequisites'
    
    # Check for schedule
    if re.search(r'[0-9]{1,2}\s+[A-Z][a-z]+\s+[0-9]{4}', text):
        return 'schedule'
    
    # Check for credits/hours
    if re.search(r'credits?|hrs?\.|hours\s+per\s+week', text_lower):
        return 'credits_info'
    
    return 'general'

def extract_subject_info(text: str) -> Dict[str, str]:
    """Extract subject/course information from text"""
    info = {}
    
    # Extract course code (e.g., CS301, CS-301, 101)
    course_code_match = re.search(r'([A-Z]{2,4}\s*[-]?\s*\d{3,4}|[A-Z]{2,4}\d{3,4})', text)
    if course_code_match:
        info['course_code'] = course_code_match.group(1).strip()
    
    # Extract course name
    course_name_match = re.search(r'(?:Course|Subject)?\s*(?:Title|Name)[:\s]*([^\n]+?)(?:\n|$)', text, re.IGNORECASE)
    if course_name_match:
        info['course_name'] = course_name_match.group(1).strip()
    
    # Extract credits
    credits_match = re.search(r'Credits?\s*[:=]?\s*(\d+(?:\.\d)?)', text, re.IGNORECASE)
    if credits_match:
        info['credits'] = credits_match.group(1).strip()
    
    # Extract semester (Roman numerals or numbers)
    semester_match = re.search(r'(?:Sem|Semester)\s*[:=]?\s*([IVX]+|[1-8])', text, re.IGNORECASE)
    if semester_match:
        info['semester'] = semester_match.group(1).strip().lower()
    
    # Extract teaching hours/week
    hours_match = re.search(r'(\d+)\s*(?:hrs?|hours)\s*/\s*(?:week|wk)', text, re.IGNORECASE)
    if hours_match:
        info['teaching_hours'] = hours_match.group(1).strip()
    
    # Extract course type (Core, Elective, Lab, etc.)
    type_match = re.search(r'(?:Course\s+)?Type[:\s]*([^\n]+?)(?:\n|$)', text, re.IGNORECASE)
    if type_match:
        info['course_type'] = type_match.group(1).strip()
    
    return info

def chunk_by_semantic_sections(
    text: str,
    min_chunk_size: int = 250,
    max_chunk_size: int = 1000
) -> List[Dict[str, any]]:
    """
    Intelligently chunk text by semantic sections
    Handles:
    - Section headers (numbered or lettered)
    - Tables
    - Lists
    - Course information
    
    Args:
        text: Input text
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters
    
    Returns:
        List of chunk dicts with text and metadata
    """
    text = clean_text(text)
    chunks = []
    
    # Split by major section headers (numbered or Roman numeral prefixes)
    # Examples: "1.", "I.", "A.", "SEM-I", "MODULE 1"
    section_pattern = r'^(?:(?:[A-Z][.)])|(?:[IVX]+[.)])|(?:\d+[.)])|(?:SEM-[IVX])|(?:MODULE\s+\d+))\s+.+'
    
    sections = re.split(f'({section_pattern})', text, flags=re.MULTILINE)
    
    current_chunk = ""
    current_section_header = ""
    chunk_count = 0
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        # Check if this is a header
        is_header = bool(re.match(section_pattern, section.strip(), flags=re.MULTILINE))
        
        if is_header:
            # Save current chunk if it exists and meets minimum size
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunk_dict = {
                    'text': current_chunk.strip(),
                    'section': current_section_header.strip() if current_section_header else 'general',
                    'type': detect_section_type(current_chunk),
                    'metadata': extract_subject_info(current_chunk),
                    'size': len(current_chunk),
                    'chunk_num': chunk_count
                }
                chunks.append(chunk_dict)
                chunk_count += 1
            elif current_chunk.strip():
                # For small chunks, try to merge with next section
                if current_chunk:
                    current_chunk = section.strip() + "\n" + current_chunk
                    continue
            
            # Start new section
            current_section_header = section.strip()
            current_chunk = ""
        else:
            # Add to current chunk
            current_chunk += "\n" + section
            
            # If chunk is too large, split it at sentence or table boundaries
            if len(current_chunk) > max_chunk_size:
                # Try to split at double newlines (paragraph boundaries) first
                paragraphs = current_chunk.split('\n\n')
                temp_chunk = ""
                
                for para in paragraphs:
                    if len(temp_chunk) + len(para) > max_chunk_size and temp_chunk.strip():
                        # Save the accumulated chunk
                        chunk_dict = {
                            'text': temp_chunk.strip(),
                            'section': current_section_header.strip() if current_section_header else 'general',
                            'type': detect_section_type(temp_chunk),
                            'metadata': extract_subject_info(temp_chunk),
                            'size': len(temp_chunk),
                            'chunk_num': chunk_count
                        }
                        chunks.append(chunk_dict)
                        chunk_count += 1
                        temp_chunk = para
                    else:
                        if temp_chunk:
                            temp_chunk += "\n\n" + para
                        else:
                            temp_chunk = para
                
                current_chunk = temp_chunk
    
    # Don't forget last chunk
    if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
        chunk_dict = {
            'text': current_chunk.strip(),
            'section': current_section_header.strip() if current_section_header else 'general',
            'type': detect_section_type(current_chunk),
            'metadata': extract_subject_info(current_chunk),
            'size': len(current_chunk),
            'chunk_num': chunk_count
        }
        chunks.append(chunk_dict)
    elif current_chunk.strip() and len(chunks) > 0:
        # Append small remaining chunk to last chunk
        last_chunk = chunks[-1]
        last_chunk['text'] += "\n" + current_chunk.strip()
        last_chunk['size'] += len(current_chunk)
    
    return chunks

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
    use_semantic: bool = True
) -> List[Dict[str, any]]:
    """
    Split text into overlapping chunks with metadata
    
    Args:
        text: Input text
        chunk_size: Characters per chunk (for non-semantic mode)
        overlap: Overlap between chunks
        use_semantic: Use semantic chunking if True, else character-based
    
    Returns:
        List of chunk dicts with text and metadata
    """
    if use_semantic:
        return chunk_by_semantic_sections(text, min_chunk_size=250, max_chunk_size=1000)
    
    # Fallback to character-based chunking
    text = clean_text(text)
    chunks = []
    start = 0
    text_length = len(text)
    chunk_num = 0
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunk_dict = {
                'text': chunk.strip(),
                'section': 'general',
                'type': detect_section_type(chunk),
                'metadata': extract_subject_info(chunk),
                'size': len(chunk),
                'chunk_num': chunk_num
            }
            chunks.append(chunk_dict)
            chunk_num += 1
        
        start += chunk_size - overlap
    
    return chunks

def chunk_by_sentences(
    text: str,
    sentences_per_chunk: int = 5,
    overlap: int = 1
) -> List[Dict[str, any]]:
    """
    Alternative: chunk by sentences
    
    Args:
        text: Input text
        sentences_per_chunk: Number of sentences per chunk
        overlap: Overlap in sentences
    
    Returns:
        List of chunk dicts
    """
    text = clean_text(text)
    
    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    chunk_num = 0
    
    for i in range(0, len(sentences), sentences_per_chunk - overlap):
        chunk_text = ' '.join(sentences[i:i + sentences_per_chunk])
        if chunk_text.strip():
            chunk_dict = {
                'text': chunk_text.strip(),
                'section': 'general',
                'type': detect_section_type(chunk_text),
                'metadata': extract_subject_info(chunk_text),
                'size': len(chunk_text),
                'chunk_num': chunk_num
            }
            chunks.append(chunk_dict)
            chunk_num += 1
    
    return chunks


def chunk_by_semantic_sections(
    text: str,
    min_chunk_size: int = 300,
    max_chunk_size: int = 800
) -> List[Dict[str, any]]:
    """
    Intelligently chunk text by semantic sections
    
    Args:
        text: Input text
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters
    
    Returns:
        List of chunk dicts with text and metadata
    """
    text = clean_text(text)
    chunks = []
    
    # Split by major section headers (lines starting with numbers, Roman numerals, or all caps)
    section_pattern = r'^[A-Z][.)]?\s+[A-Z][^\n]*|^[IVX]+[.)]?\s+[A-Z][^\n]*|^\d+[.)]?\s+[A-Z][^\n]*'
    sections = re.split(f'({section_pattern})', text, flags=re.MULTILINE)
    
    current_chunk = ""
    current_section_header = ""
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        # Check if this is a header
        is_header = bool(re.match(section_pattern, section, flags=re.MULTILINE))
        
        if is_header:
            # Save current chunk if it exists
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunk_dict = {
                    'text': current_chunk.strip(),
                    'section': current_section_header.strip(),
                    'type': detect_section_type(current_chunk),
                    'metadata': extract_subject_info(current_chunk),
                    'size': len(current_chunk)
                }
                chunks.append(chunk_dict)
            
            # Start new section
            current_section_header = section.strip()
            current_chunk = ""
        else:
            # Add to current chunk
            current_chunk += "\n" + section
            
            # If chunk is getting too large, split it
            if len(current_chunk) > max_chunk_size:
                # Try to split at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', current_chunk)
                temp_chunk = ""
                
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > max_chunk_size and temp_chunk.strip():
                        chunk_dict = {
                            'text': temp_chunk.strip(),
                            'section': current_section_header.strip(),
                            'type': detect_section_type(temp_chunk),
                            'metadata': extract_subject_info(temp_chunk),
                            'size': len(temp_chunk)
                        }
                        chunks.append(chunk_dict)
                        temp_chunk = sentence
                    else:
                        temp_chunk += " " + sentence
                
                current_chunk = temp_chunk
    
    # Don't forget last chunk
    if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
        chunk_dict = {
            'text': current_chunk.strip(),
            'section': current_section_header.strip(),
            'type': detect_section_type(current_chunk),
            'metadata': extract_subject_info(current_chunk),
            'size': len(current_chunk)
        }
        chunks.append(chunk_dict)
    
    return chunks

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
    use_semantic: bool = True
) -> List[Dict[str, any]]:
    """
    Split text into overlapping chunks with metadata
    
    Args:
        text: Input text
        chunk_size: Characters per chunk (for non-semantic mode)
        overlap: Overlap between chunks
        use_semantic: Use semantic chunking if True, else character-based
    
    Returns:
        List of chunk dicts with text and metadata
    """
    if use_semantic:
        return chunk_by_semantic_sections(text, min_chunk_size=300, max_chunk_size=800)
    
    # Fallback to character-based chunking
    text = clean_text(text)
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunk_dict = {
                'text': chunk.strip(),
                'section': 'general',
                'type': detect_section_type(chunk),
                'metadata': extract_subject_info(chunk),
                'size': len(chunk)
            }
            chunks.append(chunk_dict)
        
        start += chunk_size - overlap
    
    return chunks

def chunk_by_sentences(
    text: str,
    sentences_per_chunk: int = 5,
    overlap: int = 1
) -> List[Dict[str, any]]:
    """
    Alternative: chunk by sentences
    
    Args:
        text: Input text
        sentences_per_chunk: Number of sentences per chunk
        overlap: Overlap in sentences
    
    Returns:
        List of chunk dicts
    """
    text = clean_text(text)
    
    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    
    for i in range(0, len(sentences), sentences_per_chunk - overlap):
        chunk_text = ' '.join(sentences[i:i + sentences_per_chunk])
        if chunk_text.strip():
            chunk_dict = {
                'text': chunk_text.strip(),
                'section': 'general',
                'type': detect_section_type(chunk_text),
                'metadata': extract_subject_info(chunk_text),
                'size': len(chunk_text)
            }
            chunks.append(chunk_dict)
    
    return chunks
