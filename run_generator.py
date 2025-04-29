# run_generator.py

import argparse
import json
import asyncio
from pathlib import Path
from core.generator.autogen_module_generator import generate_module
from memory.structured_context import get_structured_context

def run_code_generation(only=None):
    input_dir = Path("data/output/modules")
    output_dir = Path("data/generated_code")
    summary_index_path = Path("data/output/summary_index.json")

    if not summary_index_path.exists():
        print("❌ summary_index.json not found. Please run run_clarifier.py first.")
        return

    tasks = []

    for mod_dir in sorted(input_dir.iterdir()):
        summary_path = mod_dir / "full_summary.json"
        if not summary_path.exists():
            continue

        with open(summary_path, "r") as f:
            module_data = json.load(f)

        module_name = module_data["module_name"]
        if only and module_name not in only:
            continue

        prompt = get_structured_context(module_name)
        target_path = output_dir / module_data.get("target_path", "misc")
        tasks.append(generate_module(module_name, prompt, target_path))

    if not tasks:
        print("⚠️ No modules matched.")
        return

    print(f"🚀 Generating {len(tasks)} module(s)...")
    asyncio.run(asyncio.gather(*tasks))
    print("✅ Code generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", help="Specify which modules to generate")
    parser.add_argument("--all", action="store_true", help="Generate all modules")
    args = parser.parse_args()

    if args.all:
        run_code_generation()
    elif args.only:
        run_code_generation(only=set(args.only))
    else:
        print("❌ Please specify --only <modules> or use --all")
