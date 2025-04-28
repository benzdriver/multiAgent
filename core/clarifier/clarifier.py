from pathlib import Path
from typing import Dict, List, Optional, Set, Any
# 修改导入路径，从旧的clarifier模块改为使用common或其他适当位置
# from clarifier.reader import load_input_documents
# from clarifier.summarizer import summarize_text
# from clarifier.index_generator import generate_summary_index
# from dependency_manager import DependencyManager
from .architecture_manager import ArchitectureManager
import asyncio
import json
import os
import glob

from .requirement_analyzer import RequirementAnalyzer
from .architecture_generator import ArchitectureGenerator
from core.llm.llm_executor import run_prompt
from common.logger import Logger  # 假设logger已移至common

class Clarifier:
    """需求澄清器，用于澄清需求并生成架构文档"""
    
    def __init__(self, data_dir: str = "data", llm_chat=None):
        """初始化需求澄清器
        
        Args:
            data_dir: 数据目录
            llm_chat: LLM聊天函数
        """
        self.data_dir = Path(data_dir)
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm_chat = llm_chat
        self.logger = Logger(name="clarifier")
        self.requirement_analyzer = RequirementAnalyzer(logger=self.logger)
        self.architecture_generator = ArchitectureGenerator(logger=self.logger)
        self.waiting_for_user = None
        
        # 暂时移除对旧模块的依赖
        # self.architecture_manager = None  # 将在初始化完成后设置
        
        # 核心提示模板
        self.prompts = {
            "welcome": "🚀 欢迎使用需求澄清与架构设计助手！",
            "mode_selection": "请选择操作模式：\n1. 文件解析模式（从输入文件夹读取文档）\n2. 交互式CLI模式（通过对话完成需求澄清）",
            "analysis_complete": "需求分析完成！是否继续进行架构分析和设计？",
            "architecture_complete": "🎉 需求分析和架构设计已完成！",
            "next_steps": "分析完成后，您可以:\n1. 进行深度需求澄清 - 发现潜在的需求问题和矛盾\n2. 进行深度架构推理 - 生成更详细的架构设计\n请输入选项编号继续。"
        }
    
    async def start(self):
        """启动需求澄清器"""
        self.logger.log(self.prompts["welcome"], role="system")
        
        # 检查输入文件夹是否存在
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)
            self.logger.log(f"已创建输入文件夹：{self.input_dir}", role="system")
            self.logger.log("请将您的需求文档放入此文件夹，然后重新启动程序。", role="system")
            return
        
        # 询问用户选择模式
        self.logger.log(self.prompts["mode_selection"], role="system")
        
        choice = input("\n请输入选项编号 [1/2]: ").strip()
        
        if choice == "1":
            await self._file_based_clarification()
        elif choice == "2":
            await self._interactive_clarification()
        else:
            self.logger.log("无效的选项，请重新启动并选择正确的选项。", role="system")
    
    async def _file_based_clarification(self):
        """基于文件的需求澄清"""
        self.logger.log("\n📂 正在从输入文件夹读取文档...\n", role="system")
        
        # 读取所有Markdown文件
        all_documents = await self._read_all_markdown_files()
        
        if not all_documents:
            self.logger.log("⚠️ 在输入文件夹中未找到任何Markdown文档。", role="system")
            self.logger.log("请将您的需求文档放入输入文件夹，或者切换到交互式模式。", role="system")
            
            switch = input("\n是否切换到交互式模式？[y/n]: ").strip().lower()
            if switch == 'y':
                await self._interactive_clarification()
            return
        
        # 分析所有文档内容
        self.logger.log(f"✓ 找到 {len(all_documents)} 个文档。正在分析...", role="system")
        
        # 将所有文档内容合并
        all_content = ""
        for doc_name, content in all_documents.items():
            all_content += f"\n\n# {doc_name}\n{content}"
        
        # 分析需求
        requirement_analysis = await self.requirement_analyzer.analyze_requirements(all_content, self.run_llm)
        
        # 生成需求摘要文档
        await self.requirement_analyzer.generate_requirement_summary(requirement_analysis, self.run_llm)
        
        # 提示用户继续
        self.logger.log("\n需求分析完成！", role="clarifier")
        self.logger.log(self.prompts["analysis_complete"], role="confirm")
        self.waiting_for_user = asyncio.Event()
        await self.waiting_for_user.wait()
        # 用户确认后继续
        
        # 分析架构需求
        architecture_analysis = await self.architecture_generator.analyze_architecture_needs(requirement_analysis, self.run_llm)
        
        # === 新增：打印需求-模块-技术栈映射并让用户确认 ===
        self.logger.log(f"\n===== 需求-模块-技术栈映射预览 =====\n", role="system")
        self.logger.log(f"【需求分析】\n{json.dumps(requirement_analysis.get('system_overview', {}), ensure_ascii=False, indent=2)}", role="system")
        self.logger.log(f"【功能需求】\n{json.dumps(requirement_analysis.get('functional_requirements', {}), ensure_ascii=False, indent=2)}", role="system")
        self.logger.log(f"【架构模式】\n{json.dumps(architecture_analysis.get('architecture_pattern', {}), ensure_ascii=False, indent=2)}", role="system")
        self.logger.log(f"【系统分层】\n{json.dumps(architecture_analysis.get('layers', []), ensure_ascii=False, indent=2)}", role="system")
        self.logger.log(f"【技术栈】\n{json.dumps(architecture_analysis.get('technology_stack', []), ensure_ascii=False, indent=2)}", role="system")
        self.logger.log("\n请确认上述映射是否符合预期。", role="system")
        confirm = input("是否继续进行深度架构推理？[y/n]: ").strip().lower()
        if confirm != 'y':
            self.logger.log("操作已取消。您可以在输出目录查看已生成的需求和架构分析文档。", role="system")
            return
        # === 新增结束 ===

        # === 新增：逐模块交互调整 ===
        core_components = architecture_analysis.get('core_components', [])
        if core_components:
            self.logger.log("\n===== 逐模块交互调整 =====\n", role="system")
            for i, module in enumerate(core_components):
                self.logger.log(f"\n模块 {i+1}/{len(core_components)}: {module.get('name', '未命名模块')}", role="system")
                self.logger.log(json.dumps(module, ensure_ascii=False, indent=2), role="system")
                while True:
                    action = input("[e]编辑/[s]跳过/[c]确认: ").strip().lower()
                    if action == 'e':
                        self.logger.log("请输入新的模块定义（JSON 格式），或回车取消：", role="system")
                        new_json = input()
                        if new_json.strip():
                            try:
                                new_module = json.loads(new_json)
                                core_components[i] = new_module
                                self.logger.log("✓ 已更新模块定义", role="clarifier")
                                self.logger.log(json.dumps(new_module, ensure_ascii=False, indent=2), role="system")
                                continue
                            except Exception as e:
                                self.logger.log(f"❌ JSON解析失败: {e}", role="system")
                                continue
                        else:
                            self.logger.log("未做修改。", role="system")
                            continue
                    elif action == 's':
                        self.logger.log("已跳过该模块。", role="system")
                        break
                    elif action == 'c':
                        self.logger.log("已确认该模块。", role="system")
                        break
                    else:
                        self.logger.log("无效输入，请重新选择。", role="system")
        # === 新增结束 ===
        
        # 生成架构文档
        await self.architecture_generator.generate_architecture_documents(requirement_analysis, architecture_analysis, self.run_llm)
        
        # 保存架构状态
        await self.architecture_generator.save_architecture_state(requirement_analysis, architecture_analysis)
        
        self.logger.log("\n🎉 需求分析和架构设计已完成！", role="system")
        self.logger.log(f"所有文档已保存到：{self.output_dir}", role="system")
        
        # 提供后续步骤选项
        self.logger.log(self.prompts["next_steps"], role="clarifier")
        
        choice = input("\n请输入选项编号 [1/2]: ").strip()
        if choice == "1":
            await self.deep_clarification(requirement_analysis)
        elif choice == "2":
            await self.deep_reasoning(requirement_analysis, architecture_analysis)
        else:
            self.logger.log("无效选项，操作结束。", role="system")
    
    async def deep_clarification(self, requirement_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行深度需求澄清
        
        Args:
            requirement_analysis: 现有的需求分析结果
            
        Returns:
            深度澄清的结果
        """
        self.logger.log("\n===== 开始深度需求澄清 =====\n", role="system")
        
        # 如果没有提供需求分析，使用架构管理器中的信息
        if not requirement_analysis and hasattr(self, 'architecture_manager'):
            requirement_analysis = {
                "requirements": self.architecture_manager.requirements,
                "system_overview": self.architecture_manager.system_overview,
                "functional_requirements": self.architecture_manager.functional_requirements
            }
        
        if not requirement_analysis or not requirement_analysis.get("requirements"):
            self.logger.log("⚠️ 没有需求数据可供深度澄清。请先完成需求分析。", role="system")
            return {}
        
        # 构建需求摘要
        requirements_str = "已识别的需求:\n"
        for idx, req in enumerate(requirement_analysis.get("requirements", [])):
            title = req.get("title", "") or req.get("name", f"需求 {idx+1}")
            desc = req.get("description", "无描述")
            requirements_str += f"- {title}: {desc}\n"
        
        # 构建深度澄清的提示
        prompt = (
            f"请对以下需求进行深度澄清分析，找出以下问题:\n"
            f"1. 潜在的遗漏需求\n"
            f"2. 需求间的矛盾或冲突\n"
            f"3. 模糊不清的需求描述\n"
            f"4. 隐藏的技术挑战\n"
            f"5. 改进建议\n\n"
            f"{requirements_str}"
        )
        
        self.logger.log("正在进行深度需求分析...", role="system")
        
        # 执行LLM调用
        result = await self.run_llm(
            prompt=prompt,
            system_message="你是一个专业的需求分析师，负责深入分析和澄清业务需求，确保需求的完整性、一致性和明确性。提供具体的见解和建议，不要泛泛而谈。"
        )
        
        # 记录结果
        self.logger.log("\n===== 深度需求澄清结果 =====\n", role="clarifier")
        self.logger.log(result, role="clarifier")
        
        # 保存到文件
        clarification_file = self.output_dir / "deep_requirements_clarification.md"
        try:
            with open(clarification_file, "w", encoding="utf-8") as f:
                f.write(f"# 深度需求澄清分析\n\n{result}")
            self.logger.log(f"\n深度需求澄清已保存到: {clarification_file}", role="system")
        except Exception as e:
            self.logger.log(f"保存深度澄清结果时出错: {e}", role="system")
        
        return {"clarification_result": result}
    
    async def deep_reasoning(self, requirement_analysis: Dict[str, Any] = None, architecture_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行深度架构推理
        
        Args:
            requirement_analysis: 现有的需求分析结果
            architecture_analysis: 现有的架构分析结果
            
        Returns:
            深度推理的结果
        """
        self.logger.log("\n===== 开始深度架构推理 =====\n", role="system")
        
        # 如果没有提供分析结果，使用架构管理器中的信息
        if not requirement_analysis and hasattr(self, 'architecture_manager'):
            requirement_analysis = {
                "requirements": self.architecture_manager.requirements,
                "system_overview": self.architecture_manager.system_overview,
                "functional_requirements": self.architecture_manager.functional_requirements
            }
        
        if not requirement_analysis or not requirement_analysis.get("requirements"):
            self.logger.log("⚠️ 没有需求数据可供深度架构推理。请先完成需求分析。", role="system")
            return {}
        
        if not architecture_analysis and hasattr(self, 'architecture_manager'):
            architecture_analysis = {
                "modules": self.architecture_manager.modules,
                "architecture_pattern": self.architecture_manager.architecture_pattern,
                "technology_stack": self.architecture_manager.technology_stack
            }
        
        # 构建需求和架构摘要
        requirements_str = "核心需求:\n"
        for idx, req in enumerate(requirement_analysis.get("requirements", [])[:10]):  # 限制为前10个需求
            title = req.get("title", "") or req.get("name", f"需求 {idx+1}")
            desc = req.get("description", "无描述")
            requirements_str += f"- {title}: {desc}\n"
        
        architecture_str = ""
        if architecture_analysis:
            if architecture_analysis.get("architecture_pattern"):
                pattern = architecture_analysis.get("architecture_pattern", {})
                architecture_str += f"\n架构模式: {pattern.get('name', '未指定')}\n"
                architecture_str += f"模式描述: {pattern.get('description', '无描述')}\n"
            
            if architecture_analysis.get("modules"):
                architecture_str += "\n核心模块:\n"
                for idx, module in enumerate(architecture_analysis.get("modules", [])[:10]):  # 限制为前10个模块
                    name = module.get("name", f"模块 {idx+1}")
                    desc = module.get("description", "无描述")
                    architecture_str += f"- {name}: {desc}\n"
            
            if architecture_analysis.get("technology_stack"):
                architecture_str += "\n技术栈:\n"
                tech_stack = architecture_analysis.get("technology_stack", {})
                if isinstance(tech_stack, dict):
                    for category, techs in tech_stack.items():
                        if isinstance(techs, list):
                            architecture_str += f"- {category}: {', '.join(techs)}\n"
                        else:
                            architecture_str += f"- {category}: {techs}\n"
                elif isinstance(tech_stack, list):
                    for tech in tech_stack:
                        architecture_str += f"- {tech}\n"
        
        # 构建深度推理的提示
        prompt = (
            f"请基于以下需求和初步架构设计，进行深度架构推理:\n\n"
            f"{requirements_str}\n"
            f"{architecture_str}\n\n"
            f"请详细阐述以下内容:\n"
            f"1. 架构详细设计，包括各模块的具体职责和实现方案\n"
            f"2. 组件间通信和数据流\n"
            f"3. 关键接口设计\n"
            f"4. 安全性、可扩展性和性能优化方案\n"
            f"5. 潜在技术风险及缓解策略\n"
            f"6. 部署和运维考虑\n\n"
            f"请提供详尽的技术说明和具体实现建议，避免泛泛而谈。"
        )
        
        self.logger.log("正在进行深度架构推理...", role="system")
        
        # 执行LLM调用
        result = await self.run_llm(
            prompt=prompt,
            system_message="你是一个专业的架构设计师，负责基于业务需求设计高质量的系统架构，确保架构的可扩展性、可维护性和性能。提供具体的技术建议和实现方案，不要泛泛而谈。"
        )
        
        # 记录结果
        self.logger.log("\n===== 深度架构推理结果 =====\n", role="clarifier")
        self.logger.log(result, role="clarifier")
        
        # 保存到文件
        reasoning_file = self.output_dir / "deep_architecture_reasoning.md"
        try:
            with open(reasoning_file, "w", encoding="utf-8") as f:
                f.write(f"# 深度架构推理\n\n{result}")
            self.logger.log(f"\n深度架构推理已保存到: {reasoning_file}", role="system")
        except Exception as e:
            self.logger.log(f"保存深度推理结果时出错: {e}", role="system")
        
        return {"reasoning_result": result}
    
    async def _read_all_markdown_files(self) -> Dict[str, str]:
        """读取输入文件夹中的所有Markdown文件
        
        Returns:
            包含所有文档内容的字典，键为文件名，值为文件内容
        """
        documents = {}
        
        # 获取所有Markdown文件
        md_files = list(self.input_dir.glob('**/*.md'))
        
        for file_path in md_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                # 使用相对路径作为文档名
                relative_path = file_path.relative_to(self.input_dir)
                documents[str(relative_path)] = content
                self.logger.log(f"- 已读取文档：{relative_path}", role="system")
            except Exception as e:
                self.logger.log(f"⚠️ 读取文件 {file_path} 时出错：{e}", role="system")
        
        return documents
    
    async def _interactive_clarification(self):
        """交互式需求澄清"""
        self.logger.log("\n💬 开始交互式需求澄清...\n", role="system")
        
        # 这里实现交互式需求澄清的逻辑
        # TODO: 实现交互式需求澄清
        
        self.logger.log("交互式需求澄清功能尚未实现。请使用文件解析模式。", role="system")
    
    async def run_llm(self, prompt: str, **kwargs) -> Any:
        """运行LLM，使用llm_executor中的run_prompt函数
        
        Args:
            prompt: 提示词
            kwargs: 其他参数（如 parse_response）
        Returns:
            LLM的响应
        """
        try:
            result = await run_prompt(
                chat=self.llm_chat,
                user_message=prompt,
                model="gpt-4o",
                use_mock=self.llm_chat is None,
                **kwargs
            )
            if isinstance(result, dict) and "error" in result and "status" in result:
                self.logger.log(f"⚠️ LLM调用返回错误: {result['error']}", role="system")
                self.logger.log("将使用模拟响应代替", role="system")
                result = await run_prompt(
                    chat=None,
                    user_message=prompt,
                    model="gpt-4o",
                    use_mock=True,
                    return_json="json" in prompt.lower(),
                    **kwargs
                )
            return result
        except Exception as e:
            self.logger.log(f"⚠️ 调用LLM时出错: {str(e)}", role="system")
            return {
                "error": f"调用LLM出错: {str(e)}",
                "message": "LLM调用失败，请稍后重试"
            }

    async def integrate_legacy_modules(self, input_path: str = "data/input", output_path: str = "data/output"):
        """集成legacy clarifier的功能，处理模块
        
        Args:
            input_path: 输入文件目录
            output_path: 输出目录
        """
        from pathlib import Path
        import json
        
        self.logger.log("\n🔄 开始集成legacy模块...", role="system")
        
        if not hasattr(self, 'architecture_manager'):
            self.architecture_manager = ArchitectureManager()
            self.logger.log("✅ 已创建架构管理器", role="system")
        
        output_modules_path = Path(output_path) / "modules"
        output_modules_path.mkdir(parents=True, exist_ok=True)
        
        modules_count = 0
        for module_dir in output_modules_path.iterdir():
            if not module_dir.is_dir():
                continue
                
            summary_path = module_dir / "full_summary.json"
            if not summary_path.exists():
                continue
                
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    module_data = json.load(f)
                    
                module_name = module_data.get('module_name', 'unknown')
                self.logger.log(f"🔍 集成模块: {module_name}", role="system")
                
                await self.architecture_manager.process_new_module(
                    module_data, 
                    module_data.get("requirements", [])
                )
                modules_count += 1
            except Exception as e:
                self.logger.log(f"⚠️ 处理模块 {module_dir.name} 时出错: {str(e)}", role="system")
        
        self.logger.log(f"✅ 集成legacy模块完成，共处理 {modules_count} 个模块", role="system")
        
        from .architecture_reasoner import ArchitectureReasoner
        reasoner = ArchitectureReasoner(architecture_manager=self.architecture_manager)
        cycles = reasoner._check_global_circular_dependencies()
        
        if cycles:
            self.logger.log(f"⚠️ 检测到 {len(cycles)} 个循环依赖:", role="system")
            for cycle in cycles:
                self.logger.log(f"  - {cycle}", role="system")
        else:
            self.logger.log("✅ 未检测到循环依赖", role="system")
            
        return {
            "modules_count": modules_count,
            "circular_dependencies": cycles
        }
    
    async def generate_granular_modules(self, input_path: str = "data/input", output_path: str = "data/output"):
        """生成细粒度架构模块
        
        从输入文档中提取细粒度模块，生成多维度索引，并检查架构问题
        
        Args:
            input_path: 输入文件目录
            output_path: 输出目录
            
        Returns:
            包含模块数量和问题数量的字典
        """
        from pathlib import Path
        import json
        import os
        
        self.logger.log("\n🔍 开始生成细粒度架构模块...", role="system")
        
        if not hasattr(self, 'architecture_manager'):
            self.architecture_manager = ArchitectureManager()
            self.logger.log("✅ 已创建架构管理器", role="system")
        
        self.logger.log("📂 正在加载输入文档...", role="system")
        documents = await self._read_all_markdown_files(input_path)
        
        if not documents:
            self.logger.log("❌ 未找到输入文档", role="system")
            return {"modules_count": 0, "issues_count": 0}
            
        self.logger.log(f"✅ 已加载 {len(documents)} 个文档", role="system")
        
        # 将所有文档内容合并
        all_content = ""
        for doc_name, content in documents.items():
            all_content += f"\n\n# {doc_name}\n{content}"
        
        self.logger.log("🧠 正在分析文档，提取细粒度模块...", role="system")
        
        architecture_layers = [
            "表现层 (Presentation)",
            "业务层 (Business)",
            "数据层 (Data)",
            "基础设施层 (Infrastructure)"
        ]
        
        try:
            modules = await self.requirement_analyzer.analyze_granular_modules(
                all_content, 
                self.run_llm,
                architecture_layers
            )
            
            if not modules:
                self.logger.log("❌ 未能从文档中提取模块", role="system")
                return {"modules_count": 0, "issues_count": 0}
                
            self.logger.log(f"✅ 从文档中提取了 {len(modules)} 个细粒度模块", role="system")
        except Exception as e:
            self.logger.log(f"❌ 提取模块时出错: {str(e)}", role="system")
            return {"modules_count": 0, "issues_count": 0}
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        modules_count = 0
        for module in modules:
            module_name = module.get("module_name")
            if not module_name:
                continue
                
            try:
                await self.architecture_manager.process_new_module(
                    module, 
                    module.get("requirements", [])
                )
                modules_count += 1
                self.logger.log(f"✅ 处理模块: {module_name}", role="system")
            except Exception as e:
                self.logger.log(f"❌ 处理模块 {module_name} 时出错: {str(e)}", role="system")
        
        self.logger.log(f"✅ 共处理了 {modules_count} 个模块", role="system")
        
        self.logger.log("📊 正在生成多维度索引...", role="system")
        
        try:
            from .index_generator import MultiDimensionalIndexGenerator
            
            index_generator = MultiDimensionalIndexGenerator(
                modules_dir=Path(output_path) / "modules",
                output_dir=output_dir
            )
            indices = index_generator.generate_indices()
            self.logger.log("✅ 已生成多维度索引", role="system")
        except Exception as e:
            self.logger.log(f"❌ 生成多维度索引失败: {str(e)}", role="system")
        
        self.logger.log("🔍 正在检查架构问题...", role="system")
        
        try:
            from .architecture_reasoner import ArchitectureReasoner
            
            reasoner = ArchitectureReasoner(architecture_manager=self.architecture_manager, logger=self.logger)
            issues = await reasoner.check_all_issues()
            
            issues_count = sum(len(issue_list) for issue_list in issues.values())
            
            if issues_count > 0:
                self.logger.log(f"⚠️ 检测到 {issues_count} 个架构问题:", role="system")
                for issue_type, issue_list in issues.items():
                    if issue_list:
                        self.logger.log(f"  - {issue_type}: {len(issue_list)} 个问题", role="system")
            else:
                self.logger.log("✅ 未检测到架构问题", role="system")
                
            issues_dir = output_dir / "issues"
            issues_dir.mkdir(parents=True, exist_ok=True)
            
            with open(issues_dir / "architecture_issues.json", "w", encoding="utf-8") as f:
                json.dump(issues, f, ensure_ascii=False, indent=2)
            self.logger.log(f"✅ 已保存架构问题报告到 {issues_dir / 'architecture_issues.json'}", role="system")
        except Exception as e:
            self.logger.log(f"❌ 检查架构问题失败: {str(e)}", role="system")
            issues_count = 0
        
        self.logger.log("\n🎉 细粒度模块生成完成！", role="system")
        self.logger.log(f"- 共生成 {modules_count} 个模块", role="system")
        self.logger.log(f"- 检测到 {issues_count if 'issues_count' in locals() else 0} 个架构问题", role="system")
        self.logger.log(f"- 所有文件已保存到 {output_dir}", role="system")
        
        return {
            "modules_count": modules_count,
            "issues_count": issues_count if 'issues_count' in locals() else 0
        }
    
    def continue_from_user(self):
        if self.waiting_for_user:
            self.waiting_for_user.set()

def main():
    clarifier = Clarifier()
    asyncio.run(clarifier.start())

if __name__ == "__main__":
    main()
