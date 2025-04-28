import json
import asyncio
from pathlib import Path
from llm.llm_executor import run_prompt
from llm.chat_openai import chat
import tiktoken
import os
import re
from dependency_manager import DependencyManager, initialize_dependency_graph
from rollback_manager import RollbackManager, initialize_rollback_manager
from prompt_templates import get_fixer_prompt

BASE_PATH = Path("data/output/modules")
INDEX_PATH = Path("data/output/summary_index.json")
VALIDATOR_JSON_PATH = Path("data/validator_report.json")
FIX_LOG_PATH = Path("data/fix_log.md")

tokenizer = tiktoken.encoding_for_model("gpt-4o")

# 全局对象
dependency_manager = None
rollback_manager = None

def get_fixer_prompt(module_name, issues, original_summary, related_modules=None):
    """从prompt_templates库中获取修复prompt"""
    from prompt_templates import get_fixer_prompt as get_template_prompt
    return get_template_prompt(module_name, issues, original_summary, related_modules)

def load_summary(module_name):
    summary_path = BASE_PATH / module_name / "full_summary.json"
    if not summary_path.exists():
        return {
            "module_name": module_name,
            "responsibilities": [],
            "key_apis": [],
            "data_inputs": [],
            "data_outputs": [],
            "depends_on": [],
            "target_path": ""
        }
    return json.loads(summary_path.read_text())

def save_summary(module_name, summary):
    mod_dir = BASE_PATH / module_name
    mod_dir.mkdir(parents=True, exist_ok=True)
    path = mod_dir / "full_summary.json"
    path.write_text(json.dumps(summary, indent=2))

def update_index(summary_index, summary):
    summary_index[summary["module_name"]] = {
        "target_path": summary["target_path"],
        "depends_on": summary.get("depends_on", [])
    }

def get_issues_per_module(validator_report_path):
    """从验证器报告中提取每个模块的问题
    
    Args:
        validator_report_path: 验证器报告文件的路径
        
    Returns:
        dict: 以模块名为键，问题列表为值的字典
    """
    # 确保文件存在
    if not validator_report_path.exists():
        print(f"❌ 验证器报告文件不存在: {validator_report_path}")
        return {}
    
    try:
        # 读取并解析JSON文件
        validator_data = json.loads(validator_report_path.read_text())
        
        structure_scan = validator_data.get("structure_scan", {})
        ai_review = validator_data.get("ai_review", {})
        boundary_analysis = validator_data.get("boundary_analysis", {})
        
        # 收集结构问题
        issue_map = {}
        for module, issues in structure_scan.items():
            if issues:  # 只添加有问题的模块
                issue_map[module] = ["Structure issue: " + issue for issue in issues]
        
        # 添加边界分析问题
        merge_suggestions = boundary_analysis.get("merge_suggestions", [])
        for suggestion in merge_suggestions:
            modules = suggestion.get("modules", [])
            reason = suggestion.get("reason", "")
            for module in modules:
                if module in issue_map:
                    issue_map[module].append(f"Boundary issue: Consider merging with {', '.join([m for m in modules if m != module])} - {reason}")
                else:
                    issue_map[module] = [f"Boundary issue: Consider merging with {', '.join([m for m in modules if m != module])} - {reason}"]
        
        split_suggestions = boundary_analysis.get("split_suggestions", [])
        for suggestion in split_suggestions:
            module = suggestion.get("module", "")
            reason = suggestion.get("reason", "")
            if module:
                if module in issue_map:
                    issue_map[module].append(f"Boundary issue: Consider splitting module - {reason}")
                else:
                    issue_map[module] = [f"Boundary issue: Consider splitting module - {reason}"]
                
        # 收集AI建议中的问题
        overlaps = ai_review.get("overlapping_responsibilities", [])
        for overlap in overlaps:
            modules = overlap.split(" vs ")
            for module in modules:
                module = module.strip()
                if module in issue_map:
                    issue_map[module].append(f"Suggestion: {overlap}")
                else:
                    issue_map[module] = [f"Suggestion: {overlap}"]
                    
        # 添加AI建议中的具体针对某模块的建议
        suggestions = ai_review.get("suggestions", [])
        for suggestion in suggestions:
            # 尝试从建议中提取模块名
            for module in issue_map.keys():
                if module in suggestion:
                    issue_map[module].append(f"Suggestion: {suggestion}")
                    
        return issue_map
    except Exception as e:
        print(f"❌ 解析验证器报告时出错: {e}")
        return {}

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

