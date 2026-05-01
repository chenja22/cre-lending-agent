from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

console = Console(highlight=False)

_FLAG_STYLE    = {"PASS": "bold green", "WATCH": "bold yellow", "FAIL": "bold red"}
_CREDIT_STYLE  = {"approve": "bold green", "conditional": "bold yellow", "decline": "bold red"}


def stage_header(n: int, name: str):
    console.rule(f"[bold blue]Stage {n}[/bold blue]  [dim]·[/dim]  [bold]{name}[/bold]", style="blue dim")


def stage_done(msg: str):
    console.print(f"  [bold green]✓[/bold green]  {msg}")


def print_deal_summary(deal_state: dict):
    deal_params = deal_state.get("deal_params", {})
    uw  = deal_state.get("underwriting", {})
    pm  = deal_state.get("program_match", {})
    cr  = deal_state.get("credit", {})

    flag       = uw.get("flag", "N/A")
    credit_rec = cr.get("credit_recommendation", "N/A")
    address    = deal_params.get("address", "Unknown")
    borrower   = deal_params.get("borrower", "Unknown")

    t = Table(
        title=f"[bold]{address}[/bold]   [dim]{borrower}[/dim]",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2),
        title_justify="left",
    )
    t.add_column("metric", style="dim", min_width=20)
    t.add_column("value",  min_width=28)

    t.add_row("DSCR",             f"{uw.get('dscr', 0):.2f}x")
    t.add_row("LTV",              f"{uw.get('ltv', 0):.1%}")
    t.add_row("Debt Yield",       f"{uw.get('debt_yield', 0):.1%}")
    t.add_row("Ann. Debt Service", f"${uw.get('annual_debt_service', 0):,.0f}")
    t.add_row("Stress DSCR",      f"{uw.get('stress_dscr', 0):.2f}x")
    t.add_row("Flag",             Text(flag,       style=_FLAG_STYLE.get(flag, "")))
    t.add_row("Program",          pm.get("recommended_program", "N/A"))
    t.add_row("Credit Rec",       Text(credit_rec, style=_CREDIT_STYLE.get(credit_rec, "")))

    console.print()
    console.print(t)
    console.print()


def print_batch_summary(results: dict):
    t = Table(
        title="[bold]Batch Comparison[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        padding=(0, 1),
    )
    t.add_column("Deal",        style="bold",  min_width=16)
    t.add_column("DSCR",        justify="right")
    t.add_column("LTV",         justify="right")
    t.add_column("Debt Yield",  justify="right")
    t.add_column("Flag",        justify="center")
    t.add_column("Program",     min_width=18)
    t.add_column("Credit Rec",  justify="center")

    for name, state in results.items():
        uw  = state.get("underwriting", {})
        pm  = state.get("program_match", {})
        cr  = state.get("credit", {})

        flag       = uw.get("flag", "N/A")
        credit_rec = cr.get("credit_recommendation", "N/A")

        t.add_row(
            name,
            f"{uw.get('dscr', 0):.2f}x",
            f"{uw.get('ltv', 0):.1%}",
            f"{uw.get('debt_yield', 0):.1%}",
            Text(flag,       style=_FLAG_STYLE.get(flag, "")),
            pm.get("recommended_program", "N/A"),
            Text(credit_rec, style=_CREDIT_STYLE.get(credit_rec, "")),
        )

    console.print()
    console.print(t)
    console.print()
