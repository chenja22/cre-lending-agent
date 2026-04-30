import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.underwriting import UnderwritingAgent

deal_params = {
    "property_type": "multifamily",
    "address": "2847 N Halsted St, Chicago, IL 60657",
    "borrower": "Lakeview Commons LLC",
    "loan_amount": 8000000,
    "appraised_value": 11200000,
    "noi": 600000,
    "num_units": 50,
    "occupancy_rate": 0.94,
    "loan_term_years": 5,
    "interest_rate": 6.75,
    "amortization_years": 30,
    "notes": "Sponsor has 12 years experience in Chicago multifamily."
}

agent = UnderwritingAgent()
result = agent.run(deal_params)

import json
print(json.dumps(result, indent=2))