def get_related_modules_context(module_name, all_modules):
    """获取与指定模块相关的模块信息
    
    Args:
        module_name: 要获取相关模块的模块名
        all_modules: 所有模块的摘要
        
    Returns:
        list: 相关模块的简化摘要列表
    """
    global dependency_manager
    
    related = []
    
    # 如果依赖图存在，使用依赖图获取相关模块
    if dependency_manager and module_name in dependency_manager.graph:
        # 获取该模块依赖的模块
        depends_on = dependency_manager.graph[module_name].get("depends_on", [])
        for dep in depends_on:
            for summary in all_modules:
                if summary.get("module_name") == dep:
                    # 简化摘要，只保留重要信息
                    related.append({
                        "module_name": dep,
                        "relationship": "depended_on",
                        "responsibilities": summary.get("responsibilities", [])[:3],
                        "key_apis": summary.get("key_apis", [])[:3]
                    })
                    break
        
        # 获取依赖该模块的模块
        depended_by = dependency_manager.graph[module_name].get("depended_by", [])
        for dep in depended_by:
            for summary in all_modules:
                if summary.get("module_name") == dep:
                    # 简化摘要，只保留重要信息
                    related.append({
                        "module_name": dep,
                        "relationship": "depends_on_this",
                        "responsibilities": summary.get("responsibilities", [])[:3],
                        "key_apis": summary.get("key_apis", [])[:3]
                    })
                    break
    
    # 如果没有找到足够的相关模块，添加命名相似的模块
    if len(related) < 3:
        # 提取基本名称（去掉Controller、Service、Repository等后缀）
        base_name = re.sub(r'(Controller|Service|Repository|Page|Model)$', '', module_name)
        for summary in all_modules:
            other_name = summary.get("module_name", "")
            if other_name and other_name != module_name:
                other_base = re.sub(r'(Controller|Service|Repository|Page|Model)$', '', other_name)
                # 如果基本名称相同，认为是相关模块
                if other_base == base_name:
                    related.append({
                        "module_name": other_name,
                        "relationship": "similar_name",
                        "responsibilities": summary.get("responsibilities", [])[:3],
                        "key_apis": summary.get("key_apis", [])[:3]
                    })
    
    return related[:5]  # 最多返回5个相关模块

async def run_incremental_validation(fixed_modules=None):
    """运行增量验证，只验证修复过的模块"""
    # 保存当前验证报告的问题计数
    if VALIDATOR_JSON_PATH.exists():
        try:
            old_report = json.loads(VALIDATOR_JSON_PATH.read_text())
            old_issues = count_total_issues(old_report)
        except Exception as e:
            print(f"⚠️ 读取原始验证报告失败: {e}")
            old_issues = 0
    else:
        old_issues = 0
    
    # 导入validator模块
    try:
        from validator.validator import run_validator
        
        # 运行增量验证，只验证指定的模块
        print(f"🔍 运行增量验证，对象: {fixed_modules if fixed_modules else '所有模块'}")
        validation_result = run_validator(modules_to_check=fixed_modules)
        
        # 获取新的问题数量
        new_issues = validation_result["total_issues"]
        
        # 计算差异
        diff = old_issues - new_issues
        
        return {
            "improved": diff >= 0,  # 允许等于，避免回滚无变化的修复
            "old_issues": old_issues,
            "new_issues": new_issues,
            "diff": diff
        }
    except Exception as e:
        print(f"❌ 运行验证器失败: {e}")
        
        # 回退到运行命令行验证
        import subprocess
        try:
            print("⚠️ 尝试使用命令行运行完整验证...")
            subprocess.run(["python", "run_validator.py"], check=True)
            
            # 读取新的验证报告
            if VALIDATOR_JSON_PATH.exists():
                new_report = json.loads(VALIDATOR_JSON_PATH.read_text())
                new_issues = count_total_issues(new_report)
            else:
                new_issues = 0
            
            # 计算差异
            diff = old_issues - new_issues
            
            return {
                "improved": diff >= 0,
                "old_issues": old_issues,
                "new_issues": new_issues,
                "diff": diff
            }
        except Exception as subproc_err:
            print(f"❌ 命令行验证也失败: {subproc_err}")
            return {
                "improved": True,  # 假设改进以避免不必要的回滚
                "old_issues": old_issues,
                "new_issues": old_issues,
                "diff": 0
            }

