# memory/structured_context.py

import json
from pathlib import Path
from typing import Dict, List
from memory.function_signatures import get_function_signatures
from memory.embedding_client import LocalEmbeddingClient

MODULE_SUMMARY_PATH = Path("data/output/modules")
SUMMARY_INDEX_PATH = Path("data/output/summary_index.json")


def load_summary(module_name: str) -> Dict:
    summary_file = MODULE_SUMMARY_PATH / module_name / "full_summary.json"
    if not summary_file.exists():
        raise FileNotFoundError(f"Summary not found for module: {module_name}")
    return json.loads(summary_file.read_text())


def load_summary_index() -> Dict:
    return json.loads(SUMMARY_INDEX_PATH.read_text())


def build_dependency_context(module_data: Dict, summary_index: Dict) -> str:
    ctx_lines = []
    for dep in module_data.get("depends_on", []):
        if dep in summary_index:
            path = summary_index[dep].get("target_path", "unknown")
            ctx_lines.append(f"- {dep} located at `{path}/{dep.lower()}.ts`")
    return "\n".join(ctx_lines)


def get_structured_context(module_name: str) -> str:
    summary = load_summary(module_name)
    summary_index = load_summary_index()

    responsibilities = "\n".join(f"- {r}" for r in summary.get("responsibilities", []))
    key_apis = "\n".join(f"- {a}" for a in summary.get("key_apis", []))
    deps = build_dependency_context(summary, summary_index)
    
    memory = LocalEmbeddingClient()
    memory.load()
    excerpts = memory.query(module_name, top_k=3)
    
    functions = get_function_signatures(module_name)

    context = f"""
You are a senior full-stack developer. Please implement the module **{module_name}** in TypeScript using NestJS.
"""

    if deps:
        context += f"""
This module depends on the following components:
{deps}
"""

    context += f"""
Responsibilities:
{responsibilities}

Key APIs:
{key_apis}
"""

    if functions:
        context += f"\nPreviously defined functions that should be reused or respected:\n"
        for f in functions:
            context += f"- {f}\n"

    if excerpts:
        context += f"\nRelevant architecture excerpts:\n"
        for e in excerpts:
            context += f"- {e}\n"

    context += "\nPlease return only a single code file with no markdown."
    return context.strip()
