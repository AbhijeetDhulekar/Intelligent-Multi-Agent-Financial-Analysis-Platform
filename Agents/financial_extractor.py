from typing import List, Dict, Any
import re
from models.schemas import FinancialDataPoint, QueryType, DocumentMetadata, FinancialMetric, DocumentType, Quarter
from data_processing.vector_store import FinancialVectorStore
from tools.temporal_reasoning import TemporalReasoningTool

class FinancialDataValidator:
    """Data validation class to ensure financial values are reasonable"""
    def __init__(self):
        # SEPARATE RANGES for table cells vs main financial values
        self.table_cell_ranges = {
            "net_profit": (1, 1000),           # 1M to 1B AED (table cells)
            "total_assets": (1, 10000),        # 1M to 10B AED (table cells)  
            "shareholder_equity": (1, 10000),  # 1M to 10B AED (table cells)
            "total_loans": (1, 10000),         # 1M to 10B AED (table cells)
            "total_deposits": (1, 10000),      # 1M to 10B AED (table cells)
            "net_interest_income": (1, 1000),  # 1M to 1B AED (table cells)
        }
        
        self.main_financial_ranges = {
            "net_profit": (1000, 20000),        # 1B to 20B AED (main financials)
            "total_assets": (400000, 1200000),  # 400B to 1.2T AED (main financials)
            "shareholder_equity": (80000, 120000),  # 80B to 120B AED (main financials)
            "total_loans": (200000, 500000),    # 200B to 500B AED (main financials)
            "total_deposits": (300000, 600000), # 300B to 600B AED (main financials)
            "net_interest_income": (1000, 15000), # 1B to 15B AED (main financials)
        }
        
        # All metrics can have table cell values
        self.all_metrics = list(self.main_financial_ranges.keys())

    def validate_extraction(self, metric: str, value: float, year: int, context: str = "") -> Dict[str, Any]:
        """Validate financial metrics with separate table cell vs main value handling"""
        if metric not in self.main_financial_ranges:
            return {"is_valid": True, "confidence": 0.7}
        
        # FIRST: Check if this is a table cell value (small values)
        if metric in self.table_cell_ranges:
            table_min, table_max = self.table_cell_ranges[metric]
            if table_min <= value <= table_max:
                # This is likely a valid table cell value
                confidence = 0.6  # Medium confidence for table cells
                # Higher confidence for values that make sense as table cells
                if 1 <= value <= 1000:
                    confidence = 0.7
                return {
                    "is_valid": True,
                    "confidence": confidence,
                    "note": f"Table cell value: {value:,.0f} million AED",
                    "value_type": "table_cell"
                }
        
        # SECOND: Check if this is a main financial value
        if metric in self.main_financial_ranges:
            main_min, main_max = self.main_financial_ranges[metric]
            if main_min <= value <= main_max:
                # This is likely a valid main financial value
                # Calculate confidence based on how close to expected median
                median = (main_min + main_max) / 2
                deviation = abs(value - median) / median
                confidence = max(0.7, 1 - deviation)  # Higher base confidence for main values
                return {
                    "is_valid": True,
                    "confidence": round(confidence, 2),
                    "value_type": "main_financial"
                }
        
        # FINAL: Value doesn't fit either range
        return {
            "is_valid": False,
            "confidence": 0.1,
            "issue": f"Value {value:,.0f} million AED doesn't match expected ranges for {metric}",
            "suggestion": "Table cells: 1-1,000M, Main financials: 1,000M+"
        }

