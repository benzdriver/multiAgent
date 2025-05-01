import os
import json
from pathlib import Path
from typing import Dict, Any, Callable, Awaitable, List, Optional
from core.llm.llm_executor import run_prompt
from core.llm.prompt_cleaner import clean_code_output


class RequirementAnalyzer:
    """需求分析器，用于分析需求文档并生成需求摘要"""
    
    def __init__(self, output_dir: str = "data/output", logger=None):
        """初始化需求分析器
        
        Args:
            output_dir: 输出目录
            logger: 日志记录器
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    async def analyze_requirements(self, content: str, llm_call: Callable) -> Dict[str, Any]:
        """分析需求文档内容
        
        Args:
            content: 需求文档内容
            llm_call: 调用LLM的函数
            
        Returns:
            需求分析结果
        """
        if self.logger:
            self.logger.log("📝 正在分析需求文档...", role="system")
            self.logger.log(f"LLM输入：{content[:200]}...", role="llm_prompt")
        else:
            print("📝 正在分析需求文档...")
        
        prompt = f"""
        请分析以下文档内容，提取并理解用户的需求：

        {content}

        请提供详细的需求分析，包括：

        1. 系统概述：
           - 核心目标和用途
           - 主要功能点
           - 目标用户群体

        2. 功能需求：
           - 核心功能详细描述
           - 次要功能详细描述
           - 用户交互流程

        3. 非功能需求：
           - 性能要求
           - 安全要求
           - 可用性要求
           - 可扩展性要求

        4. 约束条件：
           - 技术约束
           - 业务约束
           - 时间和资源约束

        5. 风险分析：
           - 潜在技术风险
           - 业务风险
           - 缓解策略

        6. 优先级划分：
           - 必要功能（MVP）
           - 重要功能
           - 可选功能

        请以JSON格式返回，结构如下：
        {{
            "system_overview": {{
                "core_purpose": "系统的核心目标和用途",
                "main_features": ["功能1", "功能2", ...],
                "target_users": ["用户群体1", "用户群体2", ...]
            }},
            "functional_requirements": {{
                "core_features": [
                    {{
                        "name": "功能名称",
                        "description": "详细描述",
                        "user_stories": ["用户故事1", "用户故事2", ...],
                        "acceptance_criteria": ["验收标准1", "验收标准2", ...]
                    }},
                    ...
                ],
                "secondary_features": [
                    {{
                        "name": "功能名称",
                        "description": "详细描述",
                        "user_stories": ["用户故事1", "用户故事2", ...],
                        "acceptance_criteria": ["验收标准1", "验收标准2", ...]
                    }},
                    ...
                ],
                "user_flows": [
                    {{
                        "name": "流程名称",
                        "steps": ["步骤1", "步骤2", ...],
                        "touchpoints": ["接触点1", "接触点2", ...]
                    }},
                    ...
                ]
            }},
            "non_functional_requirements": {{
                "performance": ["性能要求1", "性能要求2", ...],
                "security": ["安全要求1", "安全要求2", ...],
                "usability": ["可用性要求1", "可用性要求2", ...],
                "scalability": ["可扩展性要求1", "可扩展性要求2", ...]
            }},
            "constraints": {{
                "technical": ["技术约束1", "技术约束2", ...],
                "business": ["业务约束1", "业务约束2", ...],
                "resources": ["资源约束1", "资源约束2", ...]
            }},
            "risks": [
                {{
                    "description": "风险描述",
                    "impact": "影响程度",
                    "probability": "发生概率",
                    "mitigation": "缓解策略"
                }},
                ...
            ],
            "priority": {{
                "must_have": ["必要功能1", "必要功能2", ...],
                "should_have": ["重要功能1", "重要功能2", ...],
                "could_have": ["可选功能1", "可选功能2", ...],
                "wont_have": ["暂不考虑的功能1", "暂不考虑的功能2", ...]
            }}
        }}

        分析要确保：
        1. 全面理解文档中明确的需求
        2. 推断隐含的需求
        3. 识别可能的矛盾点
        4. 清晰划分优先级
        """
        
        try:
            # 使用传入的LLM调用函数
            result = await llm_call(prompt, parse_response=clean_code_output)
            
            if self.logger:
                self.logger.log(f"LLM响应：{str(result)[:200]}...", role="llm_response")
            
            # 如果返回的是字符串，尝试解析为JSON
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    if self.logger:
                        self.logger.log("⚠️ LLM返回的结果不是有效的JSON格式", role="error")
                    else:
                        print("⚠️ LLM返回的结果不是有效的JSON格式")
                    # 创建一个基本的结构
                    result = {
                        "error": "无法解析LLM返回的结果",
                        "raw_response": result
                    }
            
            if self.logger:
                self.logger.log("✓ 需求分析完成", role="system")
            else:
                print("✓ 需求分析完成")
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"❌ 分析需求时出错: {str(e)}", role="error")
            else:
                print(f"❌ 分析需求时出错: {str(e)}")
            return {
                "error": f"分析需求时出错: {str(e)}",
                "system_overview": {
                    "core_purpose": "未能确定",
                    "main_features": [],
                    "target_users": []
                },
                "functional_requirements": {
                    "core_features": [],
                    "secondary_features": [],
                    "user_flows": []
                },
                "non_functional_requirements": {
                    "performance": [],
                    "security": [],
                    "usability": [],
                    "scalability": []
                },
                "constraints": {
                    "technical": [],
                    "business": [],
                    "resources": []
                },
                "risks": [],
                "priority": {
                    "must_have": [],
                    "should_have": [],
                    "could_have": [],
                    "wont_have": []
                }
            }
    
    async def generate_requirement_summary(self, requirement_analysis: Dict[str, Any], llm_call=None) -> str:
        """生成需求摘要文档
        
        Args:
            requirement_analysis: 需求分析结果
            llm_call: 可选的LLM调用函数，用于生成更好的摘要文档
            
        Returns:
            生成的摘要文档路径
        """
        if self.logger:
            self.logger.log("📝 正在生成需求摘要文档...", role="system")
        else:
            print("📝 正在生成需求摘要文档...")
        
        # 创建输出目录
        requirement_dir = self.output_dir / "requirements"
        requirement_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成摘要文档路径
        summary_file = requirement_dir / "requirement_summary.md"
        
        # 如果有LLM调用函数，使用它生成更好的摘要
        if llm_call:
            prompt = f"""
            基于以下需求分析结果，生成一个清晰、结构化的需求摘要文档：

            {json.dumps(requirement_analysis, ensure_ascii=False, indent=2)}

            请生成一个Markdown格式的需求摘要文档，包括：
            1. 项目概述
            2. 核心功能与用户故事
            3. 非功能需求
            4. 约束与风险
            5. 优先级和交付计划

            文档应当清晰、专业，适合项目管理者和开发团队阅读。
            """
            
            try:
                summary_content = await llm_call(prompt)
                
                if isinstance(summary_content, dict) and "message" in summary_content:
                    summary_content = summary_content["message"]
                
            except Exception as e:
                if self.logger:
                    self.logger.log(f"⚠️ 生成摘要文档时出错: {str(e)}", role="error")
                else:
                    print(f"⚠️ 生成摘要文档时出错: {str(e)}")
                summary_content = self._generate_simple_summary(requirement_analysis)
        else:
            # 使用简单的方式生成摘要
            summary_content = self._generate_simple_summary(requirement_analysis)
        
        # 写入文件
        summary_file.write_text(summary_content, encoding="utf-8")
        
        if self.logger:
            self.logger.log(f"✓ 需求摘要文档生成完成，保存到: {summary_file}", role="system")
        else:
            print(f"✓ 需求摘要文档生成完成，保存到: {summary_file}")
        return str(summary_file)
    
    def _generate_simple_summary(self, requirement_analysis: Dict[str, Any]) -> str:
        """生成简单的需求摘要文档
        
        Args:
            requirement_analysis: 需求分析结果
            
        Returns:
            简单的需求摘要文档内容
        """
        # 如果有错误，直接返回错误信息
        if "error" in requirement_analysis:
            return f"""# 需求摘要文档

