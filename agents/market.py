import json
from agents.base import BaseAgent
from agents.schema import MarketOutput
from ui import console

SYSTEM_PROMPT = """You are a commercial real estate market research analyst.
Given a property's location and type, search for current market data and provide a concise analysis.

Use web search to find:
- Current cap rates for the property type and submarket
- Current vacancy rates
- Recent rent trends and YoY growth
- Any notable supply pipeline or new construction
- Recent news affecting the submarket

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
    "market_commentary": "",
    "sources": []
}

Include sources as a list of URLs or publication names you used.
CRITICAL: Your final response must start with { and end with }.
Do not include any text before the opening brace or after the closing brace.
Do not explain what you are doing. Output only the JSON object."""

class MarketAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_params: dict) -> dict:
        prompt = f"""
Search for current market data for this property and provide analysis:

Address: {deal_params.get('address', 'unknown')}
Property Type: {deal_params.get('property_type', 'unknown')}
Number of Units: {deal_params.get('num_units', 0)}
Current Occupancy: {deal_params.get('occupancy_rate', 0):.0%}

Search for current {deal_params.get('property_type', 'multifamily')} market data 
for {deal_params.get('address', 'this location')} including cap rates, vacancy rates, 
rent growth, and any recent market news.
"""
        raw_result = self._run_with_search(prompt)

        parse_prompt = f"""Convert this market research into structured JSON format:

{raw_result}
"""
        result = self.run_structured(parse_prompt, MarketOutput)
        return result.model_dump()

    def _run_with_search(self, user_message: str) -> str:
        tools = [{"type": "web_search_20250305", "name": "web_search"}]
        messages = [{"role": "user", "content": user_message}]

        with console.status(f"[cyan]{self.name}[/cyan]  searching the web…", spinner="dots"):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=tools,
                messages=messages,
            )

            while response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(block.input),
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
                messages.append({"role": "user", "content": tool_results})
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    tools=tools,
                    messages=messages,
                )

        for block in response.content:
            if hasattr(block, "text"):
                return block.text

        return ""