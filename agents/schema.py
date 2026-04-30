from pydantic import BaseModel
from typing import List, Optional

class DealParams(BaseModel):
    property_type: str
    address: str
    borrower: str
    loan_amount: float
    appraised_value: float
    noi: float
    num_units: int
    occupancy_rate: float
    loan_term_years: int
    interest_rate: float
    amortization_years: int
    notes: str

class UnderwritingOutput(BaseModel):
    dscr: float
    ltv: float
    debt_yield: float
    annual_debt_service: float
    stress_dscr: float
    flag: str
    dscr_assessment: str
    ltv_assessment: str
    debt_yield_assessment: str
    stress_assessment: str
    conditions: List[str]
    recommendation: str

class MarketOutput(BaseModel):
    submarket: str
    market_trend: str
    avg_cap_rate: float
    vacancy_rate: float
    avg_asking_rent_per_unit: int
    rent_growth_yoy: float
    supply_pressure: str
    demand_drivers: List[str]
    risk_factors: List[str]
    market_commentary: str
    sources: List[str]

class CreditOutput(BaseModel):
    sponsor_experience_assessment: str
    global_cash_flow_assessment: str
    entity_structure_note: str
    track_record_flag: str
    key_risks: List[str]
    mitigants: List[str]
    credit_recommendation: str
    credit_commentary: str