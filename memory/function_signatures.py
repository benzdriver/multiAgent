# memory/function_signatures.py

import re
import json
from pathlib import Path
from typing import List

GENERATED_CODE_DIR = Path("data/generated_code")
SUMMARY_INDEX_PATH = Path("data/output/summary_index.json")

TS_FUNC_PATTERN = re.compile(r"(?:export\s+)?function\s+(\w+)\s*\(")
CLASS_METHOD_PATTERN = re.compile(r"(\w+)\s*\((.*?)\)\s*{")


def extract_functions_from_file(file_path: Path) -> List[str]:
    content = file_path.read_text(errors="ignore")
    lines = []

    # Extract top-level functions
    for match in TS_FUNC_PATTERN.finditer(content):
        fn = match.group(1)
        lines.append(fn + "(...)")

    # Extract class methods
    class_body = re.findall(r"class\s+\w+\s*{(.*?)}", content, re.DOTALL)
    for body in class_body:
        for match in CLASS_METHOD_PATTERN.finditer(body):
            fn = match.group(1)
            if fn not in ["constructor"]:
                lines.append(fn + "(...)")

    return list(set(lines))


def get_function_signatures(module_name: str) -> List[str]:
    if not SUMMARY_INDEX_PATH.exists():
        return []

    summary_index = json.loads(SUMMARY_INDEX_PATH.read_text())
    target_info = summary_index.get(module_name)
    if not target_info:
        return []

    target_path = target_info.get("target_path", "unsure")
    module_path = GENERATED_CODE_DIR / target_path / f"{module_name.lower()}.ts"

    if not module_path.exists():
        return []

    return extract_functions_from_file(module_path)
