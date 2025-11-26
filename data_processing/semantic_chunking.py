from typing import List, Dict, Any, Optional
import re
from pathlib import Path

class SemanticFinancialChunking:
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        # Financial section patterns for FAB documents
        self.section_patterns = {
            "income_statement": [
                r"income statement",
                r"profit and loss", 
                r"statement of comprehensive income",
                r"consolidated income statement"
            ],
            "balance_sheet": [
                r"balance sheet",
                r"statement of financial position",
                r"consolidated balance sheet"
            ],
            "cash_flow": [
                r"cash flow statement",
                r"statement of cash flows",
                r"consolidated cash flow"
            ],
            "risk_management": [
                r"risk management",
                r"credit risk",
                r"market risk", 
                r"operational risk",
                r"risk factors"
            ],
            "management_commentary": [
                r"management discussion",
                r"executive summary",
                r"financial review",
                r"chief executive",
                r"board of directors"
            ],
            "notes_accounting": [
                r"notes to the financial",
                r"accounting policies",
                r"significant accounting"
            ]
        }
    
    def create_semantic_chunks(self, parsed_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create intelligent chunks that preserve financial context - ENHANCED LOGGING"""
        all_chunks = []
        
        table_chunk_count = 0
        text_chunk_count = 0
        metric_chunk_count = 0
        
        for doc_idx, doc in enumerate(parsed_docs):
            content = doc["content"]
            metadata = doc["metadata"]
            
            print(f"    Processing document {doc_idx + 1}...")
            
            # 1. Extract and preserve complete tables
            if doc.get("tables"):
                table_chunks = self._chunk_complete_tables(doc["tables"], metadata)
                all_chunks.extend(table_chunks)
                table_chunk_count += len(table_chunks)
                print(f"       Created {len(table_chunks)} table chunks")
            
            # 2. Section-based chunks with hierarchy
            section_chunks = self._chunk_financial_sections(content, metadata)
            all_chunks.extend(section_chunks)
            text_chunk_count += len(section_chunks)
            print(f"       Created {len(section_chunks)} text section chunks")
            
            # 3. Metric-focused chunks for key financials
            if doc.get("extracted_metrics"):
                metric_chunks = self._chunk_key_metrics(doc["extracted_metrics"], metadata)
                all_chunks.extend(metric_chunks)
                metric_chunk_count += len(metric_chunks)
                print(f"       Created {len(metric_chunks)} metric chunks")
        
        print(f"    Chunk Summary: {table_chunk_count} tables, {text_chunk_count} text, {metric_chunk_count} metrics")
        print(f" Created {len(all_chunks)} total semantic chunks")
        return all_chunks
    
    def _chunk_complete_tables(self, tables: List[Dict], metadata: Dict) -> List[Dict[str, Any]]:
        """Keep financial tables intact as single chunks"""
        table_chunks = []
        
        for i, table in enumerate(tables):
            table_data = table.get("data", [])
            table_text = table.get("text", "")
            
            # Convert table to readable format
            formatted_table = self._table_to_markdown(table_data)
            
            # Determine table type
            table_type = self._classify_table_type(table_data, table_text)
            
            # Extract metrics from this table
            extracted_metrics = self._extract_metrics_from_table_data(table_data, table_type)
            
            chunk = {
                "content": f"## FINANCIAL TABLE: {table_type.replace('_', ' ').title()}\n\n{formatted_table}",
                "metadata": {
                    **metadata,
                    "chunk_type": "financial_table",
                    "table_type": table_type,
                    "table_number": i + 1,
                    "section_type": table_type,
                    "chunk_id": f"{metadata.get('chunk_id', 'unknown')}_table_{i+1}",
                    "extracted_metrics": list(extracted_metrics.keys())
                },
                "extracted_metrics": extracted_metrics
            }
            table_chunks.append(chunk)
        
        return table_chunks
    
    def _chunk_financial_sections(self, content: str, metadata: Dict) -> List[Dict[str, Any]]:
        """Create section-based chunks with hierarchy preservation"""
        sections = self._split_into_semantic_sections(content)
        chunks = []
        
        for section_name, section_content in sections.items():
            # Skip empty sections
            if not section_content.strip():
                continue
            
            # If section is large, break it into smaller chunks but preserve context
            if len(section_content) > self.max_chunk_size:
                sub_chunks = self._split_section_intelligently(section_content, section_name)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk = {
                        "content": sub_chunk,
                        "metadata": {
                            **metadata,
                            "chunk_type": "text_section",
                            "section_type": section_name,
                            "sub_section": f"{section_name}_{i+1}",
                            "chunk_id": f"{metadata.get('chunk_id', 'unknown')}_{section_name}_{i+1}",
                            "hierarchy_level": self._get_hierarchy_level(section_name)
                        }
                    }
                    chunks.append(chunk)
            else:
                # Small section - keep as single chunk
                chunk = {
                    "content": section_content,
                    "metadata": {
                        **metadata,
                        "chunk_type": "text_section", 
                        "section_type": section_name,
                        "chunk_id": f"{metadata.get('chunk_id', 'unknown')}_{section_name}",
                        "hierarchy_level": self._get_hierarchy_level(section_name)
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_key_metrics(self, extracted_metrics: Dict, metadata: Dict) -> List[Dict[str, Any]]:
        """Create dedicated chunks for important financial metrics"""
        metric_chunks = []
        
        for metric_name, metric_info in extracted_metrics.items():
            value = metric_info.get("value", 0)
            source = metric_info.get("source", "unknown")
            confidence = metric_info.get("confidence", 0.5)
            
            # Only create chunks for high-confidence metrics
            if confidence > 0.6:
                chunk_content = self._create_metric_chunk_content(metric_name, value, source, metadata)
                
                chunk = {
                    "content": chunk_content,
                    "metadata": {
                        **metadata,
                        "chunk_type": "financial_metric",
                        "metric_name": metric_name,
                        "metric_value": value,
                        "metric_source": source,
                        "metric_confidence": confidence,
                        "chunk_id": f"{metadata.get('chunk_id', 'unknown')}_metric_{metric_name}",
                        "section_type": "key_metrics"
                    }
                }
                metric_chunks.append(chunk)
        
        return metric_chunks
    
    def _split_into_semantic_sections(self, content: str) -> Dict[str, str]:
        """Split content into meaningful financial sections"""
        sections = {}
        current_section = "header"
        sections[current_section] = ""
        
        lines = content.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            section_found = False
            
            # Check if this line starts a new section
            for section_name, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        current_section = section_name
                        sections[current_section] = line + "\n"
                        section_found = True
                        break
                if section_found:
                    break
            
            if not section_found:
                # Continue adding to current section
                sections[current_section] += line + "\n"
        
        # Clean up sections - remove empty ones
        return {k: v.strip() for k, v in sections.items() if v.strip()}
    
    def _split_section_intelligently(self, section_content: str, section_name: str) -> List[str]:
        """Split large sections while preserving financial context"""
        # For financial documents, split by paragraphs first
        paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max size, start new chunk
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we still have chunks that are too large, split by sentences
        refined_chunks = []
        for chunk in chunks:
            if len(chunk) > self.max_chunk_size:
                # Split by sentences for very large chunks
                sentences = re.split(r'[.!?]+', chunk)
                current_sentences = []
                current_length = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if current_length + len(sentence) > self.max_chunk_size and current_sentences:
                        refined_chunks.append('. '.join(current_sentences) + '.')
                        current_sentences = [sentence]
                        current_length = len(sentence)
                    else:
                        current_sentences.append(sentence)
                        current_length += len(sentence)
                
                if current_sentences:
                    refined_chunks.append('. '.join(current_sentences) + '.')
            else:
                refined_chunks.append(chunk)
        
        return refined_chunks
    
    def _table_to_markdown(self, table_data: List[List[str]]) -> str:
        """Convert table data to markdown format for better readability"""
        if not table_data or len(table_data) < 1:
            return "No table data available"
        
        markdown_lines = []
        
        # Header row
        headers = table_data[0]
        markdown_lines.append("| " + " | ".join(str(h) if h else "" for h in headers) + " |")
        markdown_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        
        # Data rows
        for row in table_data[1:]:
            markdown_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
        
        return "\n".join(markdown_lines)
    
    def _classify_table_type(self, table_data: List[List[str]], table_text: str) -> str:
        """Classify the type of financial table"""
        combined_text = table_text.lower()
        
        # Check headers in first row
        if table_data and len(table_data) > 0:
            header_row = " ".join([str(cell).lower() for cell in table_data[0] if cell])
            
            if any(keyword in header_row for keyword in ["revenue", "income", "profit", "expense"]):
                return "income_statement"
            elif any(keyword in header_row for keyword in ["assets", "liabilities", "equity"]):
                return "balance_sheet"
            elif any(keyword in header_row for keyword in ["cash flow", "operating", "investing"]):
                return "cash_flow"
        
        # Fallback to content analysis
        if any(keyword in combined_text for keyword in ["income statement", "profit and loss"]):
            return "income_statement"
        elif any(keyword in combined_text for keyword in ["balance sheet", "financial position"]):
            return "balance_sheet"
        elif any(keyword in combined_text for keyword in ["cash flow"]):
            return "cash_flow"
        else:
            return "financial_table"
    
    def _extract_metrics_from_table_data(self, table_data: List[List[str]], table_type: str) -> Dict[str, Any]:
        """Extract key metrics from table data"""
        metrics = {}
        
        if not table_data or len(table_data) < 2:
            return metrics
        
        headers = [str(cell).lower() if cell else "" for cell in table_data[0]]
        
        # Map headers to metrics based on table type
        header_to_metric = {
            "income_statement": {
                "net profit": "net_profit",
                "profit for the period": "net_profit",
                "total revenue": "total_revenue",
                "total income": "total_income"
            },
            "balance_sheet": {
                "total assets": "total_assets",
                "total equity": "shareholder_equity", 
                "shareholders equity": "shareholder_equity",
                "total loans": "total_loans",
                "customer deposits": "total_deposits"
            }
        }
        
        mapping = header_to_metric.get(table_type, {})
        
        for row in table_data[1:]:
            for i, cell in enumerate(row):
                if i >= len(headers):
                    continue
                    
                cell_value = str(cell) if cell else ""
                header = headers[i]
                
                # Look for numeric values
                if re.search(r'\d[\d,.]*\s*(?:million|AED)', cell_value):
                    numeric_value = self._convert_to_numeric(cell_value)
                    if numeric_value:
                        # Check if this header maps to a known metric
                        for pattern, metric_name in mapping.items():
                            if pattern in header:
                                metrics[metric_name] = {
                                    "value": numeric_value,
                                    "source": f"table_{table_type}",
                                    "confidence": 0.8
                                }
                                break
        
        return metrics
    
    def _get_hierarchy_level(self, section_name: str) -> int:
        """Determine hierarchy level for sections"""
        hierarchy_map = {
            "header": 1,
            "management_commentary": 1,
            "income_statement": 2,
            "balance_sheet": 2, 
            "cash_flow": 2,
            "risk_management": 2,
            "notes_accounting": 3
        }
        return hierarchy_map.get(section_name, 2)
    
    def _create_metric_chunk_content(self, metric_name: str, value: float, source: str, metadata: Dict) -> str:
        """Create content for metric-focused chunks"""
        period = f"{metadata.get('year', '')} {metadata.get('quarter', '')}"
        document_type = metadata.get('document_type', 'financial_statement')
        
        return f"""
KEY FINANCIAL METRIC EXTRACTION:

Metric: {metric_name.replace('_', ' ').title()}
Value: {value:,.0f} million AED
Period: {period}
Source: {source}
Document: {document_type}

This metric was extracted from the official financial statements and represents a key performance indicator for analysis.
"""
    
    def _convert_to_numeric(self, value_str: str) -> Optional[float]:
        """Convert string to numeric value"""
        try:
            # Remove commas and non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', value_str)
            if cleaned:
                return float(cleaned)
        except ValueError:
            pass
        return None