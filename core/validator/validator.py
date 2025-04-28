import json
import asyncio
from pathlib import Path
from core.llm.llm_executor import run_prompt, split_text_by_tokens
from core.llm.chat_openai import chat
import tiktoken
from dependency_manager import DependencyManager
import re
import time
from prompt_templates import get_validator_prompt as get_template_prompt
from architecture.module_validator import is_valid_module_name, validate_module_dependencies
import copy

def get_validator_prompt(i, total, boundary_analysis=None):
    """从prompt_templates库中获取验证器prompt"""
    return get_template_prompt(i + 1, total, boundary_analysis)

def parse_json_response(text: str) -> dict:
    """解析LLM返回的JSON响应，处理各种常见的格式问题
    
    增强版本: 处理更多边缘情况，确保有效JSON
    """
    if not text:
        return {}
    
    # 记录原始文本以便调试
    original_text = text
    
    # 1. 清理文本
    text = text.strip()
    
    # 2. 移除markdown代码块标记
    code_block_pattern = r'```(?:json|javascript|js|JSON)?(.+?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        # 使用找到的第一个代码块内容
        text = matches[0].strip()
    else:
        # 如果没有找到代码块，也处理可能的单行代码标记
        if text.startswith('```'):
            text = text[text.find('\n')+1:]
        if text.endswith('```'):
            text = text[:text.rfind('```')]
        text = text.strip()
    
    # 3. 尝试直接解析JSON
    try:
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError:
        print(f"⚠️ 初次JSON解析失败，尝试修复格式问题...")
    
    # 4. 查找并提取最外层的JSON对象
    try:
        # 查找第一个 { 和最后一个 } 之间的内容
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            extracted_text = text[start_idx:end_idx+1]
            try:
                return json.loads(extracted_text)
            except:
                print(f"⚠️ 提取JSON对象后仍然无法解析")
    except Exception as e:
        print(f"⚠️ 提取JSON失败: {e}")
    
    # 5. 尝试修复常见的JSON语法问题
    try:
        # 5.1 将单引号替换为双引号（JavaScript风格 -> JSON）
        fixed_text = re.sub(r"'([^']*)':", r'"\1":', text)
        # 5.2 给没有引号的键添加引号
        fixed_text = re.sub(r'([{,])\s*([a-zA-Z0-9_]+):', r'\1"\2":', fixed_text)
        # 5.3 删除结尾的逗号
        fixed_text = re.sub(r',\s*}', '}', fixed_text)
        fixed_text = re.sub(r',\s*]', ']', fixed_text)
        
        try:
            parsed = json.loads(fixed_text)
            print("✅ 成功通过修复JSON语法解析")
            return parsed
        except:
            print("⚠️ 修复JSON语法后仍然无法解析")
    except Exception as e:
        print(f"⚠️ 修复JSON语法时出错: {e}")
    
    # 6. 使用正则表达式尝试构建JSON对象
    try:
        # 尝试提取所有键值对
        pairs = re.findall(r'"([^"]+)"\s*:\s*("([^"\\]*(\\.[^"\\]*)*)"|\[.*?\]|{.*?}|true|false|null|-?\d+(\.\d+)?)', text)
        if pairs:
            json_obj = {}
            for pair in pairs:
                key = pair[0]
                value = pair[1]
                
                # 处理字符串值
                if value.startswith('"') and value.endswith('"'):
                    json_obj[key] = value[1:-1]
                # 处理数组值
                elif value.startswith('[') and value.endswith(']'):
                    try:
                        json_obj[key] = json.loads(value)
                    except:
                        json_obj[key] = []
                # 处理对象值
                elif value.startswith('{') and value.endswith('}'):
                    try:
                        json_obj[key] = json.loads(value)
                    except:
                        json_obj[key] = {}
                # 处理布尔值和null
                elif value in ['true', 'false', 'null']:
                    json_obj[key] = json.loads(value)
                # 处理数字
                else:
                    try:
                        json_obj[key] = float(value) if '.' in value else int(value)
                    except:
                        json_obj[key] = value
            
            if json_obj:
                print("✅ 成功通过正则表达式构建JSON对象")
                return json_obj
    except Exception as e:
        print(f"⚠️ 使用正则表达式构建JSON时出错: {e}")
    
    # 7. 最后尝试：如果完全无法解析，返回部分结构化数据
    print(f"❌ 所有解析方法均失败，返回空对象")
    print(f"原始文本的前200个字符: {original_text[:200]}")
    return {}

