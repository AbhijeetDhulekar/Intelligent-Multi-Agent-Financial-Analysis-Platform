# agents/temporal_analyzer.py
from typing import List, Dict, Any
from models.schemas import FinancialDataPoint
from tools.temporal_reasoning import TemporalReasoningTool

class TemporalAnalysisAgent:
    def __init__(self):
        self.temporal_tool = TemporalReasoningTool()
    
    def analyze(self, data_points: List[FinancialDataPoint], query: str) -> Dict[str, Any]:
        """Perform temporal analysis on financial data"""
        
        # Group data by period
        data_by_period = self._group_data_by_period(data_points)
        
        # Extract temporal references from query
        temporal_refs = self._extract_temporal_references(query)
        
        analysis = {
            "period_comparisons": [],
            "trends": {},
            "seasonal_patterns": [],
            "query_temporal_context": temporal_refs
        }
        
        if len(data_by_period) >= 2:
            # Perform period comparisons
            analysis["period_comparisons"] = self._compare_periods(data_by_period)
            
            # Calculate trends for key metrics
            analysis["trends"] = self._calculate_metric_trends(data_by_period)
        
        return analysis
    
    def _group_data_by_period(self, data_points: List[FinancialDataPoint]) -> Dict[str, Dict[str, float]]:
        """Group data points by period"""
        grouped = {}
        
        for dp in data_points:
            period = dp.period
            if period not in grouped:
                grouped[period] = {}
            grouped[period][dp.metric.value] = dp.value
        
        return grouped
    
    def _extract_temporal_references(self, query: str) -> List[Dict[str, Any]]:
        """Extract temporal context from query"""
        temporal_refs = []
        
        # Use temporal tool to parse explicit references
        primary_ref = self.temporal_tool.parse_period_reference(query)
        if primary_ref:
            temporal_refs.append(primary_ref)
        
        # Handle relative time expressions
        query_lower = query.lower()
        if "last" in query_lower and "quarter" in query_lower:
            # Extract number of quarters
            import re
            match = re.search(r"last\s+(\d+)\s+quarters?", query_lower)
            if match:
                n_quarters = int(match.group(1))
                temporal_refs.append({
                    "type": "relative_quarters",
                    "value": n_quarters,
                    "direction": "past"
                })
        
        return temporal_refs
    
    def _compare_periods(self, data_by_period: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Compare financial metrics across periods"""
        comparisons = []
        periods = sorted(data_by_period.keys())
        
        for i in range(len(periods) - 1):
            period1 = periods[i]
            period2 = periods[i + 1]
            
            comparison = {
                "period1": period1,
                "period2": period2,
                "relationship": self.temporal_tool.compare_periods(
                    {"period": period1}, {"period": period2}
                ),
                "metric_changes": {}
            }
            
            # Calculate changes for common metrics
            common_metrics = set(data_by_period[period1].keys()) & set(data_by_period[period2].keys())
            for metric in common_metrics:
                old_val = data_by_period[period1][metric]
                new_val = data_by_period[period2][metric]
                
                if old_val != 0:
                    percentage_change = ((new_val - old_val) / old_val) * 100
                    comparison["metric_changes"][metric] = {
                        "absolute_change": new_val - old_val,
                        "percentage_change": percentage_change,
                        "trend": "increasing" if percentage_change > 0 else "decreasing"
                    }
            
            comparisons.append(comparison)
        
        return comparisons
    
    def _calculate_metric_trends(self, data_by_period: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Calculate trends for each metric across periods"""
        trends = {}
        periods = sorted(data_by_period.keys())
        
        for metric in set().union(*[set(period_data.keys()) for period_data in data_by_period.values()]):
            values = []
            valid_periods = []
            
            for period in periods:
                if metric in data_by_period[period]:
                    values.append(data_by_period[period][metric])
                    valid_periods.append(period)
            
            if len(values) >= 2:
                # Simple trend analysis
                if values[-1] > values[0]:
                    trend_direction = "upward"
                elif values[-1] < values[0]:
                    trend_direction = "downward"
                else:
                    trend_direction = "stable"
                
                total_change = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
                
                trends[metric] = {
                    "direction": trend_direction,
                    "total_change_percentage": total_change,
                    "periods_analyzed": len(values),
                    "values": values,
                    "periods": valid_periods
                }
        
        return trends