"""
深度推理API模块，提供深度推理相关接口
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import traceback
from services.state_service import StateService, get_state_service
from common.json_utils import extract_json_from_response, parse_and_update_global_state

router = APIRouter()

@router.post("/deep_clarification")
async def deep_clarification(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """执行深度需求澄清"""
    clarifier = state_service.get_clarifier()
    
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier not initialized")
    
    try:
        state_service.add_conversation_message(
            "system",
            "开始进行深度需求澄清..."
        )
        
        requirement_analysis = {
            "requirements": [],
            "system_overview": {},
            "functional_requirements": {}
        }
        
        global_state = state_service.get_global_state()
        if global_state["requirements"]:
            for req_id, req_data in global_state["requirements"].items():
                requirement_analysis["requirements"].append(req_data)
        
        result = await clarifier.deep_clarification(requirement_analysis)
        
        if not result or not result.get("clarification_result"):
            state_service.add_conversation_message(
                "system",
                "深度澄清未返回结果，可能是因为需求数据不足。"
            )
            return {"status": "warning", "message": "No clarification result returned"}
        
        state_service.add_conversation_message(
            "clarifier", 
            result.get("clarification_result", "深度澄清完成，但没有具体结果。")
        )
        
        return {"status": "success", "message": "Deep clarification completed"}
    
    except Exception as e:
        state_service.add_conversation_message(
            "system",
            f"深度澄清时出错: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deep_reasoning")
async def deep_reasoning(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """执行深度架构推理"""
    clarifier = state_service.get_clarifier()
    
    if not clarifier:
        print("❌ 深度推理失败: Clarifier未初始化")
        raise HTTPException(status_code=400, detail="Clarifier not initialized")
    
    try:
        print("🔍 开始进行深度架构推理...")
        state_service.add_conversation_message(
            "system",
            "开始进行深度架构推理..."
        )
        
        requirement_analysis = {
            "requirements": [],
            "system_overview": {},
            "functional_requirements": {}
        }
        
        architecture_analysis = {
            "modules": [],
            "architecture_pattern": {},
            "technology_stack": {}
        }
        
        global_state = state_service.get_global_state()
        
        if global_state["requirements"]:
            print(f"📊 找到 {len(global_state['requirements'])} 个需求")
            for req_id, req_data in global_state["requirements"].items():
                requirement_analysis["requirements"].append(req_data)
                print(f"  - 需求: {req_data.get('name', req_id)}")
        else:
            print("⚠️ 没有找到需求数据")
        
        if global_state["modules"]:
            print(f"📊 找到 {len(global_state['modules'])} 个模块")
            for module_id, module_data in global_state["modules"].items():
                architecture_analysis["modules"].append(module_data)
                print(f"  - 模块: {module_data.get('name', module_id)}")
        else:
            print("⚠️ 没有找到模块数据")
        
        architecture_analysis["architecture_pattern"] = global_state["architecture_pattern"]
        architecture_analysis["technology_stack"] = global_state["technology_stack"]
        
        print("🔄 调用Clarifier.deep_reasoning...")
        
        result = await clarifier.deep_reasoning(requirement_analysis, architecture_analysis)
        
        print(f"✅ 深度推理完成，结果类型: {type(result)}")
        
        if not result:
            print("⚠️ 深度推理未返回任何结果")
            state_service.add_conversation_message(
                "system",
                "深度推理未返回结果，可能是因为需求或架构数据不足。"
            )
            return {"status": "warning", "message": "No reasoning result returned"}
        
        if not result.get("reasoning_result"):
            print("⚠️ 深度推理返回的结果中没有reasoning_result字段")
            state_service.add_conversation_message(
                "system",
                "深度推理未返回有效结果，可能是因为需求或架构数据不足。"
            )
            return {"status": "warning", "message": "No valid reasoning result returned"}
        
        reasoning_content = result.get("reasoning_result", "")
        print(f"📝 结果长度: {len(reasoning_content)} 字符")
        
        print("🔍 从响应中提取结构化数据...")
        extracted_json = extract_json_from_response(reasoning_content)
        
        if extracted_json:
            print(f"✅ 成功从推理结果中提取JSON数据")
            state_service.update_global_state_from_json(extracted_json)
            
            if "modules" in extracted_json:
                new_modules_count = 0
                for module_id, module_data in extracted_json["modules"].items():
                    if module_id not in global_state["modules"]:
                        new_modules_count += 1
                        
                if new_modules_count > 0:
                    print(f"🔍 从推理中识别到 {new_modules_count} 个新模块")
                    state_service.add_conversation_message(
                        "system",
                        f"深度推理发现 {new_modules_count} 个新模块。这些模块已添加到架构中。"
                    )
            
            try:
                if clarifier and hasattr(clarifier, 'architecture_manager'):
                    arch_manager = clarifier.architecture_manager
                    if hasattr(arch_manager, 'find_circular_dependencies'):
                        circular_deps = arch_manager.find_circular_dependencies()
                        if circular_deps:
                            print(f"⚠️ 检测到循环依赖: {circular_deps}")
                            state_service.add_conversation_message(
                                "system",
                                f"警告：检测到循环依赖: {', '.join([' -> '.join(dep) for dep in circular_deps])}"
                            )
            except Exception as e:
                print(f"⚠️ 检查循环依赖时出错: {e}")
        else:
            print("⚠️ 无法从推理结果中提取JSON数据，仅保存文本内容")
            global_state = state_service.get_global_state()
            updated_state = parse_and_update_global_state(reasoning_content, global_state)
            state_service.update_global_state(updated_state)
        
        try:
            from pathlib import Path
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / "deep_reasoning_result.md", "w", encoding="utf-8") as f:
                f.write(f"# 深度架构推理结果\n\n{reasoning_content}")
            print(f"✅ 已保存推理结果到: {output_dir / 'deep_reasoning_result.md'}")
            
            if extracted_json:
                with open(output_dir / "deep_reasoning_result.json", "w", encoding="utf-8") as f:
                    import json
                    json.dump(extracted_json, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存结构化推理结果到: {output_dir / 'deep_reasoning_result.json'}")
        except Exception as e:
            print(f"⚠️ 保存推理结果时出错: {e}")
        
        state_service.add_conversation_message("clarifier", reasoning_content)
        
        state_service.add_conversation_message(
            "clarifier", 
            "深度推理完成。您可以：\n1. 查看生成的模块详情\n2. 开始实现代码\n3. 进行架构验证"
        )
        
        return {"status": "success", "message": "Deep reasoning completed", "has_extracted_json": bool(extracted_json)}
    
    except Exception as e:
        print(f"❌ 深度推理时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state_service.add_conversation_message(
            "system",
            f"深度推理时出错: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check_dependencies")
async def check_dependencies(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """检查模块依赖和循环依赖"""
    clarifier = state_service.get_clarifier()
    
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier尚未初始化")
    
    try:
        if hasattr(clarifier, 'architecture_manager'):
            arch_manager = clarifier.architecture_manager
            
            from core.clarifier.architecture_reasoner import ArchitectureReasoner
            reasoner = ArchitectureReasoner(architecture_manager=arch_manager)
            
            cycles = reasoner._check_global_circular_dependencies()
            
            validation_issues = {}
            if hasattr(arch_manager, 'get_validation_issues'):
                validation_issues = arch_manager.get_validation_issues()
            
            global_state = state_service.get_global_state()
            global_state["validation_issues"] = {
                "circular_dependencies": cycles,
                "module_issues": validation_issues
            }
            state_service.update_global_state(global_state)
            
            return {
                "status": "success",
                "circular_dependencies": cycles,
                "validation_issues": validation_issues
            }
        else:
            raise HTTPException(status_code=400, detail="架构管理器不可用")
    except Exception as e:
        print(f"❌ 检查依赖时出错: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"检查依赖时出错: {str(e)}")
