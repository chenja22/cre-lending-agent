import json
from agents.base import BaseAgent

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
Return only JSON, no markdown."""

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
        result = self._run_with_search(prompt)
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"[MarketAgent] Warning: Could not parse JSON")
            return {"market_commentary": result}

    def _run_with_search(self, user_message: str) -> str:
        print(f"\n[{self.name}] Running with web search...")

        tools = [
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=tools,
            messages=[{"role": "user", "content": user_message}]
        )

        # Handle tool use loop
        messages = [{"role": "user", "content": user_message}]

        while response.stop_reason == "tool_use":
            # Add assistant response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Process tool results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(block.input)
                    })

            messages.append({"role": "user", "content": tool_results})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=tools,
                messages=messages
            )

        # Extract final text response
        for block in response.content:
            if hasattr(block, 'text'):
                print(f"\n[{self.name}] Done.")
                return block.text

        return ""