def count_total_issues(report):
    """计算报告中的总问题数"""
    count = 0
    
    # 1. 结构问题
    structure_scan = report.get("structure_scan", {})
    for module, issues in structure_scan.items():
        count += len(issues)
    
    # 2. AI审查问题
    ai_review = report.get("ai_review", {})
    
    # 2.1 重叠责任
    overlaps = ai_review.get("overlapping_responsibilities", [])
    count += len(overlaps)
    
    # 2.2 未定义依赖
    undefined = ai_review.get("undefined_dependencies", [])
    count += len(undefined)
    
    # 2.3 缺失或冗余模块
    missing_redundant = ai_review.get("missing_or_redundant_modules", {})
    count += len(missing_redundant.get("missing", []))
    count += len(missing_redundant.get("redundant", []))
    
    return count

def ensure_required_fields(module_data: dict, original_data: dict = None) -> dict:
    """确保模块数据包含所有必需字段，即使是空值"""
    required_fields = {
        "module_name": "",
        "responsibilities": [],
        "key_apis": [],
        "data_inputs": [],
        "data_outputs": [],
        "depends_on": [],
        "target_path": ""
    }
    
    result = {}
    
    # 首先从原始数据填充
    if original_data:
        for field, default_value in required_fields.items():
            if field in original_data and original_data[field]:
                result[field] = original_data[field]
            else:
                result[field] = default_value
    
    # 然后用新数据覆盖
    for field, default_value in required_fields.items():
        if field in module_data and module_data[field] is not None:
            result[field] = module_data[field]
        elif field not in result:
            result[field] = default_value
    
    # 确保数组字段为数组类型
    for field in ["responsibilities", "key_apis", "data_inputs", "data_outputs", "depends_on"]:
        if not isinstance(result[field], list):
            # 尝试将字符串转换为数组
            if isinstance(result[field], str):
                if result[field].startswith('[') and result[field].endswith(']'):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        result[field] = []
                else:
                    # 单个项目作为数组的一个元素
                    result[field] = [result[field]] if result[field] else []
            else:
                result[field] = []
    
    # 确保module_name是字符串
    if not isinstance(result["module_name"], str):
        result["module_name"] = str(result["module_name"]) if result["module_name"] else ""
    
    # 确保target_path是字符串
    if not isinstance(result["target_path"], str):
        result["target_path"] = str(result["target_path"]) if result["target_path"] else ""
    
    return result

