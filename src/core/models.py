from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Agent:
    id: int
    name: str
    license_number: Optional[str] = None
    license_expiration: Optional[str] = None
    split_type: str = 'percentage'  # 'percentage', 'tiered', 'transaction_fee'
    agent_split_pct: Optional[float] = None
    office_split_pct: Optional[float] = None
    tier_rules: Optional[str] = None  # JSON string
    transaction_fee: Optional[float] = None
    cap_amount: Optional[float] = None
    contract_date: Optional[str] = None
    is_active: int = 1
    is_test: int = 0
    notes: Optional[str] = None
    # Tax info (all optional)
    tin: str = ""
    street_address: str = ""
    city: str = ""
    state: str = "MI"
    zip_code: str = ""


@dataclass
class CommissionResult:
    gross_commission: float
    agent_split_pct_used: float
    office_split_pct_used: float
    office_share: float
    agent_share: float
    amount_toward_cap: float
    cap_before: float
    cap_after: float
    compliance_fee_amount: float
    compliance_fee_payer: str
    compliance_to_office: float
    compliance_to_agent: float
    total_payout: float
    is_capped: bool = False
    is_post_cap: bool = False


@dataclass
class Transaction:
    id: int
    agent_id: int
    invoice_number: str
    property_address: str
    gross_commission: float
    closing_date: str
    is_company_lead: int
    compliance_fee_amount: float
    compliance_fee_payer: str
    office_share: float
    agent_share: float
    amount_toward_cap: float
    cap_before_txn: float
    cap_after_txn: float
    agent_pct_used: Optional[float] = None
    office_pct_used: Optional[float] = None
    payment_method: str = ''
    total_payout: float = 0.0
    cap_year_start: Optional[str] = None
    cap_year_end: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    agent_name: Optional[str] = None  # joined field for display


@dataclass
class TaxRecord:
    id: int
    agent_id: int
    tax_year: int
    total_compensation: float = 0.0
    manual_adjustment: float = 0.0
    adjustment_note: str = ""
    filed: bool = False
    filed_date: Optional[str] = None
    agent_name: Optional[str] = None  # joined field for display

    @property
    def effective_amount(self) -> float:
        return self.total_compensation + self.manual_adjustment
