# evaluation/metrics.py
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics import precision_score, recall_score
from models.schemas import FinancialDataPoint

class EvaluationMetrics:
    def __init__(self):
        self.metrics_history = []
    
    def calculate_retrieval_metrics(self, retrieved_docs: List[Dict], 
                                  relevant_docs: List[Dict]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 for document retrieval"""
        if not retrieved_docs or not relevant_docs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        # Simple binary relevance calculation
        retrieved_ids = [doc.get('chunk_id', '') for doc in retrieved_docs]
        relevant_ids = [doc.get('chunk_id', '') for doc in relevant_docs]
        
        true_positives = len(set(retrieved_ids) & set(relevant_ids))
        false_positives = len(set(retrieved_ids) - set(relevant_ids))
        false_negatives = len(set(relevant_ids) - set(retrieved_ids))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "retrieved_count": len(retrieved_docs),
            "relevant_count": len(relevant_docs)
        }
    
    def calculate_citation_quality(self, data_points: List[FinancialDataPoint]) -> Dict[str, float]:
        """Calculate citation quality metrics"""
        if not data_points:
            return {
                "citation_rate": 0.0,
                "average_confidence": 0.0,
                "well_cited_percentage": 0.0
            }
        
        total_points = len(data_points)
        points_with_sources = sum(1 for dp in data_points if dp.metadata and dp.source_page)
        
        # Calculate average confidence
        avg_confidence = sum(dp.confidence for dp in data_points) / total_points
        
        # Points with good confidence and sources
        well_cited = sum(1 for dp in data_points if dp.confidence > 0.7 and dp.metadata and dp.source_page)
        
        return {
            "citation_rate": round(points_with_sources / total_points, 3),
            "average_confidence": round(avg_confidence, 3),
            "well_cited_percentage": round(well_cited / total_points, 3),
            "total_data_points": total_points
        }
    
    def calculate_financial_accuracy(self, extracted_values: List[float], 
                                   ground_truth_values: List[float]) -> Dict[str, float]:
        """Calculate accuracy of financial figures"""
        if not extracted_values or not ground_truth_values:
            return {"exact_match_rate": 0.0, "relative_error": 1.0}
        
        # Exact match within tolerance (for floating point)
        exact_matches = 0
        relative_errors = []
        
        for extracted, truth in zip(extracted_values, ground_truth_values):
            if abs(extracted - truth) < 0.01:  # 1% tolerance
                exact_matches += 1
            
            if truth != 0:
                relative_error = abs(extracted - truth) / abs(truth)
                relative_errors.append(relative_error)
        
        exact_match_rate = exact_matches / len(extracted_values)
        avg_relative_error = sum(relative_errors) / len(relative_errors) if relative_errors else 1.0
        
        return {
            "exact_match_rate": round(exact_match_rate, 3),
            "average_relative_error": round(avg_relative_error, 3),
            "max_relative_error": round(max(relative_errors), 3) if relative_errors else 1.0
        }
    
    def calculate_response_quality(self, response: Dict[str, Any], 
                                 query: str) -> Dict[str, float]:
        """Calculate overall response quality metrics"""
        quality_metrics = {
            "completeness": 0.0,
            "conciseness": 0.0,
            "financial_accuracy": 0.0,
            "overall_quality": 0.0
        }
        
        answer = response.get("answer", "")
        data_points = response.get("data_points", [])
        calculations = response.get("calculations", [])
        confidence = response.get("confidence", 0.0)
        
        # Completeness: Check if answer addresses the query
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        relevant_terms = query_terms & answer_terms
        completeness = len(relevant_terms) / len(query_terms) if query_terms else 0
        
        # Conciseness: Penalize very long answers without much content
        word_count = len(answer.split())
        if word_count < 50:
            conciseness = 0.3  # Too short
        elif word_count < 300:
            conciseness = 0.9  # Good length
        elif word_count < 600:
            conciseness = 0.7  # A bit long
        else:
            conciseness = 0.5  # Too long
        
        # Financial accuracy based on data points and calculations
        financial_accuracy = min(1.0, confidence * 0.7 + (len(data_points) / 10 * 0.3))
        
        # Overall quality weighted average
        overall_quality = (
            completeness * 0.3 +
            conciseness * 0.2 +
            financial_accuracy * 0.4 +
            (len(calculations) / 5 * 0.1)  # Bonus for calculations
        )
        
        return {
            "completeness": round(completeness, 3),
            "conciseness": round(conciseness, 3),
            "financial_accuracy": round(financial_accuracy, 3),
            "overall_quality": round(overall_quality, 3),
            "answer_length": word_count,
            "data_points_count": len(data_points),
            "calculations_count": len(calculations)
        }
    
    def calculate_comprehensive_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics across all test results"""
        if not test_results:
            return {}
        
        successful_tests = [r for r in test_results if r.get("status") == "passed"]
        
        # Execution times
        execution_times = [
            r.get("execution_time", 0) for r in successful_tests 
            if r.get("execution_time")
        ]
        
        # Response qualities
        response_qualities = [
            self.calculate_response_quality(r.get("response", {}), r.get("query", ""))
            for r in successful_tests if r.get("response")
        ]
        
        avg_quality = (
            sum(q["overall_quality"] for q in response_qualities) / len(response_qualities)
            if response_qualities else 0
        )
        
        return {
            "success_rate": len(successful_tests) / len(test_results),
            "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "average_response_quality": avg_quality,
            "total_tests_evaluated": len(test_results),
            "performance_grade": self._calculate_grade(avg_quality)
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        else:
            return "D"