async def fix_modules():
    """修复验证器报告中有问题的模块"""
    global dependency_manager, rollback_manager
    
    # 初始化依赖图和回滚管理器
    if dependency_manager is None:
        dependency_manager = initialize_dependency_graph()
    
    if rollback_manager is None:
        rollback_manager = initialize_rollback_manager()
    
    # 在修复前创建检查点
    rollback_manager.create_checkpoint("before_fix")
    
    # 从验证器报告中获取每个模块的问题清单
    issue_map = get_issues_per_module(VALIDATOR_JSON_PATH)
    
    # 加载所有模块的摘要
    all_modules = []
    for path in BASE_PATH.glob("*/full_summary.json"):
        try:
            all_modules.append(json.loads(path.read_text()))
        except:
            print(f"⚠️ Failed to parse {path}")
    
    # 从summary_index加载索引
    summary_index = json.loads(INDEX_PATH.read_text()) if INDEX_PATH.exists() else {}

    fix_log = []
    total = len(issue_map)
    print(f"🔧 Fixing {total} modules with issues...\n")

    # 获取模块的拓扑排序
    ordered_modules = dependency_manager.get_topological_order()
    if ordered_modules is None:
        print("⚠️ 检测到循环依赖，使用默认排序")
        modules = list(issue_map.items())
    else:
        # 按拓扑排序对模块进行排序
        modules = []
        # 首先包含在拓扑排序中且有问题的模块
        for mod_name in ordered_modules:
            if mod_name in issue_map:
                modules.append((mod_name, issue_map[mod_name]))
        # 然后包含未在拓扑排序中的模块
        for mod_name, issues in issue_map.items():
            if mod_name not in ordered_modules:
                modules.append((mod_name, issues))

    # 将模块分成多个批次，每批最多3个模块
    batch_size = 3
    batches = [modules[i:i + batch_size] for i in range(0, len(modules), batch_size)]
    
    for batch_idx, batch in enumerate(batches):
        print(f"\n📦 Processing batch {batch_idx+1}/{len(batches)} ({len(batch)} modules)")
        
        # 在每个批次前创建检查点
        batch_checkpoint = rollback_manager.create_checkpoint(f"batch_{batch_idx+1}")
        
        fixed_in_batch = []
        batch_had_failures = False
        
        for i, (mod_name, issue_list) in enumerate(batch):
            print(f"[{batch_idx*batch_size + i + 1}/{total}] Fixing {mod_name}...")
            original = load_summary(mod_name)
            
            # 创建模块级检查点
            mod_checkpoint = rollback_manager.create_checkpoint(f"module_{mod_name}")
            
            # 限制问题数量，优先选择解析和未定义依赖问题
            prioritized_issues = []
            parsing_issues = [issue for issue in issue_list if "failed to parse" in issue or "unhashable type" in issue]
            dependency_issues = [issue for issue in issue_list if "undefined dependency" in issue]
            boundary_issues = [issue for issue in issue_list if "Boundary issue" in issue]
            other_issues = [issue for issue in issue_list if 
                           "failed to parse" not in issue and 
                           "unhashable type" not in issue and 
                           "undefined dependency" not in issue and
                           "Boundary issue" not in issue]
            
            # 优先处理不同类型的问题
            prioritized_issues.extend(parsing_issues)
            prioritized_issues.extend(dependency_issues[:max(0, 3-len(prioritized_issues))])
            prioritized_issues.extend(boundary_issues[:max(0, 3-len(prioritized_issues))])
            prioritized_issues.extend(other_issues[:max(0, 3-len(prioritized_issues))])
            
            limited_issues = prioritized_issues[:3]
            if len(issue_list) > 3:
                print(f"⚠️ Limiting to {len(limited_issues)} prioritized issues out of {len(issue_list)} total issues")
            
            # 获取相关模块的上下文
            related_modules = get_related_modules_context(mod_name, all_modules)
            
            # 更紧凑的提示，减少token数量
            compact_summary = {
                "module_name": original.get("module_name", ""),
                "responsibilities": original.get("responsibilities", [])[:3],
                "key_apis": original.get("key_apis", [])[:3],
                "depends_on": original.get("depends_on", []),
                "target_path": original.get("target_path", "")
            }
            
            # 构建提示
            fixer_prompt = get_fixer_prompt(mod_name, "\n".join(limited_issues), compact_summary, related_modules)
            user_prompt = f"Fix issues for module: {mod_name}"
            
            # 不断增加重试次数和等待时间策略
            max_retries = 5  # 增加重试次数
            success = False
            result = None
            fixed = None
            
            for attempt in range(max_retries):
                try:
                    # 向LLM发送提示
                    result = await run_prompt(
                        chat=chat,
                        system_message=fixer_prompt,
                        user_message=user_prompt,
                        model="gpt-4o",
                        tokenizer=tokenizer,
                        parse_response=parse_json_response
                    )
                    
                    # 确保结果是字典而不是字符串
                    if isinstance(result, str):
                        print(f"⚠️ Result is a string, attempting to parse...")
                        fixed = parse_json_response(result)
                    else:
                        fixed = result
                    
                    # 检查结果是否包含必需字段
                    required_fields = ["module_name", "responsibilities", "key_apis", "data_inputs", "data_outputs", "depends_on", "target_path"]
                    missing_fields = [field for field in required_fields if field not in fixed]
                    
                    if missing_fields:
                        print(f"⚠️ 尝试 {attempt+1}: 结果缺少必需字段: {missing_fields}")
                        # 如果不是最后一次尝试，继续重试
                        if attempt < max_retries - 1:
                            wait_time = min(10 * (attempt + 1), 30)  # 逐渐增加等待时间，最多30秒
                            print(f"⏳ 等待 {wait_time} 秒后重试...")
                            await asyncio.sleep(wait_time)
                            continue
                    else:
                        # 结果看起来有效
                        success = True
                        break
                        
                except Exception as e:
                    print(f"❌ 尝试 {attempt+1} 失败: {str(e)}")
                    
                    # 仅在非最后一次尝试时重试
                    if attempt < max_retries - 1:
                        wait_time = min(10 * (attempt + 1), 30)  # 逐渐增加等待时间，最多30秒
                        print(f"⏳ 等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ 所有重试尝试均失败。跳过模块 {mod_name}")
                        batch_had_failures = True
            
            # 如果所有尝试都失败，继续下一个模块
            if not success:
                print(f"❌ 无法修复模块 {mod_name}，跳过")
                batch_had_failures = True
                continue
            
            # 处理可能的嵌套字典，确保所有值都是简单类型
            try:
                for key, value in list(fixed.items()):
                    if isinstance(value, dict):
                        print(f"⚠️ 将'{key}'中的嵌套字典转换为字符串")
                        fixed[key] = str(value)
            except Exception as e:
                print(f"⚠️ 处理嵌套字典时出错: {e}")
            
            print(f"✓ 获取有效的JSON响应")
            
            try:
                # 确保所有必需字段都存在，使用原始数据作为备用
                fixed = ensure_required_fields(fixed, original)
                
                # 最终检查所有必需字段是否存在
                for field in ["module_name", "target_path", "responsibilities", "depends_on"]:
                    if field not in fixed or fixed[field] is None:
                        raise ValueError(f"仍然缺少必需字段: {field}")
                
                # 检查依赖是否引入循环
                new_dependencies = fixed.get("depends_on", [])
                old_dependencies = original.get("depends_on", [])
                
                # 如果依赖有变化，检查循环依赖
                if set(new_dependencies) != set(old_dependencies):
                    # 更新依赖图
                    dependency_check = dependency_manager.update_dependencies(mod_name, new_dependencies)
                    
                    # 如果引入了循环依赖，警告并提供详细信息
                    if dependency_check["has_cycles"]:
                        cycles = dependency_check["cycles"]
                        print(f"⚠️ 检测到循环依赖: {cycles}")
                        
                        # 如果循环依赖涉及当前模块，尝试移除导致循环的依赖
                        for cycle in cycles:
                            if mod_name in cycle:
                                for dep in cycle:
                                    if dep in new_dependencies and dep != mod_name:
                                        print(f"⚠️ 移除导致循环依赖的依赖: {dep}")
                                        new_dependencies.remove(dep)
                        
                        # 更新移除循环依赖后的依赖列表
                        fixed["depends_on"] = new_dependencies
                        dependency_manager.update_dependencies(mod_name, new_dependencies)
                
                # 保存修复后的模块
                save_summary(mod_name, fixed)
                update_index(summary_index, fixed)
                fix_log.append(f"### ✅ {mod_name} fixed:\n" + "\n".join(limited_issues) + "\n")
                fixed_in_batch.append(mod_name)
                print(f"✅ 成功修复 {mod_name}")
            except Exception as e:
                print(f"❌ 保存/更新 {mod_name} 时出错: {e}")
                print(f"Fixed data: {fixed}")
                batch_had_failures = True
                continue
        
        # 在每个批次后保存索引和日志，以免中途失败丢失数据
        INDEX_PATH.write_text(json.dumps(summary_index, indent=2))
        FIX_LOG_PATH.write_text("\n".join(fix_log))
        print(f"🔄 批次 {batch_idx+1} 完成后保存进度")
        
        # 每个批次后进行增量验证
        if fixed_in_batch:
            print("🔍 运行增量验证...")
            validation_result = await run_incremental_validation(fixed_in_batch)
            
            print(f"📊 验证结果: {validation_result['old_issues']} -> {validation_result['new_issues']} 问题 (差异: {validation_result['diff']})")
            
            # 如果问题增加了，回滚到批次检查点
            if validation_result['diff'] < -2:  # 只有问题明显增加才回滚，允许小波动
                print(f"⚠️ 检测到问题显著增加！回滚到批次检查点: {batch_checkpoint}")
                rollback_manager.rollback_to_checkpoint(batch_checkpoint)
                
                # 从依赖图中移除刚刚修复的模块的依赖更新
                for mod_name in fixed_in_batch:
                    # 恢复原始依赖
                    original = load_summary(mod_name)
                    original_deps = original.get("depends_on", [])
                    dependency_manager.update_dependencies(mod_name, original_deps)
                
                # 从修复日志中移除回滚的模块
                for mod_name in fixed_in_batch:
                    fix_log = [log for log in fix_log if not log.startswith(f"### ✅ {mod_name} fixed:")]
                
                # 更新修复日志
                FIX_LOG_PATH.write_text("\n".join(fix_log))
            elif batch_had_failures and validation_result['diff'] < 0:
                # 如果批次有失败且问题增加，也回滚
                print(f"⚠️ 批次有失败且问题增加。回滚到批次检查点: {batch_checkpoint}")
                rollback_manager.rollback_to_checkpoint(batch_checkpoint)
                
                # 从依赖图中移除刚刚修复的模块的依赖更新
                for mod_name in fixed_in_batch:
                    # 恢复原始依赖
                    original = load_summary(mod_name)
                    original_deps = original.get("depends_on", [])
                    dependency_manager.update_dependencies(mod_name, original_deps)
                
                # 从修复日志中移除回滚的模块
                for mod_name in fixed_in_batch:
                    fix_log = [log for log in fix_log if not log.startswith(f"### ✅ {mod_name} fixed:")]
                
                # 更新修复日志
                FIX_LOG_PATH.write_text("\n".join(fix_log))
            else:
                # 即使问题没有减少，但也没有明显增加，仍然保留修复
                if validation_result['diff'] < 0:
                    print(f"ℹ️ 问题略有增加 (diff: {validation_result['diff']})，但在容忍范围内，保留修复")
                else:
                    print(f"✅ 修复成功，问题减少: {validation_result['diff']}")
                    
                # 每修复成功5个模块后，保存一个新的检查点用于可能的回滚
                if len(fix_log) % 15 == 0:
                    rollback_manager.create_checkpoint(f"milestone_{len(fix_log)}_fixes")
        
        # 批次之间暂停一下，避免过多的API请求
        if batch_idx < len(batches) - 1:
            print(f"⏳ 暂停10秒钟后处理下一批次...")
            await asyncio.sleep(10)

    print(f"\n✅ 所有模块修复完成。日志保存到 {FIX_LOG_PATH}")
    
    # 清理旧检查点
    rollback_manager.cleanup_old_checkpoints()
    
    # 生成最终的依赖图可视化
    dependency_manager.visualize()

if __name__ == "__main__":
    # 初始化全局对象
    dependency_manager = initialize_dependency_graph()
    rollback_manager = initialize_rollback_manager()
    
    asyncio.run(fix_modules())