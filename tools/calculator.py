from typing import Dict, Any, List
import math
from models.schemas import FinancialDataPoint

class FinancialCalculator:
    def __init__(self):
        self.calculation_history = []
    
    def calculate_percentage_change(self, old_value: float, new_value: float) -> Dict[str, Any]:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return {"error": "Cannot calculate percentage change from zero"}
        
        change = new_value - old_value
        percentage = (change / old_value) * 100
        
        result = {
            "old_value": old_value,
            "new_value": new_value,
            "absolute_change": change,
            "percentage_change": percentage,
            "calculation_type": "percentage_change"
        }
        
        self.calculation_history.append(result)
        return result
    
    def calculate_roe(self, net_income: float, shareholder_equity: float) -> Dict[str, Any]:
        """Calculate Return on Equity"""
        if shareholder_equity == 0:
            return {"error": "Cannot calculate ROE with zero equity"}
        
        roe = (net_income / shareholder_equity) * 100
        
        result = {
            "net_income": net_income,
            "shareholder_equity": shareholder_equity,
            "roe_percentage": roe,
            "calculation_type": "roe"
        }
        
        self.calculation_history.append(result)
        return result
    
    def calculate_loan_to_deposit(self, total_loans: float, total_deposits: float) -> Dict[str, Any]:
        """Calculate Loan-to-Deposit Ratio"""
        if total_deposits == 0:
            return {"error": "Cannot calculate LDR with zero deposits"}
        
        ldr = (total_loans / total_deposits) * 100
        
        result = {
            "total_loans": total_loans,
            "total_deposits": total_deposits,
            "ldr_percentage": ldr,
            "calculation_type": "loan_to_deposit_ratio"
        }
        
        self.calculation_history.append(result)
        return result
    
    def calculate_nim(self, net_interest_income: float, earning_assets: float) -> Dict[str, Any]:
        """Calculate Net Interest Margin"""
        if earning_assets == 0:
            return {"error": "Cannot calculate NIM with zero earning assets"}
        
        nim = (net_interest_income / earning_assets) * 100
        
        result = {
            "net_interest_income": net_interest_income,
            "earning_assets": earning_assets,
            "nim_percentage": nim,
            "calculation_type": "net_interest_margin"
        }
        
        self.calculation_history.append(result)
        return result
    
    def calculate_trend(self, values: List[float], periods: List[str]) -> Dict[str, Any]:
        """Calculate trend analysis over multiple periods"""
        if len(values) < 2:
            return {"error": "Need at least 2 values for trend analysis"}
        
        # Calculate basic statistics
        mean = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        min_period = periods[values.index(min_val)]
        max_period = periods[values.index(max_val)]
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(values)):
            growth = ((values[i] - values[i-1]) / values[i-1]) * 100 if values[i-1] != 0 else 0
            growth_rates.append(growth)
        
        result = {
            "periods": periods,
            "values": values,
            "mean": mean,
            "min_value": min_val,
            "min_period": min_period,
            "max_value": max_val,
            "max_period": max_period,
            "growth_rates": growth_rates,
            "average_growth": sum(growth_rates) / len(growth_rates) if growth_rates else 0,
            "calculation_type": "trend_analysis"
        }
        
        self.calculation_history.append(result)
        return result

# Example usage
if __name__ == "__main__":
    calculator = FinancialCalculator()
    
    # Test calculations
    roe_result = calculator.calculate_roe(5120, 110992)  # Net profit 5.12B, Equity 110.992B
    print(f"ROE: {roe_result['roe_percentage']:.2f}%")
    
    trend_result = calculator.calculate_trend(
        [2500, 2800, 3200, 2900, 3500, 5120],
        ["Q2 2021", "Q3 2021", "Q4 2021", "Q1 2022", "Q2 2022", "Q3 2022"]
    )
    print(f"Average growth: {trend_result['average_growth']:.2f}%")