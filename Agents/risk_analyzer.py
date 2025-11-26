
from typing import List, Dict, Any
from models.schemas import FinancialDataPoint
import re

class RiskAnalysisAgent:
    def __init__(self):
        self.risk_keywords = {
            "credit_risk": ["credit risk", "non-performing", "npl", "provision", "impairment", "loan loss"],
            "market_risk": ["market risk", "interest rate", "fx", "foreign exchange", "trading", "liquidity"],
            "operational_risk": ["operational risk", "cyber", "fraud", "compliance", "regulation", "internal control"],
            "strategic_risk": ["strategic", "competition", "market share", "innovation", "digital transformation"],
            "liquidity_risk": ["liquidity", "funding", "deposit", "cash flow", "capital adequacy"]
        }
        
        self.risk_mitigation_keywords = [
            "mitigate", "address", "manage", "control", "reduce", "minimize", 
            "strategy", "framework", "policy", "procedure", "enhance", "improve"
        ]
    
    def analyze(self, data_points: List[FinancialDataPoint], query: str) -> Dict[str, Any]:
        """Analyze risk factors from financial data and documents"""
        
        risk_analysis = {
            "identified_risks": [],
            "risk_metrics": {},
            "mitigation_mentions": [],
            "confidence": 0.0,
            "source_periods": set(),
            "risk_context": []
        }
        
        # Extract text content from data points for analysis
        text_content = self._extract_text_from_data_points(data_points)
        
        if text_content:
            # Analyze risk content in the text
            risk_analysis["identified_risks"] = self._analyze_risk_content(text_content)
            risk_analysis["mitigation_mentions"] = self._analyze_mitigation_strategies(text_content)
            risk_analysis["risk_context"] = self._extract_risk_context(text_content)
            
            # Extract source periods
            for dp in data_points:
                risk_analysis["source_periods"].add(dp.period)
            
            risk_analysis["confidence"] = self._calculate_confidence(risk_analysis)
        
        # Extract risk metrics from financial data
        risk_analysis["risk_metrics"] = self._extract_risk_metrics(data_points)
        
        return risk_analysis
    
    def _extract_text_from_data_points(self, data_points: List[FinancialDataPoint]) -> str:
        """Extract and combine text content from data points"""
        text_content = ""
        for dp in data_points:
            # If we have the actual chunk content stored somewhere, use it
            # For now, we'll rely on the metadata and extracted metrics
            text_content += f" {dp.metadata.document_type.value} {dp.period} "
        
        return text_content
    
    def _analyze_risk_content(self, text: str) -> List[Dict[str, Any]]:
        """Analyze risk content from text"""
        identified_risks = []
        text_lower = text.lower()
        
        for risk_category, keywords in self.risk_keywords.items():
            category_mentions = []
            mention_count = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    mention_count += 1
                    # Extract context around the keyword
                    context = self._extract_risk_context_snippet(text, keyword)
                    category_mentions.append({
                        "keyword": keyword,
                        "context": context,
                        "sentiment": self._assess_risk_sentiment(context)
                    })
            
            if mention_count > 0:
                identified_risks.append({
                    "risk_category": risk_category,
                    "mentions": category_mentions,
                    "mention_count": mention_count,
                    "confidence": min(0.9, mention_count * 0.3)  # Higher confidence with more mentions
                })
        
        # Sort by mention count (most mentioned risks first)
        identified_risks.sort(key=lambda x: x["mention_count"], reverse=True)
        
        return identified_risks[:5]  # Return top 5 risks
    
    def _analyze_mitigation_strategies(self, text: str) -> List[Dict[str, Any]]:
        """Analyze risk mitigation strategies mentioned"""
        mitigation_mentions = []
        text_lower = text.lower()
        
        for mitigation_word in self.risk_mitigation_keywords:
            if mitigation_word in text_lower:
                context = self._extract_risk_context_snippet(text, mitigation_word)
                mitigation_mentions.append({
                    "action": mitigation_word,
                    "context": context
                })
        
        return mitigation_mentions
    
    def _extract_risk_context(self, text: str) -> List[str]:
        """Extract relevant risk context snippets"""
        # Look for risk-related sections
        risk_contexts = []
        
        # Split by sentences and look for risk-related content
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(risk_word in sentence_lower for risk_word in ["risk", "challenge", "uncertainty", "volatility"]):
                if len(sentence) > 20:  # Meaningful length
                    risk_contexts.append(sentence.strip())
        
        return risk_contexts[:10]  # Return top 10 context snippets
    
    def _extract_risk_context_snippet(self, text: str, keyword: str, context_words: int = 30) -> str:
        """Extract context around a risk keyword"""
        words = text.split()
        try:
            # Find the keyword
            for i, word in enumerate(words):
                if keyword.lower() in word.lower():
                    start = max(0, i - context_words)
                    end = min(len(words), i + context_words + 1)
                    return ' '.join(words[start:end])
        except:
            pass
        return keyword
    
    def _assess_risk_sentiment(self, context: str) -> str:
        """Simple risk sentiment assessment"""
        context_lower = context.lower()
        
        positive_indicators = ["strong", "adequate", "improving", "manage", "control", "mitigate", "stable"]
        negative_indicators = ["concern", "challenge", "increase", "deteriorat", "weak", "pressure", "volatility"]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in context_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in context_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    
    def _extract_risk_metrics(self, data_points: List[FinancialDataPoint]) -> Dict[str, Any]:
        """Extract quantitative risk metrics"""
        risk_metrics = {}
        
        # Group by period for trend analysis
        data_by_period = {}
        for dp in data_points:
            period = dp.period
            if period not in data_by_period:
                data_by_period[period] = {}
            data_by_period[period][dp.metric.value] = dp.value
        
        # Calculate risk ratios if we have the data
        for period, metrics in data_by_period.items():
            period_risks = {}
            
            # NPL Ratio (simplified - would need non-performing loans data)
            if 'non_performing_loans' in metrics and 'total_loans' in metrics:
                npl_ratio = (metrics['non_performing_loans'] / metrics['total_loans']) * 100
                period_risks['npl_ratio'] = npl_ratio
            
            # Loan-to-Deposit Ratio
            if 'total_loans' in metrics and 'total_deposits' in metrics:
                ldr = (metrics['total_loans'] / metrics['total_deposits']) * 100
                period_risks['loan_to_deposit_ratio'] = ldr
            
            # Capital Adequacy (simplified)
            if 'shareholder_equity' in metrics and 'total_assets' in metrics:
                capital_ratio = (metrics['shareholder_equity'] / metrics['total_assets']) * 100
                period_risks['capital_adequacy_ratio'] = capital_ratio
            
            if period_risks:
                risk_metrics[period] = period_risks
        
        return risk_metrics
    
    def _calculate_confidence(self, risk_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for risk analysis"""
        confidence = 0.0
        
        # Base confidence
        if risk_analysis["identified_risks"]:
            confidence += 0.4
        
        if risk_analysis["mitigation_mentions"]:
            confidence += 0.3
        
        if risk_analysis["risk_context"]:
            confidence += 0.2
        
        if risk_analysis["risk_metrics"]:
            confidence += 0.1
        
        return min(1.0, confidence) 