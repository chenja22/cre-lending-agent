import json
import os
from unittest import result
import pdfplumber
from agents.base import BaseAgent
from agents.schema import DealParams

SYSTEM_PROMPT = """You are a commercial real estate loan intake specialist.
Extract deal parameters from loan applications OR offering memorandums (OMs).

For offering memorandums, derive loan parameters using standard assumptions:
- Loan amount: 65% of offering price (standard LTV for small multifamily)
- Appraised value: offering price
- Borrower: use property LLC name or "Prospective Buyer LLC" if unknown
- NOI: use current NOI if available, not pro forma

You must always return valid JSON with exactly this structure, no extra text:
{
    "property_type": "multifamily|office|retail|industrial|mixed-use",
    "address": "full address",
    "borrower": "borrower/LLC name",
    "loan_amount": 0,
    "appraised_value": 0,
    "noi": 0,
    "num_units": 0,
    "occupancy_rate": 0.0,
    "loan_term_years": 0,
    "interest_rate": 0.0,
    "amortization_years": 0,
    "notes": "any other relevant details including value-add upside, rent roll details, capex history"
}

Standard assumptions when not specified:
- loan_term_years: 5
- interest_rate: 6.75
- amortization_years: 30
- occupancy_rate: derive from rent roll vacancy if available

If a field is not found, use 0 for numbers and "unknown" for strings.
Always return only the JSON object, no markdown, no explanation."""

class IntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="IntakeAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_path: str) -> dict:
        raw_text = self._parse_docs(deal_path)
        result = self.run_structured(
        f"Extract deal parameters from these documents:\n\n{raw_text}",
        DealParams
    )
        return result.model_dump()

    def _parse_docs(self, deal_path: str) -> str:
        all_text = []
        if os.path.isdir(deal_path):
            for filename in os.listdir(deal_path):
                filepath = os.path.join(deal_path, filename)
                if filename.endswith(".pdf"):
                    all_text.append(self._parse_pdf(filepath))
                elif filename.endswith(".txt"):
                    with open(filepath, "r") as f:
                        all_text.append(f.read())
        else:
            if deal_path.endswith(".pdf"):
                all_text.append(self._parse_pdf(deal_path))
        return "\n\n---\n\n".join(all_text)

    def _parse_pdf(self, filepath: str) -> str:
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text.append(extracted)
        return "\n".join(text)