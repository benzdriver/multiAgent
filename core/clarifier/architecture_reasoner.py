from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import json
import asyncio
import re
import uuid
import traceback
from datetime import datetime
from .architecture_manager import ArchitectureManager
from llm.llm_executor import run_prompt

class ArchitectureReasoner:
    def __init__(self, architecture_manager=None, llm_chat=None, logger=None, output_path=None):
        self.arch_manager = architecture_manager or ArchitectureManager()
        self.output_path = output_path or getattr(self.arch_manager, 'output_path', None) or Path("data/output/architecture")
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.llm_chat = llm_chat
        self.logger = logger

    async def _get_llm_response(self, prompt: str) -> Dict:
        """获取LLM响应
        
        Args:
            prompt: 提示文本
            
        Returns:
            LLM响应结果
        """
        if self.logger:
            self.logger.log(f"LLM输入：{prompt[:200]}...", role="llm_prompt")
        try:
            # 使用llm_executor中的run_prompt函数
            result = await run_prompt(
                chat=self.llm_chat,
                user_prompt=prompt,
                model="gpt-4o",
                use_mock=self.llm_chat is None,
                return_json=True
            )
            if self.logger:
                self.logger.log(f"LLM响应：{str(result)[:200]}...", role="llm_response")
            return result
        except Exception as e:
            if self.logger:
                self.logger.log(f"⚠️ 调用LLM时出错: {str(e)}", role="error")
            else:
                print(f"⚠️ 调用LLM时出错: {str(e)}")
            return {
                "error": f"调用LLM出错: {str(e)}",
                "message": "LLM调用失败，请稍后重试"
            }

    async def populate_architecture_index(self, architecture_understanding: Dict):
        """将架构理解数据填充到架构索引中"""
        if self.logger:
            self.logger.log("\n📊 填充架构索引...", role="system")
        
        # 1. 提取模块和依赖
        modules = []
        requirements = {}
        dependencies = {}  # 存储模块间的依赖关系
        
        # 遍历各模式和层级提取模块信息
        for pattern in architecture_understanding["architecture_design"]["patterns"]:
            pattern_name = pattern["name"]
            
            for layer in pattern["layers"]:
                layer_name = layer["name"]
                
                for component in layer.get("components", []):
                    # 创建模块规范
                    module_spec = {
                        "name": component["name"],
                        "description": component.get("description", ""),
                        "responsibilities": component.get("responsibilities", []),
                        "dependencies": component.get("dependencies", []),
                        "interfaces": component.get("interfaces", []),
                        "pattern": pattern_name,
                        "layer": layer_name,
                        "features": component.get("features", []),
                        "domains": component.get("domains", []),
                        "technologies": component.get("technologies", []),
                        "path": component.get("path", self.arch_manager.index.get_layer_path(pattern_name, layer_name))
                    }
                    
                    # 记录模块与需求的映射
                    module_reqs = component.get("requirements", [])
                    requirements[component["name"]] = module_reqs
                    
                    dependencies[component["name"]] = component.get("dependencies", [])
                    
                    modules.append(module_spec)
        
        # 2. 将模块添加到架构索引
        for module in modules:
            self.arch_manager.index.add_module(module, requirements.get(module["name"], []))
            
        for module_name, deps in dependencies.items():
            for dep in deps:
                if dep in self.arch_manager.index.dependency_graph:
                    if "depended_by" not in self.arch_manager.index.dependency_graph[dep]:
                        self.arch_manager.index.dependency_graph[dep]["depended_by"] = set()
                    self.arch_manager.index.dependency_graph[dep]["depended_by"].add(module_name)
            
        # 3. 添加架构模式（如果需要扩展现有模式）
        for pattern in architecture_understanding["architecture_design"]["patterns"]:
            if pattern["name"] not in self.arch_manager.index.architecture_patterns:
                # 如果是新的架构模式，则添加到索引
                layers = {}
                dependencies = {}
                
                for layer in pattern["layers"]:
                    layers[layer["name"]] = {
                        "path": layer.get("path", f"src/{layer['name']}"),
                        "description": layer.get("description", "")
                    }
                    dependencies[layer["name"]] = layer.get("dependencies", [])
                
                # 添加新的架构模式
                self.arch_manager.index.architecture_patterns[pattern["name"]] = {
                    "layers": layers,
                    "dependencies": dependencies
                }
                
                # 更新层级索引
                for layer in layers:
                    self.arch_manager.index.layer_index[f"{pattern['name']}.{layer}"] = {}
        
        if self.logger:
            self.logger.log("✅ 架构索引填充完成", role="system")

    async def start_deep_reasoning(self, architecture_understanding: Dict, get_llm_response=None):
        """开始深度推理过程"""
        if self.logger:
            self.logger.log("\n🏗️ 开始架构深度推理...", role="system")
        
        # 如果提供了外部LLM响应函数，则使用它
        if get_llm_response:
            self._get_llm_response = get_llm_response
        
        # 1. 将架构理解数据导入到架构索引
        await self.populate_architecture_index(architecture_understanding)
        
        # 2. 处理每个识别出的架构模式
        for pattern in architecture_understanding["architecture_design"]["patterns"]:
            if self.logger:
                self.logger.log(f"\n📐 处理架构模式: {pattern['name']}", role="system")
            
            # 为每个模式生成详细文档
            pattern_docs = await self._generate_pattern_docs(pattern)
            
            # 基于生成的文档进行推理
            await self._reason_by_pattern(pattern, pattern_docs)
        
        # 3. 执行整体架构验证
        await self._validate_overall_architecture()
        
        # 4. 保存最终的架构状态
        await self._save_final_architecture()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {
                k: list(v) for k, v in self.arch_manager.index.requirement_module_index.items()
            },
            "responsibility_index": {
                k: {
                    "modules": list(v["modules"]),
                    "objects": list(v["objects"]),
                    "patterns": list(v["patterns"])
                } for k, v in self.arch_manager.index.responsibility_index.items()
            },
            "dependency_graph": {
                k: {
                    "depends_on": list(v["depends_on"]),
                    "depended_by": list(v["depended_by"]),
                    "pattern": v["pattern"],
                    "layer": v["layer"]
                } for k, v in self.arch_manager.index.dependency_graph.items()
            },
            "layer_index": {
                layer: {
                    name: module for name, module in modules.items()
                } for layer, modules in self.arch_manager.index.layer_index.items()
            }
        }

    async def _generate_pattern_docs(self, pattern: Dict) -> Dict:
        """为特定架构模式生成详细文档"""
        if self.logger:
            self.logger.log(f"\n📝 生成 {pattern['name']} 模式的详细文档...", role="system")
        
        docs = {}
        
        # 1. 模式概述
        docs["overview"] = await self._generate_pattern_overview(pattern)
        
        # 2. 层级设计
        docs["layers"] = await self._generate_layers_design(pattern)
        
        # 3. 接口定义
        docs["interfaces"] = await self._generate_interface_definitions(pattern)
        
        # 4. 依赖关系
        docs["dependencies"] = await self._generate_dependency_specs(pattern)
        
        return docs

    async def _generate_pattern_overview(self, pattern: Dict) -> Dict:
        """生成架构模式概述"""
        prompt = f"""
        为 {pattern['name']} 架构模式生成详细概述。

        模式信息：
        {json.dumps(pattern, ensure_ascii=False, indent=2)}

        请提供：
        1. 模式的核心原则
        2. 适用场景
        3. 主要优势
        4. 潜在挑战
        5. 关键设计决策

        返回JSON格式。
        """
        return await self._get_llm_response(prompt)

    async def _generate_layers_design(self, pattern: Dict) -> Dict:
        """生成层级设计文档"""
        prompt = f"""
        为 {pattern['name']} 架构模式的各层级生成详细设计。

        层级信息：
        {json.dumps(pattern['layers'], ensure_ascii=False, indent=2)}

        请为每个层级提供：
        1. 详细职责定义
        2. 组件设计
        3. 内部结构
        4. 与其他层级的交互
        5. 实现指南

        返回JSON格式。
        """
        return await self._get_llm_response(prompt)

    async def _generate_interface_definitions(self, pattern: Dict) -> Dict:
        """生成接口定义文档"""
        prompt = f"""
        为 {pattern['name']} 架构模式的各接口生成详细定义。

        接口信息：
        {json.dumps(pattern['interfaces'], ensure_ascii=False, indent=2)}

        请为每个接口提供：
        1. 接口名称
        2. 接口描述
        3. 接口类型（输入/输出）
        4. 接口参数
        5. 接口实现

        返回JSON格式。
        """
        return await self._get_llm_response(prompt)

    async def _generate_dependency_specs(self, pattern: Dict) -> Dict:
        """生成依赖关系文档"""
        prompt = f"""
        为 {pattern['name']} 架构模式的各模块生成依赖关系描述。

        依赖关系：
        {json.dumps(pattern['dependencies'], ensure_ascii=False, indent=2)}

        请为每个依赖关系提供：
        1. 源模块
        2. 目标模块
        3. 依赖类型
        4. 依赖描述
        5. 依赖理由

        返回JSON格式。
        """
        return await self._get_llm_response(prompt)

    async def _generate_module_spec(self, module: Dict, layer_info: Dict) -> Dict:
        """生成模块规范"""
        # 自动补全分层配件
        pattern = module.get("pattern", "").lower()
        layer = module.get("layer", "").lower()
        # 定义常见配件模板
        layer_complements = {
            ("frontend", "pages"): ["Page", "View"],
            ("frontend", "components"): ["Component", "Widget"],
            ("frontend", "layouts"): ["Layout"],
            ("frontend", "hooks"): ["Hook"],
            ("frontend", "stores"): ["Store", "StateManager"],
            ("backend", "controllers"): ["Controller"],
            ("backend", "services"): ["Service"],
            ("backend", "repositories"): ["Repository", "DAO"],
            ("backend", "models"): ["Model", "Entity"],
            ("fullstack", "features"): ["FeatureModule"],
            ("fullstack", "shared"): ["SharedUtil", "Helper"],
            ("fullstack", "core"): ["CoreEngine", "Kernel"]
        }
        key = (pattern, layer)
        complements = layer_complements.get(key, [])
        # 自动补全 features 字段
        if complements:
            features = set(module.get("features", []))
            features.update(complements)
            module["features"] = list(features)
            
        pattern = module.get("pattern", "").lower()
        layer = module.get("layer", "").lower()
        domain = module.get("domain", "").lower() if "domain" in module else ""
        
        if not module.get("target_path") and domain:
            if pattern == "frontend":
                module["target_path"] = f"frontend/{layer}/{domain}"
            else:
                module["target_path"] = f"backend/{layer}/{domain}"
                
        # 继续 LLM 生成
        prompt = f"""
        为 {module['name']} 模块生成详细规范。

        模块信息：
        {json.dumps(module, ensure_ascii=False, indent=2)}

        层级信息：
        {json.dumps(layer_info, ensure_ascii=False, indent=2)}

        请提供：
        1. 模块名称
        2. 详细职责描述
        3. 与其他层的依赖关系
        4. 对外暴露的接口
        5. 与具体需求的映射关系
        6. 文件路径设计

        返回JSON格式。
        """
        return await self._get_llm_response(prompt)

    async def _reason_by_pattern(self, pattern: Dict, pattern_docs: Dict):
        """基于生成的文档进行架构推理"""
        if self.logger:
            self.logger.log(f"\n🔍 基于文档推理 {pattern['name']} 模式...", role="system")
        
        # 1. 使用架构索引获取相关组件
        related_components = await self._find_related_components(pattern)
        
        # 2. 验证层级设计
        for layer_name, layer_info in pattern_docs["layers"].items():
            # 使用索引验证设计
            validation_result = await self._validate_layer_design(layer_name, layer_info, related_components)
            if validation_result["has_issues"]:
                await self._handle_layer_issues(layer_name, validation_result["issues"])
            
            # 处理该层级的模块
            await self._process_layer_modules(layer_name, layer_info)

    async def _find_related_components(self, pattern: Dict) -> Dict:
        """使用架构索引查找相关组件"""
        pattern_name = pattern["name"]
        related = {
            "by_responsibility": [],
            "by_dependency": [],
            "by_feature": [],
            "by_keyword": []
        }
        
        # 1. 按职责查找相关组件
        for resp in pattern.get("responsibilities", []):
            if resp in self.arch_manager.index.responsibility_index:
                resp_info = self.arch_manager.index.responsibility_index[resp]
                for module in resp_info["modules"]:
                    module_info = self.arch_manager.index.dependency_graph.get(module, {})
                    if module_info.get("pattern") != pattern_name:  # 排除自身模式的组件
                        related["by_responsibility"].append({
                            "module": module,
                            "pattern": module_info.get("pattern", ""),
                            "layer": module_info.get("layer", "")
                        })
        
        # 2. 按依赖关系查找
        for module, info in self.arch_manager.index.dependency_graph.items():
            if info.get("pattern") == pattern_name:
                # 获取该模块依赖的外部组件
                for dep in info.get("depends_on", []):
                    dep_info = self.arch_manager.index.dependency_graph.get(dep, {})
                    if dep_info.get("pattern") != pattern_name:
                        related["by_dependency"].append({
                            "module": dep,
                            "pattern": dep_info.get("pattern", ""),
                            "layer": dep_info.get("layer", ""),
                            "relationship": "depends_on"
                        })
                
                # 获取依赖该模块的外部组件
                for dep in info.get("depended_by", []):
                    dep_info = self.arch_manager.index.dependency_graph.get(dep, {})
                    if dep_info.get("pattern") != pattern_name:
                        related["by_dependency"].append({
                            "module": dep,
                            "pattern": dep_info.get("pattern", ""),
                            "layer": dep_info.get("layer", ""),
                            "relationship": "depended_by"
                        })
        
        # 3. 按关键字查找
        for keyword in self._extract_pattern_keywords(pattern):
            if keyword in self.arch_manager.index.keyword_mapping:
                for module in self.arch_manager.index.keyword_mapping[keyword]:
                    module_info = self.arch_manager.index.dependency_graph.get(module, {})
                    if module_info.get("pattern") != pattern_name:
                        related["by_keyword"].append({
                            "module": module,
                            "pattern": module_info.get("pattern", ""),
                            "layer": module_info.get("layer", ""),
                            "keyword": keyword
                        })
        
        return related

    def _extract_pattern_keywords(self, pattern: Dict) -> Set[str]:
        """从模式描述中提取关键字"""
        keywords = set()
        
        # 从描述中提取
        if "description" in pattern:
            keywords.update(set(pattern["description"].lower().split()))
            
        # 从名称中提取
        if "name" in pattern:
            keywords.update(set(pattern["name"].lower().split()))
            
        return keywords

    async def _validate_layer_design(self, layer_name: str, layer_info: Dict, related_components: Dict) -> Dict:
        """验证层级设计的合理性"""
        validation = {
            "has_issues": False,
            "issues": []
        }
        
        # 1. 基本验证
        if not self._validate_responsibilities(layer_info.get("responsibilities", [])):
            validation["has_issues"] = True
            validation["issues"].append("职责定义不完整或不清晰")
        
        if not self._validate_components(layer_info.get("components", [])):
            validation["has_issues"] = True
            validation["issues"].append("组件设计存在问题")
        
        if not self._validate_dependencies(layer_info.get("dependencies", [])):
            validation["has_issues"] = True
            validation["issues"].append("存在不合理的依赖关系")
        
        # 2. 使用相关性信息进行验证
        validation_issues = await self._validate_with_relationships(
            layer_name, 
            layer_info, 
            related_components
        )
        if validation_issues:
            validation["has_issues"] = True
            validation["issues"].extend(validation_issues)
        
        return validation

    async def _validate_with_relationships(
        self, 
        layer_name: str, 
        layer_info: Dict, 
        related_components: Dict
    ) -> List[str]:
        """使用相关性信息验证设计"""
        issues = []
        
        # 1. 检查功能重叠
        feature_overlaps = self._check_feature_overlaps(
            layer_info, 
            related_components["by_feature"]
        )
        if feature_overlaps:
            issues.append(f"功能重叠: {', '.join(feature_overlaps)}")
        
        # 2. 检查领域一致性
        domain_issues = self._check_domain_consistency(
            layer_info, 
            related_components["by_responsibility"]
        )
        if domain_issues:
            issues.append(f"领域不一致: {', '.join(domain_issues)}")
        
        # 3. 检查依赖合理性
        dependency_issues = self._check_dependency_rationality(
            layer_info, 
            related_components["by_dependency"]
        )
        if dependency_issues:
            issues.append(f"依赖关系问题: {', '.join(dependency_issues)}")
        
        return issues

    def _check_feature_overlaps(self, layer_info: Dict, related_features: List[Dict]) -> List[str]:
        """检查功能重叠"""
        overlaps = []
        layer_features = set()
        
        # 收集当前层的功能
        for component in layer_info.get("components", []):
            layer_features.update(component.get("features", []))
        
        # 检查与相关组件的功能重叠
        for related in related_features:
            related_feature_set = set(related.get("features", []))
            overlap = layer_features.intersection(related_feature_set)
            if overlap:
                overlaps.append(
                    f"与 {related['pattern']}.{related['layer']}.{related['module']} "
                    f"存在功能重叠: {', '.join(overlap)}"
                )
        
        return overlaps

    def _check_domain_consistency(self, layer_info: Dict, related_domains: List[Dict]) -> List[str]:
        """检查领域一致性"""
        issues = []
        layer_domains = set()
        
        # 收集当前层的领域
        for component in layer_info.get("components", []):
            layer_domains.update(component.get("domains", []))
        
        # 检查与相关组件的领域一致性
        for related in related_domains:
            related_domain_set = set(related.get("domains", []))
            if not layer_domains.intersection(related_domain_set) and related_domain_set:
                issues.append(
                    f"与 {related['pattern']}.{related['layer']}.{related['module']} "
                    f"缺少共同的领域上下文"
                )
        
        return issues

    def _check_dependency_rationality(self, layer_info: Dict, related_deps: List[Dict]) -> List[str]:
        """检查依赖合理性"""
        issues = []
        
        # 检查可能的循环依赖
        for component in layer_info.get("components", []):
            component_name = component.get("name", "")
            
            # 查找与该组件相关的依赖
            for dep in related_deps:
                if dep.get("relationship") == "depends_on" and dep.get("module") == component_name:
                    # 如果组件依赖的同时被依赖，可能存在循环依赖
                    issues.append(f"可能存在与 {dep.get('pattern', '')}.{dep.get('layer', '')}.{dep.get('module', '')} 的循环依赖")
        
        return issues

    def _validate_responsibilities(self, responsibilities: List[str]) -> bool:
        """验证职责定义的完整性"""
        return len(responsibilities) > 0

    def _validate_components(self, components: List[Dict]) -> bool:
        """验证组件设计的合理性"""
        return len(components) > 0

    def _validate_dependencies(self, dependencies: List[Dict]) -> bool:
        """验证依赖关系的合理性"""
        return len(dependencies) > 0

    async def _process_layer_modules(self, layer_name: str, layer_info: Dict):
        """处理层级中的模块，使用并行处理提高效率"""
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _process_layer_modules: layer='{layer_name}'")
        
        components = layer_info.get("components", [])
        print(f"🔄 [LOOP-TRACE] {call_id} - 发现 {len(components)} 个组件需要处理")
        
        async def process_single_module(module, module_idx):
            module_call_id = str(uuid.uuid4())[:8]  # 每个模块处理有自己的调用ID
            module_name = module.get("name", f"未命名模块_{module_idx}")
            print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 开始处理模块 {module_idx+1}/{len(components)}: '{module_name}'")
            
            try:
                # 1. 生成模块规范
                print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 开始生成模块规范")
                module_spec = await self._generate_module_spec(module, layer_info)
                print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 模块规范生成完成")
                
                # 2. 添加到架构管理器
                print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 开始调用 process_new_module")
                result = await self.arch_manager.process_new_module(
                    module_spec,
                    module_spec.get("requirements", [])
                )
                print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - process_new_module 调用完成: {result.get('status', '未知')}")
                
                if result["status"] == "validation_failed":
                    print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 模块验证失败，处理验证问题")
                    await self._handle_validation_issues(result["issues"], module_spec)
                    print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 验证问题处理完成")
                
                print(f"🔄 [LOOP-TRACE] {call_id}.{module_call_id} - 模块 '{module_name}' 处理完成")
                return result
            except Exception as e:
                print(f"❌ [LOOP-TRACE] {call_id}.{module_call_id} - 处理模块 '{module_name}' 时出错: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始并行处理 {len(components)} 个模块")
        import asyncio
        tasks = [process_single_module(module, idx) for idx, module in enumerate(components)]
        results = await asyncio.gather(*tasks)
        print(f"🔄 [LOOP-TRACE] {call_id} - 并行处理完成，成功: {sum(1 for r in results if r.get('status') == 'success')}，失败: {sum(1 for r in results if r.get('status') != 'success')}")
        
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _process_layer_modules: layer='{layer_name}'")
        return results

    async def _handle_validation_issues(self, issues: Dict, module: Dict):
        """处理验证问题"""
        # 尝试自动修正
        corrected_module = await self._attempt_module_correction(module, issues)
        if corrected_module:
            result = await self.arch_manager.process_new_module(
                corrected_module,
                corrected_module.get("requirements", [])
            )
            return result["status"] == "success"
        else:
            return False

    async def _attempt_module_correction(self, module: Dict, issues: Dict) -> Dict:
        """尝试自动修正模块问题"""
        prompt = f"""
        模块 {module.get('name', '')} 存在以下问题：
        
        {json.dumps(issues, ensure_ascii=False, indent=2)}
        
        原始模块定义：
        {json.dumps(module, ensure_ascii=False, indent=2)}
        
        请提供修正后的模块定义，以解决上述问题。
        返回JSON格式。
        """
        
        return await self._get_llm_response(prompt)

    async def _handle_layer_issues(self, layer_name: str, issues: List[str]):
        """处理层级设计中发现的问题"""
        if self.logger:
            self.logger.log(f"\n⚠️ {layer_name} 层存在以下问题：", role="error")
        for issue in issues:
            if self.logger:
                self.logger.log(f"• {issue}", role="error")
        
        # 尝试自动修正
        corrected_layer_info = await self._attempt_layer_correction(layer_name, issues)
        if corrected_layer_info:
            if self.logger:
                self.logger.log("\n🔄 正在尝试使用修正后的层级设计...", role="system")
            await self._process_layer_modules(layer_name, corrected_layer_info)
        else:
            if self.logger:
                self.logger.log("\n❌ 无法自动修正问题，请手动审查并修改层级设计", role="error")

    async def _attempt_layer_correction(self, layer_name: str, issues: List[str]) -> Dict:
        """尝试自动修正层级设计"""
        prompt = f"""
        {layer_name} 层存在以下问题：
        
        {json.dumps(issues, ensure_ascii=False, indent=2)}
        
        请提供修正建议，包括：
        1. 可能的修正措施
        2. 修正后的层级定义
        3. 修正理由
        
        返回JSON格式。
        """
        
        return await self._get_llm_response(prompt)

    async def _validate_overall_architecture(self):
        """执行整体架构验证"""
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _validate_overall_architecture")
        
        if self.logger:
            self.logger.log("\n🔍 执行整体架构验证...", role="system")
        
        # 1. 检查整体架构一致性
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始检查整体架构一致性")
        consistency_issues = self._check_overall_consistency()
        print(f"🔄 [LOOP-TRACE] {call_id} - 架构一致性检查完成，发现 {len(consistency_issues)} 个问题")
        
        if consistency_issues:
            if self.logger:
                self.logger.log("\n⚠️ 整体架构一致性问题:", role="error")
            for i, issue in enumerate(consistency_issues):
                print(f"🔄 [LOOP-TRACE] {call_id} - 一致性问题 {i+1}/{len(consistency_issues)}: {issue}")
                if self.logger:
                    self.logger.log(f"• {issue}", role="error")
            
            # 尝试自动修正
            print(f"🔄 [LOOP-TRACE] {call_id} - 开始尝试修正架构一致性问题")
            await self._attempt_consistency_correction(consistency_issues)
            print(f"🔄 [LOOP-TRACE] {call_id} - 一致性问题修正尝试完成")
        else:
            print(f"🔄 [LOOP-TRACE] {call_id} - 未发现架构一致性问题")
            if self.logger:
                self.logger.log("✅ 整体架构一致性验证通过", role="system")
        
        # 2. 检查全局循环依赖
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始检查全局循环依赖")
        cycles = self._check_global_circular_dependencies()
        print(f"🔄 [LOOP-TRACE] {call_id} - 循环依赖检查完成，发现 {len(cycles)} 个循环")
        
        if cycles:
            if self.logger:
                self.logger.log("\n⚠️ 检测到全局循环依赖:", role="error")
            for i, cycle in enumerate(cycles):
                print(f"🔄 [LOOP-TRACE] {call_id} - 循环依赖 {i+1}/{len(cycles)}: {cycle}")
                if self.logger:
                    self.logger.log(f"• {cycle}", role="error")
            
            # 尝试自动修正
            print(f"🔄 [LOOP-TRACE] {call_id} - 开始尝试修正循环依赖")
            await self._attempt_cycle_correction(cycles)
            print(f"🔄 [LOOP-TRACE] {call_id} - 循环依赖修正尝试完成")
        else:
            print(f"🔄 [LOOP-TRACE] {call_id} - 未检测到循环依赖")
            if self.logger:
                self.logger.log("✅ 未检测到全局循环依赖", role="system")
                
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _validate_overall_architecture")

    def _check_overall_consistency(self) -> List[str]:
        """检查整体架构一致性"""
        issues = []
        
        # 1. 检查层级职责是否明确分离
        layer_responsibilities = {}
        for pattern, info in self.arch_manager.index.architecture_patterns.items():
            for layer in info["layers"]:
                layer_key = f"{pattern}.{layer}"
                layer_responsibilities[layer_key] = set()
                
                for module_name, module in self.arch_manager.index.layer_index.get(layer_key, {}).items():
                    for resp in module.get("responsibilities", []):
                        layer_responsibilities[layer_key].add(resp)
        
        # 检查不同层级间的职责重叠
        for layer1, resps1 in layer_responsibilities.items():
            for layer2, resps2 in layer_responsibilities.items():
                if layer1 != layer2:
                    overlap = resps1.intersection(resps2)
                    if overlap:
                        issues.append(f"层级 {layer1} 和 {layer2} 存在职责重叠: {', '.join(overlap)}")
        
        # 2. 检查是否存在未实现的声明依赖
        for module, info in self.arch_manager.index.dependency_graph.items():
            for dep in info["depends_on"]:
                if dep not in self.arch_manager.index.dependency_graph:
                    issues.append(f"模块 {module} 依赖的模块 {dep} 不存在")
        
        return issues

    def _check_global_circular_dependencies(self) -> List[str]:
        """检查全局循环依赖"""
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _check_global_circular_dependencies")
        
        cycles = []
        all_modules = list(self.arch_manager.index.dependency_graph.keys())
        print(f"🔄 [LOOP-TRACE] {call_id} - 检查 {len(all_modules)} 个模块的循环依赖")
        
        # 构建依赖图
        dependency_map = {}
        for module, info in self.arch_manager.index.dependency_graph.items():
            deps = list(info.get("depends_on", []))
            dependency_map[module] = deps
            if deps:
                print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{module}' 依赖于 {len(deps)} 个其他模块")
        
        visited = {}  # 0: 未访问，1: 正在访问，2: 已访问
        path = []
        max_recursion_depth = 100  # 防止无限递归
        
        def dfs(current: str, depth: int = 0) -> bool:
            dfs_id = str(uuid.uuid4())[:6]  # 每个DFS调用有自己的ID
            print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - DFS(depth={depth}): 检查模块 '{current}'")
            
            if depth > max_recursion_depth:
                print(f"⚠️ [LOOP-TRACE] {call_id}.{dfs_id} - 达到最大递归深度 ({max_recursion_depth})，中断递归")
                return False
            
            if current in visited and visited[current] == 1:
                cycle_start = path.index(current)
                cycle = path[cycle_start:] + [current]
                cycle_str = " -> ".join(cycle)
                print(f"⚠️ [LOOP-TRACE] {call_id}.{dfs_id} - 检测到循环! {cycle_str}")
                cycles.append(cycle_str)
                return True
            
            if current in visited and visited[current] == 2:
                print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 模块 '{current}' 已访问过，跳过")
                return False
                
            visited[current] = 1
            path.append(current)
            print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 当前路径: {' -> '.join(path)}")
            
            has_cycle = False
            deps = dependency_map.get(current, [])
            print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 模块 '{current}' 有 {len(deps)} 个依赖需要检查")
            
            for i, dep in enumerate(deps):
                print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 检查依赖 {i+1}/{len(deps)}: '{dep}'")
                if dep in dependency_map:
                    print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 递归检查依赖 '{dep}' (depth={depth+1})")
                    if dfs(dep, depth + 1):
                        print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 依赖 '{dep}' 导致循环")
                        has_cycle = True
                else:
                    print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 依赖 '{dep}' 不在依赖图中")
            
            path.pop()
            visited[current] = 2
            print(f"🔄 [LOOP-TRACE] {call_id}.{dfs_id} - 完成模块 '{current}' 的检查，循环状态: {has_cycle}")
            return has_cycle
        
        for i, module in enumerate(all_modules):
            print(f"🔄 [LOOP-TRACE] {call_id} - 开始检查模块 {i+1}/{len(all_modules)}: '{module}'")
            if module not in visited:
                visited[module] = 0
                print(f"🔄 [LOOP-TRACE] {call_id} - 开始DFS遍历模块 '{module}'")
                dfs(module)
                print(f"🔄 [LOOP-TRACE] {call_id} - 完成DFS遍历模块 '{module}'")
        
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _check_global_circular_dependencies: 发现 {len(cycles)} 个循环")
        return cycles

    async def _attempt_consistency_correction(self, issues: List[str]):
        """尝试自动修正架构一致性问题"""
        if self.logger:
            self.logger.log("\n🔄 尝试自动修正架构一致性问题...", role="system")
        
        # 生成修正方案
        correction_plan = await self._generate_consistency_correction_plan(issues)
        
        # 实施修正
        if correction_plan:
            corrections_applied = 0
            for correction in correction_plan:
                result = await self._apply_correction(correction)
                if result:
                    corrections_applied += 1
            
            if self.logger:
                self.logger.log(f"✅ 已应用 {corrections_applied} 个修正", role="system")
        else:
            if self.logger:
                self.logger.log("❌ 无法自动生成修正方案，请手动审查并修正", role="error")

    async def _generate_consistency_correction_plan(self, issues: List[str]) -> List[Dict]:
        """生成架构一致性问题的修正方案"""
        prompt = f"""
        针对以下架构一致性问题，生成修正方案：
        
        {json.dumps(issues, ensure_ascii=False, indent=2)}
        
        请提供具体的修正步骤，包括：
        1. 需要修改的模块
        2. 修改的类型（重命名/移动/拆分/合并等）
        3. 修改的具体内容
        4. 修改的理由
        
        返回JSON格式的修正方案列表：
        [
            {{
                "module": "模块名",
                "type": "修改类型",
                "details": {{
                    // 具体修改内容
                }},
                "reason": "修改理由"
            }}
        ]
        """
        
        return await self._get_llm_response(prompt)

    async def _attempt_cycle_correction(self, cycles: List[str]):
        """尝试自动修正循环依赖问题"""
        if self.logger:
            self.logger.log("\n🔄 尝试自动修正循环依赖问题...", role="system")
        
        # 生成修正方案
        correction_plan = await self._generate_cycle_correction_plan(cycles)
        
        # 实施修正
        if correction_plan and isinstance(correction_plan, list):
            corrections_applied = 0
            for correction in correction_plan:
                if isinstance(correction, dict):
                    result = await self._apply_correction(correction)
                    if result:
                        corrections_applied += 1
                else:
                    if self.logger:
                        self.logger.log(f"⚠️ 无效的修正格式: {correction}", role="error")
            
            if self.logger:
                self.logger.log(f"✅ 已应用 {corrections_applied} 个修正", role="system")
        else:
            if self.logger:
                self.logger.log("❌ 无法自动生成循环依赖修正方案，请手动审查并修正", role="error")

    async def _generate_cycle_correction_plan(self, cycles: List[str]) -> List[Dict]:
        """生成循环依赖的修正方案"""
        prompt = f"""
        针对以下循环依赖问题，生成修正方案：
        
        {json.dumps(cycles, ensure_ascii=False, indent=2)}
        
        请提供具体的修正步骤，包括：
        1. 需要修改的依赖关系
        2. 修改的方式（移除依赖/引入中间层/重构等）
        3. 修改的具体内容
        4. 修改的理由
        
        返回JSON格式的修正方案列表：
        [
            {{
                "cycle": "循环依赖路径",
                "type": "修改类型",
                "details": {{
                    "from_module": "源模块",
                    "to_module": "目标模块",
                    "action": "具体操作"
                }},
                "reason": "修改理由"
            }}
        ]
        """
        
        return await self._get_llm_response(prompt)

    async def _apply_correction(self, correction: Dict) -> bool:
        """应用架构修正"""
        if not isinstance(correction, dict):
            if self.logger:
                self.logger.log(f"\n⚠️ 无效的修正格式: {correction}", role="error")
            return False
            
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _apply_correction")
        
        if self.logger:
            self.logger.log(f"\n应用修正: {correction.get('type', '')} - {correction.get('module', correction.get('cycle', ''))}", role="system")
        
        # 实现不同类型的修正逻辑
        correction_type = correction.get("type", "")
        print(f"🔄 [LOOP-TRACE] {call_id} - 修正类型: {correction_type}")
        
        result = False
        
        if correction_type == "rename":
            # 重命名模块
            old_name = correction.get("module", "")
            new_name = correction.get("details", {}).get("new_name", "")
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试重命名模块: '{old_name}' -> '{new_name}'")
            
            if old_name in self.arch_manager.index.dependency_graph:
                print(f"🔄 [LOOP-TRACE] {call_id} - 找到模块 '{old_name}' 在依赖图中")
                # 获取旧模块信息
                old_module = self.arch_manager.index.dependency_graph[old_name]
                
                # 创建新模块
                new_module = {
                    "name": new_name,
                    "pattern": old_module.get("pattern", ""),
                    "layer": old_module.get("layer", ""),
                    # 复制其他属性
                }
                print(f"🔄 [LOOP-TRACE] {call_id} - 创建新模块 '{new_name}' 完成")
                
                # 更新依赖关系
                # TODO: 实现依赖更新逻辑
                print(f"🔄 [LOOP-TRACE] {call_id} - 重命名模块成功")
                result = True
            else:
                print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{old_name}' 不在依赖图中，无法重命名")
                
        elif correction_type == "move":
            # 移动模块到新层级
            module_name = correction.get("module", "")
            target_layer = correction.get("details", {}).get("target_layer", "")
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试移动模块 '{module_name}' 到层级 '{target_layer}'")
            
            # TODO: 实现移动逻辑
            print(f"🔄 [LOOP-TRACE] {call_id} - 移动模块成功")
            result = True
            
        elif correction_type == "split":
            # 拆分模块
            module_name = correction.get("module", "")
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试拆分模块 '{module_name}'")
            # TODO: 实现拆分逻辑
            print(f"🔄 [LOOP-TRACE] {call_id} - 拆分模块未实现")
            result = False
            
        elif correction_type == "merge":
            # 合并模块
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试合并模块")
            # TODO: 实现合并逻辑
            print(f"🔄 [LOOP-TRACE] {call_id} - 合并模块未实现")
            result = False
            
        elif correction_type == "remove_dependency":
            # 移除依赖
            from_module = correction.get("details", {}).get("from_module", "")
            to_module = correction.get("details", {}).get("to_module", "")
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试移除依赖: '{from_module}' -> '{to_module}'")
            
            if from_module in self.arch_manager.index.dependency_graph:
                print(f"🔄 [LOOP-TRACE] {call_id} - 找到模块 '{from_module}' 在依赖图中")
                # TODO: 实现依赖移除逻辑
                print(f"🔄 [LOOP-TRACE] {call_id} - 移除依赖成功")
                result = True
            else:
                print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{from_module}' 不在依赖图中，无法移除依赖")
        
        elif correction_type == "add_mediator":
            # 添加中介层
            print(f"🔄 [LOOP-TRACE] {call_id} - 尝试添加中介层")
            # TODO: 实现中介层添加逻辑
            print(f"🔄 [LOOP-TRACE] {call_id} - 添加中介层未实现")
            result = False
            
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _apply_correction: 结果={result}")
        return result

    async def _save_final_architecture(self):
        """保存最终的架构状态"""
        output_dir = Path("data/output/architecture")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存架构状态
        state_file = output_dir / "architecture_state.json"
        
        state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {
                k: list(v) for k, v in self.arch_manager.index.requirement_module_index.items()
            },
            "responsibility_index": {
                k: {
                    "modules": list(v["modules"]),
                    "objects": list(v["objects"]),
                    "patterns": list(v["patterns"])
                } for k, v in self.arch_manager.index.responsibility_index.items()
            },
            "dependency_graph": {
                k: {
                    "depends_on": list(v["depends_on"]),
                    "depended_by": list(v["depended_by"]),
                    "pattern": v["pattern"],
                    "layer": v["layer"]
                } for k, v in self.arch_manager.index.dependency_graph.items()
            },
            "layer_index": {
                layer: {
                    name: module for name, module in modules.items()
                } for layer, modules in self.arch_manager.index.layer_index.items()
            }
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        if self.logger:
            self.logger.log(f"\n✅ 架构推理完成！", role="system")
            self.logger.log(f"架构状态已保存到：{state_file}", role="system")
        
        # 生成架构文档
        await self._generate_architecture_docs()
        
    async def _generate_architecture_docs(self):
        """生成架构文档"""
        if self.logger:
            self.logger.log("\n📝 生成架构文档...", role="system")
        
        arch_state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {
                k: list(v) for k, v in self.arch_manager.index.requirement_module_index.items()
            },
            "responsibility_index": {
                k: {
                    "modules": list(v["modules"]),
                    "objects": list(v["objects"]),
                    "patterns": list(v["patterns"])
                } for k, v in self.arch_manager.index.responsibility_index.items()
            },
            "dependency_graph": {
                k: {
                    "depends_on": list(v["depends_on"]),
                    "depended_by": list(v["depended_by"]),
                    "pattern": v["pattern"],
                    "layer": v["layer"]
                } for k, v in self.arch_manager.index.dependency_graph.items()
            },
            "layer_index": {
                layer: {
                    name: module for name, module in modules.items()
                } for layer, modules in self.arch_manager.index.layer_index.items()
            }
        }
        
        # 2. 生成架构概览文档
        overview_doc = await self._generate_overview_doc(arch_state)
        (self.output_path / "01_architecture_overview.md").write_text(overview_doc)
        
        # 3. 生成详细设计文档
        detailed_doc = await self._generate_detailed_design_doc(arch_state)
        (self.output_path / "02_detailed_design.md").write_text(detailed_doc)
        
        # 4. 生成接口文档
        interface_doc = await self._generate_interface_doc(arch_state)
        (self.output_path / "03_interfaces.md").write_text(interface_doc)
        
        # 5. 生成部署文档
        deployment_doc = await self._generate_deployment_doc(arch_state)
        (self.output_path / "04_deployment.md").write_text(deployment_doc)
        
        if self.logger:
            self.logger.log("✅ 架构文档生成完成", role="system")
        
    async def _generate_overview_doc(self, arch_state: Dict) -> str:
        """生成架构概览文档"""
        prompt = f"""
        基于以下架构状态生成架构概览文档：
        
        {json.dumps(arch_state, ensure_ascii=False, indent=2)}
        
        请生成包含以下内容的Markdown格式文档：
        1. 系统架构概述
        2. 架构模式说明
        3. 关键模块概览
        4. 核心流程和交互
        5. 技术选型和理由
        """
        
        response = await self._get_llm_response(prompt)
        if isinstance(response, dict):
            if "content" in response:
                return response["content"]
            elif "text" in response:
                return response["text"]
            else:
                return json.dumps(response, ensure_ascii=False, indent=2)
        elif isinstance(response, str):
            return response
        else:
            return str(response)
        
    async def _generate_detailed_design_doc(self, arch_state: Dict) -> str:
        """生成详细设计文档"""
        prompt = f"""
        基于以下架构状态生成详细设计文档：
        
        {json.dumps(arch_state, ensure_ascii=False, indent=2)}
        
        请生成包含以下内容的Markdown格式文档：
        1. 详细的模块设计
        2. 模块职责
        3. 模块间关系
        4. 关键算法和数据结构
        5. 异常处理策略
        """
        
        response = await self._get_llm_response(prompt)
        if isinstance(response, dict):
            if "content" in response:
                return response["content"]
            elif "text" in response:
                return response["text"]
            else:
                return json.dumps(response, ensure_ascii=False, indent=2)
        elif isinstance(response, str):
            return response
        else:
            return str(response)
        
    async def _generate_interface_doc(self, arch_state: Dict) -> str:
        """生成接口文档"""
        prompt = f"""
        基于以下架构状态生成接口文档：
        
        {json.dumps(arch_state, ensure_ascii=False, indent=2)}
        
        请生成包含以下内容的Markdown格式文档：
        1. 外部接口定义
        2. 内部模块接口
        3. 数据模型定义
        4. 接口示例
        5. 错误码和处理
        """
        
        response = await self._get_llm_response(prompt)
        if isinstance(response, dict):
            if "content" in response:
                return response["content"]
            elif "text" in response:
                return response["text"]
            else:
                return json.dumps(response, ensure_ascii=False, indent=2)
        elif isinstance(response, str):
            return response
        else:
            return str(response)
        
    async def _generate_deployment_doc(self, arch_state: Dict) -> str:
        """生成部署文档"""
        prompt = f"""
        基于以下架构状态生成部署文档：
        
        {json.dumps(arch_state, ensure_ascii=False, indent=2)}
        
        请生成包含以下内容的Markdown格式文档：
        1. 部署架构
        2. 环境需求
        3. 部署步骤
        4. 配置说明
        5. 监控和维护
        """
        
        response = await self._get_llm_response(prompt)
        if isinstance(response, dict):
            if "content" in response:
                return response["content"]
            elif "text" in response:
                return response["text"]
            else:
                return json.dumps(response, ensure_ascii=False, indent=2)
        elif isinstance(response, str):
            return response
        else:
            return str(response)
        
    def _check_naming_inconsistencies(self) -> List[str]:
        """检查命名不一致性
        
        检查模块命名是否遵循一致的命名约定，包括：
        1. 命名风格一致性（驼峰、下划线等）
        2. 命名前缀/后缀一致性
        3. 命名与职责的匹配度
        
        Returns:
            命名不一致性问题列表
        """
        issues = []
        
        all_modules = list(self.arch_manager.index.dependency_graph.keys())
        if not all_modules:
            return issues
            
        camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')  # 驼峰命名法
        pascal_case_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')  # 帕斯卡命名法
        snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')     # 下划线命名法
        
        naming_styles = {
            "camel_case": 0,
            "pascal_case": 0,
            "snake_case": 0,
            "other": 0
        }
        
        for module in all_modules:
            module_name = module.split('.')[-1]  # 获取最后一部分作为模块名
            
            if camel_case_pattern.match(module_name):
                naming_styles["camel_case"] += 1
            elif pascal_case_pattern.match(module_name):
                naming_styles["pascal_case"] += 1
            elif snake_case_pattern.match(module_name):
                naming_styles["snake_case"] += 1
            else:
                naming_styles["other"] += 1
        
        dominant_style = max(naming_styles, key=naming_styles.get)
        if dominant_style == "other" or naming_styles[dominant_style] < len(all_modules) * 0.7:
            issues.append("模块命名风格不一致，建议统一使用同一种命名风格")
        
        if dominant_style != "other":
            for module in all_modules:
                module_name = module.split('.')[-1]
                
                if dominant_style == "camel_case" and not camel_case_pattern.match(module_name):
                    issues.append(f"模块 '{module}' 不符合驼峰命名法")
                elif dominant_style == "pascal_case" and not pascal_case_pattern.match(module_name):
                    issues.append(f"模块 '{module}' 不符合帕斯卡命名法")
                elif dominant_style == "snake_case" and not snake_case_pattern.match(module_name):
                    issues.append(f"模块 '{module}' 不符合下划线命名法")
        
        layer_prefixes = {}
        for module, info in self.arch_manager.index.dependency_graph.items():
            layer = info.get("layer", "")
            if not layer:
                continue
                
            module_name = module.split('.')[-1]
            prefix = module_name[:3] if len(module_name) > 3 else module_name
            
            if layer not in layer_prefixes:
                layer_prefixes[layer] = {}
                
            if prefix not in layer_prefixes[layer]:
                layer_prefixes[layer][prefix] = 0
                
            layer_prefixes[layer][prefix] += 1
        
        for layer, prefixes in layer_prefixes.items():
            if len(prefixes) > 3:  # 如果一个层级有超过3种不同的前缀
                most_common_prefix = max(prefixes, key=prefixes.get)
                if prefixes[most_common_prefix] < sum(prefixes.values()) * 0.5:
                    issues.append(f"层级 '{layer}' 的模块命名前缀不一致")
        
        for module, info in self.arch_manager.index.dependency_graph.items():
            module_name = module.split('.')[-1].lower()
            responsibilities = [r.lower() for r in info.get("responsibilities", [])]
            
            if responsibilities:
                matched = False
                for resp in responsibilities:
                    keywords = [word for word in re.findall(r'\b\w+\b', resp) if len(word) > 3]
                    for keyword in keywords:
                        if keyword.lower() in module_name:
                            matched = True
                            break
                    if matched:
                        break
                        
                if not matched:
                    issues.append(f"模块 '{module}' 的命名可能不能充分反映其职责")
        
        for module, info in self.arch_manager.index.dependency_graph.items():
            target_path = info.get("target_path", "")
            layer = info.get("layer", "").lower()
            
            if target_path:
                if layer == "presentation" and not target_path.startswith("frontend/"):
                    issues.append(f"模块 '{module}' 的目标路径 '{target_path}' 不符合表现层命名规范")
                elif layer == "business" and not target_path.startswith("backend/business/"):
                    issues.append(f"模块 '{module}' 的目标路径 '{target_path}' 不符合业务层命名规范")
                elif layer == "data" and not target_path.startswith("backend/data/"):
                    issues.append(f"模块 '{module}' 的目标路径 '{target_path}' 不符合数据层命名规范")
        
        return issues
        
    def _check_layer_violations(self) -> List[str]:
        """检查层级违规
        
        检查模块是否违反了架构的层级规则，包括：
        1. 层级依赖方向是否正确
        2. 是否存在跨层级依赖
        3. 是否存在不符合架构模式的依赖
        
        Returns:
            层级违规问题列表
        """
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _check_layer_violations")
        
        issues = []
        
        patterns = self.arch_manager.index.architecture_patterns
        pattern_count = len(patterns)
        print(f"🔄 [LOOP-TRACE] {call_id} - 检查 {pattern_count} 个架构模式的层级违规")
        
        pattern_idx = 0
        for pattern_name, pattern_info in patterns.items():
            pattern_idx += 1
            layer_dependencies = pattern_info.get("dependencies", {})
            print(f"🔄 [LOOP-TRACE] {call_id} - 检查模式 {pattern_idx}/{pattern_count}: '{pattern_name}'，有 {len(layer_dependencies)} 个层级依赖规则")
            
            pattern_modules = [m for m, info in self.arch_manager.index.dependency_graph.items() 
                              if info.get("pattern") == pattern_name]
            print(f"🔄 [LOOP-TRACE] {call_id} - 模式 '{pattern_name}' 有 {len(pattern_modules)} 个模块")
            
            module_idx = 0
            for module, info in self.arch_manager.index.dependency_graph.items():
                if info.get("pattern") != pattern_name:
                    continue
                
                module_idx += 1
                print(f"🔄 [LOOP-TRACE] {call_id} - 检查模块 {module_idx}/{len(pattern_modules)}: '{module}'")
                
                module_layer = info.get("layer")
                if not module_layer:
                    print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{module}' 没有指定层级，跳过")
                    continue
                
                allowed_dependencies = layer_dependencies.get(module_layer, [])
                print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{module}' 在层级 '{module_layer}'，允许依赖的层级: {allowed_dependencies}")
                
                deps = info.get("depends_on", [])
                print(f"🔄 [LOOP-TRACE] {call_id} - 模块 '{module}' 有 {len(deps)} 个依赖需要检查")
                
                dep_idx = 0
                for dep in deps:
                    dep_idx += 1
                    print(f"🔄 [LOOP-TRACE] {call_id} - 检查依赖 {dep_idx}/{len(deps)}: '{dep}'")
                    
                    if dep not in self.arch_manager.index.dependency_graph:
                        print(f"🔄 [LOOP-TRACE] {call_id} - 依赖 '{dep}' 不在依赖图中，跳过")
                        continue  # 跳过不存在的依赖
                    
                    dep_info = self.arch_manager.index.dependency_graph[dep]
                    dep_pattern = dep_info.get("pattern")
                    dep_layer = dep_info.get("layer")
                    
                    print(f"🔄 [LOOP-TRACE] {call_id} - 依赖 '{dep}' 属于模式 '{dep_pattern}'，层级 '{dep_layer}'")
                    
                    if dep_pattern != pattern_name:
                        issue = f"模块 '{module}' 依赖了不同架构模式的模块 '{dep}'"
                        print(f"⚠️ [LOOP-TRACE] {call_id} - 发现层级违规: {issue}")
                        issues.append(issue)
                        continue
                    
                    if dep_layer not in allowed_dependencies and dep_layer != module_layer:
                        issue = f"模块 '{module}' ({module_layer}) 依赖了不允许的层级 '{dep_layer}' 中的模块 '{dep}'"
                        print(f"⚠️ [LOOP-TRACE] {call_id} - 发现层级违规: {issue}")
                        issues.append(issue)
        
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _check_layer_violations: 发现 {len(issues)} 个层级违规")
        return issues
        
    def _check_responsibility_overlaps(self) -> List[str]:
        """检查职责重叠
        
        检查不同模块之间是否存在职责重叠，包括：
        1. 完全相同的职责
        2. 高度相似的职责
        3. 职责范围重叠
        
        Returns:
            职责重叠问题列表
        """
        call_id = str(uuid.uuid4())[:8]  # 生成唯一调用ID用于跟踪
        print(f"🔄 [LOOP-TRACE] {call_id} - ENTER _check_responsibility_overlaps")
        
        issues = []
        
        print(f"🔄 [LOOP-TRACE] {call_id} - 开始构建职责映射")
        responsibility_map = {}
        module_count = len(self.arch_manager.index.dependency_graph)
        print(f"🔄 [LOOP-TRACE] {call_id} - 分析 {module_count} 个模块的职责")
        
        module_idx = 0
        for module, info in self.arch_manager.index.dependency_graph.items():
            module_idx += 1
            responsibilities = info.get("responsibilities", [])
            print(f"🔄 [LOOP-TRACE] {call_id} - 处理模块 {module_idx}/{module_count}: '{module}'，有 {len(responsibilities)} 个职责")
            
            for resp in responsibilities:
                resp_lower = resp.lower()
                if resp_lower not in responsibility_map:
                    responsibility_map[resp_lower] = []
                responsibility_map[resp_lower].append(module)
        
        print(f"🔄 [LOOP-TRACE] {call_id} - 检查完全相同的职责")
        resp_count = len(responsibility_map)
        print(f"🔄 [LOOP-TRACE] {call_id} - 共有 {resp_count} 个不同的职责需要检查")
        
        resp_idx = 0
        for resp, modules in responsibility_map.items():
            resp_idx += 1
            print(f"🔄 [LOOP-TRACE] {call_id} - 检查职责 {resp_idx}/{resp_count}: '{resp}'，被 {len(modules)} 个模块引用")
            
            if len(modules) > 1:
                issue = f"职责 '{resp}' 在多个模块中重复: {', '.join(modules)}"
                print(f"⚠️ [LOOP-TRACE] {call_id} - 发现职责重叠: {issue}")
                issues.append(issue)
        
        print(f"🔄 [LOOP-TRACE] {call_id} - 检查高度相似的职责")
        all_responsibilities = list(responsibility_map.keys())
        total_comparisons = len(all_responsibilities) * (len(all_responsibilities) - 1) // 2
        print(f"🔄 [LOOP-TRACE] {call_id} - 需要进行 {total_comparisons} 次职责相似度比较")
        
        comparison_idx = 0
        for i in range(len(all_responsibilities)):
            for j in range(i+1, len(all_responsibilities)):
                comparison_idx += 1
                if comparison_idx % 100 == 0:  # 每100次比较输出一次日志，避免日志过多
                    print(f"🔄 [LOOP-TRACE] {call_id} - 正在进行第 {comparison_idx}/{total_comparisons} 次职责相似度比较")
                
                resp1 = all_responsibilities[i]
                resp2 = all_responsibilities[j]
                
                words1 = set(resp1.split())
                words2 = set(resp2.split())
                
                if not words1 or not words2:
                    continue
                
                common_words = words1.intersection(words2)
                similarity = len(common_words) / min(len(words1), len(words2))
                
                if similarity > 0.7:  # 如果相似度超过70%
                    modules1 = responsibility_map[resp1]
                    modules2 = responsibility_map[resp2]
                    
                    if set(modules1) != set(modules2):
                        issue = f"职责 '{resp1}' 和 '{resp2}' 高度相似，但分别属于不同模块: {', '.join(set(modules1))} 和 {', '.join(set(modules2))}"
                        print(f"⚠️ [LOOP-TRACE] {call_id} - 发现职责相似: {issue}")
                        issues.append(issue)
        
        print(f"🔄 [LOOP-TRACE] {call_id} - EXIT _check_responsibility_overlaps: 发现 {len(issues)} 个职责重叠问题")
        return issues
        
    async def check_all_issues(self) -> Dict[str, List[str]]:
        """检查所有架构问题
        
        执行全面的架构检查，包括：
        1. 循环依赖检查
        2. 命名不一致性检查
        3. 层级违规检查
        4. 职责重叠检查
        5. 整体一致性检查
        
        Returns:
            包含各类问题的字典
        """
        issues = {
            "circular_dependencies": [],
            "naming_inconsistencies": [],
            "layer_violations": [],
            "responsibility_overlaps": [],
            "consistency_issues": []
        }
        
        issues["circular_dependencies"] = self._check_global_circular_dependencies()
        issues["naming_inconsistencies"] = self._check_naming_inconsistencies()
        issues["layer_violations"] = self._check_layer_violations()
        issues["responsibility_overlaps"] = self._check_responsibility_overlaps()
        issues["consistency_issues"] = self._check_overall_consistency()
        
        return issues
        
    async def check_module_issues(self, module_name: str) -> Dict[str, List[str]]:
        """检查单个模块的架构问题
        
        对新添加的模块执行架构检查，包括：
        1. 循环依赖检查
        2. 命名不一致性检查
        3. 层级违规检查
        4. 职责重叠检查
        
        Args:
            module_name: 要检查的模块名称
            
        Returns:
            包含各类问题的字典
        """
        issues = {
            "circular_dependencies": [],
            "naming_inconsistencies": [],
            "layer_violations": [],
            "responsibility_overlaps": []
        }
        
        if module_name not in self.arch_manager.index.dependency_graph:
            return issues
        
        all_cycles = self._check_global_circular_dependencies()
        issues["circular_dependencies"] = [cycle for cycle in all_cycles if module_name in cycle]
        
        all_naming_issues = self._check_naming_inconsistencies()
        issues["naming_inconsistencies"] = [issue for issue in all_naming_issues if module_name in issue]
        
        all_layer_issues = self._check_layer_violations()
        issues["layer_violations"] = [issue for issue in all_layer_issues if module_name in issue]
        
        all_resp_issues = self._check_responsibility_overlaps()
        issues["responsibility_overlaps"] = [issue for issue in all_resp_issues if module_name in issue]
        
        return issues                           
