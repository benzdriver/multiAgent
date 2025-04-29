"""
JSON处理工具模块，提供JSON提取和验证功能
"""

import json
import re
from typing import Dict, List, Any, Optional

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """从LLM响应中提取JSON数据，增强提取能力"""
    if not response:
        return {}
    
    json_patterns = [
        r'```(?:json)?(.*?)```',  # 标准markdown代码块
        r'{[\s\S]*"requirements"[\s\S]*}',  # 直接查找包含requirements的JSON对象
        r'{[\s\S]*"modules"[\s\S]*}',       # 直接查找包含modules的JSON对象
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    cleaned_json = match.strip()
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    print(f"⚠️ JSON解析错误，尝试清理JSON文本")
                    try:
                        no_comments = re.sub(r'^\s*//.*$', '', cleaned_json, flags=re.MULTILINE)
                        fixed_commas = re.sub(r',\s*}', '}', no_comments)
                        fixed_commas = re.sub(r',\s*]', ']', fixed_commas)
                        return json.loads(fixed_commas)
                    except json.JSONDecodeError:
                        continue  # 尝试下一个匹配项
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    return {}

def parse_and_update_global_state(response: str, global_state: Dict[str, Any]) -> Dict[str, Any]:
    """解析响应并更新全局状态（如果包含结构化数据）"""
    try:
        if "```json" in response and "```" in response:
            json_content = response.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_content)
            
            if "requirements" in data:
                global_state["requirements"].update(data["requirements"])
            if "modules" in data:
                global_state["modules"] = data["modules"]
            if "technology_stack" in data:
                global_state["technology_stack"] = data["technology_stack"]
            if "requirement_module_index" in data:
                global_state["requirement_module_index"] = data["requirement_module_index"]
            if "architecture_pattern" in data:
                global_state["architecture_pattern"] = data["architecture_pattern"]
    except Exception as e:
        print(f"Error parsing JSON from response: {e}")
    
    return global_state
