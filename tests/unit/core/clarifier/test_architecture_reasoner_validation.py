"""
单元测试 - ArchitectureReasoner 验证方法
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime

from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.architecture_manager import ArchitectureManager


class TestArchitectureReasonerValidation(unittest.IsolatedAsyncioTestCase):
    """测试 ArchitectureReasoner 验证方法"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.arch_output_dir = self.output_dir / "architecture"
        self.arch_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.mock_architecture_manager = MagicMock()
        self.mock_architecture_manager.index.requirement_module_index = {
            "REQ-001": ["UIComponent"],
            "REQ-002": ["ServiceComponent"]
        }
        self.mock_architecture_manager.index.responsibility_index = {
            "显示界面": {
                "modules": ["UIComponent"],
                "objects": ["UI"],
                "patterns": ["MVC"]
            },
            "处理业务逻辑": {
                "modules": ["ServiceComponent"],
                "objects": ["Service"],
                "patterns": ["MVC"]
            }
        }
        self.mock_architecture_manager.index.dependency_graph = {
            "UIComponent": {
                "depends_on": ["ServiceComponent"],
                "depended_by": [],
                "pattern": "MVC",
                "layer": "presentation"
            },
            "ServiceComponent": {
                "depends_on": ["DataComponent"],
                "depended_by": ["UIComponent"],
                "pattern": "MVC",
                "layer": "business"
            },
            "DataComponent": {
                "depends_on": [],
                "depended_by": ["ServiceComponent"],
                "pattern": "MVC",
                "layer": "data"
            }
        }
        self.mock_architecture_manager.index.layer_index = {
            "presentation": {
                "UIComponent": {
                    "name": "UIComponent",
                    "responsibilities": ["显示界面"]
                }
            },
            "business": {
                "ServiceComponent": {
                    "name": "ServiceComponent",
                    "responsibilities": ["处理业务逻辑"]
                }
            },
            "data": {
                "DataComponent": {
                    "name": "DataComponent",
                    "responsibilities": ["数据访问"]
                }
            }
        }
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {"content": "模拟的LLM响应"}
        
        self.mock_logger = MagicMock()
        
        self.reasoner = ArchitectureReasoner(
            architecture_manager=self.mock_architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.mock_logger,
            output_path=self.arch_output_dir
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_validate_responsibilities(self):
        """测试验证职责"""
        result = self.reasoner._validate_responsibilities(["显示界面", "处理用户输入"])
        self.assertTrue(result)
        
        result = self.reasoner._validate_responsibilities([])
        self.assertFalse(result)
        
        result = self.reasoner._validate_responsibilities([""])
        self.assertTrue(result)

    async def test_validate_components(self):
        """测试验证组件"""
        components = [
            {"name": "UIComponent", "responsibilities": ["显示界面"]},
            {"name": "ServiceComponent", "responsibilities": ["处理业务逻辑"]}
        ]
        result = self.reasoner._validate_components(components)
        self.assertTrue(result)
        
        result = self.reasoner._validate_components([])
        self.assertFalse(result)
        
        result = self.reasoner._validate_components([{}])
        self.assertTrue(result)

    async def test_validate_dependencies(self):
        """测试验证依赖"""
        dependencies = [
            {"from": "UIComponent", "to": "ServiceComponent"},
            {"from": "ServiceComponent", "to": "DataComponent"}
        ]
        result = self.reasoner._validate_dependencies(dependencies)
        self.assertTrue(result)
        
        result = self.reasoner._validate_dependencies([])
        self.assertFalse(result)
        
        result = self.reasoner._validate_dependencies([{}])
        self.assertTrue(result)

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_responsibilities')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_components')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_with_relationships')
    async def test_validate_layer_design(self, mock_relationships, mock_components, mock_responsibilities):
        """测试验证层级设计"""
        mock_responsibilities.return_value = True
        mock_components.return_value = True
        mock_relationships.return_value = []  # 返回空列表表示没有问题
        
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": [{"name": "UIComponent", "responsibilities": ["显示界面"]}],
            "dependencies": [{"from": "UIComponent", "to": "ServiceComponent"}]
        }
        related_components = {
            "by_dependency": [{"name": "ServiceComponent", "layer": "business"}],
            "by_feature": [{"name": "DataComponent", "features": ["数据访问"]}],
            "by_keyword": [],
            "by_responsibility": []
        }
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertFalse(result["has_issues"])
        self.assertEqual(result["issues"], [])
        
        mock_responsibilities.assert_called_once_with(["显示界面", "处理用户输入"])
        mock_components.assert_called_once_with([{"name": "UIComponent", "responsibilities": ["显示界面"]}])
        mock_relationships.assert_called_once()
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = False
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0], "职责定义不完整或不清晰")
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = True
        mock_components.return_value = False
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0], "组件设计存在问题")
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = True
        mock_components.return_value = True
        mock_relationships.return_value = ["关系问题1", "关系问题2"]
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 2)
        self.assertEqual(result["issues"][0], "关系问题1")
        self.assertEqual(result["issues"][1], "关系问题2")

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_feature_overlaps')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_domain_consistency')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_dependency_rationality')
    async def test_validate_with_relationships(self, mock_dependency, mock_domain, mock_feature):
        """测试验证关系"""
        mock_feature.return_value = []
        mock_domain.return_value = []
        mock_dependency.return_value = []
        
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": [{"name": "UIComponent", "responsibilities": ["显示界面"]}]
        }
        related_components = {
            "by_dependency": [{"name": "ServiceComponent", "layer": "business"}],
            "by_feature": [{"name": "DataComponent", "features": ["数据访问"]}],
            "by_keyword": [],
            "by_responsibility": [{"name": "ServiceComponent", "domains": ["业务"]}]
        }
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertEqual(result, [])
        
        mock_feature.assert_called_once_with(layer_info, related_components["by_feature"])
        mock_domain.assert_called_once_with(layer_info, related_components["by_responsibility"])
        mock_dependency.assert_called_once_with(layer_info, related_components["by_dependency"])
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = ["特性重叠问题"]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "功能重叠: 特性重叠问题")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = []
        mock_domain.return_value = ["领域不一致问题"]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "领域不一致: 领域不一致问题")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = []
        mock_domain.return_value = []
        mock_dependency.return_value = ["依赖问题"]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "依赖关系问题: 依赖问题")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = ["特性重叠问题"]
        mock_domain.return_value = ["领域不一致问题"]
        mock_dependency.return_value = ["依赖问题"]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "功能重叠: 特性重叠问题")
        self.assertEqual(result[1], "领域不一致: 领域不一致问题")
        self.assertEqual(result[2], "依赖关系问题: 依赖问题")

    async def test_check_feature_overlaps(self):
        """测试检查特性重叠"""
        layer_info = {
            "components": [
                {
                    "name": "UIComponent",
                    "features": ["UI渲染", "用户交互"]
                }
            ]
        }
        related_features = [
            {
                "name": "DataComponent",
                "features": ["数据访问", "数据验证"],
                "pattern": "MVC",
                "layer": "data",
                "module": "DataComponent"
            }
        ]
        
        result = self.reasoner._check_feature_overlaps(layer_info, related_features)
        
        self.assertEqual(result, [])
        
        layer_info = {
            "components": [
                {
                    "name": "UIComponent",
                    "features": ["UI渲染", "数据访问"]
                }
            ]
        }
        
        result = self.reasoner._check_feature_overlaps(layer_info, related_features)
        
        self.assertEqual(len(result), 1)
        self.assertIn("存在功能重叠", result[0])
        self.assertIn("数据访问", result[0])

    async def test_check_domain_consistency(self):
        """测试检查领域一致性"""
        layer_info = {
            "components": [
                {
                    "name": "UIComponent",
                    "domains": ["前端", "UI"]
                }
            ]
        }
        related_domains = [
            {
                "name": "ServiceComponent",
                "domains": ["业务", "服务"],
                "pattern": "MVC",
                "layer": "business",
                "module": "ServiceComponent"
            }
        ]
        
        result = self.reasoner._check_domain_consistency(layer_info, related_domains)
        
        self.assertEqual(len(result), 1)
        self.assertIn("缺少共同的领域上下文", result[0])
        
        layer_info = {
            "components": [
                {
                    "name": "UIComponent",
                    "domains": ["前端", "业务"]
                }
            ]
        }
        
        result = self.reasoner._check_domain_consistency(layer_info, related_domains)
        
        self.assertEqual(result, [])

    async def test_check_dependency_rationality(self):
        """测试检查依赖合理性"""
        layer_info = {
            "components": [
                {
                    "name": "UIComponent",
                    "dependencies": ["ServiceComponent"]
                }
            ]
        }
        related_deps = [
            {
                "module": "UIComponent",
                "relationship": "depends_on",
                "pattern": "MVC",
                "layer": "business"
            }
        ]
        
        result = self.reasoner._check_dependency_rationality(layer_info, related_deps)
        
        self.assertEqual(len(result), 1)
        self.assertIn("可能存在与", result[0])
        self.assertIn("循环依赖", result[0])
        
        related_deps = [
            {
                "module": "OtherComponent",
                "relationship": "depends_on",
                "pattern": "MVC",
                "layer": "business"
            }
        ]
        
        result = self.reasoner._check_dependency_rationality(layer_info, related_deps)
        
        self.assertEqual(result, [])
