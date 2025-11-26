import PyPDF2
import pdfplumber
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from models.schemas import DocumentMetadata, DocumentType, Quarter
from config.settings import settings
from data_processing.table_metrics import TableMetricsExtractor

class FABDocumentParser:
    def __init__(self):
        self.metric_patterns = {
            "net_profit": [
                r"net profit.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"profit.*?after.*?tax.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"net.*?profit.*?after.*?tax.*?(\d[\d,.]*)",
                r"Profit\s+for\s+the\s+(?:period|year)[^\d]*AED?\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000|M)"
            ],
            "total_assets": [
                r"total assets.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"assets.*?total.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"Total\s+assets[^\d]{0,50}AED?\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000|M)"
            ],
            "total_loans": [
                r"loans.*?advances.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"total loans.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"loans and advances.*?(\d[\d,.]*)",
                r"Total\s+loans[^\d]{0,50}AED?\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000|M)"
            ],
            "total_deposits": [
                r"customer deposits.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"total deposits.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"deposits.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"Customer\s+deposits[^\d]{0,50}AED?\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000|M)"
            ],
            "shareholder_equity": [
                r"shareholder.*?equity.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"total equity.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"equity.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"Total\s+equity[^\d]{0,50}AED?\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000|M)"
            ],
            "net_interest_income": [
                r"net interest income.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)",
                r"interest income.*?net.*?(\d[\d,.]*\s*(?:million|billion|bn|mn|AED)?)"
            ]
        }
        
        # Content type patterns for better chunk classification
        self.content_type_patterns = {
            "financial_data": [
                r"income statement", r"balance sheet", r"cash flow", r"financial position",
                r"profit and loss", r"statement of comprehensive income"
            ],
            "management_commentary": [
                r"management discussion", r"executive summary", r"financial review", 
                r"chief executive", r"board of directors", r"outlook", r"future prospects"
            ],
            "risk_analysis": [
                r"risk management", r"credit risk", r"market risk", r"operational risk",
                r"risk factors", r"challenges", r"mitigation"
            ],
            "business_segments": [
                r"segment information", r"business segments", r"geographical segments",
                r"wholesale banking", r"consumer banking", r"treasury"
            ]
        }

        self.table_metrics_extractor = TableMetricsExtractor()

    def extract_metadata_from_filename(self, filename: str) -> Optional[DocumentMetadata]:
        """Extract metadata from standardized FAB filename"""
        # Check for annual report pattern
        annual_pattern = r"FAB_(\d{4})_Annual_Report\.pdf"
        annual_match = re.match(annual_pattern, filename)
        
        if annual_match:
            year = int(annual_match.group(1))
            print(f" Annual Report detected: {filename}")
            
            return DocumentMetadata(
                year=year,
                quarter=Quarter.ANNUAL,
                document_type=DocumentType.ANNUAL_REPORT,
                document_category="annual_report",
                file_path=filename
            )
        
        # Check for quarterly pattern
        pattern = r"FAB_(\d{4})_(Q[1-4])_(.+)\.pdf"
        match = re.match(pattern, filename)
        
        if match:
            year, quarter, doc_type_str = match.groups()
            
            doc_type_map = {
                "Financial_Statement": DocumentType.FINANCIAL_STATEMENT,
                "Earnings_Presentation": DocumentType.EARNINGS_PRESENTATION, 
                "Results_Call": DocumentType.RESULTS_CALL
            }
            
            document_type = doc_type_map.get(doc_type_str)
            
            if not document_type:
                doc_type_lower = doc_type_str.lower()
                if "financial" in doc_type_lower or "statement" in doc_type_lower:
                    document_type = DocumentType.FINANCIAL_STATEMENT
                elif "earnings" in doc_type_lower or "presentation" in doc_type_lower:
                    document_type = DocumentType.EARNINGS_PRESENTATION
                elif "results" in doc_type_lower or "call" in doc_type_lower:
                    document_type = DocumentType.RESULTS_CALL
                else:
                    document_type = DocumentType.FINANCIAL_STATEMENT
            
            return DocumentMetadata(
                year=int(year),
                quarter=Quarter(quarter),
                document_type=document_type,
                document_category=doc_type_str.lower().replace("_", " "),
                file_path=filename
            )
        
        print(f" Filename pattern mismatch: {filename}")
        return None

    def parse_financial_statement(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse financial statement PDF - ENHANCED TO STORE BOTH METRICS AND TEXT"""
        chunks = []
        metadata = self.extract_metadata_from_filename(Path(file_path).name)
        
        if not metadata:
            print(f" Could not extract metadata from {file_path}")
            metadata = self._create_fallback_metadata(file_path)
            if not metadata:
                return chunks
        
        print(f" Processing {file_path}...")
        print(f"    Metadata: {metadata.year} {metadata.quarter} {metadata.document_type}")
        
        try:
            # STEP 1: Extract ALL text content with enhanced section detection
            print("    Enhanced text extraction with content classification...")
            text_chunks = self._extract_enhanced_text_content(file_path, metadata)
            print(f"    Created {len(text_chunks)} text chunks with content classification")
            chunks.extend(text_chunks)
            
            # STEP 2: Extract tables with metrics
            print("    Table extraction with metric preservation...")
            table_chunks = self._extract_tables_with_metrics(file_path, metadata)
            print(f"    Created {len(table_chunks)} table chunks with metrics")
            chunks.extend(table_chunks)
            
            if not chunks:
                print(f"     No chunks created from {file_path}")
                fallback_chunk = self._create_fallback_chunk(file_path, metadata)
                if fallback_chunk:
                    chunks.append(fallback_chunk)
                    print(f"    Created fallback chunk")
            
        except Exception as e:
            print(f" Error parsing {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            fallback_chunk = self._create_fallback_chunk(file_path, metadata)
            if fallback_chunk:
                chunks.append(fallback_chunk)
        
        print(f"    Final chunks: {len(chunks)}")
        return chunks

    def _extract_enhanced_text_content(self, file_path: str, metadata: DocumentMetadata) -> List[Dict[str, Any]]:
        """Extract text content with enhanced classification and metric preservation"""
        text_chunks = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print(f"    Extracting text from {total_pages} pages...")
                
                current_section = "header"
                current_content_type = "other"
                section_content = ""
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if not text or not text.strip():
                        continue
                    
                    # Enhanced: Identify both section AND content type
                    new_section = self._identify_financial_section(text, page_num + 1)
                    new_content_type = self._identify_content_type(text)
                    
                    # If section or content type changed, save previous section
                    if (new_section != current_section or new_content_type != current_content_type) and section_content:
                        if len(section_content.strip()) > 50:
                            # Extract metrics from this section
                            metrics = self._extract_metrics_from_text_with_context(section_content, page_num, metadata)
                            
                            # Create enhanced chunk with both content and metrics
                            chunk = self._create_enhanced_chunk(
                                section_content, 
                                current_section, 
                                current_content_type,
                                metrics, 
                                metadata, 
                                page_num
                            )
                            text_chunks.append(chunk)
                            print(f"       Section '{current_section}' ({current_content_type}): {len(metrics)} metrics, {len(section_content)} chars")
                        
                        section_content = ""
                        current_section = new_section
                        current_content_type = new_content_type
                    
                    section_content += text + "\n"
                
                # Save the last section
                if section_content.strip():
                    metrics = self._extract_financial_metrics(section_content, total_pages, metadata)
                    chunk = self._create_enhanced_chunk(
                        section_content, 
                        current_section, 
                        current_content_type,
                        metrics, 
                        metadata, 
                        total_pages
                    )
                    text_chunks.append(chunk)
                    print(f"       Final section '{current_section}' ({current_content_type}): {len(metrics)} metrics")
                
        except Exception as e:
            print(f"     Enhanced text extraction failed: {str(e)}")
        
        return text_chunks
    def _extract_metrics_from_text_with_context(self, text: str, page_num: int, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Extract financial metrics with better context awareness"""
        metrics = {}
        
        for metric_name, patterns in self.metric_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    for match in matches:
                        value_str = match.group(1)
                        numeric_value = self._convert_to_numeric(value_str)
                        
                        if numeric_value and numeric_value > 0:
                            # Get context around the match for better validation
                            context_start = max(0, match.start() - 100)
                            context_end = min(len(text), match.end() + 100)
                            context = text[context_start:context_end]
                            
                            # Check if this looks like a valid financial value in context
                            if self._is_valid_financial_context(context, metric_name, numeric_value):
                                metrics[metric_name] = {
                                    "value": numeric_value,
                                    "raw_text": match.group(0),
                                    "page": page_num,
                                    "context": context.replace('\n', ' ')[:200],  # Truncated context
                                    "confidence": 0.8
                                }
                                print(f"       Extracted {metric_name}: {numeric_value:,.0f} from context")
                                break  # Use first valid match
                except Exception as e:
                    continue
        
        return metrics

    def _is_valid_financial_context(self, context: str, metric_name: str, value: float) -> bool:
        """Check if the context suggests this is a valid financial value"""
        context_lower = context.lower()
        
        # Look for financial statement indicators in context
        financial_indicators = [
            "million", "aed", "profit", "income", "assets", "loans", "deposits", "equity",
            "statement", "balance", "financial", "consolidated"
        ]
        
        indicator_count = sum(1 for indicator in financial_indicators if indicator in context_lower)
        
        # If we have multiple financial indicators, it's likely valid
        if indicator_count >= 2:
            return True
        
        # For very small values, require more context
        if value < 100 and indicator_count < 2:
            return False
            
        return True
    def _extract_tables_with_metrics(self, file_path: str, metadata: DocumentMetadata) -> List[Dict[str, Any]]:
        """Extract tables and preserve both table content AND metrics"""
        table_chunks = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    for table_num, table_data in enumerate(tables):
                        if table_data and len(table_data) > 1:
                            # Convert table to readable text
                            table_text = self._table_to_readable_text(table_data)
                            
                            # Extract metrics from table using the dedicated extractor
                            extracted_metrics = self.table_metrics_extractor.extract_metrics_from_table_data(table_data, "financial_table")
                            
                            # Determine content type based on table content
                            content_type = self._classify_table_content(table_data)
                            
                            chunk = {
                                "content": table_text,
                                "metadata": {
                                    **metadata.dict(),
                                    "page_number": page_num + 1,
                                    "section_type": "table",
                                    "content_type": content_type,
                                    "chunk_type": "structured_table",
                                    "table_number": table_num + 1,
                                    "chunk_id": f"{metadata.year}_{metadata.quarter}_table_{page_num + 1}_{table_num + 1}",
                                    "has_metrics": len(extracted_metrics) > 0
                                },
                                "extracted_metrics": extracted_metrics
                            }
                            table_chunks.append(chunk)
                            
                            if extracted_metrics:
                                print(f"       Table {table_num + 1} ({content_type}): {len(extracted_metrics)} metrics")
            
            print(f"       Processed {len(table_chunks)} tables with metrics")
                            
        except Exception as e:
            print(f"        Table extraction failed: {e}")
        
        return table_chunks

    def _create_enhanced_chunk(self, content: str, section_type: str, content_type: str,
                             metrics: Dict, metadata: DocumentMetadata, page_num: int) -> Dict[str, Any]:
        """Create enhanced chunk that stores both content and metrics"""
        return {
            "content": content,
            "metadata": {
                **metadata.dict(),
                "page_number": page_num,
                "section_type": section_type,
                "content_type": content_type,
                "chunk_type": "text_section",
                "metrics_found": list(metrics.keys()),
                "chunk_id": f"{metadata.year}_{metadata.quarter}_{section_type}_{content_type}_{page_num}",
                "has_metrics": len(metrics) > 0
            },
            "extracted_metrics": metrics
        }

    def _identify_content_type(self, text: str) -> str:
        """Identify the type of content for better retrieval"""
        text_lower = text.lower()
        
        for content_type, patterns in self.content_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return content_type
        
        return "other"

    def _classify_table_content(self, table_data: List[List[str]]) -> str:
        """Classify table content type"""
        if not table_data:
            return "other"
        
        # Combine all table text for analysis
        all_text = " ".join([str(cell) for row in table_data for cell in row if cell])
        all_text_lower = all_text.lower()
        
        for content_type, patterns in self.content_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, all_text_lower, re.IGNORECASE):
                    return content_type
        
        return "financial_data"  # Default for financial tables

    def _table_to_readable_text(self, table_data: List[List[str]]) -> str:
        """Convert table data to readable text format"""
        if not table_data:
            return "Empty table"
        
        text_parts = ["FINANCIAL TABLE:"]
        text_parts.append("=" * 40)
        
        # Add headers
        headers = [str(cell) if cell else "" for cell in table_data[0]]
        text_parts.append(" | ".join(headers))
        text_parts.append("-" * 30)
        
        # Add data rows
        for row in table_data[1:]:
            row_cells = [str(cell) if cell else "" for cell in row]
            text_parts.append(" | ".join(row_cells))
        
        return "\n".join(text_parts)



    def _identify_financial_section(self, text: str, page_num: int) -> str:
        """Identify financial statement sections with high accuracy"""
        text_lower = text.lower()
        
        # Financial statement sections
        if any(keyword in text_lower for keyword in ['statement of financial position', 'balance sheet']):
            return "balance_sheet"
        elif any(keyword in text_lower for keyword in ['statement of profit or loss', 'income statement', 'profit and loss']):
            return "income_statement" 
        elif any(keyword in text_lower for keyword in ['statement of comprehensive income']):
            return "comprehensive_income"
        elif any(keyword in text_lower for keyword in ['statement of changes in equity']):
            return "equity_changes"
        elif any(keyword in text_lower for keyword in ['statement of cash flows', 'cash flow']):
            return "cash_flow"
        elif any(keyword in text_lower for keyword in ['notes to the financial statements']):
            return "notes"
        elif any(keyword in text_lower for keyword in ['risk management', 'credit risk', 'market risk']):
            return "risk_management"
        elif any(keyword in text_lower for keyword in ['management discussion', 'executive summary']):
            return "management_commentary"
        elif page_num <= 2:
            return "header"
        else:
            return "other"

    def _extract_financial_metrics(self, text: str, page_num: int, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Extract financial metrics from text using enhanced patterns"""
        metrics = {}
        
        for metric_name, patterns in self.metric_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    for match in matches:
                        value_str = match.group(1)
                        numeric_value = self._convert_to_numeric(value_str)
                        
                        if numeric_value and numeric_value > 0:
                            if self._is_reasonable_value(metric_name, numeric_value):
                                metrics[metric_name] = {
                                    "value": numeric_value,
                                    "raw_text": match.group(0),
                                    "page": page_num,
                                    "confidence": 0.8
                                }
                                break
                except Exception as e:
                    continue
        
        return metrics

    def _convert_to_numeric(self, value_str: str) -> Optional[float]:
        """Convert string financial values to numeric"""
        try:
            cleaned = re.sub(r'[^\d.]', '', value_str)
            if cleaned:
                value = float(cleaned)
                if 'billion' in value_str.lower() or 'bn' in value_str.lower():
                    value *= 1000
                return value
        except ValueError:
            pass
        return None

    def _is_reasonable_value(self, metric: str, value: float) -> bool:
        """Basic validation for financial values"""
        reasonable_ranges = {
            "net_profit": (100, 10000),
            "total_assets": (100000, 2000000),
            "shareholder_equity": (50000, 200000),
            "total_loans": (50000, 500000),
            "total_deposits": (50000, 600000),
            "net_interest_income": (1000, 10000)
        }
        
        if metric in reasonable_ranges:
            min_val, max_val = reasonable_ranges[metric]
            return min_val <= value <= max_val
        
        return True

    def _create_fallback_metadata(self, file_path: str) -> Optional[DocumentMetadata]:
        """Create fallback metadata when filename parsing fails"""
        try:
            filename = Path(file_path).name
            print(f" Creating fallback metadata for: {filename}")
            
            patterns = [
                r"FAB_(\d{4})_(Q[1-4])",
                r"(\d{4})_Q([1-4])",
                r"Q([1-4])_(\d{4})"
            ]
            
            year = 2022
            quarter = Quarter.Q1
            doc_type = DocumentType.FINANCIAL_STATEMENT
            
            for pattern in patterns:
                match = re.search(pattern, filename)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        if groups[0].isdigit() and len(groups[0]) == 4:
                            year = int(groups[0])
                            quarter_str = f"Q{groups[1]}" if not groups[1].startswith('Q') else groups[1]
                        else:
                            year = int(groups[1])
                            quarter_str = f"Q{groups[0]}" if not groups[0].startswith('Q') else groups[0]
                        
                        try:
                            quarter = Quarter(quarter_str)
                        except:
                            pass
                    break
            
            if "earnings" in filename.lower() or "presentation" in filename.lower():
                doc_type = DocumentType.EARNINGS_PRESENTATION
            elif "results" in filename.lower() or "call" in filename.lower():
                doc_type = DocumentType.RESULTS_CALL
            elif "financial" in filename.lower() or "statement" in filename.lower():
                doc_type = DocumentType.FINANCIAL_STATEMENT
            
            return DocumentMetadata(
                year=year,
                quarter=quarter,
                document_type=doc_type,
                document_category="fallback",
                file_path=filename
            )
        except Exception as e:
            print(f" Fallback metadata creation failed: {e}")
            return None

    def _create_fallback_chunk(self, file_path: str, metadata: DocumentMetadata) -> Optional[Dict[str, Any]]:
        """Create a fallback chunk when no content is extracted"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                first_page = pdf_reader.pages[0]
                raw_text = first_page.extract_text() or "No text content available"
                
                return {
                    "content": f"Document: {metadata.document_type.value} {metadata.year} {metadata.quarter.value}\nContent: {raw_text[:500]}...",
                    "metadata": {
                        **metadata.dict(),
                        "page_number": 1,
                        "section_type": "fallback",
                        "content_type": "other",
                        "chunk_type": "fallback",
                        "chunk_id": f"{metadata.year}_{metadata.quarter}_fallback"
                    },
                    "extracted_metrics": {}
                }
        except:
            return None