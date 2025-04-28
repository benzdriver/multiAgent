import os
import json
from typing import List, Dict
from dependency_graph import dependency_graph

SUMMARY_DIR = "./generated_code"

class MemoryManager:
    def __init__(self, summary_dir: str = SUMMARY_DIR, graph: Dict[str, List[str]] = dependency_graph):
        self.summary_dir = summary_dir
        self.dependency_graph = graph

    def get_relevant_summaries(self, module_name: str) -> List[Dict]:
        visited = set()
        summaries = []

        def dfs(mod):
            if mod in visited:
                return
            visited.add(mod)
            path = os.path.join(self.summary_dir, mod, "summary.json")
            if os.path.exists(path):
                with open(path) as f:
                    summaries.append(json.load(f))
            for dep in self.dependency_graph.get(mod, []):
                dfs(dep)

        dfs(module_name)
        return summaries

    def get_module_source(self, module_name: str) -> str:
        summary_path = os.path.join(self.summary_dir, module_name, "summary.json")
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                summary = json.load(f)
            code_path = os.path.join(self.summary_dir, module_name, summary["filename"])
            if os.path.exists(code_path):
                with open(code_path) as f:
                    return f.read()
        return ""