def custom_merge_sections(acc, current):
    """简单收集结果用于调试
    
    Args:
        acc: 累积的结果
        current: 当前需要合并的结果
        
    Returns:
        合并后的结果
    """
    # 收集结果用于调试
    if not hasattr(custom_merge_sections, 'all_results'):
        custom_merge_sections.all_results = []
    
    if current:
        custom_merge_sections.all_results.append(current)
    
    # 总是返回第一个有效结果
    return current if not acc else acc

def check_module_structure(summary: dict, summary_index: dict, issues: dict):
    """检查模块的结构性问题，更加容错"""
    name = summary.get("module_name", "<unknown>")
    problems = []

    # 使用module_validator验证模块名称
    is_valid, error = is_valid_module_name(name)
    if not is_valid:
        problems.append(f"invalid module name: {error}")

    # 检查职责
    if not summary.get("responsibilities"):
        problems.append("missing responsibilities")
    elif isinstance(summary["responsibilities"], list) and len(summary["responsibilities"]) < 2:
        problems.append("too few responsibilities")
    elif not isinstance(summary["responsibilities"], list):
        problems.append("responsibilities should be an array")

    # 检查API
    if not summary.get("key_apis"):
        problems.append("missing key_apis")
    elif not isinstance(summary["key_apis"], list):
        problems.append("key_apis should be an array")

    # 检查数据输入输出
    if not summary.get("data_inputs"):
        problems.append("missing data_inputs")
    elif not isinstance(summary["data_inputs"], list):
        problems.append("data_inputs should be an array")

    if not summary.get("data_outputs"):
        problems.append("missing data_outputs")
    elif not isinstance(summary["data_outputs"], list):
        problems.append("data_outputs should be an array")

    # 检查目标路径
    if not summary.get("target_path"):
        problems.append("missing target_path")
    
    # 检查依赖
    depends_on = summary.get("depends_on", [])
    if not isinstance(depends_on, list):
        problems.append("depends_on should be an array")
        # 尝试转换非列表依赖为列表
        try:
            if isinstance(depends_on, str):
                depends_on = [depends_on]
        except:
            depends_on = []
    
    # 使用module_validator验证依赖关系
    if isinstance(depends_on, list) and name and len(depends_on) > 0:
        dependency_errors = validate_module_dependencies(name, depends_on)
        if dependency_errors:
            problems.extend(dependency_errors)
    
    # 检查未定义依赖
    for dep in depends_on:
        if dep and dep not in summary_index and dep != name:  # 避免自依赖
            problems.append(f"undefined dependency: {dep}")

    if problems:
        issues[name] = problems
    
    return len(problems) == 0  # 返回是否检查通过

