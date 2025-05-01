from typing import Dict, List, Set
from pathlib import Path
import json
import uuid
import traceback
from datetime import datetime

class ArchitectureIndex:
    def __init__(self):
        self.requirement_module_index = {}
        self.responsibility_index = {}
        self.dependency_graph = {}
        self.keyword_mapping = {}
        
        # 更灵活的架构层级定义
        self.architecture_patterns = {
            "frontend": {
                "layers": {
                    "pages": {"path": "src/pages", "description": "页面组件"},
                    "components": {"path": "src/components", "description": "可复用组件"},
                    "layouts": {"path": "src/layouts", "description": "布局组件"},
                    "hooks": {"path": "src/hooks", "description": "自定义钩子"},
                    "stores": {"path": "src/stores", "description": "状态管理"}
                },
                "dependencies": {
                    "pages": ["components", "layouts", "hooks", "stores"],
                    "components": ["hooks", "stores"],
                    "layouts": ["components", "hooks"],
                    "hooks": ["stores"],
                    "stores": []
                }
            },
            "backend": {
                "layers": {
                    "controllers": {"path": "src/controllers", "description": "控制器层"},
                    "services": {"path": "src/services", "description": "服务层"},
                    "repositories": {"path": "src/repositories", "description": "数据访问层"},
                    "models": {"path": "src/models", "description": "数据模型层"}
                },
                "dependencies": {
                    "controllers": ["services"],
                    "services": ["repositories"],
                    "repositories": ["models"],
                    "models": []
                }
            },
            "fullstack": {
                "layers": {
                    "features": {"path": "src/features", "description": "完整功能模块"},
                    "shared": {"path": "src/shared", "description": "共享资源"},
                    "core": {"path": "src/core", "description": "核心功能"}
                },
                "dependencies": {
                    "features": ["shared", "core"],
                    "shared": ["core"],
                    "core": []
                }
            }
        }
        
        # 动态创建层级索引
        self.layer_index = {}
        for pattern, config in self.architecture_patterns.items():
            for layer in config["layers"]:
                self.layer_index[f"{pattern}.{layer}"] = {}

    def add_module(self, module: Dict, requirements: List[str]):
        """添加新模块到索引"""
        module_name = module['name']
        
        # 1. 更新需求索引
        for req in requirements:
            if req not in self.requirement_module_index:
                self.requirement_module_index[req] = set()
            self.requirement_module_index[req].add(module_name)
        
        # 2. 更新职责索引
        for resp in module.get('responsibilities', []):
            if resp not in self.responsibility_index:
                self.responsibility_index[resp] = {
                    "modules": set(),
                    "objects": set(),
                    "patterns": set()  # 记录模块所属的架构模式
                }
            self.responsibility_index[resp]["modules"].add(module_name)
            self.responsibility_index[resp]["patterns"].add(module.get('pattern', ''))
        
        # 3. 更新依赖图
        self.dependency_graph[module_name] = {
            "depends_on": set(module.get('dependencies', [])),
            "depended_by": set(),
            "pattern": module.get('pattern', ''),  # 记录架构模式
            "layer": module.get('layer', '')       # 记录层级
        }
        
        # 4. 更新关键字映射
        keywords = self._extract_keywords(module.get('description', ''))
        for keyword in keywords:
            if keyword not in self.keyword_mapping:
                self.keyword_mapping[keyword] = set()
            self.keyword_mapping[keyword].add(module_name)
        
        # 5. 更新层级索引
        pattern = module.get('pattern', '')
        layer = module.get('layer', '')
        layer_key = f"{pattern}.{layer}"
        if layer_key in self.layer_index:
            self.layer_index[layer_key][module_name] = module

    def _extract_keywords(self, text: str) -> Set[str]:
        """从文本中提取关键字"""
        # TODO: 实现关键字提取逻辑
        # 可以使用NLP库或简单的词频分析
        return set(text.lower().split())

    def get_allowed_dependencies(self, pattern: str, layer: str) -> List[str]:
        """获取特定架构模式和层级允许的依赖"""
        if pattern in self.architecture_patterns:
            return self.architecture_patterns[pattern]["dependencies"].get(layer, [])
        return []

    def get_layer_path(self, pattern: str, layer: str) -> str:
        """获取特定架构模式和层级的文件路径"""
        if pattern in self.architecture_patterns:
            return self.architecture_patterns[pattern]["layers"].get(layer, {}).get("path", "")
        return ""
        
    def get_current_state(self) -> Dict:
        """获取当前架构索引的状态"""
        state = {
            "requirement_module_index": {
                k: list(v) for k, v in self.requirement_module_index.items()
            },
            "responsibility_index": {
                k: {
                    "modules": list(v["modules"]),
                    "objects": list(v["objects"]),
                    "patterns": list(v["patterns"])
                } for k, v in self.responsibility_index.items()
            },
            "dependency_graph": {
                k: {
                    "depends_on": list(v["depends_on"]),
                    "depended_by": list(v["depended_by"]),
                    "pattern": v.get("pattern", ""),
                    "layer": v.get("layer", "")
                } for k, v in self.dependency_graph.items()
            },
            "layer_index": {
                layer: {
                    name: module for name, module in modules.items()
                } for layer, modules in self.layer_index.items()
            }
        }
        return state

