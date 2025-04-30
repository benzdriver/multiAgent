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
async def get_global_state(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取前端所需的全局状态，格式化为前端需要的结构"""
    try:
        global_state = state_service.get_global_state()
        
        requirements = []
        modules = []
        tech_stack = []
        validation_issues = []
        circular_dependencies = []
        
        for req_id, req_data in global_state.get("requirements", {}).items():
            requirements.append({
                "id": req_id,
                "name": req_data.get("name", ""),
                "description": req_data.get("description", ""),
                "priority": req_data.get("priority", "中"),
                "status": req_data.get("status", "待处理"),
                "relatedModules": global_state.get("requirement_module_index", {}).get(req_id, [])
            })
        
        for module_data in global_state.get("modules", []):
            module_id = module_data.get("id", "")
            if not module_id:
                module_id = f"module_{len(modules) + 1}"
                module_data["id"] = module_id
                
            modules.append({
                "id": module_id,
                "name": module_data.get("name", ""),
                "description": module_data.get("description", ""),
                "responsibilities": module_data.get("responsibilities", []),
                "dependencies": module_data.get("dependencies", []),
                "layer": module_data.get("layer", ""),
                "domain": module_data.get("domain", ""),
                "relatedRequirements": []  # 将在后续处理中填充
            })
        
        tech_id = 1
        for category, techs in global_state.get("technology_stack", {}).items():
            for tech in techs:
                tech_stack.append({
                    "id": f"tech_{tech_id}",
                    "name": tech,
                    "category": category,
                    "description": f"{category}类别的{tech}技术"
                })
                tech_id += 1
        
        issue_id = 1
        for issue_type, issues in global_state.get("validation_issues", {}).items():
            for issue in issues:
                validation_issues.append({
                    "id": f"issue_{issue_id}",
                    "type": issue_type,
                    "description": issue.get("description", ""),
                    "relatedItems": issue.get("related_items", []),
                    "severity": issue.get("severity", "中")
                })
                issue_id += 1
        
        dep_id = 1
        for dep in global_state.get("circular_dependencies", []):
            circular_dependencies.append({
                "id": f"dep_{dep_id}",
                "modules": dep.get("modules", []),
                "description": dep.get("description", "")
            })
            dep_id += 1
        
        module_name_to_id = {m.get("name", ""): m.get("id", "") for m in modules}
        req_module_index = global_state.get("requirement_module_index", {})
        
        for req_id, module_ids in req_module_index.items():
            for module_id in module_ids:
                for module in modules:
                    if module["id"] == module_id or module_name_to_id.get(module["name"]) == module_id:
                        if req_id not in module["relatedRequirements"]:
                            module["relatedRequirements"].append(req_id)
        
        print(f"✅ 全局状态API: 返回 {len(modules)} 个模块, {len(requirements)} 个需求")
        
        return {
            "requirements": requirements,
            "modules": modules,
            "techStack": tech_stack,
            "validationIssues": validation_issues,
            "circularDependencies": circular_dependencies,
            "mode": state_service.get_current_mode() or "default"
        }
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
