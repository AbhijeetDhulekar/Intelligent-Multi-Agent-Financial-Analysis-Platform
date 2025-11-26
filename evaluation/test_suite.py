# evaluation/test_suite.py
import json
from typing import List, Dict, Any
from datetime import datetime


class FinancialTestSuite:
    def __init__(self):
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load 20+ comprehensive test cases covering all requirements"""
        return [
            # === SIMPLE FACTUAL QUERIES (5 cases) ===
            {
                "id": "TF-001",
                "query": "What was FAB's net profit in Q1 2022?",
                "category": "single_fact",
                "expected_metrics": ["net_profit"],
                "expected_periods": ["2022_Q1"],
                "difficulty": "easy",
                "requires_calculation": False
            },
            {
                "id": "TF-002", 
                "query": "What were the total assets reported in Q3 2022?",
                "category": "single_fact",
                "expected_metrics": ["total_assets"],
                "expected_periods": ["2022_Q3"],
                "difficulty": "easy",
                "requires_calculation": False
            },
            {
                "id": "TF-003",
                "query": "How much were total loans in Q4 2022?",
                "category": "single_fact", 
                "expected_metrics": ["total_loans"],
                "expected_periods": ["2022_Q4"],
                "difficulty": "easy",
                "requires_calculation": False
            },
            {
                "id": "TF-004",
                "query": "What was the shareholder equity in Q2 2023?",
                "category": "single_fact",
                "expected_metrics": ["shareholder_equity"],
                "expected_periods": ["2023_Q2"],
                "difficulty": "easy",
                "requires_calculation": False
            },
            {
                "id": "TF-005",
                "query": "What were total deposits in Q1 2023?",
                "category": "single_fact",
                "expected_metrics": ["total_deposits"],
                "expected_periods": ["2023_Q1"],
                "difficulty": "easy",
                "requires_calculation": False
            },

            # === MULTI-HOP REASONING (5 cases) ===
            {
                "id": "MH-001",
                "query": "What was the year-over-year percentage change in Net Profit between Q3 2022 and Q3 2023? Calculate the growth rate and explain the key factors driving this change.",
                "category": "multi_hop",
                "expected_metrics": ["net_profit"],
                "expected_periods": ["2022_Q3", "2023_Q3"],
                "requires_calculation": True,
                "requires_synthesis": True,
                "difficulty": "hard"
            },
            {
                "id": "MH-002",
                "query": "How has FAB's Return on Equity (ROE) trended over the last 4 quarters? Calculate the ROE for each quarter and identify the best and worst performing quarters.",
                "category": "multi_hop", 
                "expected_metrics": ["net_profit", "shareholder_equity"],
                "expected_periods": ["2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3"],
                "requires_calculation": True,
                "requires_temporal": True,
                "difficulty": "hard"
            },
            {
                "id": "MH-003",
                "query": "Compare FAB's loan-to-deposit ratio between Q4 2022 and Q4 2023. Has the bank's lending activity increased or decreased relative to its deposit base?",
                "category": "multi_hop",
                "expected_metrics": ["total_loans", "total_deposits"],
                "expected_periods": ["2022_Q4", "2023_Q4"],
                "requires_calculation": True,
                "requires_comparison": True,
                "difficulty": "medium"
            },
            {
                "id": "MH-004",
                "query": "What were the top 2 risk factors mentioned in the 2023 reports, and how did management address them in subsequent quarters?",
                "category": "multi_hop",
                "expected_metrics": [],
                "expected_periods": ["2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"],
                "requires_risk_analysis": True,
                "requires_synthesis": True,
                "difficulty": "hard"
            },
            {
                "id": "MH-005", 
                "query": "Analyze the trend in net interest income over the last 6 quarters and explain the key drivers mentioned in management discussions.",
                "category": "multi_hop",
                "expected_metrics": ["net_interest_income"],
                "expected_periods": ["2022_Q2", "2022_Q3", "2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3"],
                "requires_temporal": True,
                "requires_synthesis": True,
                "difficulty": "hard"
            },

            # === CALCULATION-HEAVY QUERIES (5 cases) ===
            {
                "id": "CH-001",
                "query": "Calculate the quarterly growth rate of total assets from Q1 2022 to Q4 2022.",
                "category": "calculation",
                "expected_metrics": ["total_assets"],
                "expected_periods": ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4"],
                "requires_calculation": True,
                "difficulty": "medium"
            },
            {
                "id": "CH-002",
                "query": "What was the average Return on Equity (ROE) across all quarters of 2022?",
                "category": "calculation",
                "expected_metrics": ["net_profit", "shareholder_equity"],
                "expected_periods": ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4"],
                "requires_calculation": True,
                "difficulty": "medium"
            },
            {
                "id": "CH-003",
                "query": "Calculate the loan-to-deposit ratio for each quarter in 2023 and identify the quarter with the highest ratio.",
                "category": "calculation",
                "expected_metrics": ["total_loans", "total_deposits"],
                "expected_periods": ["2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"],
                "requires_calculation": True,
                "requires_comparison": True,
                "difficulty": "medium"
            },
            {
                "id": "CH-004",
                "query": "What percentage of total assets were comprised of loans in Q2 2023?",
                "category": "calculation",
                "expected_metrics": ["total_loans", "total_assets"],
                "expected_periods": ["2023_Q2"],
                "requires_calculation": True,
                "difficulty": "easy"
            },
            {
                "id": "CH-005",
                "query": "Calculate the compound quarterly growth rate of net profit from Q1 2022 to Q4 2023.",
                "category": "calculation",
                "expected_metrics": ["net_profit"],
                "expected_periods": ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"],
                "requires_calculation": True,
                "difficulty": "hard"
            },

            # === TEMPORAL COMPARISONS (3 cases) ===
            {
                "id": "TC-001",
                "query": "Compare FAB's net profit in Q1 2022 vs Q1 2023. What was the absolute and percentage difference?",
                "category": "temporal_comparison",
                "expected_metrics": ["net_profit"],
                "expected_periods": ["2022_Q1", "2023_Q1"],
                "requires_calculation": True,
                "requires_comparison": True,
                "difficulty": "medium"
            },
            {
                "id": "TC-002",
                "query": "How did total deposits change from Q4 2022 to Q4 2023? Show the trend across all intermediate quarters.",
                "category": "temporal_comparison",
                "expected_metrics": ["total_deposits"],
                "expected_periods": ["2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"],
                "requires_temporal": True,
                "requires_calculation": True,
                "difficulty": "medium"
            },
            {
                "id": "TC-003",
                "query": "Analyze the seasonality pattern in FAB's financial performance across quarters. Which quarter typically shows the strongest results?",
                "category": "temporal_comparison", 
                "expected_metrics": ["net_profit"],
                "expected_periods": ["2022_Q1", "2022_Q2", "2022_Q3", "2022_Q4", "2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4"],
                "requires_temporal": True,
                "requires_analysis": True,
                "difficulty": "hard"
            },

            # === EDGE CASES (2 cases) ===
            {
                "id": "EC-001",
                "query": "What was FAB's net profit in Q5 2023?",
                "category": "edge_case",
                "expected_behavior": "refuse",
                "expected_response": "should clarify that Q5 doesn't exist",
                "difficulty": "easy"
            },
            {
                "id": "EC-002",
                "query": "Compare FAB's performance with Emirates NBD in Q2 2023.",
                "category": "edge_case", 
                "expected_behavior": "refuse",
                "expected_response": "should state it only has FAB data",
                "difficulty": "easy"
            }
        ]
    
    def run_test_suite(self, orchestrator) -> Dict[str, Any]:
        """Run all test cases and return comprehensive results"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_cases),
                "passed": 0,
                "failed": 0,
                "skipped": 0
            },
            "detailed_results": [],
            "category_breakdown": {},
            "metrics": {}
        }
        
        for test_case in self.test_cases:
            print(f"🧪 Running test {test_case['id']}: {test_case['query']}")
            
            try:
                # Run the query through the orchestrator
                test_result = self._run_single_test(test_case, orchestrator)
                results["detailed_results"].append(test_result)
                
                if test_result["status"] == "passed":
                    results["summary"]["passed"] += 1
                elif test_result["status"] == "failed":
                    results["summary"]["failed"] += 1
                else:
                    results["summary"]["skipped"] += 1
                    
            except Exception as e:
                print(f"❌ Test {test_case['id']} crashed: {e}")
                results["detailed_results"].append({
                    **test_case,
                    "status": "error",
                    "error": str(e),
                    "execution_time": 0
                })
                results["summary"]["failed"] += 1
        
        # Calculate category breakdown
        results["category_breakdown"] = self._calculate_category_breakdown(results["detailed_results"])
        results["metrics"] = self._calculate_overall_metrics(results)
        
        return results
    
    def _run_single_test(self, test_case: Dict[str, Any], orchestrator) -> Dict[str, Any]:
        """Run a single test case"""
        start_time = datetime.now()
        
        try:
            response = orchestrator.process_query(test_case["query"])
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Convert FinancialDataPoint to dict for JSON serialization
            if "data_points" in response:
                response["data_points"] = [
                    dp.dict() if hasattr(dp, 'dict') else dp 
                    for dp in response["data_points"]
                ]
            
            # Evaluate the response
            evaluation = self._evaluate_response(test_case, response)
            
            return {
                **test_case,
                "status": "passed" if evaluation["passed"] else "failed",
                "response": response,
                "evaluation": evaluation,
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {
                **test_case,
                "status": "error",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _evaluate_response(self, test_case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a response against test case expectations"""
        evaluation = {
            "passed": True,
            "checks": [],
            "issues": []
        }
        
        # Check if answer is provided
        if not response.get("answer") or len(response["answer"].strip()) < 10:
            evaluation["passed"] = False
            evaluation["issues"].append("Answer is empty or too short")
        
        # Check data points were extracted
        if test_case["category"] not in ["edge_case"]:
            if not response.get("data_points"):
                evaluation["passed"] = False
                evaluation["issues"].append("No data points extracted")
            else:
                evaluation["checks"].append(f"Extracted {len(response['data_points'])} data points")
        
        # Check calculations if required
        if test_case.get("requires_calculation") and not response.get("calculations"):
            evaluation["passed"] = False
            evaluation["issues"].append("No calculations performed for calculation-required query")
        
        # Check confidence score
        confidence = response.get("confidence", 0)
        if confidence < 0.5:
            evaluation["issues"].append(f"Low confidence score: {confidence}")
        
        return evaluation
    
    def _calculate_category_breakdown(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance by category"""
        categories = {}
        for result in results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            
            categories[category]["total"] += 1
            if result["status"] == "passed":
                categories[category]["passed"] += 1
        
        # Calculate percentages
        for category in categories:
            categories[category]["success_rate"] = (
                categories[category]["passed"] / categories[category]["total"] * 100
            )
        
        return categories
    
    def _calculate_overall_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall performance metrics"""
        detailed_results = results["detailed_results"]
        
        total_tests = len(detailed_results)
        passed_tests = sum(1 for r in detailed_results if r["status"] == "passed")
        
        # Calculate average execution time for successful tests
        successful_times = [
            r["execution_time"] for r in detailed_results 
            if r["status"] == "passed" and "execution_time" in r
        ]
        avg_execution_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        return {
            "overall_accuracy": (passed_tests / total_tests) * 100,
            "average_execution_time": avg_execution_time,
            "test_coverage": (total_tests / len(self.test_cases)) * 100
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        report = [
            "=" * 60,
            "FAB FINANCIAL ANALYZER - TEST SUITE REPORT",
            "=" * 60,
            f"Timestamp: {results['timestamp']}",
            f"Total Tests: {results['summary']['total_tests']}",
            f"Passed: {results['summary']['passed']}",
            f"Failed: {results['summary']['failed']}",
            f"Skipped: {results['summary']['skipped']}",
            f"Overall Accuracy: {results['metrics']['overall_accuracy']:.1f}%",
            "",
            "CATEGORY BREAKDOWN:",
            "-" * 30
        ]
        
        for category, stats in results["category_breakdown"].items():
            report.append(
                f"{category.upper():<20} {stats['success_rate']:>5.1f}% "
                f"({stats['passed']}/{stats['total']})"
            )
        
        report.extend([
            "",
            "DETAILED RESULTS:",
            "-" * 30
        ])
        
        for result in results["detailed_results"]:
            status_icon = "✅" if result["status"] == "passed" else "❌"
            report.append(f"{status_icon} {result['id']}: {result['query'][:50]}...")
            if "evaluation" in result and result["evaluation"]["issues"]:
                for issue in result["evaluation"]["issues"]:
                    report.append(f"   ⚠️  {issue}")
        
        return "\n".join(report)

def run_test_suite():
    """Main function to run the test suite"""
    from agents.orchestrator import OrchestratorAgent
    
    print("🚀 Starting Comprehensive Test Suite...")
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Run test suite
    test_suite = FinancialTestSuite()
    results = test_suite.run_test_suite(orchestrator)
    
    # Generate and print report
    report = test_suite.generate_report(results)
    print(report)
    
    # Save results to file
    with open("evaluation/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📊 Results saved to evaluation/test_results.json")
    
    return results["summary"]["passed"] / results["summary"]["total_tests"] >= 0.8

if __name__ == "__main__":
    run_test_suite()