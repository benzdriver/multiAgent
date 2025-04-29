#!/usr/bin/env python
"""
运行新版Clarifier，使用OpenAI作为LLM提供者
支持多种运行模式：
- clarify: 标准需求澄清模式
- generate-modules: 生成细粒度架构模块
- check-issues: 检查架构问题
"""
import asyncio
import argparse
from core.clarifier.clarifier import Clarifier
from core.llm.chat_openai import chat as openai_chat

async def main():
    parser = argparse.ArgumentParser(description="运行架构澄清器")
    parser.add_argument("--mode", choices=["clarify", "generate-modules", "check-issues"], 
                       default="clarify", help="运行模式：标准澄清(clarify)、生成细粒度模块(generate-modules)、检查架构问题(check-issues)")
    parser.add_argument("--input", default="data/input", help="输入文件目录")
    parser.add_argument("--output", default="data/output", help="输出目录")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    args = parser.parse_args()
    
    # 创建Clarifier实例，传入LLM调用函数
    clarifier = Clarifier(llm_chat=openai_chat)
    
    if args.mode == "clarify":
        print(f"🚀 以标准澄清模式启动，输入目录: {args.input}，输出目录: {args.output}")
        await clarifier.start()
    
    elif args.mode == "generate-modules":
        print(f"🔍 以生成细粒度模块模式启动，输入目录: {args.input}，输出目录: {args.output}")
        result = await clarifier.generate_granular_modules(
            input_path=args.input, 
            output_path=args.output
        )
        
        print("\n===== 生成结果摘要 =====")
        print(f"✅ 共生成 {result.get('modules_count', 0)} 个细粒度模块")
        print(f"⚠️ 检测到 {result.get('issues_count', 0)} 个架构问题")
        print(f"📂 所有文件已保存到 {args.output}")
    
    elif args.mode == "check-issues":
        print(f"🔍 以检查架构问题模式启动，输出目录: {args.output}")
        
        from core.clarifier.architecture_reasoner import ArchitectureReasoner
        from core.clarifier.architecture_manager import ArchitectureManager
        
        architecture_manager = ArchitectureManager()
        reasoner = ArchitectureReasoner(architecture_manager=architecture_manager)
        
        await clarifier.integrate_legacy_modules(output_path=args.output)
        
        issues = await reasoner.check_all_issues()
        
        print("\n===== 架构问题报告 =====\n")
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        
        if total_issues == 0:
            print("✅ 未检测到架构问题")
        else:
            print(f"⚠️ 共检测到 {total_issues} 个架构问题:")
            
            for issue_type, issue_list in issues.items():
                if issue_list:
                    print(f"\n## {issue_type} ({len(issue_list)}个问题)")
                    if args.verbose:
                        for i, issue in enumerate(issue_list):
                            print(f"{i+1}. {issue}")
                    else:
                        print(f"使用 --verbose 查看详细问题列表")
                else:
                    print(f"\n## {issue_type} (无问题)")
        
        import json
        from pathlib import Path
        
        issues_dir = Path(args.output) / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        
        with open(issues_dir / "architecture_issues.json", "w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)
        print(f"\n📄 问题报告已保存到 {issues_dir / 'architecture_issues.json'}")

if __name__ == "__main__":
    asyncio.run(main())      