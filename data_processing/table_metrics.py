import re
from typing import List, Dict, Any

class TableMetricsExtractor:
    def __init__(self):
        self.metric_mapping = {
            "net_profit": [
                "net profit", "profit for the", "net income", "profit after"
            ],
            "total_assets": [
                "total assets", "assets total"
            ],
            "total_loans": [
                "total loans", "loans and advances", "net loans"
            ],
            "total_deposits": [
                "total deposits", "customer deposits", "deposits"
            ],
            "shareholder_equity": [
                "total equity", "shareholders equity", "equity"
            ],
            "net_interest_income": [
                "net interest income", "interest income net"
            ]
        }
    
    def extract_metrics_from_table_data(self, table_data: List[List[str]], table_type: str) -> Dict[str, Any]:
        """Extract metrics from table data"""
        metrics = {}
        
        if not table_data or len(table_data) < 2:
            return metrics
        
        print(f"       Analyzing table with {len(table_data)} rows, {len(table_data[0])} columns")
        
        # Try to extract from structured financial tables
        for row_idx, row in enumerate(table_data):
            if not row:
                continue
                
            # Look for descriptive text in first few columns
            row_description = ""
            for col_idx in range(min(3, len(row))):
                if row[col_idx] and isinstance(row[col_idx], str):
                    cell_text = row[col_idx].strip().lower()
                    if len(cell_text) > 3 and not self._is_numeric_only(cell_text):
                        row_description = cell_text
                        break
            
            if not row_description:
                continue
            
            # Look for numeric values in the row
            for col_idx, cell in enumerate(row):
                if cell and self._is_financial_value(cell):
                    numeric_value = self._convert_to_numeric(str(cell))
                    if numeric_value and numeric_value > 0:
                        # Try to match row description to known metrics
                        for metric_name, patterns in self.metric_mapping.items():
                            for pattern in patterns:
                                if pattern in row_description:
                                    metrics[metric_name] = {
                                        "value": numeric_value,
                                        "source": f"table_{table_type}",
                                        "row_description": row_description,
                                        "confidence": 0.7
                                    }
                                    print(f"       Table extracted {metric_name}: {numeric_value:,.0f}")
                                    break
        
        return metrics
    
    def _is_numeric_only(self, text: str) -> bool:
        """Check if text contains only numbers and basic punctuation"""
        return bool(re.match(r'^[\d,.\-()=]+$', text.strip()))
    
    def _is_financial_value(self, cell) -> bool:
        """Check if cell contains a financial value"""
        if not cell:
            return False
        
        cell_str = str(cell).strip()
        
        # Look for patterns like "5,673", "5673", "5.673", etc.
        if re.match(r'^[\d,.\s]+$', cell_str):
            # Remove commas and check if it's a reasonable number
            cleaned = re.sub(r'[^\d.]', '', cell_str)
            if cleaned and '.' in cleaned:
                # Has decimal, likely a financial value
                return True
            elif cleaned and len(cleaned) >= 3:  # At least 3 digits
                return True
        
        return False
    
    def _convert_to_numeric(self, value_str: str) -> float:
        """Convert string to numeric value"""
        try:
            # Remove commas and non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', value_str)
            if cleaned:
                value = float(cleaned)
                
                # Handle units (already in millions based on FAB statements)
                # No conversion needed as FAB reports in millions
                return value
                
        except ValueError:
            pass
        return 0.0