def analyze_module_boundaries(summaries, dependency_manager):
    """分析模块边界和合并建议，增加容错处理"""
    merge_suggestions = []
    split_suggestions = []
    
    try:
        # 分析可能需要合并的模块（基于命名相似性）
        name_patterns = {}
        for summary in summaries:
            name = summary.get("module_name", "")
            if not name:
                continue
                
            # 提取基本名称（去掉Controller、Service、Repository等后缀）
            base_name = re.sub(r'(Controller|Service|Repository|Page|Model)$', '', name)
            if base_name not in name_patterns:
                name_patterns[base_name] = []
            name_patterns[base_name].append(name)
        
        for base, modules in name_patterns.items():
            if len(modules) > 1:
                # 检查这些模块是否有重叠职责
                module_map = {m: next((s for s in summaries if s.get("module_name") == m), {}) for m in modules}
                responsibilities = {}
                for m, data in module_map.items():
                    for resp in data.get("responsibilities", []):
                        if not resp:
                            continue
                        resp_key = resp.lower()
                        if resp_key not in responsibilities:
                            responsibilities[resp_key] = []
                        responsibilities[resp_key].append(m)
                
                overlapping = [r for r, ms in responsibilities.items() if len(ms) > 1]
                if overlapping:
                    merge_suggestions.append({
                        "modules": modules,
                        "reason": f"命名相似且职责重叠: {', '.join(overlapping[:3])}"
                    })
        
        # 检查循环依赖，可能需要合并
        cycles = dependency_manager.check_circular_dependencies()
        if cycles["has_cycles"]:
            for cycle in cycles["cycles"]:
                if len(cycle) > 1:
                    merge_suggestions.append({
                        "modules": cycle,
                        "reason": f"存在循环依赖: {' -> '.join(cycle)} -> {cycle[0]}"
                    })
        
        # 检查依赖过多的模块（可能需要拆分）
        for module_name, data in dependency_manager.graph.items():
            if len(data.get("depends_on", [])) > 5:  # 依赖过多可能需要拆分
                split_suggestions.append({
                    "module": module_name,
                    "reason": f"依赖过多 ({len(data['depends_on'])} 个依赖)"
                })
            if len(data.get("depended_by", [])) > 5:  # 被过多模块依赖可能需要拆分
                split_suggestions.append({
                    "module": module_name,
                    "reason": f"被过多模块依赖 ({len(data['depended_by'])} 个模块)"
                })
        
        # 分析责任过多的模块
        for summary in summaries:
            name = summary.get("module_name", "")
            resps = summary.get("responsibilities", [])
            if isinstance(resps, list) and len(resps) > 8:  # 责任过多可能需要拆分
                split_suggestions.append({
                    "module": name,
                    "reason": f"责任过多 ({len(resps)} 个责任)"
                })
    except Exception as e:
        print(f"⚠️ 分析模块边界时出错: {e}")
    
    return {
        "merge_suggestions": merge_suggestions,
        "split_suggestions": split_suggestions
    }

