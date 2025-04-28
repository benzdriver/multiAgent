import json
from pathlib import Path

def generate_summary_index(input_dir: Path, output_file: Path):
    index = {}

    for module_dir in input_dir.iterdir():
        if not module_dir.is_dir():
            continue
        summary_path = module_dir / "full_summary.json"
        if not summary_path.exists():
            continue
        try:
            with open(summary_path, "r") as f:
                data = json.load(f)
                module_name = data.get("module_name")
                if module_name:
                    index[module_name] = {
                        "target_path": data.get("target_path", ""),
                        "depends_on": data.get("depends_on", []),
                        "responsibilities": data.get("responsibilities", [])
                    }
        except Exception as e:
            print(f"⚠️ Failed to read {summary_path}: {e}")

    with open(output_file, "w") as f:
        json.dump(index, f, indent=2)

    print(f"✅ summary_index.json written with {len(index)} modules.")
