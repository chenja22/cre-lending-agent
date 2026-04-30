# CRE Lending Agent

A multi-agent AI system for commercial real estate loan underwriting. Drop in a deal package and get a full institutional-grade credit memorandum in minutes.

Built with the Anthropic Claude API and Claude Code.

## What It Does

Most CRE loan underwriting is manual, slow, and siloed. An analyst pulls financials, a separate team runs market comps, a credit officer writes the memo — often over days or weeks.

This system replicates that workflow with five specialized AI agents coordinated by an orchestrator:
```
Orchestrator
├── Intake Agent -> parses deal documents, extracts structured parameters
├── Underwriting Agent -> calculates DSCR, LTV, debt yield, stress tests
├── Market Agent -> submarket analysis, cap rates, vacancy, rent trends
├── Credit Agent -> sponsor strength, track record, documentation gaps
└── Memo Agent -> assembles IC-ready credit memorandum as PDF
```
Each agent receives structured input, returns structured JSON, and passes context forward. The final output is a full credit memo with a clear APPROVE / CONDITIONAL / DECLINE recommendation.

---

## Demo

```bash
python main.py --deal data/sample_deal
```

**Sample deal:** 50-unit multifamily, Chicago (Lakeview), $8M loan ask, 6.75% fixed, 30-year amortization.

**Output (truncated):**
[IntakeAgent] Running...
[IntakeAgent] Done.
[UnderwritingAgent] Running...
[UnderwritingAgent] Done.
[MarketAgent] Running...
[MarketAgent] Done.
[CreditAgent] Running...
[CreditAgent] Done.
[MemoAgent] Running...
[MemoAgent] Done. PDF saved to outputs/credit_memo_2847_N_Halsted.pdf
RECOMMENDATION: DECLINE
DSCR: 0.96x | LTV: 71.4% | Debt Yield: 7.5% | Stress DSCR: 0.81x

The full credit memo PDF is saved to `outputs/`.

---

## Architecture

### Agent Design
Each agent extends `BaseAgent`, which handles the Anthropic API call, model selection, and token management. Agents are stateless — they receive a prompt, return a response.

### State Management
The orchestrator maintains a central `deal_state` dict that accumulates outputs from each agent and passes relevant context downstream. No agent sees more than it needs.

### Data Flow
deal docs (PDF/TXT)
→ IntakeAgent → deal_params (JSON)
→ UnderwritingAgent → underwriting metrics + qualitative assessment (JSON)
→ MarketAgent → submarket analysis (JSON)
→ CreditAgent → sponsor credit assessment (JSON)
→ MemoAgent → full credit memo (text + PDF)

### Financial Logic
Core underwriting calculations are handled in `tools/calculator.py`, separate from the agent layer:
- **DSCR** = NOI / Annual Debt Service
- **LTV** = Loan Amount / Appraised Value  
- **Debt Yield** = NOI / Loan Amount
- **Annual Debt Service** = standard mortgage amortization formula
- **Stress DSCR** = DSCR recalculated at 8% interest rate

Underwriting thresholds follow institutional CRE lending standards:
| Metric | Strong | Acceptable | Fail |
|--------|--------|------------|------|
| DSCR | >1.25x | 1.10–1.25x | <1.10x |
| LTV | <65% | 65–75% | >75% |
| Debt Yield | >10% | 8–10% | <8% |

---

## Setup

**Requirements:** Python 3.9+, Anthropic API key

```bash
# Clone and install
git clone https://github.com/chenja22/cre-lending-agent
cd cre-lending-agent
pip install -r requirements.txt

# Add API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run on sample deal
python main.py --deal data/sample_deal
```

---

## Project Structure
cre-lending-agent/
├── main.py # entry point
├── orchestrator.py # agent coordination + state management
├── agents/
│   ├── base.py # shared agent class (Anthropic API wrapper)
│   ├── intake.py # document parsing + parameter extraction
│   ├── underwriting.py  # financial analysis + credit assessment
│   ├── market.py # submarket research
│   ├── credit.py # sponsor evaluation
│   └── memo.py # credit memo generation + PDF output
├── tools/
│   └── calculator.py # DSCR, LTV, debt yield, amortization
├── data/
│   └── sample_deal/ # sample deal documents (TXT/PDF)
├── outputs/ # generated credit memos land here
└── tests/ # agent unit tests

---

## Tech Stack

- [Anthropic Claude API](https://docs.anthropic.com)** — claude-haiku-4-5 for fast, cost-efficient agent calls
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [pydantic](https://docs.pydantic.dev) — data validation
- [fpdf2](https://py-fpdf2.readthedocs.io) — PDF generation
- [python-dotenv](https://github.com/theskumar/python-dotenv) — environment management

---

## Cost

Each full deal run costs approximately $0.10–0.15 using claude-haiku-4-5. For development, the model can be swapped to any Claude model in `agents/base.py`.

---

## Background

Built as a portfolio project to demonstrate multi-agent AI system design applied to institutional CRE lending workflows. The underwriting logic and credit standards reflect real CMBS and balance-sheet lending practices.

Domain context informed by JPMorgan CRELS (Commercial Real Estate Lending & Structuring) and industry resources including Green Street, The Real Deal, and CoStar.