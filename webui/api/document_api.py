"""
文档API模块，提供文档处理相关接口
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Dict, List, Any, Optional
from pathlib import Path
import os
import json
import traceback
from services.state_service import StateService, get_state_service
from common.json_utils import extract_json_from_response

router = APIRouter()

@router.post("/set_mode")
async def set_mode(
    mode: str = Form(...),
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """设置操作模式"""
    if mode not in ["interactive", "file_based"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'interactive' or 'file_based'.")
    
    state_service.set_current_mode(mode)
    print(f"设置模式为: {mode}")
    
    if mode == "file_based":
        state_service.clear_uploaded_files()
        
        os.makedirs("data/input", exist_ok=True)
        print(f"检查目录: data/input")
        
        data_input_dir = Path("data/input")
        if data_input_dir.exists():
            print(f"data/input目录存在")
            md_files = list(data_input_dir.glob('**/*.md'))
            print(f"找到了 {len(md_files)} 个.md文件")
            
            if md_files:
                for file_path in md_files:
                    abs_path = str(file_path.absolute())
                    state_service.add_uploaded_file(abs_path)
                    print(f"添加文件: {abs_path}")
                
                file_names = [f.name for f in md_files]
                msg = f"系统检测到input目录中有 {len(md_files)} 个Markdown文档: {', '.join(file_names)}"
                print(msg)
                state_service.add_conversation_message("system", msg)
                
                state_service.add_conversation_message(
                    "clarifier",
                    "已检测到input目录中的文档。是否立即分析这些文件？请输入Y开始分析。"
                )
            else:
                print("未在data/input目录中找到.md文件")
                state_service.add_conversation_message(
                    "clarifier",
                    "未在input目录中找到Markdown文件。请上传文档后继续。"
                )
        else:
            print("data/input目录不存在")
            state_service.add_conversation_message(
                "clarifier",
                "input目录不存在，已创建。请上传文档后继续。"
            )
    
    return {"status": "success", "mode": mode}

@router.post("/upload_file")
async def upload_file(
    file: UploadFile = File(...),
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """上传文件"""
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown (.md) files are supported")
    
    try:
        input_dir = "data/input"
        os.makedirs(input_dir, exist_ok=True)
        
        file_path = os.path.join(input_dir, file.filename)
        print(f"保存文件到: {file_path}")
        
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
        
        abs_path = str(Path(file_path).absolute())
        state_service.add_uploaded_file(abs_path)
        print(f"文件已添加到上传列表: {abs_path}")
        
        state_service.add_conversation_message(
            "system",
            f"文件 '{file.filename}' 上传成功。"
        )
        
        uploaded_files = state_service.get_uploaded_files()
        if len(uploaded_files) == 1:
            state_service.add_conversation_message(
                "clarifier",
                "文件已上传。您可以继续上传更多文件，或输入Y开始分析当前文件。"
            )
        else:
            state_service.add_conversation_message(
                "clarifier",
                f"已上传 {len(uploaded_files)} 个文件。请输入Y开始分析，或继续上传更多文件。"
            )
        
        return {"status": "success", "filename": file.filename}
    
    except Exception as e:
        print(f"文件上传出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_documents")
async def analyze_documents(
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """分析上传的文档"""
    uploaded_files = state_service.get_uploaded_files()
    
    if not uploaded_files:
        input_dir = Path("data/input")
        if input_dir.exists():
            md_files = list(input_dir.glob('**/*.md'))
            txt_files = list(input_dir.glob('**/*.txt'))
            input_files = md_files + txt_files
            
            if input_files:
                print(f"✅ 检测到 {len(input_files)} 个输入文档，自动加载...")
                
                for file_path in input_files:
                    state_service.add_uploaded_file(str(file_path.absolute()))
                
                uploaded_files = state_service.get_uploaded_files()
                print(f"✅ 自动加载了 {len(uploaded_files)} 个文档")
            else:
                raise HTTPException(status_code=400, detail="没有找到已上传的文件，data/input目录也为空")
        else:
            raise HTTPException(status_code=400, detail="没有找到已上传的文件")
    
    try:
        all_content = ""
        file_contents = []
        
        for file_path in uploaded_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    file_contents.append({"name": Path(file_path).name, "content": content})
                    all_content += f"\n\n--- {Path(file_path).name} ---\n{content}"
            except Exception as e:
                print(f"读取文件 {file_path} 时出错: {str(e)}")
                continue
        
        system_message = f"系统已经接收到以下文档内容进行分析:\n{all_content}"
        state_service.add_conversation_message("system", system_message)
        
        clarifier = state_service.get_clarifier()
        if not clarifier:
            raise HTTPException(status_code=500, detail="系统尚未初始化，请先启动系统")
        
        prompt = f"""
        分析以下文档内容，提取关键信息并以JSON格式返回结果:
        
        {all_content}
        
        请返回完整的系统架构分析，包括以下内容（必须使用以下确切的JSON结构）:
        
        {{
            "requirements": {{
                "req_1": {{ "id": "req_1", "name": "需求名称", "description": "需求描述", "priority": "高/中/低", "source": "来源" }},
                "req_2": {{ "id": "req_2", "name": "需求名称", "description": "需求描述", "priority": "高/中/低", "source": "来源" }}
                // 其他需求...
            }},
            "modules": {{
                "module_1": {{ 
                    "id": "module_1", 
                    "name": "模块名称", 
                    "description": "模块详细描述", 
                    "responsibilities": ["职责1", "职责2"], 
                    "dependencies": ["依赖模块ID"], 
                    "technologies": ["技术1", "技术2"],
                    "module_name": "模块名称",  // 确保包含这个字段
                    "target_path": "模块目标路径"  // 确保包含这个字段
                }},
                "module_2": {{ 
                    "id": "module_2", 
                    "name": "模块名称", 
                    "description": "模块详细描述",
                    "responsibilities": ["职责1", "职责2"],
                    "dependencies": ["依赖模块ID"],
                    "technologies": ["技术1", "技术2"],
                    "module_name": "模块名称",  // 确保包含这个字段
                    "target_path": "模块目标路径"  // 确保包含这个字段
                }}
                // 其他模块...
            }},
            "technology_stack": {{
                "frontend": ["技术1", "技术2"],
                "backend": ["技术1", "技术2"],
                "database": ["技术1"],
                "devops": ["技术1"]
            }},
            "requirement_module_index": {{
                "req_1": ["module_1", "module_2"],
                "req_2": ["module_1", "module_3"]
                // 需求ID到模块ID的映射关系
            }},
            "architecture_pattern": {{
                "name": "架构模式名称",
                "description": "架构模式描述",
                "layers": ["层1", "层2", "层3"],
                "patterns": ["设计模式1", "设计模式2"]
            }}
        }}
        
        请确保每个模块有清晰的名称、描述、职责和技术选择，同时明确说明需求和模块之间的对应关系。
        要求：
        1. 所有字段必须包含有意义的内容，不要使用占位符
        2. 请确保JSON格式正确，可以被解析
        3. requirement_module_index必须正确地将需求ID映射到相关模块ID的列表
        4. 模块名称应该反映其主要功能
        5. 每个模块必须包含module_name和target_path字段
        6. 返回的JSON必须能够被direct parse（不要有markdown标记）
        7. 进行细粒度模块划分，生成至少50个以上的模块，每个模块应该具有单一职责
        8. 将大型功能模块拆分成更小的子模块，确保每个模块专注于特定功能
        9. 不同层级的功能应该分别创建独立模块，如数据访问层、业务逻辑层、表示层等
        10. 考虑横切关注点（如日志、安全、缓存等）创建专门的模块
        """.strip()
        
        response = None
        try:
            if hasattr(clarifier, 'llm_executor') and hasattr(clarifier.llm_executor, 'run_prompt'):
                print("📝 使用LLM执行器调用...")
                response = clarifier.llm_executor.run_prompt(user_message=prompt)
            else:
                print("📝 使用Clarifier.run_llm方法调用...")
                response = await clarifier.run_llm(prompt=prompt)
                
            if not response:
                raise HTTPException(status_code=500, detail="无法获取有效的LLM响应")
            
            print(f"✅ 收到LLM响应: {response[:100]}...")
            
            json_data = extract_json_from_response(response)
            
            if not json_data:
                raise HTTPException(status_code=500, detail="无法从LLM响应中提取JSON数据")
            
            print(f"✅ 成功解析JSON数据: 包含 {len(json_data.get('modules', {}))} 个模块")
            
            modules_dir = Path("data/output/modules")
            modules_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 已确保模块目录存在: {modules_dir}")
            
            modules_data = json_data.get("modules", {})
            if modules_data:
                print(f"📁 开始创建模块目录和摘要文件...")
                for module_id, module_data in modules_data.items():
                    if "module_name" not in module_data:
                        module_data["module_name"] = module_data.get("name", module_id)
                    
                    module_name = module_data["module_name"]
                    module_dir = modules_dir / str(module_name)
                    module_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
                        json.dump(module_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ 创建了模块目录和摘要: {module_dir}")
            
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(output_dir / "full_analysis.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存完整分析结果到: {output_dir / 'full_analysis.json'}")
                
                with open(output_dir / "requirements.json", "w", encoding="utf-8") as f:
                    json.dump(json_data.get("requirements", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存需求到: {output_dir / 'requirements.json'}")
                
                with open(output_dir / "modules.json", "w", encoding="utf-8") as f: 
                    json.dump(json_data.get("modules", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存模块到: {output_dir / 'modules.json'}")
                
                with open(output_dir / "requirement_module_index.json", "w", encoding="utf-8") as f:
                    json.dump(json_data.get("requirement_module_index", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存需求-模块索引到: {output_dir / 'requirement_module_index.json'}")
                
                try:
                    dependency_graph = {}
                    for module_id, module_data in modules_data.items():
                        module_name = module_data.get("module_name", "")
                        depends_on = module_data.get("dependencies", [])
                        dependency_graph[module_name] = depends_on
                    
                    with open(output_dir / "dependency_graph.py", "w", encoding="utf-8") as f:
                        f.write("# Auto-generated module dependency graph\n")
                        f.write("dependency_graph = ")
                        json.dump(dependency_graph, f, ensure_ascii=False, indent=2)
                    
                    summary_index = {}
                    for module_id, module_data in modules_data.items():
                        module_name = module_data.get("module_name", "")
                        if module_name: 
                            summary_index[module_name] = {
                                "target_path": module_data.get("target_path", ""),
                                "depends_on": module_data.get("dependencies", []),
                                "responsibilities": module_data.get("responsibilities", [])
                            }
                    
                    with open(output_dir / "summary_index.json", "w", encoding="utf-8") as f:
                        json.dump(summary_index, f, ensure_ascii=False, indent=2)
                    
                except Exception as e:
                    print(f"⚠️ 生成依赖图或索引时出错: {e}")
                
            except Exception as e:
                print(f"⚠️ 保存分析结果文件时出错: {e}")
            
            print(f"✅ 文档分析完成，生成了 {len(json_data.get('modules', {}))} 个模块")
            await state_service.update_global_state_from_json(json_data)
            
            state_service.add_conversation_message(
                "user",
                "请分析我上传的文档内容，并提取关键信息。"
            )
            
            global_state = state_service.get_global_state()
            req_count = len(global_state['requirements'])
            module_count = len(global_state['modules'])
            tech_stack = []
            for category in global_state['technology_stack'].values():
                if isinstance(category, list):
                    tech_stack.extend(category)
            
            state_service.add_conversation_message(
                "system",
                f"文档分析完成，已提取到以下信息:\n" +
                f"- 需求数量: {req_count}\n" +
                f"- 模块数量: {module_count}\n" +
                f"- 技术栈: {', '.join(tech_stack)}\n" +
                f"- 模块目录已生成在: data/output/modules/\n" +
                (f"- 验证问题: {global_state.get('validation_issues', {})}" if global_state.get('validation_issues') else "")
            )
            
            state_service.add_conversation_message(
                "clarifier",
                "文档分析已完成，现在您可以选择以下操作:\n\n" + 
                "1. 进行深度需求澄清，帮助完善需求细节\n" +
                "2. 进行深度架构推理，生成更详细的架构设计\n\n" +
                "请输入选项的编号(1或2)继续，或输入其他问题。"
            )
            
            return {"status": "success", "message": "文档分析完成", "global_state": global_state}
            
        except Exception as e:
            error_message = f"分析文档时出错: {str(e)}"
            print(error_message)
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=error_message)
    
    except Exception as e:
        error_message = f"处理文档时出错: {str(e)}"
        print(error_message)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

@router.post("/update_requirement/{req_id}")
async def update_requirement(
    req_id: str,
    data: Dict[str, Any],
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """更新需求"""
    global_state = state_service.get_global_state()
    
    if req_id not in global_state["requirements"]:
        raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")
    
    global_state["requirements"][req_id].update(data)
    state_service.update_global_state({"requirements": global_state["requirements"]})
    
    affected_modules = []
    for module_id, module_data in global_state["requirement_module_index"].items():
        if "requirements" in module_data and req_id in module_data["requirements"]:
            affected_modules.append(module_id)
    
    return {
        "status": "success", 
        "requirement": global_state["requirements"][req_id],
        "affected_modules": affected_modules
    }