## 错误信息

{requirement_analysis["error"]}

请检查输入文档并重试。
"""
        
        # 获取系统概述
        system = requirement_analysis.get("system_overview", {})
        core_purpose = system.get("core_purpose", "未定义")
        main_features = system.get("main_features", [])
        target_users = system.get("target_users", [])
        
        # 构建功能需求部分
        func_req = requirement_analysis.get("functional_requirements", {})
        core_features = func_req.get("core_features", [])
        secondary_features = func_req.get("secondary_features", [])
        
        # 构建非功能需求部分
        non_func = requirement_analysis.get("non_functional_requirements", {})
        
        # 构建约束部分
        constraints = requirement_analysis.get("constraints", {})
        
        # 构建风险部分
        risks = requirement_analysis.get("risks", [])
        
        # 构建优先级部分
        priority = requirement_analysis.get("priority", {})
        
        # 生成文档
        doc = f"""# 需求摘要文档

## 1. 项目概述

### 核心目标
{core_purpose}

### 主要功能
{"".join([f"- {feature}\\n" for feature in main_features])}

### 目标用户
{"".join([f"- {user}\\n" for user in target_users])}

## 2. 功能需求

### 核心功能
"""
        
        for feature in core_features:
            name = feature.get("name", "未命名功能")
            desc = feature.get("description", "无描述")
            stories = feature.get("user_stories", [])
            criteria = feature.get("acceptance_criteria", [])
            
            doc += f"""
