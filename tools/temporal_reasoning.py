from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from models.schemas import Quarter

class TemporalReasoningTool:
    def __init__(self):
        self.quarter_map = {
            "Q1": ("01-01", "03-31"),
            "Q2": ("04-01", "06-30"),
            "Q3": ("07-01", "09-30"),
            "Q4": ("10-01", "12-31"),
            "Annual": ("01-01", "12-31")
        }
    
    def parse_period_reference(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse temporal references from text - ENHANCED FOR ANNUAL"""
        patterns = [
            r"(Q[1-4])\s*(\d{4})",
            r"(\d{4})\s*(Q[1-4])", 
            r"(\w+)\s*quarter\s*(\d{4})",
            r"(\d{4})\s*(\w+)\s*quarter",
            r"(\d{4})\s*annual",  # NEW: Annual pattern
            r"annual\s*(\d{4})",  # NEW: Annual pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Handle annual patterns
                if "annual" in pattern:
                    year_str = groups[0] if groups[0].isdigit() else groups[1]
                    try:
                        year = int(year_str)
                        return {
                            "year": year,
                            "quarter": Quarter.ANNUAL,
                            "period": f"{year}_Annual",
                            "confidence": 0.9
                        }
                    except ValueError:
                        continue
                
                # Handle quarterly patterns (existing code)
                if len(groups) == 2:
                    quarter_str = groups[0] if groups[0].upper().startswith('Q') else groups[1]
                    year_str = groups[1] if groups[0].upper().startswith('Q') else groups[0]
                    
                    try:
                        year = int(year_str)
                        quarter = Quarter(quarter_str.upper())
                        return {
                            "year": year,
                            "quarter": quarter,
                            "period": f"{year}_{quarter}",
                            "confidence": 0.9
                        }
                    except (ValueError, ValueError):
                        continue
        
        return None
    
    def get_previous_periods(self, year: int, quarter: Quarter, n_periods: int = 4) -> List[Dict[str, Any]]:
        """Get list of previous periods for trend analysis"""
        periods = []
        current_year = year
        current_quarter = quarter
        
        quarter_sequence = ["Q4", "Q3", "Q2", "Q1"]
        
        for i in range(n_periods):
            # Find current quarter position
            current_idx = quarter_sequence.index(current_quarter.value)
            
            # Move to previous quarter
            if current_idx == 3:  # Q1 -> go to previous year Q4
                prev_quarter = "Q4"
                prev_year = current_year - 1
            else:
                prev_quarter = quarter_sequence[current_idx + 1]
                prev_year = current_year
            
            periods.append({
                "year": prev_year,
                "quarter": Quarter(prev_quarter),
                "period": f"{prev_year}_{prev_quarter}",
                "sequence": i + 1
            })
            
            current_year = prev_year
            current_quarter = Quarter(prev_quarter)
        
        return periods
    
    def compare_periods(self, period1: Dict[str, Any], period2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two periods and describe the relationship"""
        year1, quarter1 = period1["year"], period1["quarter"]
        year2, quarter2 = period2["year"], period2["quarter"]
        
        if year1 == year2:
            if quarter1 == quarter2:
                relationship = "same period"
            else:
                quarter_diff = self._get_quarter_difference(quarter1, quarter2)
                relationship = f"same year, {abs(quarter_diff)} quarter(s) {'later' if quarter_diff > 0 else 'earlier'}"
        else:
            year_diff = year2 - year1
            total_quarters_diff = year_diff * 4 + self._get_quarter_difference(quarter1, quarter2)
            relationship = f"{abs(year_diff)} year(s) and {abs(total_quarters_diff % 4)} quarter(s) {'later' if total_quarters_diff > 0 else 'earlier'}"
        
        return {
            "period1": period1,
            "period2": period2,
            "relationship": relationship,
            "year_difference": year2 - year1,
            "quarter_difference": self._get_quarter_difference(quarter1, quarter2)
        }
    
    def _get_quarter_difference(self, q1: Quarter, q2: Quarter) -> int:
        """Calculate difference between two quarters"""
        quarter_values = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
        return quarter_values[q2.value] - quarter_values[q1.value]

# Example usage
if __name__ == "__main__":
    temporal_tool = TemporalReasoningTool()
    
    # Parse period reference
    period = temporal_tool.parse_period_reference("Q3 2022")
    print(f"Parsed period: {period}")
    
    # Get previous periods
    previous = temporal_tool.get_previous_periods(2022, Quarter.Q3, 4)
    print("Previous periods:", previous)
    
    # Compare periods
    comparison = temporal_tool.compare_periods(
        {"year": 2022, "quarter": Quarter.Q1},
        {"year": 2023, "quarter": Quarter.Q1}
    )
    print("Period comparison:", comparison)