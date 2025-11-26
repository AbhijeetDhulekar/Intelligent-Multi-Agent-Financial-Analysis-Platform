# evaluation/llm_judge.py
import openai
from typing import Dict, Any, List
import json
from config.settings import settings

class LLMJudge:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.evaluation_prompt = """
        You are an expert financial analyst evaluating AI-generated financial analysis.
        
        QUERY: {query}
        RESPONSE: {response}
        
        Please evaluate the response on these criteria:
        
        1. ACCURACY (40%): Are the financial figures correct? Are calculations accurate?
        2. COMPLETENESS (25%): Does it fully address the query? Any missing elements?
        3. CLARITY (15%): Is the explanation clear and well-structured?
        4. SOURCING (10%): Are data sources properly cited?
        5. INSIGHT (10%): Does it provide valuable business insights?
        
        Scoring scale: 1-10 for each category, then calculate weighted average.
        
        Provide specific feedback for improvement.
        """
    
    def evaluate_response(self, query: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to evaluate response quality"""
        try:
            prompt = self.evaluation_prompt.format(
                query=query,
                response=response.get("answer", "")
            )
            
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strict but fair financial analysis evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            evaluation_text = completion.choices[0].message.content
            return self._parse_evaluation(evaluation_text, query, response)
            
        except Exception as e:
            return {
                "error": str(e),
                "overall_score": 0,
                "categories": {}
            }
    
    def _parse_evaluation(self, evaluation_text: str, query: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM evaluation into structured format"""
        # Simple parsing - in production you'd use more sophisticated parsing
        lines = evaluation_text.split('\n')
        
        scores = {}
        current_category = None
        
        for line in lines:
            line = line.strip()
            if any(category in line.lower() for category in ['accuracy', 'completeness', 'clarity', 'sourcing', 'insight']):
                # Extract category and score
                for category in ['ACCURACY', 'COMPLETENESS', 'CLARITY', 'SOURCING', 'INSIGHT']:
                    if category in line.upper():
                        current_category = category.lower()
                        # Try to extract score
                        import re
                        score_match = re.search(r'(\d+)/10', line)
                        if score_match:
                            scores[current_category] = int(score_match.group(1))
                        break
        
        # Calculate weighted average
        weights = {'accuracy': 0.4, 'completeness': 0.25, 'clarity': 0.15, 'sourcing': 0.1, 'insight': 0.1}
        overall_score = sum(scores.get(cat, 0) * weight for cat, weight in weights.items())
        
        return {
            "overall_score": round(overall_score, 1),
            "category_scores": scores,
            "evaluation_text": evaluation_text,
            "query": query,
            "response_preview": response.get("answer", "")[:200] + "..."
        }
    
    def batch_evaluate(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate multiple test results using LLM judge"""
        evaluations = []
        
        for result in test_results:
            if result.get("status") == "passed" and "response" in result:
                print(f"🧠 LLM Evaluating: {result['id']}")
                
                evaluation = self.evaluate_response(
                    result["query"],
                    result["response"]
                )
                
                evaluations.append({
                    "test_id": result["id"],
                    "query": result["query"],
                    **evaluation
                })
        
        return evaluations