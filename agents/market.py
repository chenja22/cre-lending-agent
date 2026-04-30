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
        result = self._run_with_search(prompt)
        result = self._extract_json(result)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"[MarketAgent] Warning: Could not parse JSON, attempting recovery...")
            return self._recover_json(result)

    def _extract_json(self, text: str) -> str:
        """Robustly extract JSON from text that may have preamble or markdown."""
        text = text.strip()
        text = text.removeprefix("```json").removeprefix("```")
        text = text.removesuffix("```").strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
        return text

    def _recover_json(self, bad_response: str) -> dict:
        """Ask Claude to extract JSON from a malformed response."""
        recovery_prompt = f"""
The following text should be a JSON object but may have extra content.
Extract ONLY the JSON object and return it with no other text:

{bad_response}
"""
        result = super().run(recovery_prompt)
        result = self._extract_json(result)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"[MarketAgent] Recovery failed, returning empty market data")
            return {"market_commentary": bad_response[:500], "sources": []}

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

        messages = [{"role": "user", "content": user_message}]

        while response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

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

        for block in response.content:
            if hasattr(block, 'text'):
                print(f"\n[{self.name}] Done.")
                return block.text

        return ""