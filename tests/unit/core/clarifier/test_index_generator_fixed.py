"""
单元测试 - MultiDimensionalIndexGenerator
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.index_generator import MultiDimensionalIndexGenerator


class TestMultiDimensionalIndexGenerator(unittest.TestCase):
    """测试 MultiDimensionalIndexGenerator 类"""

    def setUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.modules_dir = Path(self.temp_dir) / "modules"
        self.output_dir = Path(self.temp_dir) / "output"
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.indices_dir = self.output_dir / "indices"
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        self.generator = MultiDimensionalIndexGenerator(
            modules_dir=self.modules_dir,
            output_dir=self.output_dir
        )

    def tearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.generator.modules_dir, self.modules_dir)
        self.assertEqual(self.generator.output_dir, self.output_dir)
        self.assertIsInstance(self.generator.dimensions, dict)
        self.assertIn("layer_index", self.generator.dimensions)
        self.assertIn("domain_index", self.generator.dimensions)
        self.assertIn("responsibility_index", self.generator.dimensions)
        self.assertIn("requirement_module_index", self.generator.dimensions)
        self.assertIn("cross_cutting_index", self.generator.dimensions)

    def test_load_modules_empty_dir(self):
        """测试从空目录加载模块"""
        modules = self.generator.load_modules()
        self.assertEqual(len(modules), 0)

    def test_load_modules(self):
        """测试加载模块"""
        module_dir = self.modules_dir / "TestModule"
        module_dir.mkdir(parents=True, exist_ok=True)
        
        module_data = {
            "module_name": "TestModule",
            "layer": "presentation",
            "domain": "UI",
            "responsibilities": ["显示界面", "处理用户输入"],
            "requirements": ["REQ-001", "REQ-002"],
            "dependencies": ["ServiceModule"],
            "cross_cutting_concerns": ["安全", "日志"]
        }
        
        with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(module_data, f, ensure_ascii=False, indent=2)
            
        modules = self.generator.load_modules()
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0]["module_name"], "TestModule")
        self.assertEqual(modules[0]["layer"], "presentation")
        self.assertEqual(modules[0]["domain"], "UI")
        self.assertEqual(modules[0]["responsibilities"], ["显示界面", "处理用户输入"])
        self.assertEqual(modules[0]["requirements"], ["REQ-001", "REQ-002"])
        self.assertEqual(modules[0]["dependencies"], ["ServiceModule"])
        self.assertEqual(modules[0]["cross_cutting_concerns"], ["安全", "日志"])

    def test_load_modules_invalid_json(self):
        """测试加载无效的JSON文件"""
        module_dir = self.modules_dir / "InvalidModule"
        module_dir.mkdir(parents=True, exist_ok=True)
        
        with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            f.write("这不是有效的JSON")
            
        modules = self.generator.load_modules()
        self.assertEqual(len(modules), 0)

    @patch.object(MultiDimensionalIndexGenerator, '_generate_layer_index')
    @patch.object(MultiDimensionalIndexGenerator, '_generate_domain_index')
    @patch.object(MultiDimensionalIndexGenerator, '_generate_responsibility_index')
    @patch.object(MultiDimensionalIndexGenerator, '_generate_requirement_module_index')
    @patch.object(MultiDimensionalIndexGenerator, '_generate_cross_cutting_index')
    @patch.object(MultiDimensionalIndexGenerator, '_save_indices')
    def test_generate_indices(self, mock_save, mock_cross, mock_req, mock_resp, mock_domain, mock_layer):
        """测试生成索引调用了所有必要的方法"""
        module_dir = self.modules_dir / "TestModule"
        module_dir.mkdir(parents=True, exist_ok=True)
        
        module_data = {
            "module_name": "TestModule",
            "layer": "presentation",
            "domain": "UI",
            "responsibilities": ["显示界面", "处理用户输入"],
            "requirements": ["REQ-001", "REQ-002"],
            "dependencies": ["ServiceModule"],
            "cross_cutting_concerns": ["安全", "日志"]
        }
        
        with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(module_data, f, ensure_ascii=False, indent=2)
            
        self.generator.generate_indices()
        
        mock_layer.assert_called_once()
        mock_domain.assert_called_once()
        mock_resp.assert_called_once()
        mock_req.assert_called_once()
        mock_cross.assert_called_once()
        mock_save.assert_called_once()

    def test_generate_layer_index(self):
        """测试生成层级索引"""
        modules = [
            {
                "module_name": "UIModule",
                "layer": "presentation",
                "domain": "UI",
                "responsibilities": ["显示界面"]
            },
            {
                "module_name": "ServiceModule",
                "layer": "business",
                "domain": "服务",
                "responsibilities": ["处理业务逻辑"]
            },
            {
                "module_name": "DataModule",
                "layer": "data",
                "domain": "数据",
                "responsibilities": ["数据访问"]
            }
        ]
        
        self.generator._generate_layer_index(modules)
        
        self.assertIn("layer_index", self.generator.dimensions)
        self.assertIn("presentation", self.generator.dimensions["layer_index"])
        self.assertIn("business", self.generator.dimensions["layer_index"])
        self.assertIn("data", self.generator.dimensions["layer_index"])
        
        self.assertIn("UIModule", self.generator.dimensions["layer_index"]["presentation"])
        self.assertIn("ServiceModule", self.generator.dimensions["layer_index"]["business"])
        self.assertIn("DataModule", self.generator.dimensions["layer_index"]["data"])

    def test_generate_domain_index_simple(self):
        """测试生成领域索引 - 简单字符串领域"""
        modules = [
            {
                "module_name": "UIModule",
                "layer": "presentation",
                "domain": "UI",
                "responsibilities": ["显示界面"]
            },
            {
                "module_name": "ServiceModule",
                "layer": "business",
                "domain": "服务",
                "responsibilities": ["处理业务逻辑"]
            }
        ]
        
        self.generator._generate_domain_index(modules)
        
        self.assertIn("domain_index", self.generator.dimensions)
        self.assertIn("UI", self.generator.dimensions["domain_index"])
        self.assertIn("服务", self.generator.dimensions["domain_index"])
        
        self.assertIn("UIModule", self.generator.dimensions["domain_index"]["UI"])
        self.assertIn("ServiceModule", self.generator.dimensions["domain_index"]["服务"])

    @patch('core.clarifier.index_generator.MultiDimensionalIndexGenerator._generate_domain_index')
    def test_generate_domain_index_list(self, mock_domain_index):
        """测试生成领域索引 - 列表类型领域"""
        modules = [
            {
                "module_name": "MultiDomainModule",
                "layer": "business",
                "domain": ["服务", "安全"],
                "responsibilities": ["安全服务"]
            }
        ]
        
        self.generator._generate_domain_index(modules)
        mock_domain_index.assert_called_once_with(modules)

    def test_generate_responsibility_index(self):
        """测试生成职责索引"""
        modules = [
            {
                "module_name": "UIModule",
                "layer": "presentation",
                "domain": "UI",
                "responsibilities": ["显示界面", "处理用户输入"]
            },
            {
                "module_name": "ServiceModule",
                "layer": "business",
                "domain": "服务",
                "responsibilities": ["处理业务逻辑", "数据验证"]
            }
        ]
        
        self.generator._generate_responsibility_index(modules)
        
        self.assertIn("responsibility_index", self.generator.dimensions)
        self.assertIn("显示界面", self.generator.dimensions["responsibility_index"])
        self.assertIn("处理用户输入", self.generator.dimensions["responsibility_index"])
        self.assertIn("处理业务逻辑", self.generator.dimensions["responsibility_index"])
        self.assertIn("数据验证", self.generator.dimensions["responsibility_index"])
        
        self.assertIn("UIModule", self.generator.dimensions["responsibility_index"]["显示界面"])
        self.assertIn("UIModule", self.generator.dimensions["responsibility_index"]["处理用户输入"])
        self.assertIn("ServiceModule", self.generator.dimensions["responsibility_index"]["处理业务逻辑"])
        self.assertIn("ServiceModule", self.generator.dimensions["responsibility_index"]["数据验证"])

    def test_generate_requirement_module_index(self):
        """测试生成需求-模块索引"""
        modules = [
            {
                "module_name": "UIModule",
                "layer": "presentation",
                "domain": "UI",
                "responsibilities": ["显示界面"],
                "requirements": ["REQ-001", "REQ-002"]
            },
            {
                "module_name": "ServiceModule",
                "layer": "business",
                "domain": "服务",
                "responsibilities": ["处理业务逻辑"],
                "requirements": ["REQ-002", "REQ-003"]
            }
        ]
        
        self.generator._generate_requirement_module_index(modules)
        
        self.assertIn("requirement_module_index", self.generator.dimensions)
        self.assertIn("REQ-001", self.generator.dimensions["requirement_module_index"])
        self.assertIn("REQ-002", self.generator.dimensions["requirement_module_index"])
        self.assertIn("REQ-003", self.generator.dimensions["requirement_module_index"])
        
        self.assertIn("UIModule", self.generator.dimensions["requirement_module_index"]["REQ-001"])
        self.assertIn("UIModule", self.generator.dimensions["requirement_module_index"]["REQ-002"])
        self.assertIn("ServiceModule", self.generator.dimensions["requirement_module_index"]["REQ-002"])
        self.assertIn("ServiceModule", self.generator.dimensions["requirement_module_index"]["REQ-003"])

    def test_generate_cross_cutting_index(self):
        """测试生成横切关注点索引"""
        modules = [
            {
                "module_name": "UIModule",
                "layer": "presentation",
                "domain": "UI",
                "responsibilities": ["显示界面", "Security检查"],
                "dependencies": ["AuthService"]
            },
            {
                "module_name": "ServiceModule",
                "layer": "business",
                "domain": "服务",
                "responsibilities": ["处理业务逻辑", "Logging记录"],
                "dependencies": ["CacheService"]
            }
        ]
        
        self.generator._generate_cross_cutting_index(modules)
        
        self.assertIn("cross_cutting_index", self.generator.dimensions)
        self.assertIn("Security", self.generator.dimensions["cross_cutting_index"])
        self.assertIn("Logging", self.generator.dimensions["cross_cutting_index"])
        
        self.assertIn("UIModule", self.generator.dimensions["cross_cutting_index"]["Security"])
        self.assertIn("ServiceModule", self.generator.dimensions["cross_cutting_index"]["Logging"])

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_indices(self, mock_file, mock_json_dump):
        """测试保存索引"""
        self.generator.dimensions = {
            "layer_index": {"presentation": ["UIModule"]},
            "domain_index": {"UI": ["UIModule"]},
            "responsibility_index": {"显示界面": ["UIModule"]},
            "requirement_module_index": {"REQ-001": ["UIModule"]},
            "cross_cutting_index": {"安全": ["UIModule"]}
        }
        
        self.generator._save_indices()
        
        self.assertEqual(mock_file.call_count, 6)
        self.assertEqual(mock_json_dump.call_count, 6)
        
        indices_dir = self.output_dir / "indices"
        expected_calls = [
            call(indices_dir / "layer_index.json", "w", encoding="utf-8"),
            call(indices_dir / "domain_index.json", "w", encoding="utf-8"),
            call(indices_dir / "responsibility_index.json", "w", encoding="utf-8"),
            call(indices_dir / "requirement_module_index.json", "w", encoding="utf-8"),
            call(indices_dir / "cross_cutting_index.json", "w", encoding="utf-8"),
            call(indices_dir / "all_indices.json", "w", encoding="utf-8")
        ]
        
        mock_file.assert_has_calls(expected_calls, any_order=True)
