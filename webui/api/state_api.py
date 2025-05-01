"""
状态API模块，提供获取全局状态的接口
"""

from fastapi import APIRouter, Depends
from typing import Dict, List, Any
import os
from services.state_service import StateService, get_state_service

router = APIRouter()

@router.get("/state")
async def get_state(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取全局状态"""
    return state_service.get_global_state()

@router.get("/history")
async def get_history(state_service: StateService = Depends(get_state_service)) -> List[Dict[str, str]]:
    """获取对话历史"""
    return state_service.get_conversation_history()

@router.get("/mode")
async def get_mode(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取当前模式"""
    return {"mode": state_service.get_current_mode()}

@router.get("/get_global_state")
@router.get("/state/get_global_state")
async def get_global_state(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取前端所需的全局状态，格式化为前端需要的结构"""
    try:
        state_service.load_modules_from_disk()
        
        global_state = state_service.get_global_state()
        print(f"🔍 获取全局状态API: 获取全局状态")
        
        if not isinstance(global_state, dict):
            print(f"⚠️ 警告: 全局状态不是字典类型，而是 {type(global_state)}，将使用空字典")
            global_state = {}
        
        requirements = []
        modules = []
        tech_stack = []
        validation_issues = []
        circular_dependencies = []
        
        requirements_data = global_state.get("requirements", {})
        if isinstance(requirements_data, dict):
            for req_id, req_data in requirements_data.items():
                if isinstance(req_data, dict):
                    requirements.append({
                        "id": req_id,
                        "name": req_data.get("name", ""),
                        "description": req_data.get("description", ""),
                        "priority": req_data.get("priority", "中"),
                        "status": req_data.get("status", "待处理"),
                        "relatedModules": []  # 稍后填充
                    })
        
        raw_modules = global_state.get("modules", [])
        print(f"🔍 原始模块数据类型: {type(raw_modules)}")
        
        if isinstance(raw_modules, str):
            print(f"⚠️ 警告: modules是字符串类型，尝试转换为列表")
            try:
                import json
                raw_modules = json.loads(raw_modules)
                print(f"✅ 成功将modules字符串转换为列表，包含 {len(raw_modules)} 个模块")
            except Exception as e:
                print(f"❌ 转换modules字符串失败: {str(e)}")
                raw_modules = []
        
        if not isinstance(raw_modules, list):
            print(f"⚠️ 警告: modules不是列表类型，而是 {type(raw_modules)}，将使用空列表")
            raw_modules = []
        
        print(f"🔍 处理 {len(raw_modules)} 个模块")
        
        for i, module_data in enumerate(raw_modules):
            try:
                if not isinstance(module_data, dict):
                    print(f"⚠️ 警告: 模块 #{i} 数据不是字典类型，而是 {type(module_data)}，跳过")
                    continue
                    
                module_id = module_data.get("id", "")
                if not module_id:
                    module_id = f"module_{len(modules) + 1}"
                
                module_name = module_data.get("name", "")
                if not module_name:
                    module_name = f"未命名模块_{i+1}"
                
                module_obj = {
                    "id": module_id,
                    "name": module_name,
                    "description": module_data.get("description", ""),
                    "responsibilities": [],
                    "dependencies": [],
                    "layer": "",
                    "domain": "",
                    "relatedRequirements": []
                }
                
                for field in ["responsibilities", "dependencies"]:
                    if field in module_data:
                        field_value = module_data[field]
                        if isinstance(field_value, list):
                            module_obj[field] = field_value
                        elif isinstance(field_value, str):
                            try:
                                module_obj[field] = json.loads(field_value)
                            except:
                                module_obj[field] = [field_value]
                
                for field in ["layer", "domain"]:
                    if field in module_data and isinstance(module_data[field], str):
                        module_obj[field] = module_data[field]
                
                modules.append(module_obj)
            except Exception as e:
                print(f"❌ 处理模块 #{i} 时出错: {str(e)}")
                continue
        
        tech_stack_data = global_state.get("technology_stack", {})
        if isinstance(tech_stack_data, dict):
            tech_id = 1
            for category, techs in tech_stack_data.items():
                if isinstance(techs, list):
                    for tech in techs:
                        tech_stack.append({
                            "id": f"tech_{tech_id}",
                            "name": tech,
                            "category": category,
                            "description": f"{category}类别的{tech}技术"
                        })
                        tech_id += 1
        
        validation_issues_data = global_state.get("validation_issues", {})
        if isinstance(validation_issues_data, dict):
            issue_id = 1
            for issue_type, issues in validation_issues_data.items():
                if isinstance(issues, list):
                    for issue in issues:
                        if isinstance(issue, dict):
                            validation_issues.append({
                                "id": f"issue_{issue_id}",
                                "type": issue_type,
                                "description": issue.get("description", ""),
                                "relatedItems": issue.get("related_items", []),
                                "severity": issue.get("severity", "中")
                            })
                            issue_id += 1
        
        circular_deps_data = global_state.get("circular_dependencies", [])
        if isinstance(circular_deps_data, list):
            dep_id = 1
            for dep in circular_deps_data:
                if isinstance(dep, dict):
                    circular_dependencies.append({
                        "id": f"dep_{dep_id}",
                        "modules": dep.get("modules", []),
                        "description": dep.get("description", "")
                    })
                    dep_id += 1
        
        req_module_index = global_state.get("requirement_module_index", {})
        if isinstance(req_module_index, dict):
            module_name_to_id = {}
            for module in modules:
                if "name" in module and "id" in module:
                    module_name_to_id[module["name"]] = module["id"]
            
            for req in requirements:
                req_id = req["id"]
                if req_id in req_module_index:
                    module_ids = req_module_index[req_id]
                    if isinstance(module_ids, list):
                        req["relatedModules"] = module_ids
            
            for req_id, module_ids in req_module_index.items():
                if isinstance(module_ids, list):
                    for module_id in module_ids:
                        for module in modules:
                            if module["id"] == module_id or module_name_to_id.get(module["name"]) == module_id:
                                if "relatedRequirements" not in module:
                                    module["relatedRequirements"] = []
                                if req_id not in module["relatedRequirements"]:
                                    module["relatedRequirements"].append(req_id)
        
        result = {
            "requirements": requirements,
            "modules": modules,
            "techStack": tech_stack,
            "validationIssues": validation_issues,
            "circularDependencies": circular_dependencies,
            "mode": state_service.get_current_mode() or "default"
        }
        
        print(f"✅ 全局状态API: 返回 {len(modules)} 个模块, {len(requirements)} 个需求")
        if len(modules) > 0:
            print(f"✅ 第一个模块: {modules[0]['name']}")
        
        return result
    except Exception as e:
        import traceback
        print(f"❌ 获取全局状态时出错: {str(e)}")
        print(traceback.format_exc())
        return {
            "requirements": [],
            "modules": [],
            "techStack": [],
            "validationIssues": [],
            "circularDependencies": [],
            "mode": "error",
            "error": str(e)
        }