async def run_validator(modules_to_check=None):
    """验证架构
    
    Args:
        modules_to_check: 可选，指定要检查的模块列表，None表示检查所有模块
    """
    input_path = Path("data/input")
    module_path = Path("data/output/modules")
    summary_index_path = Path("data/output/summary_index.json")
    output_json_path = Path("data/validator_report.json")

    requirement_docs = [f.read_text() for f in input_path.glob("*.md")]
    requirement_text = "\n\n".join(requirement_docs)

    # 加载模块摘要
    summaries = []
    for path in module_path.glob("*/full_summary.json"):
        try:
            # 如果指定了要检查的模块，只加载这些模块
            if modules_to_check:
                module_name = path.parent.name
                if module_name not in modules_to_check:
                    continue
            summaries.append(json.loads(path.read_text()))
        except Exception as e:
            print(f"⚠️ 无法解析 {path}: {e}")

    # 加载和更新索引
    summary_index = {}
    if summary_index_path.exists():
        try:
            summary_index = json.loads(summary_index_path.read_text())
        except Exception as e:
            print(f"⚠️ 无法加载索引: {e}")
    
    # 更新索引
    for summary in summaries:
        name = summary.get("module_name")
        if name:
            summary_index[name] = {
                "target_path": summary.get("target_path", ""),
                "depends_on": summary.get("depends_on", [])
            }
    
    # 保存更新后的索引
    summary_index_path.parent.mkdir(parents=True, exist_ok=True)
    summary_index_path.write_text(json.dumps(summary_index, indent=2))
    
    # 加载依赖图
    dependency_manager = DependencyManager()
    if not Path("data/output/dependency_graph.json").exists():
        dependency_manager.build_from_modules(module_path)
    
    # 分析模块边界
    boundary_analysis = analyze_module_boundaries(summaries, dependency_manager)
    print(f"🔍 边界分析完成:")
    print(f"  - 合并建议: {len(boundary_analysis['merge_suggestions'])}")
    print(f"  - 拆分建议: {len(boundary_analysis['split_suggestions'])}")

    # 清理之前可能存在的结果
    if hasattr(custom_merge_sections, 'all_results'):
        delattr(custom_merge_sections, 'all_results')
    
    # AI验证部分的代码
    if not modules_to_check and summaries:
        # 加载之前的AI结果，如果存在
        if output_json_path.exists():
            try:
                previous_result = json.loads(output_json_path.read_text())
                ai_result = previous_result.get("ai_review", {})
            except:
                pass
        
        # 准备LLM验证的输入
        full_text = requirement_text + "\n\nSummaries:\n" + json.dumps(summaries, indent=2)
        
        try:
            tokenizer = tiktoken.encoding_for_model("gpt-4o")
            token_count = len(tokenizer.encode(full_text))
        except Exception as e:
            print(f"⚠️ 无法初始化tiktoken，使用近似计算: {str(e)}")
            # 使用简单的字符计数作为备选方案（假设平均每4个字符约等于1个token）
            token_count = len(full_text) // 4
        
        print(f"🧠 通过LLM验证架构和摘要...")
        print(f"📊 总输入大小: {token_count} tokens")
        
        # 限制输入大小，避免过大的文本
        if token_count > 100000:  # 超过10万tokens，可能太大了
            print(f"⚠️ 输入文本过大，进行截断...")
            # 只保留摘要的简要信息
            brief_summaries = []
            for s in summaries:
                brief_summary = {
                    "module_name": s.get("module_name", ""),
                    "responsibilities": s.get("responsibilities", [])[:3],  # 只保留前3个职责
                    "depends_on": s.get("depends_on", []),
                    "layer_type": s.get("layer_type", "")
                }
                brief_summaries.append(brief_summary)
            
            full_text = requirement_text + "\n\nSummaries (abbreviated):\n" + json.dumps(brief_summaries, indent=2)
            print(f"📊 截断后大小: {len(tokenizer.encode(full_text))} tokens")
        
        # 尝试多次解析，提高成功率
        for attempt in range(3):  # 最多尝试3次
            try:
                # 使用run_prompt进行处理，但提供自定义合并函数
                print(f"📦 启动第 {attempt+1} 次验证尝试...")
                
                # 明确告知LLM我们会分段发送
                def get_enhanced_prompt(i, total):
                    base_prompt = get_validator_prompt(i, total, boundary_analysis)
                    
                    # 对第一部分添加特殊指令
                    if i == 0 or i == 1:
                        return base_prompt + "\n\n重要说明：我将分多个部分发送文档，请在收到全部内容后再进行分析回复。"
                    
                    # 对最后一部分添加特殊指令
                    if i == total:
                        return base_prompt + "\n\n这是最后一部分，请基于全部接收到的内容提供完整分析。必须使用JSON格式返回结果。"
                    
                    # 对中间部分
                    return "继续接收第 " + str(i) + "/" + str(total) + " 部分内容。请等待完整接收所有部分后再回复。"
                
                print("📦 开始验证处理...")
                # 使用较大的max_input_tokens来减少分块数量
                ai_result = await run_prompt(
                    chat=chat,
                    user_prompt=full_text,
                    model="gpt-4o",
                    tokenizer=tokenizer,
                    max_input_tokens=15000,  # 增加单块大小以减少分块数
                    parse_response=parse_json_response,
                    merge_result=custom_merge_sections,  # 使用自定义的非递归合并函数
                    get_system_prompt=get_enhanced_prompt,  # 使用增强的系统提示
                    use_pipeline=False  # 关闭流水线模式，使用串行处理
                )
                
                # 检查结果是否有效
                if ai_result and isinstance(ai_result, dict) and "functional_coverage" in ai_result:
                    print("✅ 成功获取AI验证结果")
                    break
                else:
                    print(f"⚠️ 尝试 {attempt+1}/3: AI结果无效，重试...")
                    time.sleep(10)  # 等待10秒后重试
            except Exception as e:
                print(f"⚠️ 尝试 {attempt+1}/3: AI验证失败 - {str(e)[:200]}")
                time.sleep(10)  # 等待10秒后重试
        
        if not ai_result or not isinstance(ai_result, dict) or "functional_coverage" not in ai_result:
            print("❌ 无法获取有效的AI验证结果，使用默认空结构")
            ai_result = {
                "functional_coverage": {"conclusion": "❓", "explanation": "验证失败"},
                "missing_or_redundant_modules": {"missing": [], "redundant": []},
                "overlapping_responsibilities": [],
                "undefined_dependencies": [],
                "suggestions": ["由于技术原因，无法完成完整验证"]
            }

        # 在run_prompt之后，处理收集到的所有结果
        if hasattr(custom_merge_sections, 'all_results') and custom_merge_sections.all_results:
            print(f"📝 合并所有收集到的结果 ({len(custom_merge_sections.all_results)} 个块)...")
            
            # 将所有结果写入临时文件以便查看
            temp_file = Path("data/temp_collected_results.json")
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file.write_text(json.dumps(custom_merge_sections.all_results, indent=2))
            print(f"✍️ 原始结果已写入: {temp_file}")
            
            # 这里先使用第一个结果作为基础结构
            ai_result = custom_merge_sections.all_results[0] if custom_merge_sections.all_results else {}
            
            # 清理收集到的结果
            delattr(custom_merge_sections, 'all_results')

    # 结构验证
    local_structure_issues = {}
    for path in module_path.glob("*/full_summary.json"):
        try:
            # 如果指定了要检查的模块，只检查这些模块
            module_name = path.parent.name
            if modules_to_check and module_name not in modules_to_check:
                continue
                
            data = json.loads(path.read_text())
            check_module_structure(data, summary_index, local_structure_issues)
        except Exception as e:
            module_name = path.parent.name
            local_structure_issues[module_name] = [f"failed to parse: {e}"]

    # 如果保留之前的结构问题
    if modules_to_check and output_json_path.exists():
        try:
            previous_report = json.loads(output_json_path.read_text())
            previous_issues = previous_report.get("structure_scan", {})
            
            # 保留未修改模块的问题
            for module, issues in previous_issues.items():
                if module not in modules_to_check and module not in local_structure_issues:
                    local_structure_issues[module] = issues
        except:
            pass

    # 生成报告
    report = {
        "ai_review": ai_result,
        "structure_scan": local_structure_issues,
        "boundary_analysis": boundary_analysis
    }
    
    # 保存报告
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, indent=2))
    
    print(f"✅ 结构化报告已写入 {output_json_path}")
    
    # 返回问题计数
    issue_count = sum(len(issues) for _, issues in local_structure_issues.items())
    issue_count += len(ai_result.get("overlapping_responsibilities", []))
    issue_count += len(ai_result.get("undefined_dependencies", []))
    issue_count += len(ai_result.get("missing_or_redundant_modules", {}).get("missing", []))
    issue_count += len(ai_result.get("missing_or_redundant_modules", {}).get("redundant", []))
    
    return {
        "total_issues": issue_count,
        "structure_issues": sum(len(issues) for _, issues in local_structure_issues.items()),
        "overlapping": len(ai_result.get("overlapping_responsibilities", [])),
        "undefined": len(ai_result.get("undefined_dependencies", [])),
        "missing": len(ai_result.get("missing_or_redundant_modules", {}).get("missing", [])),
        "redundant": len(ai_result.get("missing_or_redundant_modules", {}).get("redundant", []))
    }

if __name__ == "__main__":
    result = asyncio.run(run_validator())
    print(f"🔍 验证结果: 发现 {result['total_issues']} 个问题")
    print(f"  - 结构问题: {result['structure_issues']}")
    print(f"  - 重叠责任: {result['overlapping']}")
    print(f"  - 未定义依赖: {result['undefined']}")
    print(f"  - 缺失模块: {result['missing']}")
    print(f"  - 冗余模块: {result['redundant']}")
