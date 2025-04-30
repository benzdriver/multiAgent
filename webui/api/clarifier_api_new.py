"""
澄清器API模块，提供澄清器相关接口
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from services.state_service import StateService, get_state_service
from services.startup_service import StartupService, get_startup_service

router = APIRouter()

@router.post("/start_clarifier")
async def start_clarifier(
    state_service: StateService = Depends(get_state_service),
    startup_service: StartupService = Depends(get_startup_service)
) -> Dict[str, Any]:
    """启动澄清器"""
    clarifier = state_service.get_clarifier()
    if clarifier is None:
        try:
            result = await startup_service.initialize(use_mock=False)
            
            if result["status"] == "success":
                print("✅ Clarifier已成功初始化")
                
                from webui.api.document_api import analyze_documents
                try:
                    print("🔍 开始自动扫描data/input目录中的文档...")
                    state_service.set_current_mode("file_based")
                    
                    import os
                    from pathlib import Path
                    os.makedirs("data/input", exist_ok=True)
                    
                    input_dir = Path("data/input")
                    if input_dir.exists():
                        md_files = list(input_dir.glob('**/*.md'))
                        txt_files = list(input_dir.glob('**/*.txt'))
                        input_files = md_files + txt_files
                        
                        if input_files:
                            print(f"✅ 检测到 {len(input_files)} 个输入文档，开始自动分析...")
                            
                            for file_path in input_files:
                                state_service.add_uploaded_file(str(file_path.absolute()))
                            
                            await analyze_documents(state_service=state_service)
                            print("✅ 文档自动分析完成")
                        else:
                            print("⚠️ 未在data/input目录中找到文档")
                            state_service.add_conversation_message(
                                "system",
                                "未在data/input目录中找到文档，请上传文档后继续。"
                            )
                except Exception as e:
                    print(f"⚠️ 自动扫描文档失败: {str(e)}")
                    state_service.add_conversation_message(
                        "system",
                        f"自动扫描文档失败: {str(e)}"
                    )
                
                return {"status": "success", "message": "Clarifier initialized"}
            else:
                print(f"❌ Clarifier初始化失败: {result.get('message', '未知错误')}")
                state_service.add_conversation_message(
                    "system",
                    f"初始化失败: {result.get('message', '未知错误')}"
                )
                return {"status": "error", "message": result.get("message", "Clarifier initialization failed")}
        except Exception as e:
            print(f"❌ Clarifier初始化失败: {str(e)}")
            state_service.add_conversation_message(
                "system",
                f"初始化失败: {str(e)}"
            )
            return {"status": "error", "message": f"Clarifier initialization failed: {str(e)}"}
    
    return {"status": "success", "message": "Clarifier already initialized"}

@router.post("/analyze")
async def analyze_requirements(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """分析需求并生成架构"""
    clarifier = state_service.get_clarifier()
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier尚未初始化")
    
    try:
        global_state = state_service.get_global_state()
        
        if not global_state.get("requirements"):
            raise HTTPException(status_code=400, detail="没有找到需求数据，请先添加需求")
        
        requirement_analysis = {
            "requirements": [],
            "system_overview": {},
            "functional_requirements": {}
        }
        
        for req_id, req_data in global_state["requirements"].items():
            requirement_analysis["requirements"].append(req_data)
        
        print(f"📊 开始分析 {len(requirement_analysis['requirements'])} 个需求...")
        
        if hasattr(clarifier, 'generate_architecture'):
            architecture_result = await clarifier.generate_architecture(requirement_analysis)
            
            if not architecture_result:
                raise HTTPException(status_code=500, detail="架构生成失败，未返回结果")
            
            if "modules" in architecture_result:
                global_state["modules"] = architecture_result["modules"]
                print(f"✅ 已生成 {len(architecture_result['modules'])} 个模块")
            
            if "architecture_pattern" in architecture_result:
                global_state["architecture_pattern"] = architecture_result["architecture_pattern"]
                print(f"✅ 已生成架构模式: {architecture_result['architecture_pattern'].get('name', '未命名')}")
            
            if "technology_stack" in architecture_result:
                global_state["technology_stack"] = architecture_result["technology_stack"]
                print(f"✅ 已生成技术栈")
            
            if "requirement_module_index" in architecture_result:
                global_state["requirement_module_index"] = architecture_result["requirement_module_index"]
                print(f"✅ 已生成需求-模块映射")
            
            state_service.update_global_state(global_state)
            
            state_service.add_conversation_message(
                "system",
                f"架构分析完成，已生成 {len(architecture_result.get('modules', {}))} 个模块。"
            )
            
            state_service.add_conversation_message(
                "clarifier",
                "请点击已生成的模块，查看模块详情。"
            )
            
            return {
                "status": "success", 
                "message": "Architecture analysis completed",
                "modules_count": len(architecture_result.get("modules", {}))
            }
        else:
            raise HTTPException(status_code=500, detail="Clarifier不支持架构生成功能")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"架构分析失败: {str(e)}")

@router.post("/granular_modules")
async def generate_granular_modules(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """生成细粒度模块"""
    clarifier = state_service.get_clarifier()
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier尚未初始化")
    
    try:
        global_state = state_service.get_global_state()
        
        if not global_state.get("modules"):
            raise HTTPException(status_code=400, detail="没有找到模块数据，请先生成架构")
        
        if hasattr(clarifier, 'analyze_granular_modules'):
            print("🔍 开始生成细粒度模块...")
            
            architecture_analysis = {
                "modules": list(global_state["modules"].values()),
                "architecture_pattern": global_state.get("architecture_pattern", {}),
                "technology_stack": global_state.get("technology_stack", {})
            }
            
            requirement_analysis = {
                "requirements": list(global_state["requirements"].values()),
                "system_overview": {},
                "functional_requirements": {}
            }
            
            result = await clarifier.analyze_granular_modules(
                requirement_analysis=requirement_analysis,
                architecture_analysis=architecture_analysis
            )
            
            if not result:
                raise HTTPException(status_code=500, detail="细粒度模块生成失败，未返回结果")
            
            if "modules" in result:
                for module_id, module_data in result["modules"].items():
                    if module_id not in global_state["modules"]:
                        global_state["modules"][module_id] = module_data
                        print(f"✅ 添加新模块: {module_data.get('module_name', module_id)}")
            
            state_service.update_global_state(global_state)
            
            new_modules_count = len(result.get("modules", {}))
            state_service.add_conversation_message(
                "system",
                f"细粒度模块生成完成，已添加 {new_modules_count} 个新模块。"
            )
            
            return {
                "status": "success", 
                "message": "Granular modules generated",
                "new_modules_count": new_modules_count
            }
        else:
            raise HTTPException(status_code=500, detail="Clarifier不支持细粒度模块生成功能")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"细粒度模块生成失败: {str(e)}")

@router.post("/conflict_check")
async def check_conflicts(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """检查模块冲突"""
    clarifier = state_service.get_clarifier()
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier尚未初始化")
    
    try:
        global_state = state_service.get_global_state()
        
        if not global_state.get("modules"):
            raise HTTPException(status_code=400, detail="没有找到模块数据，请先生成架构")
        
        if hasattr(clarifier, 'architecture_manager') and hasattr(clarifier.architecture_manager, 'check_conflicts'):
            print("🔍 开始检查模块冲突...")
            
            conflicts = await clarifier.architecture_manager.check_conflicts()
            
            if conflicts:
                print(f"⚠️ 检测到 {len(conflicts)} 个冲突")
                
                global_state["validation_issues"]["conflicts"] = conflicts
                state_service.update_global_state(global_state)
                
                state_service.add_conversation_message(
                    "system",
                    f"检测到 {len(conflicts)} 个模块冲突。"
                )
                
                return {
                    "status": "warning", 
                    "message": f"Detected {len(conflicts)} conflicts",
                    "conflicts": conflicts
                }
            else:
                print("✅ 未检测到模块冲突")
                
                state_service.add_conversation_message(
                    "system",
                    "未检测到模块冲突。"
                )
                
                return {
                    "status": "success", 
                    "message": "No conflicts detected"
                }
        else:
            raise HTTPException(status_code=500, detail="Clarifier不支持冲突检查功能")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"冲突检查失败: {str(e)}")
