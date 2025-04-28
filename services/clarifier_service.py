"""
服务层模块，封装与Clarifier交互的所有业务逻辑
"""

import os
import asyncio
from pathlib import Path
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
import traceback

# 导入核心模块
from core.clarifier import create_clarifier, ensure_data_dir
from core.llm.llm_executor import run_prompt

class ClarifierService:
    """
    Clarifier服务类，提供所有与Clarifier交互的业务逻辑
    作为Web API和Clarifier核心逻辑之间的中间层
    """
    
    def __init__(self):
        """初始化服务"""
        self.clarifier = None
        self.architecture_manager = None
        self.is_initialized = False
        self.conversation_history = []
        self.current_mode = None
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def get_mode(self) -> Optional[str]:
        """获取当前模式"""
        return self.current_mode
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息到历史记录"""
        message = {
            "role": "system",
            "content": content
        }
        self.conversation_history.append(message)
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息到历史记录"""
        message = {
            "role": "user",
            "content": content
        }
        self.conversation_history.append(message)
    
    def add_clarifier_message(self, content: str) -> None:
        """添加澄清器消息到历史记录"""
        message = {
            "role": "clarifier",
            "content": content
        }
        self.conversation_history.append(message)
    
    async def initialize(self, use_mock: bool = False) -> Dict[str, Any]:
        """
        初始化Clarifier服务
        
        Args:
            use_mock: 是否使用模拟LLM响应
            
        Returns:
            包含初始化状态的字典
        """
        if self.is_initialized:
            return {"status": "already_initialized"}
        
        try:
            # 添加初始化消息
            self.add_system_message("系统启动中，正在初始化...")
            
            # 使用工厂方法创建Clarifier
            self.clarifier = create_clarifier(
                data_dir="data",
                use_mock=use_mock,
                verbose=True
            )
            
            # 获取架构管理器引用
            self.architecture_manager = self.clarifier.architecture_manager
            
            # 添加初始化完成消息
            module_info = (
                f"正在初始化系统组件：\n"
                f"- Clarifier 从 {self.clarifier.__class__.__module__}\n"
                f"- ArchitectureManager 从 {self.architecture_manager.__class__.__module__}"
            )
            self.add_system_message(module_info)
            
            # 标记为初始化完成
            self.is_initialized = True
            self.add_system_message("系统已初始化完成，您可以开始添加需求或询问问题。")
            
            # 添加欢迎信息
            self.add_system_message("🚀 欢迎使用需求澄清与架构设计助手！")
            
            # 检查是否有默认的输入文件
            input_files = self._get_input_files()
            if input_files:
                self.add_system_message(f"系统检测到输入目录中已有 {len(input_files)} 个Markdown文档。您可以：")
            
            # 提示选择模式
            self.add_system_message(
                "请选择操作模式：\n"
                "1. 文件解析模式（从上传的文档中分析需求）\n"
                "2. 交互式对话模式（通过对话完成需求澄清）"
            )
            
            return {"status": "success"}
        except Exception as e:
            error_trace = traceback.format_exc()
            error_message = f"初始化系统时出错: {str(e)}\n\n技术细节: {error_trace}"
            self.add_system_message(error_message)
            return {"status": "error", "message": str(e)}
    
    async def set_mode(self, mode: str) -> Dict[str, Any]:
        """
        设置操作模式
        
        Args:
            mode: 操作模式 (file_based 或 interactive)
            
        Returns:
            包含结果状态的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        # 设置模式
        self.current_mode = mode
        
        # 添加模式选择消息
        mode_display = "文件解析" if mode == "file_based" else "交互式对话"
        self.add_system_message(f"已选择{mode_display}模式。")
        
        if mode == "file_based":
            # 检查输入文件夹
            input_dir = Path("data/input")
            if not input_dir.exists():
                input_dir.mkdir(parents=True, exist_ok=True)
                self.add_system_message(f"已创建输入文件夹：{input_dir}。请上传您的需求文档。")
            else:
                # 列出已有文件
                md_files = list(input_dir.glob('**/*.md'))
                if md_files:
                    file_list = "\n".join([f"- {str(f.relative_to(input_dir))}" for f in md_files])
                    self.add_system_message(
                        f"在输入文件夹中找到以下现有文件：\n{file_list}\n\n"
                        f"您可以直接分析这些文件，或上传新文件。"
                    )
                    self.add_system_message("是否立即分析这些文件？请回复 'Y' 开始分析，或上传新文件。")
                else:
                    self.add_system_message("输入文件夹中没有找到任何Markdown文件。请上传您的需求文档。")
        else:  # 交互式模式
            self.add_system_message("您已进入交互式对话模式。请直接描述您的需求，我会帮助您进行需求澄清和架构设计。")
        
        return {"status": "success", "mode": self.current_mode}
    
    async def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        上传文件到input目录
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            包含上传状态的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        if self.current_mode != "file_based":
            return {"status": "error", "message": "只能在文件解析模式下上传文件"}
        
        # 确保文件是Markdown格式
        if not filename.endswith('.md'):
            self.add_system_message(f"⚠️ 上传失败：{filename} 不是Markdown文件。请上传.md格式的文件。")
            return {"status": "error", "message": "只支持Markdown文件"}
        
        # 保存文件
        input_dir = Path("data/input")
        input_dir.mkdir(parents=True, exist_ok=True)
        file_path = input_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        self.add_system_message(f"✓ 已上传文件：{filename}")
        return {"status": "success", "filename": filename}
    
    async def analyze_documents(self) -> Dict[str, Any]:
        """
        分析input目录中的所有文档
        
        Returns:
            包含分析状态的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        if self.current_mode != "file_based":
            return {"status": "error", "message": "只能在文件解析模式下分析文档"}
        
        # 检查文件
        input_dir = Path("data/input")
        md_files = list(input_dir.glob('**/*.md'))
        
        if not md_files:
            self.add_system_message("⚠️ 无法开始分析：输入文件夹中没有找到任何Markdown文件。请先上传文件。")
            return {"status": "error", "message": "没有找到任何文件"}
        
        # 添加开始分析消息
        self.add_system_message("📂 开始分析文档...")
        
        try:
            # 读取所有文件
            all_documents = {}
            for file_path in md_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    relative_path = file_path.relative_to(input_dir)
                    all_documents[str(relative_path)] = content
                    self.add_system_message(f"- 已读取文档：{relative_path}")
                except Exception as e:
                    self.add_system_message(f"⚠️ 读取文件 {file_path} 时出错：{str(e)}")
            
            # 检查是否有成功读取的文档
            if not all_documents:
                self.add_system_message("⚠️ 没有成功读取任何文档。请检查文件内容和编码。")
                return {"status": "error", "message": "没有成功读取任何文档"}
            
            # 合并文档内容
            all_content = ""
            for doc_name, content in all_documents.items():
                all_content += f"\n\n# {doc_name}\n{content}"
            
            # 分析需求
            self.add_system_message(f"✓ 找到 {len(all_documents)} 个文档。正在分析需求...")
            
            # 调用需求分析器
            requirement_analysis = await self.clarifier.requirement_analyzer.analyze_requirements(
                all_content, self.clarifier.run_llm
            )
            
            # 生成需求摘要文档
            self.add_system_message("正在生成需求摘要文档...")
            
            await self.clarifier.requirement_analyzer.generate_requirement_summary(
                requirement_analysis, self.clarifier.run_llm
            )
            
            # 保存分析结果到架构管理器
            self.architecture_manager.requirements = requirement_analysis.get("requirements", [])
            self.architecture_manager.system_overview = requirement_analysis.get("system_overview", {})
            self.architecture_manager.functional_requirements = requirement_analysis.get("functional_requirements", {})
            
            # 添加分析完成消息
            self.add_system_message("✓ 需求分析完成！您可以继续进行架构分析，或查看需求摘要。")
            
            return {
                "status": "success", 
                "message": "需求分析完成",
                "requirements_count": len(requirement_analysis.get("requirements", []))
            }
        except Exception as e:
            error_trace = traceback.format_exc()
            self.add_system_message(f"⚠️ 分析文档时出错：{str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def process_message(self, message_content: str) -> str:
        """
        处理用户消息，并返回澄清器的响应
        
        Args:
            message_content: 用户消息内容
            
        Returns:
            澄清器的响应
        """
        if not self.clarifier:
            self.add_system_message("系统尚未初始化，正在尝试初始化...")
            init_result = await self.initialize()
            if init_result.get("status") != "success":
                self.add_system_message(f"初始化失败: {init_result.get('message', '未知错误')}")
                raise Exception("系统尚未初始化且无法自动初始化")
        
        # 添加"思考中"消息
        self.add_system_message("正在思考中...")
        
        try:
            # 调用LLM
            response = await self.clarifier.run_llm(
                prompt=message_content,
                system_message="你是一个需求澄清和架构设计助手，请根据用户的输入，帮助分析需求和设计架构。"
            )
            
            # 从历史记录中移除"思考中"的消息
            if (self.conversation_history 
                and self.conversation_history[-1]["role"] == "system" 
                and self.conversation_history[-1]["content"] == "正在思考中..."):
                self.conversation_history.pop()
            
            return response
        except Exception as e:
            # 从历史记录中移除"思考中"的消息
            if (self.conversation_history 
                and self.conversation_history[-1]["role"] == "system" 
                and self.conversation_history[-1]["content"] == "正在思考中..."):
                self.conversation_history.pop()
            
            error_message = f"处理消息时出错: {str(e)}"
            self.add_system_message(error_message)
            raise Exception(error_message)
    
    async def analyze_architecture(self) -> Dict[str, Any]:
        """
        分析架构需求并生成架构文档
        
        Returns:
            包含分析状态的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            # 通知用户分析开始
            self.add_system_message("开始分析需求并生成架构...")
            
            # 调用澄清器分析需求
            await self.clarifier.analyze_requirements()
            
            # 调用澄清器生成架构
            await self.clarifier.analyze_architecture_needs()
            
            # 通知用户分析完成
            self.add_system_message("需求分析和架构生成已完成。")
            
            return {"status": "success"}
        except Exception as e:
            error_message = f"分析需求失败: {str(e)}"
            self.add_system_message(error_message)
            return {"status": "error", "message": str(e)}
    
    def get_state(self) -> Dict[str, Any]:
        """
        获取当前全局状态
        
        Returns:
            包含全局状态的字典
        """
        if not self.is_initialized:
            return {
                "requirements": {},
                "modules": {},
                "technology_stack": {},
                "requirement_module_index": {},
                "architecture_pattern": {}
            }
        
        # 从架构管理器获取状态
        # 获取需求
        requirements = {}
        if hasattr(self.architecture_manager, 'requirements') and self.architecture_manager.requirements:
            for idx, req in enumerate(self.architecture_manager.requirements):
                requirements[f"req_{idx}"] = {
                    "title": req.get("title", f"需求 {idx+1}"),
                    "description": req.get("description", ""),
                    "priority": req.get("priority", "中")
                }
        
        # 获取模块
        modules = {}
        if hasattr(self.architecture_manager, 'modules') and self.architecture_manager.modules:
            for idx, module in enumerate(self.architecture_manager.modules):
                modules[f"module_{idx}"] = {
                    "name": module.get("name", f"模块 {idx+1}"),
                    "description": module.get("description", ""),
                    "technologies": module.get("technologies", {}),
                    "dependencies": module.get("dependencies", [])
                }
        
        # 获取技术栈
        tech_stack = {}
        if hasattr(self.architecture_manager, 'technology_stack') and self.architecture_manager.technology_stack:
            tech_stack = self.architecture_manager.technology_stack
        
        # 获取或构建需求-模块索引
        req_module_index = {}
        if hasattr(self.architecture_manager, 'modules') and self.architecture_manager.modules:
            for idx, module in enumerate(self.architecture_manager.modules):
                module_id = f"module_{idx}"
                req_module_index[module_id] = {
                    "requirements": []
                }
                # 扫描每个模块的需求关联
                if module.get("requirements"):
                    for req_idx, req in enumerate(self.architecture_manager.requirements):
                        if req.get("id") in module.get("requirements", []):
                            req_module_index[module_id]["requirements"].append(f"req_{req_idx}")
        
        # 获取架构模式
        architecture_pattern = {}
        if hasattr(self.architecture_manager, 'architecture_pattern') and self.architecture_manager.architecture_pattern:
            architecture_pattern = {
                "name": self.architecture_manager.architecture_pattern.get("name", "自定义架构"),
                "description": self.architecture_manager.architecture_pattern.get("description", "")
            }
        
        return {
            "requirements": requirements,
            "modules": modules,
            "technology_stack": tech_stack,
            "requirement_module_index": req_module_index,
            "architecture_pattern": architecture_pattern
        }
    
    async def update_requirement(self, req_id: str, data: dict) -> Dict[str, Any]:
        """
        更新需求
        
        Args:
            req_id: 需求ID
            data: 需求数据
            
        Returns:
            包含更新状态的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        # 提取需求ID的索引
        try:
            req_idx = int(req_id.split("_")[1])
        except:
            return {"status": "error", "message": "无效的需求ID格式"}
        
        # 更新需求
        try:
            if req_idx >= len(self.architecture_manager.requirements):
                return {"status": "error", "message": "需求不存在"}
            
            # 保存原始需求用于比较
            original_req = self.architecture_manager.requirements[req_idx].copy()
            
            # 更新需求
            for key, value in data.items():
                if key in self.architecture_manager.requirements[req_idx]:
                    self.architecture_manager.requirements[req_idx][key] = value
            
            # 记录更新
            self.add_system_message(f"需求 '{original_req.get('title', f'需求 {req_idx+1}')}' 已更新。")
            
            # 找出受影响的模块
            affected_modules = []
            for idx, module in enumerate(self.architecture_manager.modules):
                if module.get("requirements") and original_req.get("id") in module.get("requirements", []):
                    affected_modules.append({
                        "id": f"module_{idx}",
                        "name": module.get("name", f"模块 {idx+1}")
                    })
            
            # 如果有受影响的模块，通知用户
            if affected_modules:
                modules_str = ", ".join([m["name"] for m in affected_modules])
                self.add_system_message(f"以下模块可能受到影响: {modules_str}")
            
            return {
                "status": "success",
                "updated_requirement": self.architecture_manager.requirements[req_idx],
                "affected_modules": affected_modules
            }
        except Exception as e:
            return {"status": "error", "message": f"更新需求失败: {str(e)}"}
    
    def _get_input_files(self) -> List[Path]:
        """获取input目录中的文件"""
        input_dir = Path("data/input")
        if not input_dir.exists():
            return []
        
        return list(input_dir.glob('**/*.md'))

# 创建全局服务实例
clarifier_service = ClarifierService() 