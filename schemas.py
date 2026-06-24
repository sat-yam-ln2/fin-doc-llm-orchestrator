from pydantic import BaseModel
from typing import Optional, List


class BankStatementData(BaseModel):
    account_number: Optional[str]
    account_holder: Optional[str]
    transactions: List[str]
    total_credits: Optional[str]
    total_debits: Optional[str]
    risk_keywords: List[str]
    date_range: Optional[str]


class InvoiceData(BaseModel):
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    buyer_name: Optional[str]
    amount: Optional[str]
    due_date: Optional[str]
    line_items: List[str]
    risk_keywords: List[str]


class DisputeLetterData(BaseModel):
    claimant_name: Optional[str]
    account_number: Optional[str]
    disputed_amount: Optional[str]
    dispute_reason: Optional[str]
    transaction_dates: List[str]
    risk_keywords: List[str]


class NewsSnippetData(BaseModel):
    entities_mentioned: List[str]
    event_summary: Optional[str]
    risk_keywords: List[str]
    date: Optional[str]


class RiskSummary(BaseModel):
    document_type: str
    risk_level: str  # low, medium, high
    key_findings: List[str]
    recommended_action: str

class ToneAnalysis(BaseModel):
    urgency_score: int          # 0 to 10
    evasiveness_score: int      # 0 to 10
    tone_summary: str           # one line explanation
    combined_risk_signal: str   # low, medium, high

class VerificationResult(BaseModel):
    status: str           # verified, partially_verified, unverified
    confidence: int        # 0 to 100
    reason: str            # one line explanation
    flagged_fields: List[str]   # which fields look suspicious, empty if none