#### {name}
{desc}

**用户故事:**
{"".join([f"- {story}\\n" for story in stories])}

**验收标准:**
{"".join([f"- {c}\\n" for c in criteria])}
"""
        
        doc += """
### 次要功能
"""
        
        for feature in secondary_features:
            name = feature.get("name", "未命名功能")
            desc = feature.get("description", "无描述")
            
            doc += f"""
#### {name}
{desc}
"""
        
        doc += """
## 3. 非功能需求

### 性能要求
"""
        doc += "".join([f"- {item}\\n" for item in non_func.get("performance", [])])
        
        doc += """
### 安全要求
"""
        doc += "".join([f"- {item}\\n" for item in non_func.get("security", [])])
        
        doc += """
### 可用性要求
"""
        doc += "".join([f"- {item}\\n" for item in non_func.get("usability", [])])
        
        doc += """
### 可扩展性要求
"""
        doc += "".join([f"- {item}\\n" for item in non_func.get("scalability", [])])
        
        doc += """
## 4. 约束条件

### 技术约束
"""
        doc += "".join([f"- {item}\\n" for item in constraints.get("technical", [])])
        
        doc += """
### 业务约束
"""
        doc += "".join([f"- {item}\\n" for item in constraints.get("business", [])])
        
        doc += """
### 资源约束
"""
        doc += "".join([f"- {item}\\n" for item in constraints.get("resources", [])])
        
        doc += """
## 5. 风险分析
"""
        
        for risk in risks:
            desc = risk.get("description", "未描述的风险")
            impact = risk.get("impact", "未评估")
            prob = risk.get("probability", "未评估")
            mitigation = risk.get("mitigation", "无缓解策略")
            
            doc += f"""
### {desc}
- **影响:** {impact}
- **概率:** {prob}
- **缓解策略:** {mitigation}
"""
        
        doc += """
## 6. 优先级划分

### 必要功能 (Must Have)
"""
        doc += "".join([f"- {item}\\n" for item in priority.get("must_have", [])])
        
        doc += """
### 重要功能 (Should Have)
"""
        doc += "".join([f"- {item}\\n" for item in priority.get("should_have", [])])
        
        doc += """
