from typing import List, Dict, Any
from models.schemas import FinancialDataPoint
from tools.calculator import FinancialCalculator

class CalculationAgent:
    def __init__(self):
        self.calculator = FinancialCalculator()
    
    def perform_calculations(self, data_points: List[FinancialDataPoint], query: str) -> List[Dict[str, Any]]:
        """Perform financial calculations based on extracted data and query"""
        calculations = []
        
        # Group data points by period for trend analysis
        data_by_period = self._group_data_by_period(data_points)
        
        # Determine what calculations are needed based on query
        if 'roe' in query.lower() or 'return on equity' in query.lower():
            calculations.extend(self._calculate_roe_trend(data_by_period))
        
        if 'loan-to-deposit' in query.lower() or 'ldr' in query.lower():
            calculations.extend(self._calculate_ldr_trend(data_by_period))
        
        if 'percentage change' in query.lower() or 'growth' in query.lower():
            calculations.extend(self._calculate_growth_rates(data_by_period, query))
        
        if 'trend' in query.lower():
            calculations.extend(self._calculate_comprehensive_trends(data_by_period))
        
        return calculations
    
    def _group_data_by_period(self, data_points: List[FinancialDataPoint]) -> Dict[str, Dict[str, float]]:
        """Group financial data by period"""
        grouped = {}
        
        for dp in data_points:
            period = dp.period
            if period not in grouped:
                grouped[period] = {}
            
            grouped[period][dp.metric] = dp.value
        
        return grouped
    
    def _calculate_roe_trend(self, data_by_period: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Calculate ROE trend across periods"""
        calculations = []
        roe_values = []
        periods = []
        
        for period, metrics in data_by_period.items():
            if 'net_profit' in metrics and 'shareholder_equity' in metrics:
                roe_result = self.calculator.calculate_roe(
                    metrics['net_profit'],
                    metrics['shareholder_equity']
                )
                calculations.append(roe_result)
                roe_values.append(roe_result['roe_percentage'])
                periods.append(period)
        
        # Calculate trend if we have multiple periods
        if len(roe_values) > 1:
            trend_result = self.calculator.calculate_trend(roe_values, periods)
            calculations.append({
                **trend_result,
                "metric": "roe_trend",
                "description": "Return on Equity trend analysis"
            })
        
        return calculations
    
    def _calculate_ldr_trend(self, data_by_period: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Calculate Loan-to-Deposit ratio trend"""
        calculations = []
        ldr_values = []
        periods = []
        
        for period, metrics in data_by_period.items():
            if 'total_loans' in metrics and 'total_deposits' in metrics:
                ldr_result = self.calculator.calculate_loan_to_deposit(
                    metrics['total_loans'],
                    metrics['total_deposits']
                )
                calculations.append(ldr_result)
                ldr_values.append(ldr_result['ldr_percentage'])
                periods.append(period)
        
        if len(ldr_values) > 1:
            trend_result = self.calculator.calculate_trend(ldr_values, periods)
            calculations.append({
                **trend_result,
                "metric": "ldr_trend",
                "description": "Loan-to-Deposit ratio trend analysis"
            })
        
        return calculations
    
    def _calculate_growth_rates(self, data_by_period: Dict[str, Dict[str, float]], query: str) -> List[Dict[str, Any]]:
        """Calculate growth rates for specific metrics"""
        calculations = []
        
        # Extract metric to analyze from query
        target_metric = None
        for metric in ['net_profit', 'total_assets', 'total_loans', 'total_deposits']:
            if metric.replace('_', ' ') in query.lower():
                target_metric = metric
                break
        
        if target_metric:
            values = []
            periods = []
            
            for period, metrics in sorted(data_by_period.items()):
                if target_metric in metrics:
                    values.append(metrics[target_metric])
                    periods.append(period)
            
            if len(values) >= 2:
                # Calculate growth between first and last period for YoY analysis
                if 'year' in query.lower() and len(values) >= 2:
                    growth_result = self.calculator.calculate_percentage_change(values[0], values[-1])
                    calculations.append({
                        **growth_result,
                        "metric": f"{target_metric}_yoy_growth",
                        "periods": [periods[0], periods[-1]]
                    })
                
                # Calculate sequential growth rates
                for i in range(1, len(values)):
                    growth_result = self.calculator.calculate_percentage_change(values[i-1], values[i])
                    calculations.append({
                        **growth_result,
                        "metric": f"{target_metric}_sequential_growth",
                        "periods": [periods[i-1], periods[i]]
                    })
        
        return calculations
    
    def _calculate_comprehensive_trends(self, data_by_period: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Calculate comprehensive trend analysis for multiple metrics"""
        calculations = []
        
        key_metrics = ['net_profit', 'total_assets', 'total_loans', 'total_deposits']
        
        for metric in key_metrics:
            values = []
            periods = []
            
            for period, metrics in sorted(data_by_period.items()):
                if metric in metrics:
                    values.append(metrics[metric])
                    periods.append(period)
            
            if len(values) > 1:
                trend_result = self.calculator.calculate_trend(values, periods)
                calculations.append({
                    **trend_result,
                    "metric": f"{metric}_trend",
                    "description": f"{metric.replace('_', ' ').title()} trend analysis"
                })
        
        return calculations