class ArchitectureValidator:
    def __init__(self, index: ArchitectureIndex):
        self.index = index
        self.validation_issues = {}

    async def validate_new_module(self, module: Dict, requirements: List[str]) -> Dict:
        """验证新模块的合理性"""
        issues = {
            "responsibility_overlaps": [],
            "circular_dependencies": [],
            "layer_violations": [],
            "interface_inconsistencies": []
        }
        
        # 1. 检查职责重叠
        overlaps = self._check_responsibility_overlaps(module)
        if overlaps:
            issues["responsibility_overlaps"].extend(overlaps)
        
        # 2. 检查循环依赖
        cycles = self._check_circular_dependencies(module)
        if cycles:
            issues["circular_dependencies"].extend(cycles)
        
        # 3. 检查层级违规
        layer_issues = self._check_layer_violations(module)
        if layer_issues:
            issues["layer_violations"].extend(layer_issues)
        
        # 保存验证结果
        self.validation_issues[module.get('name', 'unknown')] = issues
        
        return issues
    
    def get_validation_issues(self) -> Dict:
        """获取所有验证问题"""
        result = {}
        for module_name, issues in self.validation_issues.items():
            if any(issues.values()):  # 只返回有问题的模块
                result[module_name] = issues
        return result

    def _check_responsibility_overlaps(self, module: Dict) -> List[str]:
        """检查职责重叠"""
        overlaps = []
        module_responsibilities = set(module.get('responsibilities', []))
        
        for resp in module_responsibilities:
            if resp in self.index.responsibility_index:
                existing_modules = self.index.responsibility_index[resp]["modules"]
                if existing_modules:
                    overlaps.append(f"职责'{resp}'与模块{existing_modules}重叠")
        
        return overlaps

    def _check_circular_dependencies(self, module: Dict) -> List[str]:
        """检查循环依赖"""
        cycles = []
        module_name = module['name']
        dependencies = set(module.get('dependencies', []))
        
        # 模拟添加新模块后的依赖图
        temp_graph = self.index.dependency_graph.copy()
        temp_graph[module_name] = {"depends_on": dependencies, "depended_by": set()}
        
        # 检查是否形成环
        visited = set()
        path = []
        
        def dfs(current: str) -> bool:
            if current in path:
                cycle_start = path.index(current)
                cycles.append(" -> ".join(path[cycle_start:] + [current]))
                return True
            
            if current in visited:
                return False
                
            visited.add(current)
            path.append(current)
            
            for dep in temp_graph[current]["depends_on"]:
                if dep in temp_graph and dfs(dep):
                    return True
                    
            path.pop()
            return False
            
        dfs(module_name)
        return cycles
        
    def _check_layer_violations(self, module: Dict) -> List[str]:
        """检查层级违规"""
        violations = []
        pattern = module.get('pattern', '')
        layer = module.get('layer', '')
        
        if pattern in self.index.architecture_patterns:
            allowed_deps = self.index.get_allowed_dependencies(pattern, layer)
            for dep in module.get('dependencies', []):
                dep_info = self.index.dependency_graph.get(dep, {})
                dep_layer = dep_info.get('layer', '')
                
                if dep_layer and dep_layer not in allowed_deps:
                    violations.append(f"依赖 '{dep}' 违反了 '{pattern}' 架构中 '{layer}' 层级的依赖规则")
        
        return violations

