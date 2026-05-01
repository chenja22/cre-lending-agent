# CRE Lending Stack

A multi-agent AI system for commercial real estate loan underwriting. Drop in a deal package and get a full institutional-grade credit memo, execution recommendation, and browser dashboard in minutes.

Built with the Anthropic Claude API and Claude Code.

---

## What It Does

Most CRE loan underwriting is manual, slow, and siloed. An analyst pulls financials, a separate team runs market comps, a credit officer writes the memo — often over days or weeks.

This system replicates that full workflow with six specialized AI agents coordinated by an orchestrator:

```
Orchestrator
├── Stage 1 · Intake Agent          → parses deal docs, extracts structured parameters
├── Stage 2 · Underwriting Agent    → calculates DSCR, LTV, debt yield, stress tests
├── Stage 3 · Market Agent          → live web search: cap rates, vacancy, rent trends
├── Stage 4 · Credit Agent          → sponsor strength, track record, documentation gaps
├── Stage 5 · Program Matcher       → recommends Agency / CMBS / Balance Sheet / Bridge
└── Stage 6 · Memo Agent            → assembles IC-ready credit memo as PDF
```

Each agent receives structured input, returns a validated Pydantic schema (enforced at the API level via Anthropic's structured outputs beta), and passes context forward. The final output is a full credit memo with a clear APPROVE / CONDITIONAL / DECLINE recommendation and a specific loan execution channel.

---

## Demo

**Single deal:**
```bash
python main.py --deal data/sample_deal
```

**Batch — run all deals in a directory and print a side-by-side comparison:**
```bash
python main.py --batch data/
```

**Browser dashboard:**
```bash
python -m http.server 8000
# open http://localhost:8000/dashboard.html
```

### Terminal output (Rich CLI)

```
────────────────── CRE Lending Stack ──────────────────
──── Stage 1 · Intake ──────────────────────────────────
  ✓  420 W Illinois St, Chicago, IL · multifamily · $6,500,000 loan
──── Stage 2 · Underwriting ────────────────────────────
  ✓  DSCR 1.44x · LTV 65.0% · Debt Yield 11.2% · [PASS]
──── Stage 3 · Market Research ─────────────────────────
  ✓  West Loop / Downtown Chicago · improving · avg cap rate 5.50%
──── Stage 4 · Credit ──────────────────────────────────
  ✓  Sponsor: strong · Rec: approve
──── Stage 5 · Program Matching ────────────────────────
  ✓  Fannie Mae DUS · agency eligible: True · bridge required: False
──── Stage 6 · Credit Memo ─────────────────────────────
  ✓  memo generated

╭─────────────────────────────────────────────────────────╮
│ 420 W Illinois St, Chicago, IL  River North Plaza LLC   │
├──────────────────────┬──────────────────────────────────┤
│ DSCR                 │ 1.44x                            │
│ LTV                  │ 65.0%                            │
│ Debt Yield           │ 11.2%                            │
│ Ann. Debt Service    │ $505,907                         │
│ Stress DSCR          │ 1.22x                            │
│ Flag                 │ PASS                             │
│ Program              │ Fannie Mae DUS                   │
│ Credit Rec           │ approve                          │
╰──────────────────────┴──────────────────────────────────╯
```

### Batch comparison table

```
╭────────────────┬────────┬───────┬────────────┬───────┬──────────────────┬────────────╮
│ Deal           │ DSCR   │ LTV   │ Debt Yield │ Flag  │ Program          │ Credit Rec │
├────────────────┼────────┼───────┼────────────┼───────┼──────────────────┼────────────┤
│ sample_deal    │ 0.96x  │ 71.4% │ 7.5%       │ FAIL  │ Balance Sheet    │ decline    │
│ sample_deal_2  │ 1.44x  │ 65.0% │ 11.2%      │ PASS  │ Fannie Mae DUS   │ approve    │
│ sample_deal_3  │ 1.45x  │ 65.0% │ 11.4%      │ PASS  │ Balance Sheet    │ approve    │
╰────────────────┴────────┴───────┴────────────┴───────┴──────────────────┴────────────╯
```

---

## Architecture

### Agent Design
Each agent extends `BaseAgent`, which wraps the Anthropic API, handles model selection, and exposes two call patterns:
- `run(prompt)` — free-form text response (used by MemoAgent)
- `run_structured(prompt, Schema)` — structured output validated against a Pydantic model via `client.beta.messages.parse()`; schema is enforced at the API level, eliminating JSON parsing failures

### Structured Outputs
All agents except MemoAgent use `run_structured`. Output schemas are defined in `agents/schema.py`:

| Agent | Schema |
|---|---|
| IntakeAgent | `DealParams` |
| UnderwritingAgent | `UnderwritingOutput` |
| MarketAgent | `MarketOutput` |
| CreditAgent | `CreditOutput` |
| ProgramMatcherAgent | `ProgramMatchOutput` |

### State Management
The orchestrator maintains a central `deal_state` dict that accumulates outputs from each agent and passes relevant context downstream.

### Data Flow
```
deal docs (PDF / TXT)
  → IntakeAgent        → DealParams
  → UnderwritingAgent  → UnderwritingOutput  (locally calculated metrics override LLM values)
  → MarketAgent        → MarketOutput        (web search loop → structured parse)
  → CreditAgent        → CreditOutput
  → ProgramMatcherAgent → ProgramMatchOutput  (sees all 4 prior outputs)
  → MemoAgent          → credit memo text + PDF
```

### Program Matcher Logic
The ProgramMatcherAgent evaluates all upstream outputs against real execution criteria:

| Program | Criteria |
|---|---|
| **Fannie Mae DUS / Freddie Mac Optigo** | Multifamily 5+ units, occupancy ≥ 90%, DSCR ≥ 1.25x, LTV ≤ 75%, loan ≥ $1M |
| **CMBS** | Any commercial type, loan ≥ $5M, stabilized, DSCR ≥ 1.25x, LTV ≤ 70% |
| **Balance Sheet** | Flexible — complex structures, relationship deals, loans outside agency/CMBS box |
| **Bridge** | Transitional/value-add, occupancy < 85%, sized to stabilized NOI |

### Market Agent
Uses Anthropic's `web_search_20250305` tool in a tool-use loop to retrieve live submarket data, then passes the free-form results to `run_structured` for schema-validated JSON output.

### Financial Logic
Core underwriting calculations live in `tools/calculator.py`, separate from the agent layer:
- **DSCR** = NOI / Annual Debt Service
- **LTV** = Loan Amount / Appraised Value
- **Debt Yield** = NOI / Loan Amount
- **Annual Debt Service** = standard mortgage amortization formula
- **Stress DSCR** = DSCR recalculated at 8% interest rate

Underwriting thresholds follow institutional CRE lending standards:

| Metric | Strong | Acceptable | Fail |
|---|---|---|---|
| DSCR | > 1.25x | 1.10 – 1.25x | < 1.10x |
| LTV | < 65% | 65 – 75% | > 75% |
| Debt Yield | > 10% | 8 – 10% | < 8% |

---

## Dashboard

`dashboard.html` is a single-file browser dashboard served via `python -m http.server`. It reads `outputs/deal_result.json` (and `outputs/batch_results.json` if present) with no build step.

**Tabs:**
- **Overview** — 8 metric cards + radar spider chart (5-axis normalized deal profile) + deal parameters
- **Underwriting** — animated threshold bars with tick marks, benchmark bar chart, full assessment notes, conditions list
- **Market** — 7 stat cards, market data chart, commentary, demand drivers, risk factors, sources
- **Credit & Program** — sponsor assessment + program recommendation with eligibility tags side-by-side
- **Credit Memo** — full memo rendered from markdown
- **Batch** — comparison table with flag/recommendation pills + normalized 0–10 score bar chart across deals

---

## Setup

**Requirements:** Python 3.9+, Anthropic API key

```bash
git clone https://github.com/chenja22/cre-lending-agent
cd cre-lending-agent
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Single deal
python main.py --deal data/sample_deal

# Batch
python main.py --batch data/

# Dashboard
python -m http.server 8000
```

---

## Project Structure

```
cre-lending-agent/
├── main.py                  # CLI entry point (--deal / --batch)
├── orchestrator.py          # 6-stage agent coordination
├── dashboard.html           # browser dashboard (single file, no build)
├── ui.py                    # Rich CLI helpers (spinners, tables, colors)
├── agents/
│   ├── base.py              # BaseAgent: run() + run_structured()
│   ├── schema.py            # Pydantic output schemas for all agents
│   ├── intake.py            # document parsing + parameter extraction
│   ├── underwriting.py      # financial analysis + credit assessment
│   ├── market.py            # web search + submarket analysis
│   ├── credit.py            # sponsor evaluation
│   ├── program_matcher.py   # loan execution channel recommendation
│   └── memo.py              # credit memo generation + PDF output
├── tools/
│   └── calculator.py        # DSCR, LTV, debt yield, amortization
├── data/
│   ├── sample_deal/         # deal 1: Chicago multifamily TXT
│   ├── sample_deal_2/       # deal 2: Chicago multifamily TXT
│   └── sample_deal_3/       # deal 3: real PDF offering memorandum
└── outputs/                 # generated JSONs, PDFs, batch results
```

---

## Tech Stack

- **[Anthropic Claude API](https://docs.anthropic.com)** — claude-haiku-4-5 for agents, claude-sonnet-4-5 for structured outputs; web search via `web_search_20250305` tool
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** — PDF text extraction (including real offering memorandums)
- **[pydantic](https://docs.pydantic.dev)** — output schema definitions and validation
- **[rich](https://github.com/Textualize/rich)** — colored terminal output, progress spinners, summary tables
- **[fpdf2](https://py-fpdf2.readthedocs.io)** — PDF credit memo generation
- **[Chart.js](https://www.chartjs.org)** — radar, bar, and benchmark charts in the dashboard
- **[marked.js](https://marked.js.org)** — markdown rendering for the memo tab
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — environment management

---

## Cost

Each full deal run costs approximately $0.10–0.20 using claude-haiku-4-5 (structured output calls use claude-sonnet-4-5 and cost slightly more). A batch run across 3 deals is under $0.60.

---

## Background

Built as a portfolio project to demonstrate multi-agent AI system design applied to institutional CRE lending workflows. The underwriting logic, credit standards, and program eligibility criteria reflect real CMBS, agency, and balance-sheet lending practices.

Domain context informed by JPMorgan CRELS (Commercial Real Estate Lending & Structuring) and industry resources including Green Street, The Real Deal, and CoStar.
