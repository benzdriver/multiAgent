from pathlib import Path
from clarifier.reader import load_input_documents
from clarifier.summarizer import summarize_text
from clarifier.index_generator import generate_summary_index
from dependency_manager import DependencyManager
import asyncio

def main():
    input_path = Path("data/input")
    output_modules_path = Path("data/output/modules")
    summary_index_path = Path("data/output/summary_index.json")

    print("📥 Loading input documents...")
    all_text = load_input_documents(input_path)

    print("🧠 Summarizing modules...")
    asyncio.run(summarize_text(all_text, output_modules_path))

    print("📦 Generating summary index...")
    generate_summary_index(output_modules_path, summary_index_path)
    
    print("🔗 Building dependency graph...")
    dependency_manager = DependencyManager()
    dependency_manager.build_from_modules(output_modules_path)
    dependency_manager.visualize()
    
    # 检查循环依赖
    cycles = dependency_manager.check_circular_dependencies()
    if cycles["has_cycles"]:
        print("⚠️ 检测到循环依赖:")
        for cycle in cycles["cycles"]:
            print(f"  - {' -> '.join(cycle)} -> {cycle[0]}")
    else:
        print("✅ 没有检测到循环依赖")

    print("🎉 Clarifier complete.")

if __name__ == "__main__":
    main()
