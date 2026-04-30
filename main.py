import argparse
import json
import os
from orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="CRE Lending Agent")
    parser.add_argument("--deal", required=True, help="Path to deal folder")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    result = orchestrator.run(args.deal)

    # Save output
    os.makedirs("outputs", exist_ok=True)
    output_path = f"outputs/deal_result.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nFull result saved to {output_path}")
    print("\n--- CREDIT MEMO ---")
    print(result.get("memo", "No memo generated"))

if __name__ == "__main__":
    main()