class ArchitectureManager:
    def __init__(self):
        self.index = ArchitectureIndex()
        self.validator = ArchitectureValidator(self.index)
        self.output_path = Path("data/output/architecture")
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.modules = []  # 存储所有模块
        self.requirements = []  # 存储所有需求
        self.system_overview = {}  # 系统概述
        self.functional_requirements = {}  # 功能需求
        self.technology_stack = {}  # 技术栈
        self.architecture_pattern = {}  # 架构模式

    def get_validation_issues(self) -> Dict:
        """获取所有架构验证问题"""
        if hasattr(self.validator, 'get_validation_issues'):
            return self.validator.get_validation_issues()
        return {}
    
    def add_module(self, module_data: Dict) -> None:
        """添加或更新模块
        
        Args:
            module_data: 模块数据
        """
        # 检查是否已存在同名模块
        module_name = module_data.get("name")
        existing_index = None
        
        for i, module in enumerate(self.modules):
            if module.get("name") == module_name:
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新现有模块
            self.modules[existing_index] = module_data
        else:
            # 添加新模块
            self.modules.append(module_data)
    
    def add_requirement(self, req_data: Dict) -> None:
        """添加或更新需求
        
        Args:
            req_data: 需求数据
        """
        # 检查是否已存在同ID需求
        req_id = req_data.get("id")
        if not req_id:
            req_id = f"req_{len(self.requirements) + 1}"
            req_data["id"] = req_id
        
        existing_index = None
        for i, req in enumerate(self.requirements):
            if req.get("id") == req_id:
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新现有需求
            self.requirements[existing_index] = req_data
        else:
            # 添加新需求
            self.requirements.append(req_data)

    async def process_new_module(self, module_spec: Dict, requirements: List[str]) -> Dict:
        """处理新模块"""
        module_name = module_spec.get('name', 'unknown')
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER process_new_module: '{module_name}'")
        
        # 1. 验证新模块
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始验证模块 '{module_name}'")
        validation_result = await self.validator.validate_new_module(
            module_spec, 
            requirements
        )
        print(f"🔄 [LOOP-TRACE] {call_id} - 验证完成: 发现 {sum(len(issues) for issues in validation_result.values())} 个问题")
        
        # 2. 如果有问题，返回验证结果
        if any(validation_result.values()):
            print(f"🔄 [LOOP-TRACE] {call_id} - 模块验证失败，返回问题列表")
            return {
                "status": "validation_failed",
                "issues": validation_result
            }
        
        # 3. 如果验证通过，添加到索引
        print(f"🔄 [LOOP-TRACE] {call_id} - 验证通过，添加模块到索引")
        self.index.add_module(module_spec, requirements)
        
        # 3.1 添加到模块列表
        print(f"🔄 [LOOP-TRACE] {call_id} - 添加模块到模块列表")
        self.add_module(module_spec)

        # 3.2 自动生成 full_summary.json
        module_name = module_spec.get("name")
        if module_name:
            print(f"🔄 [LOOP-TRACE] {call_id} - 为模块 '{module_name}' 创建目录和摘要文件")
            try:
                module_dir = Path("data/output/modules") / str(module_name)
                module_dir.mkdir(parents=True, exist_ok=True)
                
                summary_path = module_dir / "full_summary.json"
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(module_spec, f, ensure_ascii=False, indent=2)
                print(f"🔄 [LOOP-TRACE] {call_id} - 成功创建摘要文件: {summary_path}")
                
                safe_module_name = ''.join(c for c in module_name if c.isalnum() or c in ['-', '_', ' '])
                if safe_module_name and safe_module_name != module_name:
                    safe_module_dir = Path("data/output/modules") / safe_module_name
                    safe_module_dir.mkdir(parents=True, exist_ok=True)
                    safe_summary_path = safe_module_dir / "full_summary.json"
                    with open(safe_summary_path, "w", encoding="utf-8") as f:
                        module_data_with_safe_name = dict(module_spec)
                        module_data_with_safe_name["safe_module_name"] = safe_module_name
                        json.dump(module_data_with_safe_name, f, ensure_ascii=False, indent=2)
                    print(f"🔄 [LOOP-TRACE] {call_id} - 同时创建了安全名称摘要文件: {safe_summary_path}")
            except Exception as e:
                print(f"❌ [LOOP-TRACE] {call_id} - 创建摘要文件失败: {str(e)}")
                import traceback
                print(traceback.format_exc())
        else:
            print(f"⚠️ [LOOP-TRACE] {call_id} - 模块缺少名称，无法创建目录")
        
        # 4. 保存更新后的架构信息
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始保存架构状态")
        await self._save_architecture_state()
        print(f"🔄 [LOOP-TRACE] {call_id} - 架构状态保存完成")
        
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT process_new_module: '{module_name}'")
        return {
            "status": "success",
            "module": module_spec
        }

    async def _save_architecture_state(self):
        """保存当前架构状态"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {
                k: list(v) for k, v in self.index.requirement_module_index.items()
            },
            "responsibility_index": {
                k: {
                    "modules": list(v["modules"]),
                    "objects": list(v["objects"]),
                    "patterns": list(v["patterns"])
                } for k, v in self.index.responsibility_index.items()
            },
            "dependency_graph": {
                k: {
                    "depends_on": list(v["depends_on"]),
                    "depended_by": list(v["depended_by"]),
                    "pattern": v["pattern"],
                    "layer": v["layer"]
                } for k, v in self.index.dependency_graph.items()
            },
            "layer_index": {
                layer: {
                    name: module for name, module in modules.items()
                } for layer, modules in self.index.layer_index.items()
            }
        }
        
        state_file = self.output_path / "architecture_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)                  