class FinancialDataExtractor:
    def __init__(self):
        self.vector_store = FinancialVectorStore()
        self.temporal_tool = TemporalReasoningTool()
    
        # ENHANCED REGEX PATTERNS - FAB SPECIFIC
        self.metric_patterns = {
            "net_profit": [
                # FAB-specific patterns for main financial values
                r"Profit\s+for\s+the\s+(?:period|year)[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Net\s+profit\s+for\s+the\s+(?:period|year)[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Profit\s+after\s+tax[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Look for values in billions specifically
                r"Profit.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)\s*AED",
                r"Net profit.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                # Income Statement profit patterns
                r"Profit\s+for\s+the\s+(?:period|year)[^\d]{0,100}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Net\s+profit\s+for\s+the\s+(?:period|year)[^\d]{0,100}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Profit\s+after\s+tax[^\d]{0,100}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Look for values in billions
                r"Profit.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                # FAB Income Statement patterns
                r"Profit\s+for\s+the\s+(?:period|year)[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Net\s+profit\s+for\s+the\s+(?:period|year)[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Profit\s+after\s+tax[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Table patterns with AED and units
                r"Profit\s+for\s+the\s+period[\s\S]{1,200}?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Net\s+profit[\s\S]{1,200}?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Fallback patterns
                r"net profit.*?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion)?",
                r"Net profit.*?(\d[\d,.]*\s*million)",
            ],
            "shareholder_equity": [
                r"Total\s+equity[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Shareholders.*?equity.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                # Balance Sheet equity patterns
                r"Total\s+equity[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Shareholders['\s]*equity[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)", 
                r"Equity[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total\s+shareholders['\s]*equity[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Table context
                r"Equity[\s\S]{1,200}?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Fallback patterns
                r"Equity.*?AED\s*(?:million|'000).*?\n\s*([\d,]+(?:\.\d+)?)",
                r"equity.*?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion)?",
            ],
            "total_assets": [
                r"Total\s+assets[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total assets.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)\s*AED",
                r"Total\s+assets[^\d]{0,100}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total\s+assets.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                r"Total\s+assets[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Assets\s+total[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total\s+assets[\s\S]{1,200}?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Fallback patterns
                r"total assets.*?([\d,]+(?:\.\d+)?)\s*trillion",
                r"Total assets.*?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion|trillion)?",
            ],
            "total_loans": [
                r"Total\s+loans[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Loans and advances.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                r"Loans\s+and\s+advances[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total\s+loans[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Net\s+loans[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Fallback patterns
                r"loans.*?AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion)?",
                r"Loans.*?([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion)",
                r"total loans.*?AED\s*([\d,]+(?:\.\d+)?)",
            ],
            "total_deposits": [
                r"Total\s+deposits[^\d]{0,200}AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Customer deposits.*?([\d,]+(?:\.\d+)?)\s*(?:billion|bn)",
                r"Customer\s+deposits[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Total\s+deposits[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                r"Deposits[^\d]*AED\s*([\d,]+(?:\.\d+)?)\s*(?:million|'000)",
                # Fallback patterns
                r"Customer deposits.*?(\d{3}\.\d)\s+(\d{3}\.\d)\s+(\d{3}\.\d)\s+(\d{3}\.\d)\s+(\d{3}\.\d)",
                r"deposits.*?AED\s*([\d,]+(?:\.\d+)?)",
                r"Deposits.*?([\d,]+(?:\.\d+)?)\s*(?:million|bn|billion)",
            ]
        }
        
        # ADD DATA VALIDATOR
        self.validator = FinancialDataValidator()
    
    def extract_data(self, query: str, query_type: QueryType) -> List[FinancialDataPoint]:
        data_points = []
        
        target_periods = self._extract_target_periods(query)
        
        # ENHANCED: Build much stricter search filters
        search_filters = {}
        if target_periods:
            # Extract specific years and quarters for filtering
            year_filters = []
            quarter_filters = []
            
            for period in target_periods:
                if '_' in period:
                    year_str, quarter_str = period.split('_')
                    try:
                        year_filters.append(int(year_str))
                        quarter_filters.append(quarter_str)
                    except ValueError:
                        continue
            
            # Use the first year for filtering (ChromaDB limitation)
            if year_filters:
                search_filters["year"] = year_filters[0]
        
        # ENHANCED: Add period context to search query
        enhanced_query = query
        if target_periods:
            enhanced_query += " " + " ".join(target_periods)
        
        search_results = self.vector_store.search(enhanced_query, search_filters, n_results=20)
        
        print(f" Vector search returned {len(search_results)} results")
        
        # Extract financial metrics from search results
        for i, result in enumerate(search_results):
            print(f"   Processing result {i+1}...")
            try:
                metrics = self._extract_metrics_from_chunk(result, query)
                data_points.extend(metrics)
            except Exception as e:
                print(f"   Failed to extract metrics from chunk {i+1}: {e}")
                continue
        
        print(f" Extracted {len(data_points)} total data points")
        
        # NEW: Validate we have data for required periods
        if target_periods:
            missing_periods = []
            for period in target_periods:
                period_data = self._filter_by_period(data_points, period)
                if not period_data:
                    missing_periods.append(period)
                    print(f" No data found for period: {period}")
            
            if missing_periods:
                print(f" Missing data for periods: {missing_periods}")
        
        return data_points
    
    def _extract_metrics_from_chunk(self, chunk: Dict[str, Any], query: str) -> List[FinancialDataPoint]:
        """Extract metrics with enhanced validation and table support"""
        metrics = []
        content = chunk["content"]
        raw_metadata = chunk["metadata"]
        
        # CLEAN METADATA PROPERLY
        cleaned_metadata = {
            "bank": raw_metadata.get("bank", "FAB"),
            "year": int(raw_metadata.get("year", 2022)),  # Ensure int
            "quarter": Quarter(raw_metadata.get("quarter", "Q1")),
            "document_type": DocumentType(raw_metadata.get("document_type", "financial_statement")),
            "document_category": raw_metadata.get("document_category", ""),
            "file_path": raw_metadata.get("file_path", ""),
            "reporting_date": raw_metadata.get("reporting_date"),
            "release_date": raw_metadata.get("release_date"),
            "pages": self._clean_pages_value(raw_metadata.get("pages")),  # Clean pages
            "currency": raw_metadata.get("currency", "AED"),
            "units": raw_metadata.get("units", "millions")
        }
            # ENHANCED: Generate period based on document type
        if cleaned_metadata['quarter'] == Quarter.ANNUAL:
            period = f"{cleaned_metadata['year']}_Annual"  # Annual period format
        else:
            period = f"{cleaned_metadata['year']}_{cleaned_metadata['quarter'].value}"  # Quarterly format
        
        # NEW: EXTRACT FROM TABLES IF AVAILABLE (from enhanced document parser)
        if chunk.get("extracted_metrics"):
            table_metrics = self._extract_metrics_from_table_data(chunk["extracted_metrics"], cleaned_metadata, raw_metadata)
            metrics.extend(table_metrics)
            print(f"    Extracted {len(table_metrics)} metrics from table structure")
        
        # EXTRACT FROM TEXT USING ENHANCED PATTERNS
        for metric_name, patterns in self.metric_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value_str = match.group(1)
                    numeric_value = self._convert_to_numeric(value_str)
                    
                    # VALIDATE THE EXTRACTED VALUE
                    if numeric_value and numeric_value > 0:  # Only consider positive values
                        validation = self.validator.validate_extraction(
                            metric_name, numeric_value, cleaned_metadata['year']
                        )
                        
                        if validation["is_valid"]:
                            try:
                                data_point = FinancialDataPoint(
                                    metric=FinancialMetric(metric_name),
                                    value=numeric_value,
                                    period=period,  # Use the dynamically generated period
                                    metadata=DocumentMetadata(**cleaned_metadata),
                                    source_page=raw_metadata.get('page_number', 1),
                                    source_section=raw_metadata.get('section_type', 'unknown'),
                                    confidence=validation.get("confidence", 0.7)
                                )
                                metrics.append(data_point)
                                print(f"       Extracted {metric_name}: {numeric_value:,.0f} million AED for {period} (confidence: {validation['confidence']:.2f})")
                            except Exception as e:
                                print(f"       Failed to create data point for {metric_name}: {e}")
                        else:
                            print(f"        Rejected {metric_name}: {numeric_value:,.0f} - {validation.get('issue', 'validation failed')}")
        
        return metrics
    
    def _extract_metrics_from_table_data(self, extracted_metrics: Dict, cleaned_metadata: Dict, raw_metadata: Dict) -> List[FinancialDataPoint]:
        """Extract metrics from structured table data"""
        metrics = []
        
        for metric_name, metric_info in extracted_metrics.items():
            value = metric_info.get("value", 0)
            source = metric_info.get("source", "table")
            confidence = metric_info.get("confidence", 0.8)
            
            # Validate table-extracted values too
            validation = self.validator.validate_extraction(metric_name, value, cleaned_metadata['year'])
            
            if validation["is_valid"]:
                try:
                    # Use validation confidence or table confidence, whichever is higher
                    final_confidence = max(validation.get("confidence", 0.7), confidence)
                    
                    data_point = FinancialDataPoint(
                        metric=FinancialMetric(metric_name),
                        value=value,
                        period=f"{cleaned_metadata['year']}_{cleaned_metadata['quarter'].value}",
                        metadata=DocumentMetadata(**cleaned_metadata),
                        source_page=raw_metadata.get('page_number', 1),
                        source_section=raw_metadata.get('section_type', 'table'),
                        confidence=final_confidence
                    )
                    metrics.append(data_point)
                    print(f"       Table extracted {metric_name}: {value:,.0f} million AED (confidence: {final_confidence:.2f})")
                except Exception as e:
                    print(f"       Failed to create table data point for {metric_name}: {e}")
            else:
                print(f"        Rejected table {metric_name}: {value:,.0f} - {validation.get('issue', 'validation failed')}")
        
        return metrics
    
    def _filter_by_period(self, data_points: List[FinancialDataPoint], target_period: str) -> List[FinancialDataPoint]:
        """Filter data points by specific period"""
        return [dp for dp in data_points if dp.period == target_period]
    
    def _extract_target_periods(self, query: str) -> List[str]:
        """Extract specific periods mentioned in query"""
        import re
        periods = []
        
        # Look for QX YYYY patterns
        period_patterns = [
            r"(Q[1-4])\s*(\d{4})",
            r"(\d{4})\s*(Q[1-4])"
        ]
        
        for pattern in period_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    quarter = match.group(1) if match.group(1).upper().startswith('Q') else match.group(2)
                    year = match.group(2) if match.group(1).upper().startswith('Q') else match.group(1)
                    period = f"{year}_{quarter.upper()}"
                    periods.append(period)
        
        return list(set(periods))  # Remove duplicates

    def _extract_temporal_references(self, query: str) -> List[Dict[str, Any]]:
        """Extract temporal references from query"""
        periods = []
        
        # Look for specific period mentions
        temporal_ref = self.temporal_tool.parse_period_reference(query)
        if temporal_ref:
            periods.append(temporal_ref)
        
        # Look for relative time references
        if 'last' in query.lower() and 'quarter' in query.lower():
            # This would be expanded to handle various relative time expressions
            pass
        
        return periods
    
    def _build_search_filters(self, query: str, temporal_refs: List[Dict], query_type: QueryType) -> Dict[str, Any]:
        """Build filters for vector store search with correct ChromaDB syntax"""
        filters = {}
        
        if temporal_refs:
            # Use the first temporal reference found
            ref = temporal_refs[0]
            filters["year"] = ref["year"]
            filters["quarter"] = ref["quarter"].value
        
        # Adjust filters based on query type - FIXED SYNTAX
        if query_type == QueryType.RISK_ANALYSIS:
            filters["section_type"] = "risk_management"
        elif query_type in [QueryType.CALCULATION, QueryType.TREND_ANALYSIS]:
            filters["section_type"] = "income_statement"
        
        # Convert to proper ChromaDB filter format
        if filters:
            # ChromaDB expects filters in this format
            chroma_filters = {}
            for key, value in filters.items():
                chroma_filters[key] = value
            return chroma_filters
        
        return {}

    def _clean_pages_value(self, pages_value):
        """Clean pages value to handle empty strings and None"""
        if pages_value is None or pages_value == "":
            return None
        if isinstance(pages_value, str) and pages_value.isdigit():
            return int(pages_value)
        return pages_value
    
    def _convert_to_numeric(self, value_str: str) -> float:
        """Convert string financial values to numeric - IMPROVED VERSION"""
        if not value_str:
            return 0.0
            
        try:
            # Remove commas and spaces, keep decimal points and numbers
            cleaned = re.sub(r'[^\d.]', '', value_str.strip())
            if not cleaned:
                return 0.0
                
            value = float(cleaned)
            
            # Handle different units based on context
            if 'trillion' in value_str.lower():
                value *= 1000000  # Convert to millions (1 trillion = 1,000,000 million)
            elif 'billion' in value_str.lower() or 'bn' in value_str.lower():
                value *= 1000  # Convert to millions (1 billion = 1,000 million)
            elif "'000" in value_str:  # Like AED'000 means thousands
                value /= 1000  # Convert to millions (thousands / 1000 = millions)
            # Note: "AED million" means the number is already in millions
            
            return value
            
        except ValueError:
            print(f"  Could not convert value: '{value_str}'")
            return 0.0