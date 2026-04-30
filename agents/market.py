import json
from agents.base import BaseAgent

SYSTEM_PROMPT = """You are a commercial real estate market research analyst.
Given a property's location and type, provide a concise market analysis.

Return JSON only, no markdown:
{
    "submarket": "",
    "market_trend": "improving|stable|declining",
    "avg_cap_rate": 0.0,
    "vacancy_rate": 0.0,
    "avg_asking_rent_per_unit": 0,
    "rent_growth_yoy": 0.0,
    "supply_pressure": "low|moderate|high",
    "demand_drivers": [],
    "risk_factors": [],
    "market_commentary": ""
}

Use realistic market data based on your knowledge of the submarket.
For cap rates: multifamily Chicago is typically 4.5-5.5%.
For vacancy: Chicago multifamily is typically 5-7%.
Be specific to the submarket — Lakeview/Lincoln Park commands premium rents vs South Side.
Return only JSON, no markdown."""

class MarketAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_params: dict) -> dict:
        prompt = f"""
Provide market analysis for this property:

Address: {deal_params.get('address', 'unknown')}
Property Type: {deal_params.get('property_type', 'unknown')}
Number of Units: {deal_params.get('num_units', 0)}
Current Occupancy: {deal_params.get('occupancy_rate', 0):.0%}
"""
        result = super().run(prompt)
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"[MarketAgent] Warning: Could not parse JSON")
            return {"market_commentary": result}