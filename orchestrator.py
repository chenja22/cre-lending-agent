import json
from agents.intake import IntakeAgent
from agents.underwriting import UnderwritingAgent
from agents.market import MarketAgent
from agents.credit import CreditAgent
from agents.memo import MemoAgent

class Orchestrator:
    def __init__(self):
        self.intake = IntakeAgent()
        self.underwriting = UnderwritingAgent()
        self.market = MarketAgent()
        self.credit = CreditAgent()
        self.memo = MemoAgent()

    def run(self, deal_path: str) -> dict:
        print("\n=== CRE LENDING AGENT STARTING ===")

        # Initialize deal state
        deal_state = {}

        # Stage 1: Intake
        deal_state["deal_params"] = self.intake.run(deal_path)
        print(f"Deal params extracted: {json.dumps(deal_state['deal_params'], indent=2)}")

        # Stage 2: Underwriting
        deal_state["underwriting"] = self.underwriting.run(deal_state["deal_params"])
        print(f"Underwriting complete: {json.dumps(deal_state['underwriting'], indent=2)}")

        # Stage 3: Market (runs in parallel conceptually, sequential here)
        deal_state["market"] = self.market.run(deal_state["deal_params"])
        print(f"Market analysis complete: {json.dumps(deal_state['market'], indent=2)}")

        # Stage 4: Credit
        deal_state["credit"] = self.credit.run(deal_state["deal_params"])
        print(f"Credit analysis complete: {json.dumps(deal_state['credit'], indent=2)}")

        # Stage 5: Memo assembly
        deal_state["memo"] = self.memo.run(deal_state)
        print("\n=== CREDIT MEMO GENERATED ===")

        return deal_state