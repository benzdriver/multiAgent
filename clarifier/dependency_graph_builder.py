import json
from pathlib import Path

modules_path = Path("data/output/modules")
output_path = Path("data/output/dependency_graph.py")

dependency_graph = {}

for module_dir in modules_path.iterdir():
    summary_file = module_dir / "full_summary.json"
    if not summary_file.exists():
        continue
    with open(summary_file, "r") as f:
        data = json.load(f)
        name = data["module_name"]
        depends = data.get("depends_on", [])
        dependency_graph[name] = depends

# 写入为 Python 文件
with open(output_path, "w") as f:
    f.write("# Auto-generated module dependency graph\n")
    f.write("dependency_graph = ")
    json.dump(dependency_graph, f, indent=2)

print(f"✅ Dependency graph written to {output_path}")