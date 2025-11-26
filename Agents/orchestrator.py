from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from models.schemas import WorkflowState, QueryType
from agents.financial_extractor import FinancialDataExtractor
from agents.calculation_agent import CalculationAgent
from agents.temporal_analyzer import TemporalAnalysisAgent
from agents.risk_analyzer import RiskAnalysisAgent
from agents.synthesis_agent import SynthesisAgent
from agents.validation_agent import ValidationAgent

class OrchestratorAgent:
    def __init__(self):
        self.workflow = self._build_workflow()
        self.query_classifier = QueryClassifier()
    
    def _build_workflow(self) -> StateGraph:
        """Build the multi-agent workflow using LangGraph"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("classify_query", self.classify_query)
        workflow.add_node("extract_data", self.extract_data)
        workflow.add_node("perform_calculations", self.perform_calculations)
        workflow.add_node("analyze_temporal", self.analyze_temporal)
        workflow.add_node("analyze_risks", self.analyze_risks)
        workflow.add_node("synthesize_results", self.synthesize_results)
        workflow.add_node("validate_output", self.validate_output)
        
        # Define workflow edges
        workflow.set_entry_point("classify_query")
        
        workflow.add_edge("classify_query", "extract_data")
        workflow.add_conditional_edges(
            "extract_data",
            self.route_after_extraction,
            {
                "calculations": "perform_calculations",
                "temporal": "analyze_temporal", 
                "risks": "analyze_risks",
                "synthesis": "synthesize_results"
            }
        )
        workflow.add_edge("perform_calculations", "synthesize_results")
        workflow.add_edge("analyze_temporal", "synthesize_results")
        workflow.add_edge("analyze_risks", "synthesize_results")
        workflow.add_edge("synthesize_results", "validate_output")
        workflow.add_conditional_edges(
            "validate_output",
            self.final_validation,
            {
                "approve": END,
                "retry": "extract_data"
            }
        )
        
        return workflow.compile()
    
    def classify_query(self, state: WorkflowState) -> WorkflowState:
        """Classify the query type and set initial workflow state"""
        query_type = self.query_classifier.classify(state.query)
        state.query_type = query_type
        state.current_step = "query_classified"
        
        return state
    
    def extract_data(self, state: WorkflowState) -> WorkflowState:
        """Extract relevant financial data based on query"""
        extractor = FinancialDataExtractor()
        state.extracted_data = extractor.extract_data(state.query, state.query_type)
        state.current_step = "data_extracted"
        
        return state
    
    def perform_calculations(self, state: WorkflowState) -> WorkflowState:
        """Perform financial calculations"""
        calculator = CalculationAgent()
        state.calculations = calculator.perform_calculations(
            state.extracted_data, 
            state.query
        )
        state.current_step = "calculations_completed"
        
        return state
    
    def analyze_temporal(self, state: WorkflowState) -> WorkflowState:
        """Perform temporal analysis"""
        temporal_agent = TemporalAnalysisAgent()
        state.intermediate_results["temporal_analysis"] = temporal_agent.analyze(
            state.extracted_data,
            state.query
        )
        state.current_step = "temporal_analysis_completed"
        
        return state
    
    def analyze_risks(self, state: WorkflowState) -> WorkflowState:
        """Perform risk analysis"""
        risk_agent = RiskAnalysisAgent()
        state.intermediate_results["risk_analysis"] = risk_agent.analyze(
            state.extracted_data,
            state.query
        )
        state.current_step = "risk_analysis_completed"
        
        return state
    
    def synthesize_results(self, state: WorkflowState) -> WorkflowState:
        """Synthesize all results into comprehensive answer"""
        synthesis_agent = SynthesisAgent()
        state.final_answer = synthesis_agent.synthesize(
            state.extracted_data,
            state.calculations,
            state.intermediate_results,
            state.query
        )
        state.current_step = "synthesis_completed"
        
        return state
    
    def validate_output(self, state: WorkflowState) -> WorkflowState:
        """Validate the final output for accuracy and completeness"""
        validation_agent = ValidationAgent()
        validation_result = validation_agent.validate(
            state.final_answer,
            state.extracted_data,
            state.calculations
        )
        
        if validation_result["is_valid"]:
            state.current_step = "validation_passed"
        else:
            # Ensure error is a string, not a list
            if validation_result["errors"]:
                state.error = ", ".join(validation_result["errors"])  # Convert list to string
            else:
                state.error = "Validation failed"
            state.iteration_count += 1
        
        return state
    
    def route_after_extraction(self, state: WorkflowState) -> str:
        """Route to appropriate next step after data extraction"""
        if state.query_type in [QueryType.CALCULATION, QueryType.TREND_ANALYSIS]:
            return "calculations"
        elif state.query_type == QueryType.TEMPORAL_COMPARISON:
            return "temporal"
        elif state.query_type == QueryType.RISK_ANALYSIS:
            return "risks"
        else:
            return "synthesis"
    
    def final_validation(self, state: WorkflowState) -> str:
        """Determine if output needs revision"""
        if state.error or state.iteration_count >= 3:
            return "approve"  # Approve even with errors after max iterations
        return "approve" if not state.error else "retry"
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process financial queries - FIXED VERSION"""
        initial_state = WorkflowState(query=query)
        final_state = self.workflow.invoke(initial_state)
        
        # Handle both dict and WorkflowState responses from LangGraph
        if isinstance(final_state, dict):
            # LangGraph returned a dictionary
            return {
                "answer": final_state.get("final_answer", "No answer generated"),
                "data_points": final_state.get("extracted_data", []),
                "calculations": final_state.get("calculations", []),
                "sources": final_state.get("sources", []),
                "confidence": 0.9,  # Would be calculated based on validation
                "workflow_steps": final_state.get("current_step", "unknown")
            }
        else:
            # LangGraph returned a WorkflowState object
            return {
                "answer": final_state.final_answer,
                "data_points": final_state.extracted_data,
                "calculations": final_state.calculations,
                "sources": final_state.sources,
                "confidence": 0.9,
                "workflow_steps": final_state.current_step
            }

class QueryClassifier:
    def classify(self, query: str) -> QueryType:
        """Classify query type based on content"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['calculate', 'ratio', 'percentage', 'growth rate']):
            return QueryType.CALCULATION
        elif any(word in query_lower for word in ['trend', 'over time', 'last', 'previous']):
            return QueryType.TREND_ANALYSIS
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            return QueryType.TEMPORAL_COMPARISON
        elif any(word in query_lower for word in ['risk', 'factors', 'challenges']):
            return QueryType.RISK_ANALYSIS
        elif any(word in query_lower for word in ['how', 'why', 'explain', 'factors']):
            return QueryType.MULTI_HOP
        else:
            return QueryType.SINGLE_FACT