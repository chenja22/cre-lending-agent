import json
import os
from datetime import date
from agents.base import BaseAgent
from fpdf import FPDF
from fpdf.enums import XPos, YPos

SYSTEM_PROMPT = """You are a senior credit officer writing a formal credit memorandum for an investment committee.

Given a complete deal analysis package, write a professional credit memo in this exact structure:

EXECUTIVE SUMMARY
[2-3 sentence deal overview and recommendation]

PROPERTY & LOAN OVERVIEW
[Key deal parameters in prose]

UNDERWRITING ANALYSIS
[DSCR, LTV, debt yield discussion with specific numbers]

MARKET ANALYSIS
[Submarket context, cap rates, vacancy, rent trends]

SPONSOR ASSESSMENT
[Sponsor track record and credit evaluation]

STRESS TESTING
[Stressed DSCR and rate sensitivity discussion]

CONDITIONS & MITIGANTS
[Numbered list of conditions for approval or reasons for decline]

RECOMMENDATION
[Clear APPROVE / CONDITIONAL APPROVE / DECLINE with one paragraph rationale]

Be direct, use specific numbers, write like an institutional lender. No fluff."""

class MemoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MemoAgent",
            system_prompt=SYSTEM_PROMPT,
            model="claude-haiku-4-5-20251001",
            max_tokens=4096
    )

    def run(self, deal_state: dict) -> str:
        prompt = f"""
Write a credit memorandum for this deal:

DEAL PARAMETERS:
{json.dumps(deal_state.get('deal_params', {}), indent=2)}

UNDERWRITING METRICS:
{json.dumps(deal_state.get('underwriting', {}), indent=2)}

MARKET ANALYSIS:
{json.dumps(deal_state.get('market', {}), indent=2)}

CREDIT ASSESSMENT:
{json.dumps(deal_state.get('credit', {}), indent=2)}
"""
        memo_text = super().run(prompt)
        self._save_pdf(memo_text, deal_state.get('deal_params', {}))
        return memo_text

    def _clean(self, text: str) -> str:
        replacements = {
            "—": "--", "–": "-", "‒": "-",
            "“": '"', "”": '"', "‘": "'", "’": "'",
            "…": "...", "·": "*", "•": "*",
        }
        for char, sub in replacements.items():
            text = text.replace(char, sub)
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _save_pdf(self, memo_text: str, deal_params: dict):
        os.makedirs("outputs", exist_ok=True)

        pdf = FPDF()
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "CREDIT MEMORANDUM", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Date: {date.today().strftime('%B %d, %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.cell(0, 6, self._clean(f"Property: {deal_params.get('address', 'N/A')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.cell(0, 6, self._clean(f"Borrower: {deal_params.get('borrower', 'N/A')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(8)

        # Divider
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        # Body
        pdf.set_font("Helvetica", "", 10)
        for line in memo_text.split('\n'):
            line = self._clean(line.strip())
            if not line:
                pdf.ln(3)
            elif line.isupper() and len(line) > 3:
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 10)
            else:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(pdf.epw, 5, line)

        address = deal_params.get('address', 'deal').replace(' ', '_').replace(',', '')
        filename = f"outputs/credit_memo_{address[:30]}.pdf"
        pdf.output(filename)
        print(f"\n[MemoAgent] PDF saved to {filename}")