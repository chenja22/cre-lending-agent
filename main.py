import argparse
import json
import os
from orchestrator import Orchestrator
from ui import console, print_deal_summary, print_batch_summary


def save_result(result: dict, deal_name: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/{deal_name}_result.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(description="CRE Lending Stack")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--deal",  help="Path to a single deal folder or file")
    group.add_argument("--batch", help="Directory of deal subfolders to process in batch")
    args = parser.parse_args()

    orchestrator = Orchestrator()

    if args.deal:
        result = orchestrator.run(args.deal)
        deal_name = os.path.basename(args.deal.rstrip("/"))
        path = save_result(result, deal_name)

        print_deal_summary(result)

        console.rule("[bold]Credit Memo[/bold]", style="dim")
        console.print(result.get("memo", "No memo generated"))
        console.print()
        console.print(f"[dim]Full result saved to {path}[/dim]")

    elif args.batch:
        batch_dir = args.batch.rstrip("/")
        deal_dirs = sorted(
            os.path.join(batch_dir, d)
            for d in os.listdir(batch_dir)
            if os.path.isdir(os.path.join(batch_dir, d))
        )

        if not deal_dirs:
            console.print(f"[red]No deal subdirectories found in {batch_dir}[/red]")
            return

        names = [os.path.basename(d) for d in deal_dirs]
        console.print(f"\n[bold]Found {len(deal_dirs)} deals:[/bold] {', '.join(names)}")

        all_results = {}

        for deal_path in deal_dirs:
            deal_name = os.path.basename(deal_path)
            try:
                result = orchestrator.run(deal_path)
                save_result(result, deal_name)
                all_results[deal_name] = result
            except Exception as e:
                console.print(f"[red][ERROR] {deal_name}: {e}[/red]")
                all_results[deal_name] = {}

        os.makedirs("outputs", exist_ok=True)
        with open("outputs/batch_results.json", "w") as f:
            json.dump(all_results, f, indent=2)

        print_batch_summary(all_results)
        console.print(f"[dim]Full results saved to outputs/batch_results.json[/dim]")


if __name__ == "__main__":
    main()