### 可选功能 (Could Have)
"""
        doc += "".join([f"- {item}\\n" for item in priority.get("could_have", [])])
        
        return doc      
        
    def _validate_and_fix_module_name(self, module: Dict[str, Any]) -> None:
        """验证并修复模块名称，确保符合命名规范
        
        Args:
            module: 模块信息字典
        """
        module_name = module.get("module_name", "")
        module_type = module.get("module_type", "")
        layer = module.get("layer", "")
        domain = module.get("domain", "")
        
        naming_conventions = {
            "表现层": {
                "UI组件": "{}UI",
                "页面": "{}Page",
                "视图": "{}View",
                "布局组件": "{}Layout",
                "组件": "{}Component"
            },
            "业务层": {
                "服务": "{}Service",
                "控制器": "{}Controller",
                "验证器": "{}Validator",
                "中间件": "{}Middleware",
                "管理器": "{}Manager",
                "处理器": "{}Processor"
            },
            "数据层": {
                "模型": "{}Model",
                "仓储": "{}Repository",
                "数据访问对象": "{}DAO",
                "数据传输对象": "{}DTO",
                "实体": "{}Entity"
            },
            "基础设施层": {
                "API客户端": "{}Client",
                "存储服务": "{}Storage",
                "认证服务": "{}Auth",
                "日志服务": "{}Logger",
                "配置": "{}Config",
                "工具": "{}Util"
            }
        }
        
        english_layer_map = {
            "表现层": "Presentation",
            "业务层": "Business",
            "数据层": "Data",
            "基础设施层": "Infrastructure"
        }
        
        english_type_map = {
            "UI组件": "UIComponent",
            "页面": "Page",
            "视图": "View",
            "布局组件": "Layout",
            "组件": "Component",
            "服务": "Service",
            "控制器": "Controller",
            "验证器": "Validator",
            "中间件": "Middleware",
            "管理器": "Manager",
            "处理器": "Processor",
            "模型": "Model",
            "仓储": "Repository",
            "数据访问对象": "DAO",
            "数据传输对象": "DTO",
            "实体": "Entity",
            "API客户端": "Client",
            "存储服务": "Storage",
            "认证服务": "Auth",
            "日志服务": "Logger",
            "配置": "Config",
            "工具": "Util"
        }
        
        if layer in naming_conventions and module_type in naming_conventions[layer]:
            functionality = module_name
            for suffix in english_type_map.values():
                if module_name.endswith(suffix):
                    functionality = module_name[:-len(suffix)]
                    break
            
            pattern = naming_conventions[layer][module_type]
            new_name = pattern.format(functionality)
            
            module["module_name"] = new_name
            
            if self.logger:
                if new_name != module_name:
                    self.logger.log(f"✓ 修复模块名称: {module_name} -> {new_name}", role="system")
            else:
                if new_name != module_name:
                    print(f"✓ 修复模块名称: {module_name} -> {new_name}")
            
            layer_en = english_layer_map.get(layer, layer)
            module_type_en = english_type_map.get(module_type, module_type)
            domain_clean = module_name.lower().replace(" ", "_")
            
            if layer_en == "Presentation":
                target_path = f"frontend/presentation/{domain_clean}"
            elif layer_en == "Business":
                target_path = f"backend/business/{domain_clean}"
            elif layer_en == "Data":
                target_path = f"backend/data/{domain_clean}"
            elif layer_en == "Infrastructure":
                target_path = f"backend/infrastructure/{domain_clean}"
            else:
                target_path = f"misc/{domain_clean}"
            
            module["target_path"] = target_path
    
    async def analyze_granular_modules(self, content: str, llm_call: Callable, architecture_layers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """分析文档内容，提取细粒度模块
        
        Args:
            content: 需求文档或架构文档内容
            llm_call: 调用LLM的函数
            architecture_layers: 可选的架构层级列表，用于指导模块提取
            
        Returns:
            细粒度模块列表，每个模块包含详细信息
        """
        if self.logger:
            self.logger.log("🔍 正在提取细粒度模块...", role="system")
            self.logger.log(f"LLM输入：{content[:200]}...", role="llm_prompt")
        else:
            print("🔍 正在提取细粒度模块...")
        
        layers_prompt = ""
        if architecture_layers:
            layers_prompt = "请基于以下架构层级提取模块：\n"
            for layer in architecture_layers:
                layers_prompt += f"- {layer}\n"
        else:
            layers_prompt = """请基于以下常见架构层级提取模块：
