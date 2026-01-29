"""
Syllabus structure parser for automatic metadata extraction.

Extracts:
- Semester (SEM-I to SEM-VIII)
- Course Code (e.g., COM224001)
- Course Name (e.g., Deep Learning)
- Unit (Unit I to Unit V)

from syllabus PDF text.
"""

import re
from typing import Dict, Optional, List, Tuple


class SyllabusParser:
    """Parse syllabus PDF text and extract structured metadata."""
    
    # Regex patterns
    SEMESTER_PATTERN = r'(?:SEM-|Semester:?\s*|^SEMESTER\s+)([IVX]+|[0-9]{1,2})'
    COURSE_CODE_PATTERN = r'([A-Z]{3}\d{6}(?:\d{3})?)'  # e.g., COM224001
    UNIT_PATTERN = r'(?:^|\n)\s*Unit\s+([IVX]+|[0-9]{1,2})\s*[-:]?\s*(.+?)(?=\n\s*Unit\s+[IVX]|\n\n|$)'
    
    @staticmethod
    def extract_semester_from_chunk(chunk_text: str) -> Optional[str]:
        """
        Extract semester from chunk text.
        
        Examples:
        - "SEM-VII" -> "VII"
        - "Semester: 7" -> "7"
        - "SEMESTER VII" -> "VII"
        
        Args:
            chunk_text: Text chunk to search
        
        Returns:
            Semester string (e.g., "VII" or "7") or None
        """
        match = re.search(SyllabusParser.SEMESTER_PATTERN, chunk_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None
    
    @staticmethod
    def extract_course_code_from_chunk(chunk_text: str) -> Optional[str]:
        """
        Extract course code from chunk text.
        
        Examples:
        - "COM224001" -> "COM224001"
        - "COM224001: Deep Learning" -> "COM224001"
        
        Args:
            chunk_text: Text chunk to search
        
        Returns:
            Course code string or None
        """
        match = re.search(SyllabusParser.COURSE_CODE_PATTERN, chunk_text)
        if match:
            return match.group(1).strip()
        return None
    
    @staticmethod
    def extract_course_name_from_chunk(chunk_text: str) -> Optional[str]:
        """
        Extract course name from chunk text.
        
        Pattern: Course code is typically followed by course name
        Examples:
        - "COM224001: Deep Learning" -> "Deep Learning"
        - "COM224001 Deep Learning" -> "Deep Learning"
        
        Args:
            chunk_text: Text chunk to search
        
        Returns:
            Course name string or None
        """
        # Look for pattern: COURSE_CODE: NAME or COURSE_CODE NAME
        # Extract up to 100 chars after code
        pattern = r'([A-Z]{3}\d{6}(?:\d{3})?)\s*[:–-]?\s*([A-Za-z][A-Za-z0-9\s&(),-]*?)(?:\n|$)'
        match = re.search(pattern, chunk_text)
        
        if match:
            name = match.group(2).strip()
            # Clean up: remove trailing numbers, credits info
            name = re.sub(r'\s+\([^)]*\).*$', '', name)  # Remove (L-T-P) etc
            name = re.sub(r'\s*Credits?.*$', '', name, flags=re.IGNORECASE)
            return name if len(name) > 2 else None
        
        return None
    
    @staticmethod
    def extract_unit_from_chunk(chunk_text: str) -> Optional[str]:
        """
        Extract unit number from chunk text.
        
        Examples:
        - "Unit I - Introduction" -> "Unit I"
        - "Unit 1: Basics" -> "Unit 1"
        - "UNIT II" -> "Unit II"
        
        Args:
            chunk_text: Text chunk to search
        
        Returns:
            Unit string (e.g., "Unit I" or "Unit 1") or None
        """
        # Match "Unit X" where X is roman or arabic number
        pattern = r'(?:^|\n)\s*(?:UNIT|Unit)\s+([IVX]+|[0-9]{1,2})'
        match = re.search(pattern, chunk_text, re.MULTILINE | re.IGNORECASE)
        
        if match:
            unit_num = match.group(1).strip()
            # Standardize format: "Unit X"
            return f"Unit {unit_num}"
        
        return None
    
    @staticmethod
    def extract_section_type_from_chunk(chunk_text: str) -> str:
        """
        Extract section type from chunk (course objectives, outcomes, contents, etc).
        
        Args:
            chunk_text: Text chunk to analyze
        
        Returns:
            Section type or "general"
        """
        section_keywords = {
            "objective": ["course objective", "objectives", "aim"],
            "outcome": ["course outcome", "co1", "co2", "learning outcome"],
            "unit": ["unit i", "unit ii", "unit iii", "unit iv", "unit v"],
            "textbook": ["textbook", "text book", "reference", "suggested reading"],
            "evaluation": ["evaluation", "assessment", "examination", "marks", "weightage"],
            "content": ["content", "syllabus", "curriculum"],
        }
        
        text_lower = chunk_text.lower()
        
        for section, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section
        
        return "general"
    
    @staticmethod
    def parse_syllabus_text(full_text: str) -> List[Dict[str, str]]:
        """
        Parse entire syllabus text and track current semester/course/unit.
        
        This returns a list of dict containing extracted context for each logical section.
        
        Args:
            full_text: Complete syllabus PDF text
        
        Returns:
            List of dicts with extracted metadata and corresponding text
        """
        results = []
        
        # Track current metadata as we parse
        current_semester = None
        current_course_code = None
        current_course_name = None
        current_unit = None
        
        # Split by lines to process sequentially
        lines = full_text.split('\n')
        section_buffer = []
        
        for line in lines:
            # Check for semester change
            semester_match = re.search(SyllabusParser.SEMESTER_PATTERN, line, re.IGNORECASE)
            if semester_match:
                current_semester = semester_match.group(1).strip()
                section_buffer = []  # Reset on semester change
            
            # Check for course code + name
            course_match = re.search(
                r'([A-Z]{3}\d{6}(?:\d{3})?)\s*[:–-]?\s*([A-Za-z][A-Za-z0-9\s&(),-]*?)(?:\n|$)',
                line
            )
            if course_match:
                current_course_code = course_match.group(1).strip()
                current_course_name = course_match.group(2).strip()
                # Clean course name
                current_course_name = re.sub(r'\s+\([^)]*\).*$', '', current_course_name)
                current_course_name = re.sub(r'\s*Credits?.*$', '', current_course_name, flags=re.IGNORECASE)
                section_buffer = []
            
            # Check for unit
            unit_match = re.search(
                r'(?:UNIT|Unit)\s+([IVX]+|[0-9]{1,2})',
                line,
                re.IGNORECASE
            )
            if unit_match:
                current_unit = f"Unit {unit_match.group(1).strip()}"
                section_buffer = []
            
            section_buffer.append(line)
        
        return results
    
    @staticmethod
    def enrich_chunk_metadata(chunk_dict: Dict, full_syllabus_text: str = None) -> Dict:
        """
        Enrich a chunk's metadata with extracted semester, course, unit info.
        
        If full_syllabus_text is provided, attempts to find context by searching backwards.
        Otherwise extracts directly from chunk.
        
        Args:
            chunk_dict: Chunk dict with 'text' and 'metadata' keys
            full_syllabus_text: Optional full syllabus text for context
        
        Returns:
            Enhanced chunk dict
        """
        chunk_text = chunk_dict.get('text', '')
        
        # Try to extract directly from chunk
        semester = SyllabusParser.extract_semester_from_chunk(chunk_text)
        course_code = SyllabusParser.extract_course_code_from_chunk(chunk_text)
        course_name = SyllabusParser.extract_course_name_from_chunk(chunk_text)
        unit = SyllabusParser.extract_unit_from_chunk(chunk_text)
        section_type = SyllabusParser.extract_section_type_from_chunk(chunk_text)
        
        # Update metadata
        if not chunk_dict.get('metadata'):
            chunk_dict['metadata'] = {}
        
        if semester:
            chunk_dict['metadata']['semester'] = semester
        if course_code:
            chunk_dict['metadata']['course_code'] = course_code
        if course_name:
            chunk_dict['metadata']['course_name'] = course_name
        if unit:
            chunk_dict['metadata']['unit'] = unit
        if section_type:
            chunk_dict['metadata']['section_type'] = section_type
        
        return chunk_dict
