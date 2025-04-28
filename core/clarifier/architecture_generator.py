from pathlib import Path
import json
from typing import Dict, List, Any, Callable, Awaitable
from llm.llm_executor import run_prompt
from llm.prompt_cleaner import clean_code_output


class ArchitectureGenerator:
    """架构生成器，负责生成架构文档"""

    def __init__(self, logger=None):
        self.output_dir = Path("data/output/architecture")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    async def analyze_architecture_needs(self, requirement_analysis: Dict, llm_call: Callable) -> Dict:
        """根据需求分析结果，分析架构需求
        
        Args:
            requirement_analysis: 需求分析结果
            llm_call: LLM调用函数
            
        Returns:
            架构需求分析结果
        """
        if self.logger:
            self.logger.log("\n🔍 正在分析架构需求...", role="system")
        else:
            print("\n🔍 正在分析架构需求...")
        
        prompt = f"""
        基于以下需求分析结果，确定系统架构需求：
        
        {json.dumps(requirement_analysis, ensure_ascii=False, indent=2)}
        
        请分析并确定适合该系统的架构模式、层次结构和技术选型。返回以下信息：
        
        1. 推荐的架构模式（如微服务、单体、事件驱动等）及理由
        2. 系统分层（如前端、后端、数据层等）及每层的职责
        3. 核心组件及其交互方式
        4. 关键接口定义
        5. 技术栈选择及理由
        6. 部署架构建议
        7. 可扩展性和性能考虑
        
        以JSON格式返回，结构如下：
        
        {{
            "architecture_pattern": {{
                "name": "架构模式名称",
                "rationale": "选择理由",
                "advantages": ["优势1", "优势2"],
                "challenges": ["挑战1", "挑战2"]
            }},
            "layers": [
                {{
                    "name": "层名称",
                    "responsibilities": ["职责1", "职责2"],
                    "components": ["组件1", "组件2"]
                }}
            ],
            "core_components": [
                {{
                    "name": "组件名称",
                    "description": "组件描述",
                    "responsibilities": ["职责1", "职责2"],
                    "interfaces": ["接口1", "接口2"]
                }}
            ],
            "key_interfaces": [
                {{
                    "name": "接口名称",
                    "description": "接口描述",
                    "operations": ["操作1", "操作2"],
                    "data_format": "数据格式"
                }}
            ],
            "technology_stack": [
                {{
                    "category": "类别",
                    "technology": "技术名称",
                    "rationale": "选择理由"
                }}
            ],
            "deployment_architecture": {{
                "model": "部署模型",
                "environments": ["环境1", "环境2"],
                "infrastructure": "基础设施描述"
            }},
            "scalability_considerations": [
                "考虑点1", "考虑点2"
            ]
        }}
        
        确保您的建议与需求分析结果一致，并考虑所有功能和非功能需求。
        
        **请严格只返回JSON，不要有任何解释、说明、注释或多余内容。**
        """
        
        # 调用LLM获取分析结果
        if self.logger:
            self.logger.log(f"LLM输入：{prompt[:200]}...", role="llm_prompt")
        result = await llm_call(prompt, parse_response=clean_code_output)
        if self.logger:
            self.logger.log(f"LLM响应：{str(result)[:200]}...", role="llm_response")
        
        # 如果结果是字符串，尝试解析JSON
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception as e:
                if self.logger:
                    self.logger.log(f"警告：架构需求分析结果解析失败: {e}", role="error")
                    self.logger.log("LLM原始返回内容如下：\n" + result, role="llm_response")
                else:
                    print(f"警告：架构需求分析结果解析失败: {e}")
                    print("LLM原始返回内容如下：\n" + result)
                # 直接返回原始内容，方便用户人工判断
                return result
        
        return result
    
    async def generate_architecture_documents(self, requirement_analysis: Dict, architecture_analysis: Dict, llm_call: Callable):
        """生成架构文档
        
        Args:
            requirement_analysis: 需求分析结果
            architecture_analysis: 架构分析结果
            llm_call: LLM调用函数
        """
        if self.logger:
            self.logger.log("\n📝 生成架构文档...", role="system")
        else:
            print("\n📝 生成架构文档...")
        await self._generate_architecture_overview(requirement_analysis, architecture_analysis, llm_call)
        await self._generate_detailed_design(requirement_analysis, architecture_analysis, llm_call)
        await self._generate_interface_documentation(architecture_analysis, llm_call)
        await self._generate_deployment_documentation(architecture_analysis, llm_call)
        if self.logger:
            self.logger.log(f"✅ 架构文档生成完成！已保存到：{self.output_dir}", role="system")
        else:
            print(f"✅ 架构文档生成完成！已保存到：{self.output_dir}")
    
    async def _generate_architecture_overview(self, requirement_analysis: Dict, architecture_analysis: Dict, llm_call: Callable):
        """生成架构概述文档
        
        Args:
            requirement_analysis: 需求分析结果
            architecture_analysis: 架构分析结果
            llm_call: LLM调用函数
        """
        if self.logger:
            self.logger.log("- 生成架构概述文档...", role="system")
        else:
            print("- 生成架构概述文档...")
        
        prompt = f"""
        基于以下需求分析和架构分析结果，生成一个架构概述文档：
        
        需求分析：
        {json.dumps(requirement_analysis, ensure_ascii=False, indent=2)}
        
        架构分析：
        {json.dumps(architecture_analysis, ensure_ascii=False, indent=2)}
        
        请生成一个Markdown格式的架构概述文档，包括：
        
        1. 引言
           - 文档目的
           - 系统背景
           - 架构目标
           
        2. 架构决策
           - 所选架构模式及理由
           - 关键设计决策
           - 备选方案分析
           
        3. 系统概述
           - 高层架构图（用文本描述）
           - 主要组件
           - 系统边界
           - 外部依赖
           
        4. 架构特性
           - 可扩展性
           - 性能
           - 安全性
           - 可维护性
           - 容错性
           
        5. 技术栈
           - 选型及理由
           - 版本信息
           
        确保文档清晰、简洁，并与需求和架构分析保持一致。
        """
        
        overview_content = await llm_call(prompt)
        
        # 保存架构概述文档
        overview_file = self.output_dir / "01_architecture_overview.md"
        
        # 如果结果是字典，转换为字符串
        if isinstance(overview_content, dict):
            overview_content = json.dumps(overview_content, ensure_ascii=False, indent=2)
            
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write(overview_content)
        
        if self.logger:
            self.logger.log(f"  ✓ 架构概述文档已保存到：{overview_file}", role="system")
        else:
            print(f"  ✓ 架构概述文档已保存到：{overview_file}")
    
    async def _generate_detailed_design(self, requirement_analysis: Dict, architecture_analysis: Dict, llm_call: Callable):
        """生成详细设计文档
        
        Args:
            requirement_analysis: 需求分析结果
            architecture_analysis: 架构分析结果
            llm_call: LLM调用函数
        """
        if self.logger:
            self.logger.log("- 生成详细设计文档...", role="system")
        else:
            print("- 生成详细设计文档...")
        
        prompt = f"""
        基于以下需求分析和架构分析结果，生成一个详细设计文档：
        
        需求分析：
        {json.dumps(requirement_analysis, ensure_ascii=False, indent=2)}
        
        架构分析：
        {json.dumps(architecture_analysis, ensure_ascii=False, indent=2)}
        
        请生成一个Markdown格式的详细设计文档，包括：
        
        1. 系统分层
           - 各层职责
           - 层间依赖
           - 层内组件
           
        2. 核心组件详细设计
           - 每个组件的详细描述
           - 组件职责
           - 组件依赖
           - 关键算法和数据结构
           - 状态管理
           
        3. 数据模型
           - 主要实体
           - 实体关系
           - 数据流
           
        4. 异常处理
           - 错误处理策略
           - 日志和监控
           
        5. 安全设计
           - 认证与授权
           - 数据安全
           - 通信安全
           
        确保文档详细、准确，并与需求和架构分析保持一致。为每个组件提供足够的细节，使开发团队能够基于此文档进行实现。
        """
        
        design_content = await llm_call(prompt)
        
        # 保存详细设计文档
        design_file = self.output_dir / "02_detailed_design.md"
        
        # 如果结果是字典，转换为字符串
        if isinstance(design_content, dict):
            design_content = json.dumps(design_content, ensure_ascii=False, indent=2)
            
        with open(design_file, 'w', encoding='utf-8') as f:
            f.write(design_content)
        
        if self.logger:
            self.logger.log(f"  ✓ 详细设计文档已保存到：{design_file}", role="system")
        else:
            print(f"  ✓ 详细设计文档已保存到：{design_file}")
    
    async def _generate_interface_documentation(self, architecture_analysis: Dict, llm_call: Callable):
        """生成接口文档
        
        Args:
            architecture_analysis: 架构分析结果
            llm_call: LLM调用函数
        """
        if self.logger:
            self.logger.log("- 生成接口文档...", role="system")
        else:
            print("- 生成接口文档...")
        
        prompt = f"""
        基于以下架构分析结果，生成一个接口文档：
        
        {json.dumps(architecture_analysis, ensure_ascii=False, indent=2)}
        
        请生成一个Markdown格式的接口文档，包括：
        
        1. 接口概述
           - 接口设计原则
           - 接口分类
           
        2. API定义
           - 对于每个API接口：
             - 接口名称
             - 接口URL/路径
             - 请求方法
             - 请求参数
             - 响应格式
             - 状态码
             - 示例请求和响应
             - 错误处理
             
        3. 内部接口
           - 组件间接口
           - 模块间通信
           - 事件定义
           
        4. 外部接口
           - 与第三方系统的集成接口
           - 数据交换格式
           
        5. 接口版本控制
           - 版本管理策略
           - 向后兼容性考虑
           
        确保文档详细、准确，为每个接口提供足够的细节，使开发团队能够基于此文档进行实现和集成。
        """
        
        interface_content = await llm_call(prompt)
        
        # 保存接口文档
        interface_file = self.output_dir / "03_interfaces.md"
        
        # 如果结果是字典，转换为字符串
        if isinstance(interface_content, dict):
            interface_content = json.dumps(interface_content, ensure_ascii=False, indent=2)
            
        with open(interface_file, 'w', encoding='utf-8') as f:
            f.write(interface_content)
        
        if self.logger:
            self.logger.log(f"  ✓ 接口文档已保存到：{interface_file}", role="system")
        else:
            print(f"  ✓ 接口文档已保存到：{interface_file}")
    
    async def _generate_deployment_documentation(self, architecture_analysis: Dict, llm_call: Callable):
        """生成部署文档
        
        Args:
            architecture_analysis: 架构分析结果
            llm_call: LLM调用函数
        """
        if self.logger:
            self.logger.log("- 生成部署文档...", role="system")
        else:
            print("- 生成部署文档...")
        
        prompt = f"""
        基于以下架构分析结果，生成一个部署文档：
        
        {json.dumps(architecture_analysis, ensure_ascii=False, indent=2)}
        
        请生成一个Markdown格式的部署文档，包括：
        
        1. 部署架构
           - 部署拓扑图（用文本描述）
           - 环境定义（开发、测试、生产）
           - 组件部署分布
           
        2. 基础设施需求
           - 服务器规格
           - 网络要求
           - 存储需求
           - 中间件和第三方服务
           
        3. 部署流程
           - 构建过程
           - 部署步骤
           - 配置管理
           - 持续集成/持续部署策略
           
        4. 运维考虑
           - 监控策略
           - 备份和恢复
           - 扩展策略
           - 故障转移
           
        5. 性能优化
           - 缓存策略
           - 负载均衡
           - 数据库优化
           
        确保文档详细、准确，为部署和运维团队提供足够的细节，使他们能够基于此文档进行系统部署和维护。
        """
        
        deployment_content = await llm_call(prompt)
        
        # 保存部署文档
        deployment_file = self.output_dir / "04_deployment.md"
        
        # 如果结果是字典，转换为字符串
        if isinstance(deployment_content, dict):
            deployment_content = json.dumps(deployment_content, ensure_ascii=False, indent=2)
            
        with open(deployment_file, 'w', encoding='utf-8') as f:
            f.write(deployment_content)
        
        if self.logger:
            self.logger.log(f"  ✓ 部署文档已保存到：{deployment_file}", role="system")
        else:
            print(f"  ✓ 部署文档已保存到：{deployment_file}")
    
    async def save_architecture_state(self, requirement_analysis: Dict, architecture_analysis: Dict):
        """保存架构状态
        
        Args:
            requirement_analysis: 需求分析结果
            architecture_analysis: 架构分析结果
        """
        if self.logger:
            self.logger.log("- 保存架构状态...", role="system")
        else:
            print("- 保存架构状态...")
        
        from datetime import datetime
        
        architecture_state = {
            "requirement_analysis": requirement_analysis,
            "architecture_analysis": architecture_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存架构状态
        state_file = self.output_dir / "architecture_state.json"
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(architecture_state, f, ensure_ascii=False, indent=2)
        
        if self.logger:
            self.logger.log(f"  ✓ 架构状态已保存到：{state_file}", role="system")
        else:
            print(f"  ✓ 架构状态已保存到：{state_file}") 