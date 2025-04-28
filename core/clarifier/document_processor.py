from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import json
from llm.llm_executor import run_prompt

class DocumentProcessor:
    """负责读取和分析文档"""
    
    def __init__(self, input_path: Path = None, logger=None):
        """初始化文档处理器"""
        self.input_path = input_path or Path("data/input")
        if not self.input_path.exists():
            self.input_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    async def read_all_markdown_files(self) -> Dict[str, str]:
        """读取input目录下的所有markdown文件"""
        documents = {}
        
        if not self.input_path.exists():
            if self.logger:
                self.logger.log(f"创建输入目录：{self.input_path}", role="system")
            else:
                print(f"创建输入目录：{self.input_path}")
            self.input_path.mkdir(parents=True)
            return documents
            
        for file_path in self.input_path.glob("*.md"):
            try:
                content = file_path.read_text(encoding='utf-8')
                documents[file_path.name] = content
                if self.logger:
                    self.logger.log(f"✓ 已读取: {file_path.name}", role="system")
                else:
                    print(f"✓ 已读取: {file_path.name}")
            except Exception as e:
                if self.logger:
                    self.logger.log(f"⚠️ 读取文件 {file_path.name} 时出错: {str(e)}", role="error")
                else:
                    print(f"⚠️ 读取文件 {file_path.name} 时出错: {str(e)}")
                
        return documents
    
    async def analyze_all_documents(self, documents: Dict[str, str], llm_call) -> Dict:
        """分析所有文档并理解架构"""
        print("\n🔍 正在分析所有文档...")
        
        # 将所有文档内容组合成一个上下文
        combined_content = "\n\n=== 文档分隔符 ===\n\n".join(
            f"文件：{filename}\n\n{content}" 
            for filename, content in documents.items()
        )
        
        prompt = f"""
        请分析以下所有文档，理解系统的整体架构设计：

        {combined_content}

        请提供完整的架构分析，包括：

        1. 系统概述：
           - 核心功能和目标
           - 关键需求和约束
           - 技术选型理由

        2. 架构设计：
           - 架构模式选择
           - 系统分层
           - 模块划分
           - 关键接口

        3. 依赖关系：
           - 模块间的依赖
           - 数据流向
           - 交互模式

        4. 技术实现：
           - 具体技术栈
           - 框架选择
           - 部署方案

        5. 质量属性：
           - 性能考虑
           - 安全措施
           - 可扩展性设计

        请以JSON格式返回，包含以下结构：
        {{
            "system_overview": {{
                "core_features": [],
                "key_requirements": [],
                "technical_choices": []
            }},
            "architecture_design": {{
                "patterns": [
                    {{
                        "name": "模式名称",
                        "description": "描述",
                        "layers": [
                            {{
                                "name": "层级名称",
                                "responsibility": "职责",
                                "components": []
                            }}
                        ]
                    }}
                ],
                "key_interfaces": []
            }},
            "dependencies": {{
                "module_dependencies": [],
                "data_flows": [],
                "interaction_patterns": []
            }},
            "implementation": {{
                "tech_stack": [],
                "frameworks": [],
                "deployment": {{}}
            }},
            "quality_attributes": {{
                "performance": [],
                "security": [],
                "scalability": []
            }}
        }}
        """
        
        return await llm_call(prompt)
    
    async def extract_architecture_info(self, architecture_doc: str, llm_call) -> Dict:
        """从技术架构文档中提取架构信息"""
        prompt = f"""
        请分析以下技术架构文档，提取关键的架构信息：

        {architecture_doc}

        请提取以下信息：
        1. 已定义的架构模式
        2. 各个层级的定义和职责
        3. 模块间的依赖关系
        4. 技术选型和约束
        5. 已识别的关键模块

        返回格式为JSON：
        {{
            "architecture_patterns": [
                {{
                    "name": "模式名称",
                    "description": "模式描述",
                    "layers": [
                        {{
                            "name": "层级名称",
                            "responsibility": "职责描述",
                            "constraints": ["约束1", "约束2"]
                        }}
                    ]
                }}
            ],
            "dependencies": [
                {{
                    "from": "源模块",
                    "to": "目标模块",
                    "type": "依赖类型"
                }}
            ],
            "key_modules": [
                {{
                    "name": "模块名称",
                    "pattern": "所属模式",
                    "layer": "所属层级",
                    "description": "描述"
                }}
            ],
            "technical_constraints": [
                {{
                    "category": "约束类别",
                    "description": "具体约束",
                    "rationale": "原因"
                }}
            ]
        }}
        """
        
        return await llm_call(prompt)
    
    async def generate_mapping_doc(self, analysis: Dict, architecture_info: Dict, llm_call) -> str:
        """生成需求到架构的映射文档"""
        prompt = f"""
        基于以下分析结果和架构信息，生成需求到架构的映射文档：

        需求分析：
        {json.dumps(analysis, ensure_ascii=False, indent=2)}

        架构信息：
        {json.dumps(architecture_info, ensure_ascii=False, indent=2)}
        
        请生成一个清晰的映射文档，包括：
        1. 每个需求如何映射到具体的架构模式和层级
        2. 需要创建的具体模块
        3. 模块间的交互方式
        4. 技术实现建议

        返回Markdown格式的文档。
        """
        
        mapping_content = await llm_call(prompt)
        
        # 保存映射文档
        mapping_file = self.input_path / "architecture_mapping.md"
        mapping_file.write_text(mapping_content)
        
        return mapping_content 