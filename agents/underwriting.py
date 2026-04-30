import json
from agents.base import BaseAgent
from tools.calculator import (
    calculate_annual_debt_service,
    calculate_dscr,
    calculate_ltv,
    calculate_debt_yield,
    calculate_stress_dscr,
    flag_deal
)

SYSTEM_PROMPT = """You are a senior commercial real estate underwriter at a major institutional lender.
You have been given quantitative metrics for a loan and must provide a rigorous credit assessment.

Your analysis should cover:
1. DSCR assessment — is cash flow coverage adequate? What are the risks?
2. LTV assessment — is the collateral position strong enough?
3. Debt yield assessment — does this meet minimum return thresholds?
4. Stress test interpretation — how does the deal perform under rate stress?
5. Overall recommendation with specific conditions or mitigants

Use institutional underwriting standards:
- DSCR: >1.25x strong, 1.10-1.25x watch, <1.10x fail
- LTV: <65% strong, 65-75% acceptable, >75% elevated risk
- Debt yield: >10% strong, 8-10% acceptable, <8% weak
- Minimum acceptable debt yield for multifamily: 7.5%

Be direct and specific. Flag any concerns clearly. Return JSON only, no markdown:
{
    "dscr": 0.0,
    "ltv": 0.0,
    "debt_yield": 0.0,
    "annual_debt_service": 0.0,
    "stress_dscr": 0.0,
    "flag": "PASS|WATCH|FAIL",
    "dscr_assessment": "",
    "ltv_assessment": "",
    "debt_yield_assessment": "",
    "stress_assessment": "",
    "conditions": [],
    "recommendation": ""
}"""

class UnderwritingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="UnderwritingAgent", system_prompt=SYSTEM_PROMPT)

    def run(self, deal_params: dict) -> dict:
        # Calculate metrics locally first
        ads = calculate_annual_debt_service(
            deal_params.get("loan_amount", 0),
            deal_params.get("interest_rate", 0),
            deal_params.get("amortization_years", 30)
        )
        dscr = calculate_dscr(deal_params.get("noi", 0), ads)
        ltv = calculate_ltv(deal_params.get("loan_amount", 0), deal_params.get("appraised_value", 0))
        debt_yield = calculate_debt_yield(deal_params.get("noi", 0), deal_params.get("loan_amount", 0))
        stress_dscr = calculate_stress_dscr(deal_params.get("noi", 0), ads)
        flag = flag_deal(dscr, ltv, debt_yield)

        # Build prompt with calculated metrics
        prompt = f"""
Underwrite this CRE loan:

DEAL PARAMETERS:
{json.dumps(deal_params, indent=2)}

CALCULATED METRICS:
- Annual Debt Service: ${ads:,.2f}
- DSCR: {dscr:.2f}x
- LTV: {ltv:.1%}
- Debt Yield: {debt_yield:.1%}
- Stress DSCR (at 8%): {stress_dscr:.2f}x
- Preliminary Flag: {flag}

Provide your full underwriting assessment.
"""
        result = super().run(prompt)
        result = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(result)
            # Ensure calculated metrics are in output
            parsed["dscr"] = dscr
            parsed["ltv"] = ltv
            parsed["debt_yield"] = debt_yield
            parsed["annual_debt_service"] = ads
            parsed["stress_dscr"] = stress_dscr
            parsed["flag"] = flag
            return parsed
        except json.JSONDecodeError:
            print(f"[UnderwritingAgent] Warning: Could not parse JSON")
            return {
                "dscr": dscr,
                "ltv": ltv,
                "debt_yield": debt_yield,
                "annual_debt_service": ads,
                "stress_dscr": stress_dscr,
                "flag": flag,
                "recommendation": result
            }