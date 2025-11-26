# agents/validation_agent.py
from typing import List, Dict, Any
from models.schemas import FinancialDataPoint

class ValidationAgent:
    def __init__(self):
        self.validation_rules = {
            "net_profit_margin": lambda x: 0 <= x <= 100,
            "roe": lambda x: -100 <= x <= 100,  # ROE can be negative
            "loan_to_deposit_ratio": lambda x: 0 <= x <= 200,
            "percentage_change": lambda x: -1000 <= x <= 1000,  # Allow large changes
        }
    
    def validate(self, answer: str, data_points: List[FinancialDataPoint], 
                 calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the final answer for accuracy and completeness"""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "confidence_score": 1.0,
            "validation_checks": []
        }
        
        # 1. Validate data points
        data_validation = self._validate_data_points(data_points)
        validation_result["validation_checks"].extend(data_validation["checks"])
        if not data_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(data_validation["errors"])
        
        # 2. Validate calculations
        calc_validation = self._validate_calculations(calculations)
        validation_result["validation_checks"].extend(calc_validation["checks"])
        if not calc_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(calc_validation["errors"])
        
        # 3. Validate answer completeness
        answer_validation = self._validate_answer_completeness(answer, data_points, calculations)
        validation_result["validation_checks"].extend(answer_validation["checks"])
        validation_result["warnings"].extend(answer_validation["warnings"])
        
        # 4. Calculate confidence score
        validation_result["confidence_score"] = self._calculate_confidence_score(
            validation_result["validation_checks"]
        )
        
        return validation_result
    
    def _validate_data_points(self, data_points: List[FinancialDataPoint]) -> Dict[str, Any]:
        """Validate individual data points"""
        validation = {
            "is_valid": True,
            "errors": [],
            "checks": []
        }
        
        if not data_points:
            validation["is_valid"] = False
            validation["errors"].append("No data points extracted")  # String, not list
            validation["checks"].append({
                "check": "data_points_exist",
                "passed": False,
                "message": "No financial data points were extracted"
            })
            return validation
        
        # Check data point quality
        low_confidence_points = [dp for dp in data_points if dp.confidence < 0.5]
        if low_confidence_points:
            validation["warnings"] = [f"{len(low_confidence_points)} data points have low confidence"]
            validation["checks"].append({
                "check": "data_confidence",
                "passed": True,
                "message": f"Found {len(low_confidence_points)} low confidence data points"
            })
        
        # Validate numerical ranges
        for dp in data_points:
            check_name = f"{dp.metric.value}_range"
            if dp.metric.value in self.validation_rules:
                is_valid = self.validation_rules[dp.metric.value](dp.value)
                validation["checks"].append({
                    "check": check_name,
                    "passed": is_valid,
                    "message": f"{dp.metric.value} value {dp.value} is within valid range" if is_valid 
                              else f"{dp.metric.value} value {dp.value} is outside expected range"
                })
                if not is_valid:
                    validation["is_valid"] = False
                    validation["errors"].append(f"Invalid {dp.metric.value}: {dp.value}")
        
        validation["checks"].append({
            "check": "data_points_validation",
            "passed": validation["is_valid"],
            "message": f"Validated {len(data_points)} data points"
        })
        
        return validation
    
    def _validate_calculations(self, calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate calculation results"""
        validation = {
            "is_valid": True,
            "errors": [],
            "checks": []
        }
        
        if not calculations:
            validation["checks"].append({
                "check": "calculations_exist",
                "passed": True,
                "message": "No calculations to validate (may be acceptable for some queries)"
            })
            return validation
        
        for i, calc in enumerate(calculations):
            calc_type = calc.get('calculation_type', 'unknown')
            
            # Validate calculation structure
            if 'error' in calc:
                validation["is_valid"] = False
                validation["errors"].append(f"Calculation {i+1} error: {calc['error']}")
                continue
            
            # Validate numerical results based on calculation type
            if calc_type == 'percentage_change':
                if not self.validation_rules['percentage_change'](calc.get('percentage_change', 0)):
                    validation["is_valid"] = False
                    validation["errors"].append(f"Invalid percentage change: {calc.get('percentage_change')}")
            
            elif calc_type == 'roe':
                if not self.validation_rules['roe'](calc.get('roe_percentage', 0)):
                    validation["is_valid"] = False
                    validation["errors"].append(f"Invalid ROE: {calc.get('roe_percentage')}")
            
            validation["checks"].append({
                "check": f"calculation_{i+1}",
                "passed": 'error' not in calc,
                "message": f"Calculation {calc_type} validated"
            })
        
        return validation
    
    def _validate_answer_completeness(self, answer: str, data_points: List[FinancialDataPoint],
                                    calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that the answer is complete and addresses the query"""
        validation = {
            "warnings": [],
            "checks": []
        }
        
        # Check answer length and structure
        if len(answer.strip()) < 50:
            validation["warnings"].append("Answer appears very brief")
            validation["checks"].append({
                "check": "answer_length",
                "passed": False,
                "message": "Answer is very short"
            })
        else:
            validation["checks"].append({
                "check": "answer_length",
                "passed": True,
                "message": "Answer has sufficient length"
            })
        
        # Check for key financial terms (basic completeness check)
        financial_terms = ["profit", "growth", "ratio", "quarter", "year", "percent"]
        found_terms = [term for term in financial_terms if term in answer.lower()]
        
        if len(found_terms) >= 2:
            validation["checks"].append({
                "check": "financial_terminology",
                "passed": True,
                "message": f"Answer contains relevant financial terms: {found_terms}"
            })
        else:
            validation["warnings"].append("Answer may lack financial context")
            validation["checks"].append({
                "check": "financial_terminology",
                "passed": False,
                "message": "Limited financial terminology in answer"
            })
        
        return validation
    
    def _calculate_confidence_score(self, validation_checks: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score based on validation checks"""
        if not validation_checks:
            return 0.5  # Default medium confidence
        
        passed_checks = [check for check in validation_checks if check.get('passed', False)]
        total_checks = len(validation_checks)
        
        if total_checks == 0:
            return 0.5
        
        base_score = len(passed_checks) / total_checks
        
        # Adjust for critical checks
        critical_checks = [check for check in validation_checks if 'data_points' in check['check']]
        if critical_checks and all(check.get('passed', False) for check in critical_checks):
            base_score = min(1.0, base_score * 1.2)  # Boost for critical checks passing
        
        return round(base_score, 2)