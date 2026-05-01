from agents.intake import IntakeAgent
from agents.underwriting import UnderwritingAgent
from agents.market import MarketAgent
from agents.credit import CreditAgent
from agents.program_matcher import ProgramMatcherAgent
from agents.memo import MemoAgent
from ui import console, stage_header, stage_done

class Orchestrator:
    def __init__(self):
        self.intake = IntakeAgent()
        self.underwriting = UnderwritingAgent()
        self.market = MarketAgent()
        self.credit = CreditAgent()
        self.program_matcher = ProgramMatcherAgent()
        self.memo = MemoAgent()

    def run(self, deal_path: str) -> dict:
        console.rule("[bold]CRE Lending Stack[/bold]", style="blue")

        deal_state = {}

        stage_header(1, "Intake")
        deal_state["deal_params"] = self.intake.run(deal_path)
        p = deal_state["deal_params"]
        stage_done(f"{p.get('address', 'unknown')}  ·  {p.get('property_type', '')}  ·  ${p.get('loan_amount', 0):,.0f} loan")

        stage_header(2, "Underwriting")
        deal_state["underwriting"] = self.underwriting.run(deal_state["deal_params"])
        uw = deal_state["underwriting"]
        stage_done(f"DSCR {uw.get('dscr', 0):.2f}x  ·  LTV {uw.get('ltv', 0):.1%}  ·  Debt Yield {uw.get('debt_yield', 0):.1%}  ·  [{uw.get('flag', '')}]")

        stage_header(3, "Market Research")
        deal_state["market"] = self.market.run(deal_state["deal_params"])
        mk = deal_state["market"]
        stage_done(f"{mk.get('submarket', 'unknown')}  ·  {mk.get('market_trend', '')}  ·  avg cap rate {mk.get('avg_cap_rate', 0):.2%}")

        stage_header(4, "Credit")
        deal_state["credit"] = self.credit.run(deal_state["deal_params"])
        cr = deal_state["credit"]
        stage_done(f"Sponsor: {cr.get('track_record_flag', 'unknown')}  ·  Rec: {cr.get('credit_recommendation', 'N/A')}")

        stage_header(5, "Program Matching")
        deal_state["program_match"] = self.program_matcher.run(deal_state)
        pm = deal_state["program_match"]
        stage_done(f"{pm.get('recommended_program', 'N/A')}  ·  agency eligible: {pm.get('agency_eligible')}  ·  bridge required: {pm.get('bridge_required')}")

        stage_header(6, "Credit Memo")
        deal_state["memo"] = self.memo.run(deal_state)
        stage_done("memo generated")

        return deal_state
