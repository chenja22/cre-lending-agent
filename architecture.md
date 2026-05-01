# Architecture

## Why Multi-Agent?

The naive approach to this problem is a single prompt: paste in a deal document, ask Claude to underwrite it, get a credit memo back. That works for demos. It breaks in production.

The problem is that CRE underwriting is not one task — it's five distinct tasks with different data sources, different reasoning patterns, and different failure modes. An intake specialist reads documents differently than an underwriter runs stress tests. A market analyst needs live web data that a credit officer doesn't. Collapsing these into one prompt means every failure contaminates everything else, and you can't improve one without risking the others.

A multi-agent architecture solves this by giving each task its own system prompt, its own context, and its own output schema. The orchestrator threads state between agents — each one reads only what it needs, writes only what it produces. When the market agent fails a JSON parse, the underwriting output is unaffected. When you want to improve sponsor credit analysis, you edit one file.

The tradeoff is latency and cost. Five sequential API calls take longer than one. The bet is that reliability and modularity are worth it — which they are for any real production system.

## Agent Design

Each agent extends `BaseAgent`, which wraps the Anthropic SDK and exposes two methods:

- `run()` — standard text completion for the memo agent, which needs prose output
- `run_structured()` — uses `client.beta.messages.parse()` with a Pydantic schema, enforcing output structure at the token generation level

The structured outputs approach replaced an earlier implementation that used JSON prompting + string stripping. That version worked ~85% of the time. The Pydantic approach works 100% of the time because Claude literally cannot generate tokens that violate the schema — it's constrained decoding, not prompt engineering.

The one exception is the market agent, which uses the Anthropic web search tool. Tool use and structured outputs can't be combined in a single API call (tool use requires a free-form response loop), so the market agent runs two passes: a free-form web search pass, then a structured parse pass that converts the raw research into a validated schema.

## State Management

The orchestrator maintains a single `deal_state` dict that accumulates outputs:
deal_state = {
"deal_params": {...}, # populated by intake agent
"underwriting": {...}, # populated by underwriting agent
"market": {...}, # populated by market agent
"credit": {...}, # populated by credit agent
"lender": {...}, # populated by lender agent
"memo": "..." # populated by memo agent
}

Each agent receives only the fields it needs. The underwriting agent gets `deal_params`. The lender agent gets `deal_params` and `underwriting`. The memo agent gets the entire state. This minimizes context window usage and prevents agents from reasoning about data they shouldn't have.

## Financial Logic

Core underwriting calculations live in `tools/calculator.py`, deliberately separated from the agent layer. DSCR, LTV, debt yield, and amortization math are computed locally in Python — not by the LLM — and passed into the underwriting agent as facts. The agent's job is qualitative assessment and condition generation, not arithmetic.

This matters because LLMs make arithmetic errors. Compute the numbers yourself, let the model interpret them.

## Document Parsing

The intake agent uses `pdfplumber` to extract text from offering memorandums and loan applications. Real OMs are messy — tables, columns, image-heavy layouts. `pdfplumber` handles most of it, with the extracted text passed to Claude for structured parameter extraction.

The intake system prompt handles both loan applications (explicit loan amount, borrower, NOI) and offering memorandums (where loan amount must be derived — typically 65% LTV on offering price). This lets the system accept real-world documents without preprocessing.

## Web Search Integration

The market agent uses Anthropic's native web search tool to pull live submarket data — cap rates, vacancy rates, rent trends, recent news. This replaces what would otherwise be stale training data with current market intelligence.

The tool use loop runs until `stop_reason != "tool_use"`, handling multi-step searches where Claude decides to run additional queries based on initial results. In practice, the market agent runs 3-5 searches per deal.

Sources are captured in the structured output and surfaced in the credit memo, providing auditability.

## Lender Program Matching

The sixth agent maps underwriting metrics to loan programs using explicit criteria encoded in the system prompt:

- **Agency (Fannie/Freddie):** Multifamily only, DSCR ≥ 1.25x, LTV ≤ 75%, occupancy ≥ 90%
- **CMBS:** All property types, DSCR ≥ 1.20x, non-recourse, 5-10yr fixed
- **Balance Sheet:** Flexible structure, relationship-driven, recourse typically required
- **Bridge:** Transitional assets, sub-1.0x DSCR acceptable, floating rate, 12-36 months

This mirrors how a real capital markets desk thinks about deal placement. The agent returns eligibility flags for all four programs plus a primary recommendation with rationale.

## Cost

Each full deal run costs approximately $0.10-0.15 using `claude-haiku-4-5`. The market agent uses `claude-sonnet-4-5` for structured parsing (Haiku doesn't support structured outputs), which adds ~$0.05 per run.

Batch mode across three deals runs for roughly $0.45 total.

## What I'd Build Next

- **Async orchestration** — market and credit agents have no data dependency on each other and could run in parallel, cutting latency by ~40%
- **Vector store for comparables** — cache parsed OMs and retrieve similar deals at underwriting time
- **Feedback loop** — track predicted vs actual outcomes on historical deals to calibrate the underwriting thresholds
- **CMBS data integration** — pull live TREPP delinquency data into the stress indicator layer