import json
from agents.base import BaseAgent

SYSTEM_PROMPT = """You are a senior credit officer evaluating sponsor strength for a CRE loan.

Assess the borrower/sponsor based on available information and return JSON only, no markdown:
{
    "sponsor_experience_assessment": "",
    "global_cash_flow_assessment": "",
    "entity_structure_note": "",
    "track_record_flag": "strong|adequate|weak|unknown",
    "key_risks": [],
    "mitigants": [],
    "credit_recommendation": "approve|conditional|decline",
    "credit_commentary": ""
}

Standards:
- Strong sponsor: 10+ years experience, no defaults, documented net worth 10x loan amount
- Adequate sponsor: 5-10 years, clean record, net worth 5x loan amount  
- Weak sponsor: <5 years, any defaults, thin net worth
- Unknown: insufficient information provided

Return only JSON, no markdown."""

class CreditAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CreditAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_params: dict) -> dict:
        prompt = f"""
Evaluate sponsor/borrower credit for this loan request:

Borrower: {deal_params.get('borrower', 'unknown')}
Loan Amount: ${deal_params.get('loan_amount', 0):,}
Property Type: {deal_params.get('property_type', 'unknown')}
Notes: {deal_params.get('notes', 'None provided')}
"""
        result = super().run(prompt)
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"[CreditAgent] Warning: Could not parse JSON")
            return {"credit_commentary": result}