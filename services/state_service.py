"""
状态服务模块，管理全局状态
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import traceback
from fastapi import Depends
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
            "modules": {},
            "technology_stack": {},
            "requirement_module_index": {},
            "architecture_pattern": {},
            "validation_issues": {}  # 保存验证问题
        }
        self.uploaded_files: List[str] = []
        self.current_mode: Optional[str] = None
        self.input_dir = "data/input"
    
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
    
    def update_global_state(self, new_state: Dict[str, Any]) -> None:
        """更新全局状态"""
        for key, value in new_state.items():
            if key in self.global_state:
                if isinstance(value, dict) and isinstance(self.global_state[key], dict):
                    self.global_state[key].update(value)
                else:
                    self.global_state[key] = value
    
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
    
    def update_global_state_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON数据更新全局状态，并使用现有架构管理器执行验证"""
        print(f"🔄 开始从JSON更新全局状态...")
        
        if "requirements" in data and isinstance(data["requirements"], dict):
            self.global_state["requirements"] = data["requirements"]
            print(f"✅ 更新了 {len(data['requirements'])} 个需求")
        
        if "modules" in data and isinstance(data["modules"], dict):
            self.global_state["modules"] = data["modules"]
            print(f"✅ 更新了 {len(data['modules'])} 个模块")
            
            modules_dir = Path("data/output/modules")
            modules_dir.mkdir(parents=True, exist_ok=True)
            
            for module_id, module_data in data["modules"].items():
                if "module_name" not in module_data:
                    module_data["module_name"] = module_data.get("name", module_id)
                    
                module_name = module_data["module_name"]
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
            
            self.global_state["responsibility_index"] = responsibility_index
            self.global_state["layer_index"] = layer_index
            self.global_state["domain_index"] = domain_index
            print(f"✅ 已更新多维度模块索引")
        
        try:
            modules_data = data.get("modules", {})
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
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
        
        self._validate_architecture_with_manager(data)
        
        return self.global_state
    
    def _validate_architecture_with_manager(self, data: Dict[str, Any]) -> None:
        """使用架构管理器验证架构"""
        try:
            if self.clarifier and hasattr(self.clarifier, 'architecture_manager'):
                arch_manager = self.clarifier.architecture_manager
                print(f"🔍 使用ArchitectureManager验证架构...")
                
                if "requirements" in data:
                    for req_id, req_data in data["requirements"].items():
                        if hasattr(arch_manager, 'add_requirement'):
                            arch_manager.add_requirement(req_data)
                            print(f"✅ 添加需求 '{req_id}' 到架构管理器")
                
                for module_id, module in self.global_state["modules"].items():
                    requirements = []
                    if "requirement_module_index" in data:
                        for req_id, modules in data["requirement_module_index"].items():
                            if module_id in modules:
                                requirements.append(req_id)
                                print(f"📊 模块 '{module_id}' 关联到需求 '{req_id}'")
                    
                    module_name = module.get("module_name", module_id)
                    if hasattr(arch_manager.index, 'dependency_graph') and module_name not in arch_manager.index.dependency_graph:
                        print(f"🔄 添加模块 '{module_name}' 到架构索引...")
                        try:
                            if hasattr(arch_manager, 'process_new_module'):
                                process_result = arch_manager.process_new_module(module, requirements)
                                print(f"✅ 模块处理结果: {process_result.get('status', '未知')}")
                        except Exception as e:
                            print(f"❌ 处理模块 '{module_name}' 时出错: {e}")
                
                try:
                    if hasattr(arch_manager, 'get_validation_issues'):
                        validation_issues = arch_manager.get_validation_issues()
                        if validation_issues:
                            self.global_state["validation_issues"] = validation_issues
                            print(f"⚠️ 检测到架构验证问题: {validation_issues}")
                except Exception as e:
                    print(f"⚠️ 获取验证问题时出错: {e}")
                
        except Exception as e:
            print(f"⚠️ 架构验证出错: {str(e)}")
            traceback.print_exc()

state_service = StateService()

def get_state_service() -> StateService:
    """获取状态服务实例，用于依赖注入"""
    return state_service
