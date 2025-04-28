from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pydantic import BaseModel
import sys
import asyncio
from typing import Dict, List, Any, Optional, Union
import shutil
from enum import Enum
from pathlib import Path
import re
import traceback

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 更新导入路径，使用services层的服务
from services.clarifier_service import ClarifierService

from webui.api import clarifier_api, validator_api, fixer_api, generator_api

# 使用新的core路径
from core.clarifier.clarifier import Clarifier
from core.clarifier.architecture_manager import ArchitectureManager
from core.clarifier.architecture_reasoner import ArchitectureReasoner

app = FastAPI(title="需求澄清与架构设计系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clarifier_api.router, prefix="/api/clarifier", tags=["clarifier"])
app.include_router(validator_api.router, prefix="/api/validator", tags=["validator"])
app.include_router(fixer_api.router, prefix="/api/fixer", tags=["fixer"])
app.include_router(generator_api.router, prefix="/api/generator", tags=["generator"])

# 创建一个全局的服务实例
clarifier_service = ClarifierService()

# 静态文件
app.mount("/static", StaticFiles(directory="webui/static"), name="static")

# 全局状态
clarifier: Optional[Clarifier] = None
conversation_history: List[Dict[str, str]] = []
global_state: Dict[str, Any] = {
    "requirements": {},
    "modules": {},
    "technology_stack": {},
    "requirement_module_index": {},
    "architecture_pattern": {},
    "validation_issues": {}  # 新增：保存验证问题
}
uploaded_files: List[str] = []
current_mode: str = None  # 'interactive' or 'file_based'
input_dir = "data/input"

# 操作模式枚举
class OperationMode(str, Enum):
    FILE_BASED = "file_based"
    INTERACTIVE = "interactive"

# API模型
class Message(BaseModel):
    content: str

class ModeRequest(BaseModel):
    mode: str

class StartClarifierResponse(BaseModel):
    status: str
    message: Optional[str] = None

# 静态文件路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("webui/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 获取全局状态
@app.get("/api/state")
async def get_state():
    return global_state

# 获取对话历史
@app.get("/api/history")
async def get_history():
    return conversation_history

# 获取当前模式
@app.get("/api/mode")
async def get_mode():
    return {"mode": current_mode}

# 启动澄清器
@app.post("/api/start_clarifier")
async def start_clarifier():
    global clarifier
    if clarifier is None:
        try:
            # 使用core.clarifier包中的工厂方法创建Clarifier实例
            from core.clarifier import create_clarifier, ensure_data_dir
            clarifier = create_clarifier(
                data_dir="data",
                use_mock=True,  # 测试阶段使用模拟LLM
                verbose=True
            )
            print("✅ Clarifier已成功初始化")
            
            conversation_history.append({
                "role": "system",
                "content": "欢迎使用需求澄清与架构设计系统！请选择使用模式：\n1. 基于文件分析 (上传需求文档)\n2. 交互式对话 (直接描述您的需求)"
            })
            return {"status": "success", "message": "Clarifier initialized"}
        except Exception as e:
            print(f"❌ Clarifier初始化失败: {str(e)}")
            conversation_history.append({
                "role": "system",
                "content": f"初始化失败: {str(e)}"
            })
            return {"status": "error", "message": f"Clarifier initialization failed: {str(e)}"}
    return {"status": "success", "message": "Clarifier already initialized"}

# 获取data/input目录中的文件
def get_input_files(data_dir="data"):
    input_dir = Path(data_dir) / "input"
    if not input_dir.exists():
        return []
    
    return list(input_dir.glob('**/*.md'))

# 修改set_mode函数，确保能正确检测到文件
@app.post("/api/set_mode")
async def set_mode(mode_request: ModeRequest):
    global current_mode, conversation_history, uploaded_files
    
    mode = mode_request.mode
    if mode not in ["interactive", "file_based"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'interactive' or 'file_based'.")
    
    current_mode = mode
    print(f"设置模式为: {current_mode}")
    
    # 如果是文件模式，自动检查data/input目录
    if mode == "file_based":
        # 确保uploaded_files是空的，防止重复
        uploaded_files = []
        
        # 创建input目录（如果不存在）
        os.makedirs("data/input", exist_ok=True)
        print(f"检查目录: data/input")
        
        # 检查data/input目录中的文件
        data_input_dir = Path("data/input")
        if data_input_dir.exists():
            print(f"data/input目录存在")
            md_files = list(data_input_dir.glob('**/*.md'))
            print(f"找到了 {len(md_files)} 个.md文件")
            
            if md_files:
                # 将这些文件添加到已上传文件列表
                for file_path in md_files:
                    abs_path = str(file_path.absolute())
                    uploaded_files.append(abs_path)
                    print(f"添加文件: {abs_path}")
                
                file_names = [f.name for f in md_files]
                msg = f"系统检测到input目录中有 {len(md_files)} 个Markdown文档: {', '.join(file_names)}"
                print(msg)
                conversation_history.append({
                    "role": "system",
                    "content": msg
                })
                
                conversation_history.append({
                    "role": "clarifier",
                    "content": "已检测到input目录中的文档。是否立即分析这些文件？请输入Y开始分析。"
                })
            else:
                print("未在data/input目录中找到.md文件")
                conversation_history.append({
                    "role": "clarifier",
                    "content": "未在input目录中找到Markdown文件。请上传文档后继续。"
                })
        else:
            print("data/input目录不存在")
            conversation_history.append({
                "role": "clarifier",
                "content": "input目录不存在，已创建。请上传文档后继续。"
            })
    
    return {"status": "success", "mode": current_mode}

# 文件上传
@app.post("/api/upload_file")
async def upload_file(file: UploadFile = File(...)):
    global uploaded_files, conversation_history
    
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown (.md) files are supported")
    
    try:
        # 确保目录存在
        os.makedirs(input_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(input_dir, file.filename)
        print(f"保存文件到: {file_path}")
        
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
        
        # 使用绝对路径保存到上传文件列表
        abs_path = str(Path(file_path).absolute())
        uploaded_files.append(abs_path)
        print(f"文件已添加到上传列表: {abs_path}")
        
        # 更新对话历史
        conversation_history.append({
            "role": "system",
            "content": f"文件 '{file.filename}' 上传成功。"
        })
        
        if len(uploaded_files) == 1:
            conversation_history.append({
                "role": "clarifier",
                "content": "文件已上传。您可以继续上传更多文件，或输入Y开始分析当前文件。"
            })
        else:
            conversation_history.append({
                "role": "clarifier",
                "content": f"已上传 {len(uploaded_files)} 个文件。请输入Y开始分析，或继续上传更多文件。"
            })
        
        return {"status": "success", "filename": file.filename}
    
    except Exception as e:
        print(f"文件上传出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 开始文档分析
@app.post("/api/analyze_documents")
async def analyze_documents():
    """分析上传的文档，使用LLM进行理解并更新全局状态"""
    global uploaded_files, conversation_history, global_state
    
    # 检查是否有上传的文件
    if not uploaded_files:
        raise HTTPException(status_code=400, detail="没有找到已上传的文件")
    
    try:
        # 读取所有上传文件的内容
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
        
        # 添加系统消息
        system_message = {
            "role": "system",
            "content": f"系统已经接收到以下文档内容进行分析:\n{all_content}"
        }
        conversation_history.append(system_message)
        
        # 调用LLM进行分析
        if not clarifier:
            raise HTTPException(status_code=500, detail="系统尚未初始化，请先启动系统")
        
        # 构建提示
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
        """.strip()
        
        # 使用clarifier的LLM执行器调用LLM
        response = None
        try:
            # 获取LLM响应
            if hasattr(clarifier, 'llm_executor') and hasattr(clarifier.llm_executor, 'run_prompt'):
                print("📝 使用LLM执行器调用...")
                response = clarifier.llm_executor.run_prompt(user_message=prompt)
            else:
                # 使用备用方法
                print("📝 使用Clarifier.run_llm方法调用...")
                response = await clarifier.run_llm(prompt=prompt)
                
            if not response:
                raise HTTPException(status_code=500, detail="无法获取有效的LLM响应")
            
            print(f"✅ 收到LLM响应: {response[:100]}...")
            
            # 从响应中提取JSON数据
            json_data = extract_json_from_response(response)
            
            if not json_data:
                raise HTTPException(status_code=500, detail="无法从LLM响应中提取JSON数据")
            
            print(f"✅ 成功解析JSON数据: 包含 {len(json_data.get('modules', {}))} 个模块")
            
            # 确保modules目录存在
            modules_dir = Path("data/output/modules")
            modules_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 已确保模块目录存在: {modules_dir}")
            
            # 为每个模块创建目录和full_summary.json
            modules_data = json_data.get("modules", {})
            if modules_data:
                print(f"📁 开始创建模块目录和摘要文件...")
                for module_id, module_data in modules_data.items():
                    # 确保module_name和module_id字段存在
                    if "module_name" not in module_data:
                        module_data["module_name"] = module_data.get("name", module_id)
                    
                    module_name = module_data["module_name"]
                    module_dir = modules_dir / str(module_name)
                    module_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 写入full_summary.json
                    with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
                        json.dump(module_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ 创建了模块目录和摘要: {module_dir}")
            
            # 如果解析成功，保存结果到文件
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # 保存完整的分析结果
                with open(output_dir / "full_analysis.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存完整分析结果到: {output_dir / 'full_analysis.json'}")
                
                # 单独保存需求
                with open(output_dir / "requirements.json", "w", encoding="utf-8") as f:
                    json.dump(json_data.get("requirements", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存需求到: {output_dir / 'requirements.json'}")
                
                # 单独保存模块
                with open(output_dir / "modules.json", "w", encoding="utf-8") as f:
                    json.dump(json_data.get("modules", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存模块到: {output_dir / 'modules.json'}")
                
                # 保存索引
                with open(output_dir / "requirement_module_index.json", "w", encoding="utf-8") as f:
                    json.dump(json_data.get("requirement_module_index", {}), f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存需求-模块索引到: {output_dir / 'requirement_module_index.json'}")
                
                # 生成依赖图
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
                    print(f"✅ 已生成依赖图到: {output_dir / 'dependency_graph.py'}")
                    
                    # 生成summary_index.json
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
                    print(f"✅ 已生成summary_index.json: {output_dir / 'summary_index.json'}")
                    
                except Exception as e:
                    print(f"⚠️ 生成依赖图或索引时出错: {e}")
                
            except Exception as e:
                print(f"⚠️ 保存分析结果文件时出错: {e}")
            
            # 更新全局状态并进行架构验证
            update_global_state_from_json(json_data)
            
            # 使用ArchitectureManager进行模块处理
            if clarifier and hasattr(clarifier, 'architecture_manager'):
                arch_manager = clarifier.architecture_manager
                for module_id, module_data in modules_data.items():
                    # 获取关联的需求
                    requirements = []
                    for req_id, modules in json_data.get("requirement_module_index", {}).items():
                        if module_id in modules:
                            requirements.append(req_id)
                    
                    # 处理模块
                    print(f"📊 处理模块: {module_id}")
                    result = await arch_manager.process_new_module(module_data, requirements)
                    print(f"🔍 模块处理结果: {result.get('status')}")
            
            # 添加用户和系统消息到对话历史
            user_message = {
                "role": "user",
                "content": "请分析我上传的文档内容，并提取关键信息。"
            }
            
            # 统计模块和需求数量
            req_count = len(global_state['requirements'])
            module_count = len(global_state['modules'])
            tech_stack = []
            for category in global_state['technology_stack'].values():
                if isinstance(category, list):
                    tech_stack.extend(category)
            
            system_response = {
                "role": "system",
                "content": f"文档分析完成，已提取到以下信息:\n" +
                           f"- 需求数量: {req_count}\n" +
                           f"- 模块数量: {module_count}\n" +
                           f"- 技术栈: {', '.join(tech_stack)}\n" +
                           f"- 模块目录已生成在: data/output/modules/\n" +
                           (f"- 验证问题: {global_state.get('validation_issues', {})}" if global_state.get('validation_issues') else "")
            }
            
            # 添加完成分析后的深度推理引导消息
            clarifier_next_steps = {
                "role": "clarifier",
                "content": "文档分析已完成，现在您可以选择以下操作:\n\n" + 
                          "1. 进行深度需求澄清，帮助完善需求细节\n" +
                          "2. 进行深度架构推理，生成更详细的架构设计\n\n" +
                          "请输入选项的编号(1或2)继续，或输入其他问题。"
            }
            
            conversation_history.append(user_message)
            conversation_history.append(system_response)
            conversation_history.append(clarifier_next_steps)
            
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

# 更新需求
@app.post("/api/update_requirement/{req_id}")
async def update_requirement(req_id: str, data: Dict[str, Any]):
    global global_state
    
    if req_id not in global_state["requirements"]:
        raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")
    
    # Update the requirement
    global_state["requirements"][req_id].update(data)
    
    # Find affected modules (in a real implementation, this would trigger regeneration)
    affected_modules = []
    for module_id, module_data in global_state["requirement_module_index"].items():
        if "requirements" in module_data and req_id in module_data["requirements"]:
            affected_modules.append(module_id)
    
    # In a real implementation, you would regenerate these modules
    # For now, just return them
    return {
        "status": "success", 
        "requirement": global_state["requirements"][req_id],
        "affected_modules": affected_modules
    }

# 分析需求并生成架构
@app.post("/api/analyze")
async def analyze_requirements():
    try:
        return await clarifier_service.analyze_architecture()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 发送消息
@app.post("/api/chat")
async def chat(message: Message):
    global clarifier, conversation_history, current_mode, global_state, uploaded_files
    
    # Initialize clarifier if needed
    if clarifier is None:
        print("⚠️ Clarifier未初始化，正在初始化...")
        await start_clarifier()
    
    # Add user message to history
    user_message = message.content.strip()
    print(f"📝 用户消息: '{user_message}'")
    
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # 文档分析完成后的深度澄清和架构推理快捷触发
    if len(conversation_history) >= 2:
        prev_message = conversation_history[-2]
        if prev_message["role"] == "clarifier" and "深度澄清" in prev_message["content"] and "深度推理" in prev_message["content"]:
            print(f"🔍 检测到深度分析选项提示，用户输入: '{user_message}'")
            
            if user_message == "1":
                # 触发深度澄清
                print("📊 用户选择了深度澄清")
                conversation_history.append({
                    "role": "system",
                    "content": "正在触发深度澄清..."
                })
                try:
                    await deep_clarification()
                    return {"status": "success", "message": "Deep clarification triggered"}
                except Exception as e:
                    print(f"❌ 深度澄清出错: {str(e)}")
                    conversation_history.append({
                        "role": "system",
                        "content": f"触发深度澄清时出错: {str(e)}"
                    })
                    return {"status": "error", "message": str(e)}
            
            elif user_message == "2":
                # 触发深度推理
                print("🏗️ 用户选择了深度推理")
                conversation_history.append({
                    "role": "system",
                    "content": "正在触发深度架构推理..."
                })
                try:
                    print("🔄 调用deep_reasoning函数")
                    result = await deep_reasoning()
                    print(f"✅ 深度推理完成，结果: {result}")
                    return {"status": "success", "message": "Deep reasoning triggered"}
                except Exception as e:
                    print(f"❌ 触发深度推理时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    conversation_history.append({
                        "role": "system",
                        "content": f"触发深度架构推理时出错: {str(e)}"
                    })
                    return {"status": "error", "message": str(e)}
    
    # Handle mode selection if not set
    if current_mode is None:
        if user_message == "1":
            current_mode = "file_based"
            conversation_history.append({
                "role": "clarifier",
                "content": "您选择了基于文件分析模式。请上传需求文档（.md格式）。"
            })
            return {"status": "success", "mode": current_mode}
        elif user_message == "2":
            current_mode = "interactive"
            conversation_history.append({
                "role": "clarifier",
                "content": "您选择了交互式对话模式。请描述您的业务需求，我将帮助您澄清需求并生成架构建议。"
            })
            return {"status": "success", "mode": current_mode}
    
    # Process the message based on current mode
    if current_mode == "file_based":
        # In file-based mode, just acknowledge messages unless files need to be processed
        if len(uploaded_files) > 0 and user_message.upper() == "Y":
            # Handle file analysis confirmation
            return await analyze_documents()
        else:
            conversation_history.append({
                "role": "clarifier",
                "content": "请上传需求文档（.md格式）或输入Y开始分析已上传的文档。"
            })
    else:
        # Interactive mode - process with clarifier
        if clarifier:
            try:
                # Run the clarifier with the user's message
                clarifier_response = clarifier.run_llm(
                    user_message=user_message,
                    system_message="你是一个专业的需求分析师和架构设计师，帮助用户澄清业务需求并设计合适的架构。"
                )
                
                # Update the global state if there's structured data from clarifier
                # This would be where you process and update modules, requirements, etc.
                parse_and_update_global_state(clarifier_response)
                
                # Add the response to conversation history
                conversation_history.append({
                    "role": "clarifier",
                    "content": clarifier_response
                })
            except Exception as e:
                conversation_history.append({
                    "role": "system",
                    "content": f"处理您的消息时出错: {str(e)}"
                })
    
    return {"status": "success"}

def parse_and_update_global_state(response: str):
    """Parse the clarifier response and update global state if it contains structured data."""
    global global_state
    
    # Look for JSON blocks in the response
    try:
        # Very simple JSON extraction - in production would need more robust parsing
        if "```json" in response and "```" in response:
            json_content = response.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_content)
            
            # Update global state with extracted data
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

# 更新process_files函数使其调用analyze_documents
async def process_files():
    """Process the uploaded files using the clarifier."""
    # 直接调用analyze_documents函数处理文件
    return await analyze_documents()

# 启动事件
@app.on_event("startup")
async def startup_event():
    # 自动初始化系统
    clarifier_service.add_system_message("系统启动中，正在初始化...")
    
    try:
        # 初始化系统
        await clarifier_service.initialize()
    except Exception as e:
        clarifier_service.add_system_message(f"系统初始化失败: {str(e)}")

# 修改深度澄清API以调用Clarifier类中的方法
@app.post("/api/deep_clarification")
async def deep_clarification():
    global clarifier, conversation_history, global_state
    
    if not clarifier:
        raise HTTPException(status_code=400, detail="Clarifier not initialized")
    
    try:
        conversation_history.append({
            "role": "system",
            "content": "开始进行深度需求澄清..."
        })
        
        # 构建需求数据
        requirement_analysis = {
            "requirements": [],
            "system_overview": {},
            "functional_requirements": {}
        }
        
        # 从全局状态中获取需求数据
        if global_state["requirements"]:
            for req_id, req_data in global_state["requirements"].items():
                requirement_analysis["requirements"].append(req_data)
        
        # 调用Clarifier核心类的深度澄清方法
        result = await clarifier.deep_clarification(requirement_analysis)
        
        # 如果没有得到结果，可能是因为需求数据不足
        if not result or not result.get("clarification_result"):
            conversation_history.append({
                "role": "system",
                "content": "深度澄清未返回结果，可能是因为需求数据不足。"
            })
            return {"status": "warning", "message": "No clarification result returned"}
        
        # 添加结果到对话历史
        conversation_history.append({
            "role": "clarifier", 
            "content": result.get("clarification_result", "深度澄清完成，但没有具体结果。")
        })
        
        return {"status": "success", "message": "Deep clarification completed"}
    
    except Exception as e:
        conversation_history.append({
            "role": "system",
            "content": f"深度澄清时出错: {str(e)}"
        })
        raise HTTPException(status_code=500, detail=str(e))

# 修改深度推理API以调用Clarifier类中的方法，并增加详细的日志
@app.post("/api/deep_reasoning")
async def deep_reasoning():
    global clarifier, conversation_history, global_state
    
    if not clarifier:
        print("❌ 深度推理失败: Clarifier未初始化")
        raise HTTPException(status_code=400, detail="Clarifier not initialized")
    
    try:
        print("🔍 开始进行深度架构推理...")
        conversation_history.append({
            "role": "system",
            "content": "开始进行深度架构推理..."
        })
        
        # 构建需求和架构数据
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
        
        # 从全局状态中获取需求数据
        if global_state["requirements"]:
            print(f"📊 找到 {len(global_state['requirements'])} 个需求")
            for req_id, req_data in global_state["requirements"].items():
                requirement_analysis["requirements"].append(req_data)
                print(f"  - 需求: {req_data.get('name', req_id)}")
        else:
            print("⚠️ 没有找到需求数据")
        
        # 从全局状态中获取架构数据
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
        
        # 调用Clarifier核心类的深度推理方法
        result = await clarifier.deep_reasoning(requirement_analysis, architecture_analysis)
        
        print(f"✅ 深度推理完成，结果类型: {type(result)}")
        
        # 如果没有得到结果，可能是因为数据不足
        if not result:
            print("⚠️ 深度推理未返回任何结果")
            conversation_history.append({
                "role": "system",
                "content": "深度推理未返回结果，可能是因为需求或架构数据不足。"
            })
            return {"status": "warning", "message": "No reasoning result returned"}
        
        if not result.get("reasoning_result"):
            print("⚠️ 深度推理返回的结果中没有reasoning_result字段")
            conversation_history.append({
                "role": "system",
                "content": "深度推理未返回有效结果，可能是因为需求或架构数据不足。"
            })
            return {"status": "warning", "message": "No valid reasoning result returned"}
        
        reasoning_content = result.get("reasoning_result", "")
        print(f"📝 结果长度: {len(reasoning_content)} 字符")
        
        # 尝试从响应中提取结构化数据
        print("🔍 从响应中提取结构化数据...")
        extracted_json = extract_json_from_response(reasoning_content)
        
        if extracted_json:
            print(f"✅ 成功从推理结果中提取JSON数据")
            # 更新全局状态
            update_global_state_from_json(extracted_json)
            
            # 尝试识别新模块
            if "modules" in extracted_json:
                new_modules_count = 0
                for module_id, module_data in extracted_json["modules"].items():
                    if module_id not in global_state["modules"]:
                        new_modules_count += 1
                        
                if new_modules_count > 0:
                    print(f"🔍 从推理中识别到 {new_modules_count} 个新模块")
                    conversation_history.append({
                        "role": "system",
                        "content": f"深度推理发现 {new_modules_count} 个新模块。这些模块已添加到架构中。"
                    })
            
            # 尝试识别循环依赖
            try:
                if clarifier and hasattr(clarifier, 'architecture_manager'):
                    arch_manager = clarifier.architecture_manager
                    if hasattr(arch_manager, 'find_circular_dependencies'):
                        circular_deps = arch_manager.find_circular_dependencies()
                        if circular_deps:
                            print(f"⚠️ 检测到循环依赖: {circular_deps}")
                            conversation_history.append({
                                "role": "system",
                                "content": f"警告：检测到循环依赖: {', '.join([' -> '.join(dep) for dep in circular_deps])}"
                            })
            except Exception as e:
                print(f"⚠️ 检查循环依赖时出错: {e}")
        else:
            print("⚠️ 无法从推理结果中提取JSON数据，仅保存文本内容")
            parse_and_update_global_state(reasoning_content)
        
        # 保存推理结果到文件
        try:
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为Markdown文档
            with open(output_dir / "deep_reasoning_result.md", "w", encoding="utf-8") as f:
                f.write(f"# 深度架构推理结果\n\n{reasoning_content}")
            print(f"✅ 已保存推理结果到: {output_dir / 'deep_reasoning_result.md'}")
            
            # 如果提取到了JSON，也单独保存
            if extracted_json:
                with open(output_dir / "deep_reasoning_result.json", "w", encoding="utf-8") as f:
                    json.dump(extracted_json, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存结构化推理结果到: {output_dir / 'deep_reasoning_result.json'}")
        except Exception as e:
            print(f"⚠️ 保存推理结果时出错: {e}")
        
        # 添加结果到对话历史
        conversation_history.append({
            "role": "clarifier", 
            "content": reasoning_content
        })
        
        # 添加深度推理完成的提示消息
        conversation_history.append({
            "role": "clarifier", 
            "content": "深度推理完成。您可以：\n1. 查看生成的模块详情\n2. 开始实现代码\n3. 进行架构验证"
        })
        
        return {"status": "success", "message": "Deep reasoning completed", "has_extracted_json": bool(extracted_json)}
    
    except Exception as e:
        print(f"❌ 深度推理时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        conversation_history.append({
            "role": "system",
            "content": f"深度推理时出错: {str(e)}"
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/check_dependencies")
async def check_dependencies():
    """检查模块依赖和循环依赖"""
    global clarifier, global_state
    
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
            
            # 更新全局状态
            global_state["validation_issues"] = {
                "circular_dependencies": cycles,
                "module_issues": validation_issues
            }
            
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

# 更新全局状态的函数
def update_global_state_from_json(data: Dict[str, Any]) -> None:
    """从JSON数据更新全局状态，并使用现有架构管理器执行验证"""
    global global_state, clarifier
    
    print(f"🔄 开始从JSON更新全局状态...")
    
    # 基本状态更新
    if "requirements" in data and isinstance(data["requirements"], dict):
        global_state["requirements"] = data["requirements"]
        print(f"✅ 更新了 {len(data['requirements'])} 个需求")
    
    if "modules" in data and isinstance(data["modules"], dict):
        global_state["modules"] = data["modules"]
        print(f"✅ 更新了 {len(data['modules'])} 个模块")
        
        # 为每个模块创建目录和文件
        modules_dir = Path("data/output/modules")
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        for module_id, module_data in data["modules"].items():
            # 确保module_name字段存在
            if "module_name" not in module_data:
                module_data["module_name"] = module_data.get("name", module_id)
                
            module_name = module_data["module_name"]
            module_dir = modules_dir / str(module_name)
            module_dir.mkdir(parents=True, exist_ok=True)
            
            # 写入full_summary.json
            summary_path = module_dir / "full_summary.json"
            try:
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(module_data, f, ensure_ascii=False, indent=2)
                print(f"✅ 为模块 '{module_name}' 创建了摘要文件: {summary_path}")
            except Exception as e:
                print(f"❌ 为模块 '{module_name}' 创建摘要文件失败: {e}")
    
    if "technology_stack" in data and isinstance(data["technology_stack"], dict):
        global_state["technology_stack"] = data["technology_stack"]
        print(f"✅ 更新了技术栈")
    
    if "requirement_module_index" in data and isinstance(data["requirement_module_index"], dict):
        requirement_module_map = {}
        for req_id, modules in data["requirement_module_index"].items():
            req_name = data.get("requirements", {}).get(req_id, {}).get("name", "未知需求")
            requirement_module_map[req_id] = {
                "name": req_name,
                "modules": modules
            }
        
        global_state["requirement_module_index"] = requirement_module_map
        print(f"✅ 已更新需求-模块映射关系")
    
    if "architecture_pattern" in data and isinstance(data["architecture_pattern"], dict):
        global_state["architecture_pattern"] = data["architecture_pattern"]
        print(f"✅ 更新了架构模式")
    
    if "modules" in data and isinstance(data["modules"], dict):
        modules_data = data["modules"]
        
        responsibility_index = {}
        layer_index = {}
        domain_index = {}
        
        for module_id, module_info in modules_data.items():
            for resp in module_info.get("responsibilities", []):
                if resp not in responsibility_index:
                    responsibility_index[resp] = []
                responsibility_index[resp].append(module_id)
            
            layer = module_info.get("layer", "unknown")
            if layer not in layer_index:
                layer_index[layer] = []
            layer_index[layer].append(module_id)
            
            domain = module_info.get("domain", "unknown")
            if domain not in domain_index:
                domain_index[domain] = []
            domain_index[domain].append(module_id)
        
        global_state["responsibility_index"] = responsibility_index
        global_state["layer_index"] = layer_index
        global_state["domain_index"] = domain_index
        print(f"✅ 已更新多维度模块索引")
    
    # 尝试生成依赖图和索引文件
    try:
        modules_data = data.get("modules", {})
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成依赖图
        dependency_graph = {}
        for module_id, module_data in modules_data.items():
            module_name = module_data.get("module_name", "")
            depends_on = module_data.get("dependencies", [])
            dependency_graph[module_name] = depends_on
        
        with open(output_dir / "dependency_graph.py", "w", encoding="utf-8") as f:
            f.write("# Auto-generated module dependency graph\n")
            f.write("dependency_graph = ")
            json.dump(dependency_graph, f, ensure_ascii=False, indent=2)
        print(f"✅ 已生成依赖图到: {output_dir / 'dependency_graph.py'}")
        
        # 生成summary_index.json
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
        print(f"✅ 已生成summary_index.json: {output_dir / 'summary_index.json'}")
    except Exception as e:
        print(f"⚠️ 生成依赖图或索引时出错: {e}")
    
    # 通过现有的ArchitectureManager验证架构
    try:
        # 使用现有的ArchitectureManager初始化
        if clarifier and hasattr(clarifier, 'architecture_manager'):
            arch_manager = clarifier.architecture_manager
            print(f"🔍 使用ArchitectureManager验证架构...")
            
            # 1. 先添加所有需求到架构管理器
            if "requirements" in data:
                for req_id, req_data in data["requirements"].items():
                    if hasattr(arch_manager, 'add_requirement'):
                        arch_manager.add_requirement(req_data)
                        print(f"✅ 添加需求 '{req_id}' 到架构管理器")
            
            # 2. 添加模块到架构索引
            for module_id, module in global_state["modules"].items():
                # 查找该模块对应的需求
                requirements = []
                if "requirement_module_index" in data:
                    for req_id, modules in data["requirement_module_index"].items():
                        if module_id in modules:
                            requirements.append(req_id)
                            print(f"📊 模块 '{module_id}' 关联到需求 '{req_id}'")
                
                # 检查模块是否已存在于索引中
                module_name = module.get("module_name", module_id)
                if hasattr(arch_manager.index, 'dependency_graph') and module_name not in arch_manager.index.dependency_graph:
                    print(f"🔄 添加模块 '{module_name}' 到架构索引...")
                    # 添加模块到架构索引并生成目录
                    try:
                        if hasattr(arch_manager, 'process_new_module'):
                            process_result = arch_manager.process_new_module(module, requirements)
                            print(f"✅ 模块处理结果: {process_result.get('status', '未知')}")
                    except Exception as e:
                        print(f"❌ 处理模块 '{module_name}' 时出错: {e}")
            
            # 3. 从架构管理器中获取验证问题
            try:
                if hasattr(arch_manager, 'get_validation_issues'):
                    validation_issues = arch_manager.get_validation_issues()
                    if validation_issues:
                        global_state["validation_issues"] = validation_issues
                        print(f"⚠️ 检测到架构验证问题: {validation_issues}")
            except Exception as e:
                print(f"⚠️ 获取验证问题时出错: {e}")
            
    except Exception as e:
        print(f"⚠️ 架构验证出错: {str(e)}")
        traceback.print_exc()

# 改进JSON提取函数
def extract_json_from_response(response: str) -> Dict[str, Any]:
    """从LLM响应中提取JSON数据，增强提取能力"""
    if not response:
        return {}
    
    # 寻找JSON块 - 支持多种标记方式
    json_patterns = [
        r'```(?:json)?(.*?)```',  # 标准markdown代码块
        r'{[\s\S]*"requirements"[\s\S]*}',  # 直接查找包含requirements的JSON对象
        r'{[\s\S]*"modules"[\s\S]*}',       # 直接查找包含modules的JSON对象
    ]
    
    # 尝试所有模式
    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            # 尝试解析匹配的JSON块
            for match in matches:
                try:
                    # 清理JSON文本
                    cleaned_json = match.strip()
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    print(f"⚠️ JSON解析错误，尝试清理JSON文本")
                    try:
                        # 移除注释行
                        no_comments = re.sub(r'^\s*//.*$', '', cleaned_json, flags=re.MULTILINE)
                        # 移除尾部逗号
                        fixed_commas = re.sub(r',\s*}', '}', no_comments)
                        fixed_commas = re.sub(r',\s*]', ']', fixed_commas)
                        return json.loads(fixed_commas)
                    except json.JSONDecodeError:
                        continue  # 尝试下一个匹配项
    
    # 尝试直接从文本中提取JSON (如果整个响应就是一个JSON)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 最后尝试寻找大括号包围的内容
    try:
        # 查找最外层的大括号
        curly_pattern = r'{[\s\S]*}'
        match = re.search(curly_pattern, response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass
    
    print("⚠️ 无法从响应中提取有效的JSON")
    return {}

# 主函数
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webui.app:app", host="0.0.0.0", port=8080, reload=True)                        