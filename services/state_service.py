"""
状态服务模块，管理全局状态
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import traceback
import uuid
from fastapi import Depends
from functools import lru_cache
from core.clarifier.clarifier import Clarifier

class StateService:
    """
    状态服务类，管理所有全局状态
    """
    
    def __init__(self):
        """初始化状态服务"""
        self.clarifier: Optional[Clarifier] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.global_state: Dict[str, Any] = {
            "requirements": {},
            "modules": [],
            "technology_stack": {},
            "requirement_module_index": {},
            "architecture_pattern": {},
            "validation_issues": {},  # 保存验证问题
            "circular_dependencies": []
        }
        self.uploaded_files: List[str] = []
        self.current_mode: Optional[str] = None
        self.input_dir = "data/input"
        
        self.load_modules_from_disk()
    
    def get_clarifier(self) -> Optional[Clarifier]:
        """获取Clarifier实例"""
        return self.clarifier
    
    def set_clarifier(self, clarifier: Clarifier) -> None:
        """设置Clarifier实例"""
        self.clarifier = clarifier
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def add_conversation_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_global_state(self) -> Dict[str, Any]:
        """获取全局状态"""
        return self.global_state
    
    def update_global_state(self, new_state: Dict[str, Any]) -> Dict[str, Any]:
        """更新全局状态"""
        for key, value in new_state.items():
            if key in self.global_state:
                if isinstance(value, dict) and isinstance(self.global_state[key], dict):
                    self.global_state[key].update(value)
                else:
                    self.global_state[key] = value
            else:
                self.global_state[key] = value
        return self.global_state
    
    def get_uploaded_files(self) -> List[str]:
        """获取上传的文件列表"""
        return self.uploaded_files
    
    def add_uploaded_file(self, file_path: str) -> None:
        """添加文件到上传列表"""
        if file_path not in self.uploaded_files:
            self.uploaded_files.append(file_path)
    
    def clear_uploaded_files(self) -> None:
        """清空上传文件列表"""
        self.uploaded_files = []
    
    def get_current_mode(self) -> Optional[str]:
        """获取当前模式"""
        return self.current_mode
    
    def set_current_mode(self, mode: str) -> None:
        """设置当前模式"""
        self.current_mode = mode
    
    def add_requirement(self, requirement_id: str, requirement_data: Dict[str, Any]) -> None:
        """添加需求"""
        if "requirements" not in self.global_state:
            self.global_state["requirements"] = {}
        self.global_state["requirements"][requirement_id] = requirement_data
    
    def add_module(self, module_id: str, module_data: Dict[str, Any]) -> None:
        """添加模块"""
        if "modules" not in self.global_state:
            self.global_state["modules"] = []
        
        if "id" not in module_data:
            module_data["id"] = module_id
            
        for i, existing_module in enumerate(self.global_state["modules"]):
            if existing_module.get("id") == module_id:
                self.global_state["modules"][i] = module_data
                return
                
        self.global_state["modules"].append(module_data)
    
    def add_validation_issue(self, issue_type: str, issue_data: Dict[str, Any]) -> None:
        """添加验证问题"""
        if "validation_issues" not in self.global_state:
            self.global_state["validation_issues"] = {}
        if issue_type not in self.global_state["validation_issues"]:
            self.global_state["validation_issues"][issue_type] = []
        self.global_state["validation_issues"][issue_type].append(issue_data)
    
    def add_circular_dependency(self, dependency_data: Dict[str, Any]) -> None:
        """添加循环依赖"""
        if "circular_dependencies" not in self.global_state:
            self.global_state["circular_dependencies"] = []
        self.global_state["circular_dependencies"].append(dependency_data)
    
    def clear_global_state(self) -> None:
        """清空全局状态"""
        self.global_state = {
            "requirements": {},
            "modules": [],
            "technology_stack": {},
            "requirement_module_index": {},
            "architecture_pattern": {},
            "validation_issues": {},
            "circular_dependencies": []
        }
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []
        
    def load_modules_from_disk(self):
        """从磁盘加载模块数据"""
        modules_dir = Path("data/output/modules")
        if not modules_dir.exists():
            print(f"❌ 模块目录不存在: {modules_dir}")
            return
        
        modules = []
        print(f"🔍 从磁盘加载模块数据，目录: {modules_dir}")
        
        module_count = 0
        error_count = 0
        
        module_dirs = list(modules_dir.iterdir())
        print(f"🔍 发现 {len(module_dirs)} 个模块目录")
        
        for module_dir in module_dirs:
            if not module_dir.is_dir():
                continue
            
            summary_file = module_dir / "full_summary.json"
            if not summary_file.exists():
                print(f"⚠️ 模块 {module_dir.name} 缺少full_summary.json文件")
                error_count += 1
                continue
            
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    module_data = json.load(f)
                
                module_id = str(uuid.uuid4())
                module_data["id"] = module_id
                module_data["name"] = module_dir.name  # 确保模块名称与目录名一致
                modules.append(module_data)
                module_count += 1
                print(f"✅ 成功加载模块: {module_dir.name}")
            except Exception as e:
                print(f"❌ 加载模块 {module_dir.name} 失败: {str(e)}")
                error_count += 1
        
        print(f"✅ 总共加载了 {module_count} 个模块，{error_count} 个错误")
        
        self.global_state["modules"] = modules
        print(f"🔄 全局状态现在包含 {len(self.global_state['modules'])} 个模块")
        
        if modules and len(modules) > 0:
            first_module = modules[0]
            print(f"🔍 第一个模块示例: {first_module.get('name', '未知')} (ID: {first_module.get('id', '未知')})")
            print(f"🔍 模块属性: {', '.join(first_module.keys())}")
    
    async def update_global_state_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON数据更新全局状态，并使用现有架构管理器执行验证"""
        print(f"🔄 开始从JSON更新全局状态...")
        
        if "requirements" in data and isinstance(data["requirements"], dict):
            self.global_state["requirements"] = data["requirements"]
            print(f"✅ 更新了 {len(data['requirements'])} 个需求")
        
        if "modules" in data:
            modules_list = []
            
            if isinstance(data["modules"], dict):
                for module_id, module_data in data["modules"].items():
                    if "id" not in module_data:
                        module_data["id"] = module_id
                    if "module_name" not in module_data:
                        module_data["module_name"] = module_data.get("name", module_id)
                    modules_list.append(module_data)
            elif isinstance(data["modules"], list):
                modules_list = data["modules"]
                for i, module_data in enumerate(modules_list):
                    if "id" not in module_data:
                        module_data["id"] = f"module_{i+1}"
                    if "module_name" not in module_data:
                        module_data["module_name"] = module_data.get("name", module_data["id"])
            
            self.global_state["modules"] = modules_list
            print(f"✅ 更新了 {len(modules_list)} 个模块")
            
            modules_dir = Path("data/output/modules")
            modules_dir.mkdir(parents=True, exist_ok=True)
            
            for module_data in modules_list:
                module_name = module_data.get("module_name", module_data.get("name", "unknown"))
                module_dir = modules_dir / str(module_name)
                module_dir.mkdir(parents=True, exist_ok=True)
                
                summary_path = module_dir / "full_summary.json"
                try:
                    with open(summary_path, "w", encoding="utf-8") as f:
                        json.dump(module_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ 为模块 '{module_name}' 创建了摘要文件: {summary_path}")
                except Exception as e:
                    print(f"❌ 为模块 '{module_name}' 创建摘要文件失败: {e}")
        
        if "technology_stack" in data and isinstance(data["technology_stack"], dict):
            self.global_state["technology_stack"] = data["technology_stack"]
            print(f"✅ 更新了技术栈")
        
        if "requirement_module_index" in data and isinstance(data["requirement_module_index"], dict):
            requirement_module_map = {}
            for req_id, modules in data["requirement_module_index"].items():
                req_name = data.get("requirements", {}).get(req_id, {}).get("name", "未知需求")
                requirement_module_map[req_id] = {
                    "name": req_name,
                    "modules": modules
                }
            
            self.global_state["requirement_module_index"] = requirement_module_map
            print(f"✅ 已更新需求-模块映射关系")
        
        if "architecture_pattern" in data and isinstance(data["architecture_pattern"], dict):
            self.global_state["architecture_pattern"] = data["architecture_pattern"]
            print(f"✅ 更新了架构模式")
        
        if "modules" in data:
            modules_data = data["modules"]
            
            responsibility_index = {}
            layer_index = {}
            domain_index = {}
            
            if isinstance(modules_data, dict):
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
            elif isinstance(modules_data, list):
                for module_info in modules_data:
                    module_id = module_info.get("id", "")
                    if not module_id:
                        continue
                        
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
            
            self.global_state["responsibility_index"] = responsibility_index
            self.global_state["layer_index"] = layer_index
            self.global_state["domain_index"] = domain_index
            print(f"✅ 已更新多维度模块索引")
        
        try:
            modules_data = data.get("modules", {})
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            dependency_graph = {}
            
            if isinstance(modules_data, dict):
                for module_id, module_data in modules_data.items():
                    module_name = module_data.get("module_name", "")
                    depends_on = module_data.get("dependencies", [])
                    dependency_graph[module_name] = depends_on
            elif isinstance(modules_data, list):
                for module_data in modules_data:
                    module_name = module_data.get("module_name", module_data.get("name", ""))
                    depends_on = module_data.get("dependencies", [])
                    if module_name:
                        dependency_graph[module_name] = depends_on
            
            with open(output_dir / "dependency_graph.py", "w", encoding="utf-8") as f:
                f.write("# Auto-generated module dependency graph\n")
                f.write("dependency_graph = ")
                json.dump(dependency_graph, f, ensure_ascii=False, indent=2)
            
            summary_index = {}
            
            if isinstance(modules_data, dict):
                for module_id, module_data in modules_data.items():
                    module_name = module_data.get("module_name", "")
                    if module_name:
                        summary_index[module_name] = {
                            "target_path": module_data.get("target_path", ""),
                            "depends_on": module_data.get("dependencies", []),
                            "responsibilities": module_data.get("responsibilities", [])
                        }
            elif isinstance(modules_data, list):
                for module_data in modules_data:
                    module_name = module_data.get("module_name", module_data.get("name", ""))
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
        
        await self._validate_architecture_with_manager(data)
        
        return self.global_state
    
    async def _validate_architecture_with_manager(self, data: Dict[str, Any]) -> None:
        """使用架构管理器验证架构"""
        print(f"🔍 [LOOP-TRACE] _validate_architecture_with_manager 开始执行 - 数据大小: {len(str(data))} 字符")
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] 调用ID: {call_id}")
        
        try:
            if self.clarifier and hasattr(self.clarifier, 'architecture_manager'):
                arch_manager = self.clarifier.architecture_manager
                print(f"🔍 [LOOP-TRACE] {call_id} - 获取到架构管理器")
                
                module_count = 0
                req_count = 0
                
                if "requirements" in data:
                    req_data_count = len(data["requirements"])
                    print(f"🔍 [LOOP-TRACE] {call_id} - 发现 {req_data_count} 个需求数据")
                    for req_id, req_data in data["requirements"].items():
                        if hasattr(arch_manager, 'add_requirement'):
                            print(f"🔍 [LOOP-TRACE] {call_id} - 添加需求 {req_id}")
                            arch_manager.add_requirement(req_data)
                            req_count += 1
                
                max_modules_to_process = 10  # 限制处理模块数量，防止循环过多
                modules_to_process = self.global_state["modules"][:max_modules_to_process]
                print(f"🔍 [LOOP-TRACE] {call_id} - 将处理 {len(modules_to_process)}/{len(self.global_state['modules'])} 个模块")
                
                for i, module in enumerate(modules_to_process):
                    module_id = module.get("id", "")
                    if not module_id:
                        print(f"🔍 [LOOP-TRACE] {call_id} - 跳过无ID模块 #{i}")
                        continue
                    
                    print(f"🔍 [LOOP-TRACE] {call_id} - 处理模块 {module_id} ({i+1}/{len(modules_to_process)})")
                        
                    requirements = []
                    if "requirement_module_index" in data:
                        for req_id, modules in data["requirement_module_index"].items():
                            if module_id in modules:
                                requirements.append(req_id)
                    
                    module_name = module.get("module_name", module.get("name", module_id))
                    print(f"🔍 [LOOP-TRACE] {call_id} - 模块名称: {module_name}, 关联需求: {len(requirements)}")
                    
                    if hasattr(arch_manager.index, 'dependency_graph'):
                        already_exists = module_name in arch_manager.index.dependency_graph
                        print(f"🔍 [LOOP-TRACE] {call_id} - 模块 {module_name} 已存在于依赖图: {already_exists}")
                        
                        if not already_exists:
                            try:
                                if hasattr(arch_manager, 'process_new_module'):
                                    print(f"🔍 [LOOP-TRACE] {call_id} - 开始处理新模块 {module_name}")
                                    process_result = await arch_manager.process_new_module(module, requirements)
                                    print(f"🔍 [LOOP-TRACE] {call_id} - 模块 {module_name} 处理结果: {process_result.get('status', '未知')}")
                                    module_count += 1
                            except Exception as e:
                                print(f"❌ [LOOP-TRACE] {call_id} - 处理模块 {module_name} 时出错: {str(e)}")
                                pass
                
                print(f"✅ [LOOP-TRACE] {call_id} - 架构验证完成: 处理了 {req_count} 个需求和 {module_count} 个模块")
                
                try:
                    if hasattr(arch_manager, 'get_validation_issues'):
                        print(f"🔍 [LOOP-TRACE] {call_id} - 获取验证问题")
                        validation_issues = arch_manager.get_validation_issues()
                        if validation_issues:
                            print(f"🔍 [LOOP-TRACE] {call_id} - 发现 {len(validation_issues)} 个验证问题")
                            self.global_state["validation_issues"] = validation_issues
                except Exception as e:
                    print(f"❌ [LOOP-TRACE] {call_id} - 获取验证问题时出错: {str(e)}")
                    pass
                
        except Exception as e:
            print(f"❌ [LOOP-TRACE] {call_id} - 架构验证出错: {str(e)}")
            traceback.print_exc()
            
        print(f"🔍 [LOOP-TRACE] {call_id} - _validate_architecture_with_manager 执行完成")

state_service = StateService()

def get_state_service() -> StateService:
    """获取状态服务实例，用于依赖注入"""
    return state_service
