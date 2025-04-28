from pathlib import Path
import json
import re
import asyncio
from typing import Set
from llm.llm_executor import run_prompt
from llm.chat_openai import chat
import tiktoken
from prompt_templates import get_missing_module_summary_prompt

def parse_missing_modules_from_json_report(report_data: dict) -> Set[str]:
    """从JSON格式的验证报告中提取需要修复的模块列表"""
    missing = set()
    
    # 1. 处理AI审查报告中的缺失模块
    ai_review = report_data.get("ai_review", {})
    
    # 从missing_or_redundant_modules字段提取缺失模块
    missing_modules = ai_review.get("missing_or_redundant_modules", {}).get("missing", [])
    for module in missing_modules:
        if module and module != "...":
            # 尝试从描述中提取模块名
            matches = re.findall(r'([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))', module)
            for match in matches:
                missing.add(match)
    
    # 从undefined_dependencies字段提取未定义的依赖
    undefined_deps = ai_review.get("undefined_dependencies", [])
    for dep in undefined_deps:
        if dep and dep != "moduleX":
            missing.add(dep)
    
    # 2. 处理结构扫描中的问题模块
    structure_scan = report_data.get("structure_scan", {})
    
    # 从结构扫描中提取未定义的依赖
    for module, issues in structure_scan.items():
        for issue in issues:
            if "undefined dependency" in issue:
                dep = issue.split("undefined dependency:")[1].strip()
                if dep and dep not in ["too few", "missing"]:
                    missing.add(dep)
    
    # 过滤掉一些常见的误报和占位符
    blacklist = {'too few', 'missing', 'undefined', 'dependency', '...', 'moduleX', 'module A', 'module B'}
    missing = {m for m in missing if m not in blacklist}
    
    return missing

def parse_missing_modules_from_report(report_text: str) -> Set[str]:
    """从Markdown格式的验证报告中提取需要修复的模块列表（向后兼容）"""
    missing = set()
    
    # 1. 查找章节6中的问题模块（结构问题和未定义依赖）
    section_6_match = re.search(r'## \[6\] Module Structure Issues\n(.*?)(?=##|\Z)', report_text, re.DOTALL)
    if section_6_match:
        section_6 = section_6_match.group(1)
        # 提取每行 "- ModuleName → ..." 中的模块名
        for line in section_6.split('\n'):
            if '→' in line and line.startswith('- '):
                module_name = line.split('→')[0].strip('- ').strip()
                if module_name and not module_name.startswith('too few') and not module_name.startswith('missing'):
                    missing.add(module_name)
        
        # 从问题描述中提取未定义的依赖
        undefined_deps = re.findall(r'undefined dependency: ([A-Za-z0-9/]+)', section_6)
        for dep in undefined_deps:
            if dep not in ['too few', 'missing']:
                missing.add(dep)
    
    # 2. 查找章节2中显式提到的缺失模块
    section_2_match = re.search(r'## \[2\] Missing or Redundant Modules\n.*?### Missing:\n(.*?)(?=###|##|\Z)', report_text, re.DOTALL)
    if section_2_match:
        section_2 = section_2_match.group(1)
        # 尝试提取明确提到的模块名（通常是以 "- ModuleName:" 或 "**ModuleName**" 格式）
        module_candidates = re.findall(r'\- \*\*([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))\*\*', section_2)
        module_candidates.extend(re.findall(r'\- ([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))(?:\:|\s|\.)', section_2))
        for module in module_candidates:
            if module.strip():
                missing.add(module.strip())
    
    # 3. 查找章节7中提到的需要添加的模块
    section_7_match = re.search(r'## \[7\] Fix Suggestions\n(.*?)(?=##|\Z)', report_text, re.DOTALL)
    if section_7_match:
        section_7 = section_7_match.group(1)
        # 提取明确提到需要添加的模块
        add_modules = re.findall(r'add(?:ing|ed)?\s+(?:a|the)?\s+([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))', section_7, re.IGNORECASE)
        add_modules.extend(re.findall(r'introduce\s+(?:a|the)?\s+([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))', section_7, re.IGNORECASE))
        add_modules.extend(re.findall(r'\*\*([A-Za-z0-9]+(?:Service|Module|Controller|Repository|Client))\*\*', section_7))
        for module in add_modules:
            if module.strip():
                missing.add(module.strip())
    
    # 过滤掉一些常见的误报
    blacklist = {'too few', 'missing', 'undefined', 'dependency'}
    missing = {m for m in missing if m not in blacklist}
    
    return missing

def get_summary_prompt(i: int, total: int) -> str:
    """从prompt_templates库中获取模块摘要生成prompt"""
    # 由于我们在这里不知道具体的模块名称，使用占位符
    return get_missing_module_summary_prompt("moduleX")

def parse_json(text: str):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned)
    return json.loads(cleaned.strip())

async def fix_missing_modules(modules_to_fix: Set[str], output_dir: Path):
    tokenizer = tiktoken.encoding_for_model("gpt-4o")

    for i, name in enumerate(sorted(modules_to_fix)):
        print(f"🧠 Generating summary for: {name}")
        prompt = f"Missing module: **{name}**"

        result = await run_prompt(
            chat=chat,
            user_message=prompt,
            model="gpt-4o",
            tokenizer=tokenizer,
            max_input_tokens=2000,
            parse_response=parse_json,
            get_system_prompt=get_summary_prompt,
        )

        try:
            parsed = result
            resolved_path = parsed.get("target_path", "backend/services")
            save_path = output_dir / resolved_path / parsed["module_name"].lower()
            save_path.mkdir(parents=True, exist_ok=True)

            with open(save_path / "full_summary.json", "w") as f:
                json.dump(parsed, f, indent=2)

            print(f"✅ Fixed: {parsed['module_name']} → {resolved_path}/")
        except Exception as e:
            print(f"❌ Failed to write summary for {name}: {e}")

def fix_all():
    # 优先使用JSON格式的报告
    json_report_path = Path("data/validator_report.json")
    md_report_path = Path("data/validator_report.md")
    module_path = Path("data/output/modules")

    to_fix = set()
    
    # 先尝试读取JSON格式报告
    if json_report_path.exists():
        print("📊 Found JSON validator report, using structured data...")
        try:
            report_data = json.loads(json_report_path.read_text())
            to_fix = parse_missing_modules_from_json_report(report_data)
        except Exception as e:
            print(f"❌ Error parsing JSON report: {e}")
    
    # 如果没有JSON报告或解析失败，尝试读取Markdown格式报告
    if not to_fix and md_report_path.exists():
        print("📝 Using Markdown validator report as fallback...")
        report_text = md_report_path.read_text()
        to_fix = parse_missing_modules_from_report(report_text)

    if not to_fix:
        print("✅ No modules to fix found in validator reports.")
        return

    print("🛠️ Modules to fix:", sorted(to_fix))
    asyncio.run(fix_missing_modules(to_fix, module_path))
