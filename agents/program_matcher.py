import json
from agents.base import BaseAgent
from agents.schema import ProgramMatchOutput

SYSTEM_PROMPT = """You are a senior CRE debt capital markets specialist at an institutional lender.
Given a fully underwritten deal, recommend the optimal loan execution channel.

PROGRAM CRITERIA:

Fannie Mae DUS / Freddie Mac Optigo (Agency):
- Property type: multifamily only (5+ residential units)
- Stabilized: occupancy >= 90%
- DSCR >= 1.25x (Freddie accepts >= 1.20x)
- LTV <= 75% (80% for affordable housing)
- Loan size: $1M minimum
- Non-recourse, fixed rate, 5-30 year term
- Best execution for stabilized multifamily — tightest spreads

CMBS (Commercial Mortgage-Backed Securities):
- Property types: office, retail, industrial, mixed-use, hotel, anchored multifamily
- Stabilized, in-place cash flow required
- DSCR >= 1.25x, LTV <= 70%
- Loan size: $5M+ (below this, execution costs make it uneconomical)
- Non-recourse, fixed rate, 5-10 year IO periods common
- Good for larger non-multifamily deals with clean cash flow

Balance Sheet:
- Any property type, any loan size
- Flexible credit underwriting — handles complexity, transitional assets, relationship borrowers
- Recourse or non-recourse depending on risk
- Useful when deal doesn't fit agency/CMBS box: mixed collateral, short history, below-threshold metrics
- Tighter spreads for relationship clients; wider for non-relationship

Bridge:
- Short-term (12-36 months), floating rate
- Transitional or value-add assets: occupancy < 85%, in-progress renovations, lease-up
- DSCR may be sub-1.0x on in-place income — underwritten to stabilized value
- Interest-only, sized on stabilized NOI with a path to permanent financing
- Required when the asset isn't yet stabilized enough for agency, CMBS, or long-term balance sheet

Decision hierarchy:
1. If multifamily + stabilized + DSCR/LTV in range → Agency (cheapest execution)
2. If non-multifamily + stabilized + loan >= $5M + DSCR/LTV in range → CMBS
3. If stabilized but complex/relationship or loan < $5M non-agency → Balance Sheet
4. If transitional/value-add or occupancy < 85% → Bridge

Always identify the single best execution and list viable alternatives."""

class ProgramMatcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ProgramMatcherAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_state: dict) -> dict:
        deal_params = deal_state.get("deal_params", {})
        underwriting = deal_state.get("underwriting", {})
        market = deal_state.get("market", {})
        credit = deal_state.get("credit", {})

        prompt = f"""
Recommend the optimal lending program for this deal:

DEAL PARAMETERS:
Property Type: {deal_params.get('property_type', 'unknown')}
Address: {deal_params.get('address', 'unknown')}
Loan Amount: ${deal_params.get('loan_amount', 0):,.0f}
Appraised Value: ${deal_params.get('appraised_value', 0):,.0f}
Units: {deal_params.get('num_units', 0)}
Occupancy: {deal_params.get('occupancy_rate', 0):.0%}
Loan Term Requested: {deal_params.get('loan_term_years', 0)} years
Notes: {deal_params.get('notes', 'None')}

UNDERWRITING METRICS:
DSCR: {underwriting.get('dscr', 0):.2f}x
LTV: {underwriting.get('ltv', 0):.1%}
Debt Yield: {underwriting.get('debt_yield', 0):.1%}
Flag: {underwriting.get('flag', 'unknown')}
Recommendation: {underwriting.get('recommendation', 'N/A')}

MARKET CONDITIONS:
Submarket: {market.get('submarket', 'unknown')}
Market Trend: {market.get('market_trend', 'unknown')}
Avg Cap Rate: {market.get('avg_cap_rate', 0):.2%}
Vacancy Rate: {market.get('vacancy_rate', 0):.1%}
Supply Pressure: {market.get('supply_pressure', 'unknown')}

SPONSOR / CREDIT:
Track Record: {credit.get('track_record_flag', 'unknown')}
Credit Recommendation: {credit.get('credit_recommendation', 'N/A')}
"""
        result = self.run_structured(prompt, ProgramMatchOutput)
        return result.model_dump()
