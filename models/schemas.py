from pydantic import BaseModel, Field, validator 
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

class DocumentType(str, Enum):
    FINANCIAL_STATEMENT = "financial_statement"
    EARNINGS_PRESENTATION = "earnings_presentation"
    RESULTS_CALL = "results_call"
    ANNUAL_REPORT = "annual_report"

class Quarter(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2" 
    Q3 = "Q3"
    Q4 = "Q4"
    ANNUAL = "Annual"

class FinancialMetric(str, Enum):
    NET_PROFIT = "net_profit"
    NET_INTEREST_INCOME = "net_interest_income"
    TOTAL_ASSETS = "total_assets"
    TOTAL_LOANS = "total_loans"
    TOTAL_DEPOSITS = "total_deposits"
    SHAREHOLDER_EQUITY = "shareholder_equity"
    ROE = "return_on_equity"
    ROA = "return_on_assets"
    NIM = "net_interest_margin"
    LOAN_TO_DEPOSIT = "loan_to_deposit_ratio"
    COST_OF_RISK = "cost_of_risk"
    NPL_RATIO = "npl_ratio"

class DocumentMetadata(BaseModel):
    bank: str = "FAB"
    year: int
    quarter: Quarter
    document_type: DocumentType
    document_category: str
    file_path: str
    reporting_date: Optional[str] = None
    release_date: Optional[str] = None
    pages: Optional[int] = None  # Make sure this can be None
    currency: str = "AED"
    units: str = "millions"

    # PYDANTIC V1 SYNTAX
    @validator('pages', pre=True)
    def validate_pages(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v

class FinancialDataPoint(BaseModel):
    metric: FinancialMetric
    value: float
    period: str  # e.g., "2022_Q1"
    metadata: DocumentMetadata
    source_page: int
    source_section: str
    confidence: float = Field(ge=0, le=1)

class QueryType(str, Enum):
    SINGLE_FACT = "single_fact"
    MULTI_HOP = "multi_hop"
    CALCULATION = "calculation"
    TEMPORAL_COMPARISON = "temporal_comparison"
    RISK_ANALYSIS = "risk_analysis"
    TREND_ANALYSIS = "trend_analysis"

class AgentResponse(BaseModel):
    content: str
    data_points: List[FinancialDataPoint]
    calculations: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    confidence: float
    metadata: Dict[str, Any]

class WorkflowState(BaseModel):
    query: str
    query_type: Optional[QueryType] = None
    current_step: str = "initial"
    extracted_data: List[FinancialDataPoint] = []
    intermediate_results: Dict[str, Any] = {}
    calculations: List[Dict[str, Any]] = []
    final_answer: Optional[str] = None
    sources: List[Dict[str, str]] = []
    error: Optional[str] = None
    iteration_count: int = 0