- 表现层 (Presentation)：UI组件、页面、视图等
- 业务层 (Business)：服务、控制器、用例等
- 数据层 (Data)：模型、仓储、数据访问等
- 基础设施层 (Infrastructure)：工具、配置、中间件等
"""
        
        naming_conventions = """
请严格遵循以下模块命名规范：

1. 表现层 (Presentation) 模块命名规范：
   - UI组件 (UI Components): 使用 "{功能}UI" 或 "{功能}Component"，例如：LoginUI, UserProfileComponent
   - 页面 (Pages): 使用 "{功能}Page"，例如：DashboardPage, SettingsPage
   - 视图 (Views): 使用 "{功能}View"，例如：ProductView, OrderView
   - 布局组件 (Layout Components): 使用 "{功能}Layout"，例如：MainLayout, SidebarLayout

2. 业务层 (Business) 模块命名规范：
   - 服务 (Services): 使用 "{功能}Service"，例如：AuthenticationService, NotificationService
   - 控制器 (Controllers): 使用 "{功能}Controller"，例如：UserController, ProductController
   - 验证器 (Validators): 使用 "{功能}Validator"，例如：InputValidator, FormValidator
   - 中间件 (Middleware): 使用 "{功能}Middleware"，例如：AuthMiddleware, LoggingMiddleware

3. 数据层 (Data) 模块命名规范：
   - 模型 (Models): 使用 "{实体}Model"，例如：UserModel, ProductModel
   - 仓储 (Repositories): 使用 "{实体}Repository"，例如：UserRepository, OrderRepository
   - 数据访问对象 (Data Access Objects): 使用 "{实体}DAO"，例如：UserDAO, ProductDAO
   - 数据传输对象 (Data Transfer Objects): 使用 "{实体}DTO"，例如：UserDTO, ProductDTO

4. 基础设施层 (Infrastructure) 模块命名规范：
   - API客户端 (API Clients): 使用 "{服务}Client"，例如：PaymentClient, EmailClient
   - 存储服务 (Storage Services): 使用 "{功能}Storage"，例如：FileStorage, CacheStorage
   - 认证服务 (Authentication Services): 使用 "{功能}Auth"，例如：JwtAuth, OAuthProvider
   - 日志服务 (Logging Services): 使用 "{功能}Logger"，例如：SystemLogger, EventLogger

