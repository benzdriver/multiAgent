from pathlib import Path

def load_input_documents(input_path: Path) -> str:
    all_text = ""
    for file in sorted(input_path.glob("*.md")):
        all_text += f"\n\n### FILE: {file.name} ###\n\n"
        all_text += file.read_text(encoding="utf-8")
    return all_text
