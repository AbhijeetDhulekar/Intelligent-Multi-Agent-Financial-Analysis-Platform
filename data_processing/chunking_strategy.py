from typing import List, Dict, Any
import re
from models.schemas import DocumentMetadata

class FinancialChunkingStrategy:
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def create_section_chunks(self, parsed_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create intelligent chunks - NOW WITH SEMANTIC SUPPORT"""
        
        # Try semantic chunking first, fallback to basic if needed
        try:
            from data_processing.semantic_chunking import SemanticFinancialChunking
            semantic_chunker = SemanticFinancialChunking(self.max_chunk_size, self.overlap)
            return semantic_chunker.create_semantic_chunks(parsed_docs)
        except Exception as e:
            print(f"  Semantic chunking failed, using basic: {e}")
            return self._create_basic_chunks(parsed_docs)
    
    def _create_basic_chunks(self, parsed_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback basic chunking strategy"""
        chunks = []
        
        for doc in parsed_docs:
            content = doc["content"]
            metadata = doc["metadata"]
            
            # Basic section splitting (your existing code)
            sections = self._split_by_sections(content)
            
            for section_name, section_text in sections.items():
                if len(section_text) > self.max_chunk_size:
                    sub_chunks = self._split_text(section_text)
                    for i, sub_chunk in enumerate(sub_chunks):
                        chunk_metadata = {
                            **metadata,
                            "section_type": section_name,
                            "sub_section": f"{section_name}_{i}",
                            "chunk_id": f"{metadata['chunk_id']}_{section_name}_{i}"
                        }
                        chunks.append({
                            "content": sub_chunk,
                            "metadata": chunk_metadata
                        })
                else:
                    chunk_metadata = {
                        **metadata,
                        "section_type": section_name,
                        "chunk_id": f"{metadata['chunk_id']}_{section_name}"
                    }
                    chunks.append({
                        "content": section_text,
                        "metadata": chunk_metadata
                    })
        
        return chunks
    
    def _split_by_sections(self, text: str) -> Dict[str, str]:
        """Split text into financial sections"""
        sections = {}
        
        # Common financial section patterns
        section_patterns = {
            "income_statement": r"(?:income statement|profit and loss|statement of comprehensive income)",
            "balance_sheet": r"(?:balance sheet|statement of financial position)",
            "cash_flow": r"(?:cash flow statement|statement of cash flows)",
            "notes": r"(?:notes to the financial statements|accounting policies)",
            "risk_management": r"(?:risk management|credit risk|market risk|operational risk)",
            "segment_reporting": r"(?:segment information|business segments)",
            "management_commentary": r"(?:management discussion|executive summary|financial review)"
        }
        
        current_section = "header"
        sections[current_section] = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            section_found = False
            
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line_lower):
                    current_section = section_name
                    sections[current_section] = line + "\n"
                    section_found = True
                    break
            
            if not section_found:
                sections[current_section] += line + "\n"
        
        # Remove empty sections
        sections = {k: v.strip() for k, v in sections.items() if v.strip()}
        
        return sections
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        
        start = 0
        while start < len(words):
            end = start + self.max_chunk_size
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - self.overlap
        
        return chunks