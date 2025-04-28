import os
import json
from pathlib import Path
from typing import Dict, Any, Callable, Awaitable
from llm.llm_executor import run_prompt
from llm.prompt_cleaner import clean_code_output


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