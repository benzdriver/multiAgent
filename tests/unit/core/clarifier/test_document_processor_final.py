"""
单元测试 - DocumentProcessor
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.document_processor import DocumentProcessor


class TestDocumentProcessor(unittest.IsolatedAsyncioTestCase):
    """测试 DocumentProcessor 类"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        self.doc1_path = self.input_dir / "test1.md"
        with open(self.doc1_path, "w", encoding="utf-8") as f:
            f.write("# 测试文档1\n## 测试标题\n测试内容")
            
        self.doc2_path = self.input_dir / "test2.md"
        with open(self.doc2_path, "w", encoding="utf-8") as f:
            f.write("# 测试文档2\n## 测试标题\n测试内容")
        
        self.processor = DocumentProcessor(
            input_path=self.input_dir
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_init(self):
        """测试初始化"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                default_processor = DocumentProcessor()
                self.assertEqual(default_processor.input_path, Path("data/input"))
                self.assertIsNone(default_processor.logger)
                mock_mkdir.assert_not_called()
        
        custom_path = Path(tempfile.mkdtemp()) / "custom_path"
        mock_logger = MagicMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                custom_processor = DocumentProcessor(input_path=custom_path, logger=mock_logger)
                self.assertEqual(custom_processor.input_path, custom_path)
                self.assertEqual(custom_processor.logger, mock_logger)
                mock_mkdir.assert_not_called()

    async def test_init_creates_dir(self):
        """测试初始化时创建目录"""
        custom_path = Path(tempfile.mkdtemp()) / "custom_path"
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                processor = DocumentProcessor(input_path=custom_path)
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    async def test_read_all_markdown_files(self):
        """测试读取所有Markdown文件"""
        documents = await self.processor.read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("test1.md", documents)
        self.assertIn("test2.md", documents)
        self.assertEqual(documents["test1.md"], "# 测试文档1\n## 测试标题\n测试内容")
        self.assertEqual(documents["test2.md"], "# 测试文档2\n## 测试标题\n测试内容")

    async def test_read_all_markdown_files_empty_dir(self):
        """测试读取空目录"""
        empty_dir = Path(tempfile.mkdtemp()) / "empty"
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                processor = DocumentProcessor(input_path=empty_dir)
                
                mock_mkdir.reset_mock()
                
                documents = await processor.read_all_markdown_files()
                
                self.assertEqual(len(documents), 0)
                mock_mkdir.assert_called_once_with(parents=True)

    async def test_read_all_markdown_files_error(self):
        """测试读取文件出错"""
        error_dir = Path(tempfile.mkdtemp()) / "error_dir"
        error_dir.mkdir(parents=True, exist_ok=True)
        error_file = error_dir / "error.md"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("Error content")
        
        processor = DocumentProcessor(input_path=error_dir)
        
        with patch.object(Path, 'read_text', side_effect=Exception("读取文件出错")):
            documents = await processor.read_all_markdown_files()
            
            self.assertEqual(len(documents), 0)
        
        shutil.rmtree(error_dir)

    async def test_analyze_all_documents(self):
        """测试分析所有文档"""
        documents = {
            "doc1.md": "# 文档1\n内容1",
            "doc2.md": "# 文档2\n内容2"
        }
        
        mock_response = {
            "system_overview": {
                "core_features": ["功能1", "功能2"],
                "key_requirements": ["需求1", "需求2"],
                "technical_choices": ["技术1", "技术2"]
            },
            "architecture_design": {
                "patterns": [
                    {
                        "name": "模式1",
                        "description": "描述1",
                        "layers": [
                            {
                                "name": "层级1",
                                "responsibility": "职责1",
                                "components": ["组件1", "组件2"]
                            }
                        ]
                    }
                ],
                "key_interfaces": ["接口1", "接口2"]
            }
        }
        
        async def mock_llm_call(prompt):
            return mock_response
            
        result = await self.processor.analyze_all_documents(documents, mock_llm_call)
        
        self.assertEqual(result, mock_response)

    async def test_extract_architecture_info(self):
        """测试提取架构信息"""
        architecture_doc = """
        
        采用分层架构模式
        
        - 表现层：负责用户界面
        - 业务层：负责业务逻辑
        - 数据层：负责数据访问
        """
        
        mock_response = {
            "architecture_patterns": [
                {
                    "name": "分层架构",
                    "description": "将系统分为多个层级",
                    "layers": [
                        {
                            "name": "表现层",
                            "responsibility": "负责用户界面",
                            "constraints": ["响应时间小于1秒"]
                        },
                        {
                            "name": "业务层",
                            "responsibility": "负责业务逻辑",
                            "constraints": ["高内聚低耦合"]
                        },
                        {
                            "name": "数据层",
                            "responsibility": "负责数据访问",
                            "constraints": ["数据一致性"]
                        }
                    ]
                }
            ],
            "dependencies": [
                {
                    "from": "表现层",
                    "to": "业务层",
                    "type": "调用"
                },
                {
                    "from": "业务层",
                    "to": "数据层",
                    "type": "调用"
                }
            ],
            "key_modules": [
                {
                    "name": "用户界面模块",
                    "pattern": "分层架构",
                    "layer": "表现层",
                    "description": "提供用户交互界面"
                },
                {
                    "name": "业务逻辑模块",
                    "pattern": "分层架构",
                    "layer": "业务层",
                    "description": "处理业务逻辑"
                },
                {
                    "name": "数据访问模块",
                    "pattern": "分层架构",
                    "layer": "数据层",
                    "description": "访问和管理数据"
                }
            ],
            "technical_constraints": [
                {
                    "category": "性能",
                    "description": "响应时间小于1秒",
                    "rationale": "提高用户体验"
                },
                {
                    "category": "安全",
                    "description": "数据加密传输",
                    "rationale": "保护用户数据"
                }
            ]
        }
        
        async def mock_llm_call(prompt):
            return mock_response
            
        result = await self.processor.extract_architecture_info(architecture_doc, mock_llm_call)
        
        self.assertEqual(result, mock_response)

    @patch('pathlib.Path.write_text')
    async def test_generate_mapping_doc(self, mock_write_text):
        """测试生成映射文档"""
        analysis = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证"
                },
                {
                    "id": "REQ-002",
                    "title": "数据管理",
                    "description": "系统应支持数据管理"
                }
            ]
        }
        
        architecture_info = {
            "architecture_patterns": [
                {
                    "name": "分层架构",
                    "description": "将系统分为多个层级",
                    "layers": [
                        {
                            "name": "表现层",
                            "responsibility": "负责用户界面"
                        },
                        {
                            "name": "业务层",
                            "responsibility": "负责业务逻辑"
                        },
                        {
                            "name": "数据层",
                            "responsibility": "负责数据访问"
                        }
                    ]
                }
            ],
            "key_modules": [
                {
                    "name": "认证模块",
                    "pattern": "分层架构",
                    "layer": "业务层",
                    "description": "处理用户认证"
                },
                {
                    "name": "数据模块",
                    "pattern": "分层架构",
                    "layer": "数据层",
                    "description": "管理数据"
                }
            ]
        }
        
        mock_mapping_content = """
        
        
        - 架构模式：分层架构
        - 层级：业务层
        - 模块：认证模块
        
        - 使用JWT进行认证
        - 实现登录和注销功能
        
        
        - 架构模式：分层架构
        - 层级：数据层
        - 模块：数据模块
        
        - 使用ORM框架
        - 实现CRUD操作
        """
        
        async def mock_llm_call(prompt):
            return mock_mapping_content
            
        result = await self.processor.generate_mapping_doc(analysis, architecture_info, mock_llm_call)
        
        self.assertEqual(result, mock_mapping_content)
        
        mock_write_text.assert_called_once_with(mock_mapping_content)
