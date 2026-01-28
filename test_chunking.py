"""
Test script to verify chunking on Computer_2022_Syllabus.pdf
"""
import sys
sys.path.insert(0, r'c:\Users\ADMIN\Desktop\RAG_Python_Service')
sys.stdout.reconfigure(encoding='utf-8')

from app.services.pdf_service import PDFService
from app.utils.chunking import chunk_text, clean_text
import json

# Test with the provided PDF
pdf_path = r'c:\Users\ADMIN\Downloads\Computer_2022_Syllabus.pdf'

try:
    # Read PDF
    pdf_service = PDFService()
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print("[OK] PDF loaded successfully")
    print(f"[PDF] File size: {len(pdf_bytes) / 1024 / 1024:.2f} MB")
    
    # Extract text
    text = pdf_service.extract_text(pdf_bytes)
    print(f"[OK] Text extracted: {len(text)} characters")
    print(f"[SAMPLE] First 500 characters:\n{text[:500]}\n")
    
    # Chunk text semantically
    chunks = chunk_text(text, use_semantic=True)
    print(f"[OK] Created {len(chunks)} semantic chunks")
    
    # Analyze chunks
    total_size = sum(c['size'] for c in chunks)
    print(f"\n[STATS] Chunk Statistics:")
    print(f"  - Total characters: {total_size}")
    print(f"  - Average chunk size: {total_size // len(chunks) if chunks else 0}")
    print(f"  - Min chunk size: {min(c['size'] for c in chunks) if chunks else 0}")
    print(f"  - Max chunk size: {max(c['size'] for c in chunks) if chunks else 0}")
    
    # Analyze chunk types
    type_counts = {}
    section_counts = {}
    for chunk in chunks:
        chunk_type = chunk['type']
        section = chunk['section']
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        section_counts[section] = section_counts.get(section, 0) + 1
    
    print(f"\n[TYPES] Chunk Types Distribution:")
    for chunk_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {chunk_type}: {count} chunks")
    
    print(f"\n[SECTIONS] Sections Found:")
    for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {section[:50]}...: {count} chunks" if len(section) > 50 else f"  - {section}: {count} chunks")
    
    # Show sample chunks
    print(f"\n[SAMPLES] Sample Chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Section: {chunk['section']}")
        print(f"Type: {chunk['type']}")
        print(f"Size: {chunk['size']} chars")
        if chunk.get('metadata'):
            print(f"Metadata: {json.dumps(chunk['metadata'], indent=4)}")
        print(f"Text: {chunk['text'][:200]}...")
    
    # Metadata analysis
    all_metadata = {}
    for chunk in chunks:
        if chunk.get('metadata'):
            all_metadata.update(chunk['metadata'])
    
    if all_metadata:
        print(f"\n[METADATA] Extracted Metadata:")
        for key, value in all_metadata.items():
            print(f"  - {key}: {value}")
    
    print("\n[SUCCESS] Chunking test completed successfully!")
    
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
