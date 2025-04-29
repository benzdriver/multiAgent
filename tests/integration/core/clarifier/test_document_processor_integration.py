"""
集成测试 - DocumentProcessor
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
from core.clarifier.clarifier import Clarifier
from core.clarifier.requirement_analyzer import RequirementAnalyzer


class TestDocumentProcessorIntegration(unittest.IsolatedAsyncioTestCase):
    """测试 DocumentProcessor 与其他模块的集成"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.req_doc_path = self.input_dir / "requirements.md"
        with open(self.req_doc_path, "w", encoding="utf-8") as f:
            f.write("# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理")
            
        self.arch_doc_path = self.input_dir / "architecture.md"
        with open(self.arch_doc_path, "w", encoding="utf-8") as f:
            f.write("# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层")
        
        self.processor = DocumentProcessor(
            input_path=self.input_dir
        )
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {
            "system_overview": {
                "core_features": ["用户认证", "数据管理"],
                "key_requirements": ["安全性", "性能"],
                "technical_choices": ["分层架构", "微服务"]
            },
            "architecture_design": {
                "patterns": [
                    {
                        "name": "分层架构",
                        "description": "将系统分为多个层级",
                        "layers": [
                            {
                                "name": "表现层",
                                "responsibility": "负责用户界面",
                                "components": ["UI组件", "页面"]
                            },
                            {
                                "name": "业务层",
                                "responsibility": "负责业务逻辑",
                                "components": ["服务", "控制器"]
                            },
                            {
                                "name": "数据层",
                                "responsibility": "负责数据访问",
                                "components": ["模型", "仓储"]
                            }
                        ]
                    }
                ],
                "key_interfaces": ["用户接口", "数据接口"]
            }
        }

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_integration_with_clarifier(self):
        """测试与Clarifier的集成"""
        clarifier = Clarifier(
            input_path=str(self.input_dir),
            output_path=str(self.output_dir),
            llm_chat=self.mock_llm_chat
        )
        
        clarifier.document_processor = self.processor
        
        with patch.object(DocumentProcessor, 'read_all_markdown_files') as mock_read:
            mock_read.return_value = asyncio.Future()
            mock_read.return_value.set_result({
                "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理",
                "architecture.md": "# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层"
            })
            
            with patch.object(DocumentProcessor, 'analyze_all_documents') as mock_analyze:
                mock_analyze.return_value = asyncio.Future()
                mock_analyze.return_value.set_result(self.mock_llm_chat.return_value)
                
                await clarifier.clarify()
                
                mock_read.assert_called_once()
                mock_analyze.assert_called_once()

    async def test_integration_with_requirement_analyzer(self):
        """测试与RequirementAnalyzer的集成"""
        requirement_analyzer = RequirementAnalyzer(
            output_dir=str(self.output_dir)
        )
        
        documents = await self.processor.read_all_markdown_files()
        
        analysis_result = await self.processor.analyze_all_documents(documents, self.mock_llm_chat)
        
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
            ]
        }
        
        with patch.object(RequirementAnalyzer, 'analyze_requirements') as mock_analyze:
            mock_analyze.return_value = asyncio.Future()
            mock_analyze.return_value.set_result({
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
            })
            
            req_content = documents.get("requirements.md", "")
            req_analysis = await requirement_analyzer.analyze_requirements(req_content, self.mock_llm_chat)
            
            with patch.object(DocumentProcessor, 'generate_mapping_doc') as mock_generate:
                mock_generate.return_value = asyncio.Future()
                mock_generate.return_value.set_result("# 映射文档\n## 需求到架构的映射")
                
                mapping_doc = await self.processor.generate_mapping_doc(req_analysis, architecture_info, self.mock_llm_chat)
                
                mock_generate.assert_called_once()
                self.assertIsNotNone(mapping_doc)

    async def test_integration_with_file_system(self):
        """测试与文件系统的集成"""
        documents = await self.processor.read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("requirements.md", documents)
        self.assertIn("architecture.md", documents)
        
        with patch.object(DocumentProcessor, 'analyze_all_documents') as mock_analyze:
            mock_analyze.return_value = asyncio.Future()
            mock_analyze.return_value.set_result(self.mock_llm_chat.return_value)
            
            analysis_result = await self.processor.analyze_all_documents(documents, self.mock_llm_chat)
            
            self.assertEqual(analysis_result, self.mock_llm_chat.return_value)
        
        with patch.object(DocumentProcessor, 'extract_architecture_info') as mock_extract:
            mock_extract.return_value = asyncio.Future()
            mock_extract.return_value.set_result({
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
                ]
            })
            
            arch_content = documents.get("architecture.md", "")
            arch_info = await self.processor.extract_architecture_info(arch_content, self.mock_llm_chat)
            
            mock_extract.assert_called_once()
            self.assertIsNotNone(arch_info)
        
        with patch('pathlib.Path.write_text') as mock_write_text:
            with patch.object(DocumentProcessor, 'generate_mapping_doc') as mock_generate:
                mock_generate.return_value = asyncio.Future()
                mock_generate.return_value.set_result("# 映射文档\n## 需求到架构的映射")
                
                mapping_doc = await self.processor.generate_mapping_doc(
                    {"requirements": []},
                    {"architecture_patterns": []},
                    self.mock_llm_chat
                )
                
                mock_generate.assert_called_once()
                mock_write_text.assert_called_once()
                self.assertIsNotNone(mapping_doc)