请确保每个模块的命名都遵循上述规范，并且名称能够清晰表达模块的功能和类型。
"""
        
        prompt = f"""
        请分析以下文档内容，提取细粒度的架构模块：

        {content}

        {layers_prompt}
        
        {naming_conventions}

        对于每个识别出的模块，请提供以下信息：
        1. 模块名称：按照上述命名规范，清晰、具体的名称
        2. 模块类型：UI组件、页面、服务、控制器、模型、仓储等
        3. 模块职责：该模块的主要职责和功能
        4. 所属层级：表现层、业务层、数据层、基础设施层等
        5. 所属领域：认证、用户管理、评估、报告等
        6. 依赖关系：该模块依赖的其他模块
        7. 相关需求：与该模块相关的需求
        8. 技术栈：实现该模块可能使用的技术

        请以JSON格式返回，结构如下：
        [
            {{
                "module_name": "模块名称",
                "module_type": "模块类型",
                "responsibilities": ["职责1", "职责2", ...],
                "layer": "所属层级",
                "domain": "所属领域",
                "dependencies": ["依赖1", "依赖2", ...],
                "requirements": ["需求1", "需求2", ...],
                "technology_stack": ["技术1", "技术2", ...]
            }},
            ...
        ]

        请确保：
        1. 提取的模块粒度适中，既不过于宏观也不过于微观
        2. 模块名称必须严格遵循上述命名规范
        3. 模块之间的依赖关系应当合理
        4. 每个模块都应当有明确的职责和边界
        5. 模块应当覆盖文档中提到的所有功能和需求
        6. 每个层级都应该有多种类型的模块，不要只生成Service类型的模块
        """
        
        try:
            # 使用传入的LLM调用函数
            result = await llm_call(prompt, parse_response=clean_code_output)
            
            if self.logger:
                self.logger.log(f"LLM响应：{str(result)[:200]}...", role="llm_response")
            
            # 如果返回的是字符串，尝试解析为JSON
            if isinstance(result, str):
                import re
                json_array_match = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
                
                if json_array_match:
                    json_str = json_array_match.group(0)
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError:
                            if self.logger:
                                self.logger.log("⚠️ LLM返回的结果不是有效的JSON格式", role="error")
                                self.logger.log(f"尝试解析的内容: {result[:200]}...", role="debug")
                            else:
                                print("⚠️ LLM返回的结果不是有效的JSON格式")
                            # 创建一个基本的结构
                            result = []
                else:
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        if self.logger:
                            self.logger.log("⚠️ LLM返回的结果不是有效的JSON格式", role="error")
                            self.logger.log(f"尝试解析的内容: {result[:200]}...", role="debug")
                        else:
                            print("⚠️ LLM返回的结果不是有效的JSON格式")
                        # 创建一个基本的结构
                        result = []
            
            if not isinstance(result, list):
                if self.logger:
                    self.logger.log("⚠️ LLM返回的结果不是有效的模块列表", role="error")
                else:
                    print("⚠️ LLM返回的结果不是有效的模块列表")
                result = []
            
            for module in result:
                self._validate_and_fix_module_name(module)
            
            if self.logger:
                self.logger.log(f"✓ 已提取 {len(result)} 个细粒度模块", role="system")
            else:
                print(f"✓ 已提取 {len(result)} 个细粒度模块")
            
            self._save_granular_modules(result)
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"❌ 提取细粒度模块时出错: {str(e)}", role="error")
            else:
                print(f"❌ 提取细粒度模块时出错: {str(e)}")
            return []
    
    def _save_granular_modules(self, modules: List[Dict[str, Any]]) -> None:
        """保存提取的细粒度模块
        
        Args:
            modules: 细粒度模块列表
        """
        try:
            # 创建输出目录
            granular_modules_dir = self.output_dir / "granular_modules"
            granular_modules_dir.mkdir(parents=True, exist_ok=True)
            
            all_modules_file = granular_modules_dir / "all_modules.json"
            with open(all_modules_file, "w", encoding="utf-8") as f:
                json.dump(modules, f, ensure_ascii=False, indent=2)
            
            if self.logger:
                self.logger.log(f"✓ 已保存所有模块到: {all_modules_file}", role="system")
            else:
                print(f"✓ 已保存所有模块到: {all_modules_file}")
            
            layers = {}
            for module in modules:
                layer = module.get("layer", "未分类")
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(module)
            
            for layer, layer_modules in layers.items():
                layer_dir = granular_modules_dir / layer.replace(" ", "_").replace("/", "_")
                layer_dir.mkdir(parents=True, exist_ok=True)
                
                layer_file = layer_dir / "modules.json"
                with open(layer_file, "w", encoding="utf-8") as f:
                    json.dump(layer_modules, f, ensure_ascii=False, indent=2)
                
                if self.logger:
                    self.logger.log(f"✓ 已保存 {layer} 层模块到: {layer_file}", role="system")
                else:
                    print(f"✓ 已保存 {layer} 层模块到: {layer_file}")
                
                for module in layer_modules:
                    module_name = module.get("module_name", "未命名模块")
                    module_dir = layer_dir / module_name.replace(" ", "_").replace("/", "_")
                    module_dir.mkdir(parents=True, exist_ok=True)
                    
                    summary_file = module_dir / "full_summary.json"
                    with open(summary_file, "w", encoding="utf-8") as f:
                        json.dump(module, f, ensure_ascii=False, indent=2)
                    
                    if self.logger:
                        self.logger.log(f"✓ 已保存模块 {module_name} 的full_summary.json", role="system")
                    else:
                        print(f"✓ 已保存模块 {module_name} 的full_summary.json")
        
        except Exception as e:
            if self.logger:
                self.logger.log(f"❌ 保存细粒度模块时出错: {str(e)}", role="error")
            else:
                print(f"❌ 保存细粒度模块时出错: {str(e)}")                    