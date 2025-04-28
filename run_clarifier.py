from clarifier.reader import load_input_documents
from clarifier.summarizer import summarize_text
from clarifier.index_generator import generate_summary_index
from pathlib import Path
import asyncio
import json

def run_clarifier():
    input_path = Path("data/input")
    output_modules_path = Path("data/output/modules")
    summary_index_path = Path("data/output/summary_index.json")

    print("📥 Step 1: Loading input documents...")
    all_text = load_input_documents(input_path)

    print("🧠 Step 2: Summarizing modules...")
    asyncio.run(summarize_text(all_text, output_modules_path))

    print("🗂️ Step 3: Generating summary index...")
    generate_summary_index(output_modules_path, summary_index_path)

    print("📦 Available modules:")
    for mod_dir in sorted(output_modules_path.iterdir()):
        if (mod_dir / "full_summary.json").exists():
            print(f"- {mod_dir.name}")

if __name__ == "__main__":
    run_clarifier()
