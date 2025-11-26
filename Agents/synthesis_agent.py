from typing import List, Dict, Any
from models.schemas import FinancialDataPoint, AgentResponse
import openai
from config.settings import settings

class SynthesisAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.template_library = {
            "percentage_change": self._format_percentage_change,
            "trend_analysis": self._format_trend_analysis,
            "ratio_comparison": self._format_ratio_comparison,
            "risk_analysis": self._format_risk_analysis
        }
    
    def synthesize(self, data_points: List[FinancialDataPoint], 
                   calculations: List[Dict[str, Any]],
                   intermediate_results: Dict[str, Any],
                   query: str) -> str:
        """Synthesize all information using LLM for intelligent response"""
        
        # Prepare context for LLM
        context = self._prepare_llm_context(data_points, calculations, intermediate_results, query)
        
        try:
            # Use LLM to generate comprehensive answer
            llm_response = self._call_llm(context, query)
            return llm_response
        except Exception as e:
            print(f"❌ LLM synthesis failed: {e}")
            # Fallback to template-based response
            return self._fallback_synthesis(data_points, calculations, intermediate_results, query)
    
    def _prepare_llm_context(self, data_points: List[FinancialDataPoint],
                           calculations: List[Dict[str, Any]],
                           intermediate_results: Dict[str, Any],
                           query: str) -> str:
        """Prepare structured context for LLM"""
        
        context_parts = []
        
        # Add data points
        if data_points:
            context_parts.append("EXTRACTED FINANCIAL DATA:")
            by_period = {}
            for dp in data_points:
                if dp.period not in by_period:
                    by_period[dp.period] = []
                by_period[dp.period].append(dp)
            
            for period, points in sorted(by_period.items()):
                context_parts.append(f"Period: {period}")
                for point in points:
                    context_parts.append(f"  - {point.metric.value}: {point.value:,.0f} million AED")
        
        # Add calculations
        if calculations:
            context_parts.append("\nCALCULATIONS PERFORMED:")
            for calc in calculations:
                if 'calculation_type' in calc:
                    context_parts.append(f"  - {calc['calculation_type']}: {calc}")
        
        # Add intermediate results
        if intermediate_results:
            context_parts.append("\nANALYSIS RESULTS:")
            for key, result in intermediate_results.items():
                context_parts.append(f"  - {key}: {result}")
        
        return "\n".join(context_parts)
    
    def _call_llm(self, context: str, query: str) -> str:
        """Call LLM to generate comprehensive answer"""
        
        prompt = f"""
        You are a senior financial analyst at First Abu Dhabi Bank (FAB). 
        Analyze the provided financial data and answer the user's query comprehensively.
        
        USER QUERY: {query}
        
        FINANCIAL DATA AND ANALYSIS:
        {context}
        
        REQUIREMENTS:
        1. Provide a clear, structured answer focusing on key insights
        2. Reference specific numbers and calculations
        3. Explain the business implications
        4. Highlight trends and patterns
        5. Be precise and professional
        6. Cite the specific periods and metrics used
        
        ANSWER:
        """
        
        response = self.client.chat.completions.create(
            model=settings.PRIMARY_LLM,
            messages=[
                {"role": "system", "content": "You are an expert financial analyst specializing in bank financial statements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    def _fallback_synthesis(self, data_points: List[FinancialDataPoint], 
                          calculations: List[Dict[str, Any]],
                          intermediate_results: Dict[str, Any],
                          query: str) -> str:
        """Fallback template-based synthesis if LLM fails"""
        # Your existing template-based implementation here
        answer_parts = []
        
        if calculations:
            answer_parts.append(self._synthesize_calculations(calculations, query))
        
        if data_points:
            answer_parts.append(self._synthesize_data_insights(data_points, query))
        
        if intermediate_results:
            answer_parts.append(self._synthesize_context(intermediate_results, query))
        
        answer_parts.append(self._add_sources_and_confidence(data_points))
        
        return "\n\n".join(answer_parts)
    
    # Keep all your existing template methods (_synthesize_calculations, etc.)
    def _synthesize_calculations(self, calculations: List[Dict[str, Any]], query: str) -> str:
        """Your existing implementation"""
        synthesis = "## Financial Analysis\n\n"
        for calc in calculations:
            calc_type = calc.get('calculation_type', 'unknown')
            if calc_type in self.template_library:
                synthesis += self.template_library[calc_type](calc) + "\n\n"
            else:
                synthesis += self._format_generic_calculation(calc) + "\n\n"
        return synthesis
    
    def _synthesize_data_insights(self, data_points: List[FinancialDataPoint], query: str) -> str:
        """Synthesize insights from raw data points"""
        insights = "## Key Financial Metrics\n\n"
        
        # Group by period for better organization
        by_period = {}
        for dp in data_points:
            if dp.period not in by_period:
                by_period[dp.period] = []
            by_period[dp.period].append(dp)
        
        for period, points in sorted(by_period.items()):
            insights += f"**{period}:**\n"
            for point in points:
                insights += f"- {point.metric.replace('_', ' ').title()}: AED {point.value:,.0f} million\n"
            insights += "\n"
        
        return insights
    
    def _synthesize_context(self, intermediate_results: Dict[str, Any], query: str) -> str:
        """Synthesize contextual and qualitative analysis"""
        context = "## Contextual Analysis\n\n"
        
        if 'temporal_analysis' in intermediate_results:
            temporal = intermediate_results['temporal_analysis']
            context += self._format_temporal_context(temporal)
        
        if 'risk_analysis' in intermediate_results:
            risks = intermediate_results['risk_analysis']
            context += self._format_risk_context(risks)
        
        return context
    
    def _format_percentage_change(self, calc: Dict[str, Any]) -> str:
        """Format percentage change calculation"""
        return (f"**Percentage Change Analysis:**\n"
                f"- Previous Value: AED {calc['old_value']:,.0f} million\n"
                f"- Current Value: AED {calc['new_value']:,.0f} million\n"
                f"- Absolute Change: AED {calc['absolute_change']:,.0f} million\n"
                f"- Percentage Change: {calc['percentage_change']:+.1f}%")
    
    def _format_trend_analysis(self, calc: Dict[str, Any]) -> str:
        """Format trend analysis"""
        trend = f"**Trend Analysis for {calc.get('metric', 'metric').replace('_', ' ').title()}:**\n"
        trend += f"- Average Value: AED {calc['mean']:,.0f} million\n"
        trend += f"- Highest: AED {calc['max_value']:,.0f} million ({calc['max_period']})\n"
        trend += f"- Lowest: AED {calc['min_value']:,.0f} million ({calc['min_period']})\n"
        trend += f"- Average Growth Rate: {calc['average_growth']:+.1f}% per period"
        
        return trend
    
    def _format_ratio_comparison(self, calc: Dict[str, Any]) -> str:
        """Format ratio comparison"""
        if 'roe_percentage' in calc:
            return f"**Return on Equity (ROE):** {calc['roe_percentage']:.1f}%"
        elif 'ldr_percentage' in calc:
            return f"**Loan-to-Deposit Ratio:** {calc['ldr_percentage']:.1f}%"
        elif 'nim_percentage' in calc:
            return f"**Net Interest Margin:** {calc['nim_percentage']:.1f}%"
        
        return str(calc)
    
    def _format_risk_analysis(self, calc: Dict[str, Any]) -> str:
        """Format risk analysis"""
        return "Risk analysis formatting would be implemented based on specific risk metrics"
    
    def _format_generic_calculation(self, calc: Dict[str, Any]) -> str:
        """Generic calculation formatting"""
        return f"**Calculation Result:** {calc}"
    
    def _format_temporal_context(self, temporal: Dict[str, Any]) -> str:
        """Format temporal context"""
        return f"**Period Analysis:** {temporal.get('relationship', 'N/A')}\n"
    
    def _format_risk_context(self, risks: Dict[str, Any]) -> str:
        """Format risk context"""
        return "**Risk Assessment:** Based on available risk metrics and management commentary\n"
    
    def _add_sources_and_confidence(self, data_points: List[FinancialDataPoint]) -> str:
        """Add source citations and confidence assessment"""
        sources = "## Sources & Methodology\n\n"
        sources += "*Analysis based on FAB's official financial reports and presentations.*\n"
        
        # List unique sources
        unique_sources = set()
        for dp in data_points:
            source_info = f"{dp.metadata.document_type.value} {dp.metadata.year} {dp.metadata.quarter.value}"
            unique_sources.add(source_info)
        
        if unique_sources:
            sources += "\n**Data Sources:**\n"
            for source in sorted(unique_sources):
                sources += f"- {source}\n"
        
        sources += f"\n**Confidence Level:** High (based on official financial reporting)"
        
        return sources