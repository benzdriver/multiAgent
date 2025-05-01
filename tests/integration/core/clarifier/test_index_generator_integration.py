"""
集成测试 - MultiDimensionalIndexGenerator
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.index_generator import MultiDimensionalIndexGenerator
from core.clarifier.architecture_manager import ArchitectureManager


class TestMultiDimensionalIndexGeneratorIntegration(unittest.IsolatedAsyncioTestCase):
    """测试 MultiDimensionalIndexGenerator 与其他模块的集成"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.modules_dir = Path(self.temp_dir) / "modules"
        self.output_dir = Path(self.temp_dir) / "output"
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.indices_dir = self.output_dir / "indices"
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        self.arch_dir = self.output_dir / "architecture"
        self.arch_dir.mkdir(parents=True, exist_ok=True)
        
        self.create_test_modules()
        
        self.generator = MultiDimensionalIndexGenerator(
            modules_dir=self.modules_dir,
            output_dir=self.output_dir
        )
        
        self.architecture_manager = ArchitectureManager()
        self.architecture_manager.output_path = self.arch_dir

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    def create_test_modules(self):
        """创建测试模块"""
        ui_module_dir = self.modules_dir / "UIModule"
        ui_module_dir.mkdir(parents=True, exist_ok=True)
        
        ui_module_data = {
            "module_name": "UIModule",
            "layer": "presentation",
            "domain": "UI",
            "responsibilities": ["显示界面", "处理用户输入"],
            "requirements": ["REQ-001", "REQ-002"],
            "dependencies": ["ServiceModule"],
            "cross_cutting_concerns": ["安全", "日志"]
        }
        
        with open(ui_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(ui_module_data, f, ensure_ascii=False, indent=2)
            
        service_module_dir = self.modules_dir / "ServiceModule"
        service_module_dir.mkdir(parents=True, exist_ok=True)
        
        service_module_data = {
            "module_name": "ServiceModule",
            "layer": "business",
            "domain": "服务",
            "responsibilities": ["处理业务逻辑", "数据验证"],
            "requirements": ["REQ-002", "REQ-003"],
            "dependencies": ["DataModule"],
            "cross_cutting_concerns": ["日志", "性能"]
        }
        
        with open(service_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(service_module_data, f, ensure_ascii=False, indent=2)
            
        data_module_dir = self.modules_dir / "DataModule"
        data_module_dir.mkdir(parents=True, exist_ok=True)
        
        data_module_data = {
            "module_name": "DataModule",
            "layer": "data",
            "domain": "数据",
            "responsibilities": ["数据访问", "数据持久化"],
            "requirements": ["REQ-003", "REQ-004"],
            "dependencies": [],
            "cross_cutting_concerns": ["安全", "性能"]
        }
        
        with open(data_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(data_module_data, f, ensure_ascii=False, indent=2)

    async def test_integration_with_architecture_manager(self):
        """测试与架构管理器的集成"""
        self.generator.generate_indices()
        
        self.assertTrue((self.indices_dir / "layer_index.json").exists())
        self.assertTrue((self.indices_dir / "domain_index.json").exists())
        self.assertTrue((self.indices_dir / "responsibility_index.json").exists())
        self.assertTrue((self.indices_dir / "requirement_module_index.json").exists())
        self.assertTrue((self.indices_dir / "cross_cutting_index.json").exists())
        
        self.architecture_manager.load_indices(self.indices_dir)
        
        self.assertIn("presentation", self.architecture_manager.index.layer_index)
        self.assertIn("business", self.architecture_manager.index.layer_index)
        self.assertIn("data", self.architecture_manager.index.layer_index)
        
        self.assertIn("UI", self.architecture_manager.index.domain_index)
        self.assertIn("服务", self.architecture_manager.index.domain_index)
        self.assertIn("数据", self.architecture_manager.index.domain_index)
        
        self.assertIn("显示界面", self.architecture_manager.index.responsibility_index)
        self.assertIn("处理业务逻辑", self.architecture_manager.index.responsibility_index)
        self.assertIn("数据访问", self.architecture_manager.index.responsibility_index)
        
        self.assertIn("REQ-001", self.architecture_manager.index.requirement_module_index)
        self.assertIn("REQ-002", self.architecture_manager.index.requirement_module_index)
        self.assertIn("REQ-003", self.architecture_manager.index.requirement_module_index)
        self.assertIn("REQ-004", self.architecture_manager.index.requirement_module_index)
        
        self.assertIn("安全", self.architecture_manager.index.cross_cutting_index)
        self.assertIn("日志", self.architecture_manager.index.cross_cutting_index)
        self.assertIn("性能", self.architecture_manager.index.cross_cutting_index)
        
        self.assertIn("UIModule", self.architecture_manager.index.layer_index["presentation"])
        self.assertIn("ServiceModule", self.architecture_manager.index.layer_index["business"])
        self.assertIn("DataModule", self.architecture_manager.index.layer_index["data"])
        
        self.assertIn("UIModule", self.architecture_manager.index.domain_index["UI"])
        self.assertIn("ServiceModule", self.architecture_manager.index.domain_index["服务"])
        self.assertIn("DataModule", self.architecture_manager.index.domain_index["数据"])
        
        self.assertIn("UIModule", self.architecture_manager.index.responsibility_index["显示界面"])
        self.assertIn("ServiceModule", self.architecture_manager.index.responsibility_index["处理业务逻辑"])
        self.assertIn("DataModule", self.architecture_manager.index.responsibility_index["数据访问"])
        
        self.assertIn("UIModule", self.architecture_manager.index.requirement_module_index["REQ-001"])
        self.assertIn("UIModule", self.architecture_manager.index.requirement_module_index["REQ-002"])
        self.assertIn("ServiceModule", self.architecture_manager.index.requirement_module_index["REQ-002"])
        self.assertIn("ServiceModule", self.architecture_manager.index.requirement_module_index["REQ-003"])
        self.assertIn("DataModule", self.architecture_manager.index.requirement_module_index["REQ-003"])
        self.assertIn("DataModule", self.architecture_manager.index.requirement_module_index["REQ-004"])
        
        self.assertIn("UIModule", self.architecture_manager.index.cross_cutting_index["安全"])
        self.assertIn("UIModule", self.architecture_manager.index.cross_cutting_index["日志"])
        self.assertIn("ServiceModule", self.architecture_manager.index.cross_cutting_index["日志"])
        self.assertIn("ServiceModule", self.architecture_manager.index.cross_cutting_index["性能"])
        self.assertIn("DataModule", self.architecture_manager.index.cross_cutting_index["安全"])
        self.assertIn("DataModule", self.architecture_manager.index.cross_cutting_index["性能"])

    async def test_integration_with_dependency_graph(self):
        """测试与依赖图的集成"""
        self.generator.generate_indices()
        
        self.architecture_manager.load_indices(self.indices_dir)
        
        self.architecture_manager.build_dependency_graph(self.modules_dir)
        
        self.assertIn("UIModule", self.architecture_manager.index.dependency_graph)
        self.assertIn("ServiceModule", self.architecture_manager.index.dependency_graph)
        self.assertIn("DataModule", self.architecture_manager.index.dependency_graph)
        
        self.assertIn("ServiceModule", self.architecture_manager.index.dependency_graph["UIModule"]["depends_on"])
        self.assertIn("DataModule", self.architecture_manager.index.dependency_graph["ServiceModule"]["depends_on"])
        self.assertEqual(self.architecture_manager.index.dependency_graph["DataModule"]["depends_on"], [])
        
        self.assertIn("UIModule", self.architecture_manager.index.dependency_graph["ServiceModule"]["depended_by"])
        self.assertIn("ServiceModule", self.architecture_manager.index.dependency_graph["DataModule"]["depended_by"])
        self.assertEqual(self.architecture_manager.index.dependency_graph["UIModule"]["depended_by"], [])
        
        self.assertEqual(self.architecture_manager.index.dependency_graph["UIModule"]["layer"], "presentation")
        self.assertEqual(self.architecture_manager.index.dependency_graph["ServiceModule"]["layer"], "business")
        self.assertEqual(self.architecture_manager.index.dependency_graph["DataModule"]["layer"], "data")

    async def test_integration_with_file_system(self):
        """测试与文件系统的集成"""
        self.generator.generate_indices()
        
        self.assertTrue((self.indices_dir / "layer_index.json").exists())
        self.assertTrue((self.indices_dir / "domain_index.json").exists())
        self.assertTrue((self.indices_dir / "responsibility_index.json").exists())
        self.assertTrue((self.indices_dir / "requirement_module_index.json").exists())
        self.assertTrue((self.indices_dir / "cross_cutting_index.json").exists())
        
        with open(self.indices_dir / "layer_index.json", "r", encoding="utf-8") as f:
            layer_index = json.load(f)
            self.assertIn("presentation", layer_index)
            self.assertIn("business", layer_index)
            self.assertIn("data", layer_index)
            self.assertIn("UIModule", layer_index["presentation"])
            self.assertIn("ServiceModule", layer_index["business"])
            self.assertIn("DataModule", layer_index["data"])
        
        with open(self.indices_dir / "domain_index.json", "r", encoding="utf-8") as f:
            domain_index = json.load(f)
            self.assertIn("UI", domain_index)
            self.assertIn("服务", domain_index)
            self.assertIn("数据", domain_index)
            self.assertIn("UIModule", domain_index["UI"])
            self.assertIn("ServiceModule", domain_index["服务"])
            self.assertIn("DataModule", domain_index["数据"])
        
        with open(self.indices_dir / "responsibility_index.json", "r", encoding="utf-8") as f:
            responsibility_index = json.load(f)
            self.assertIn("显示界面", responsibility_index)
            self.assertIn("处理业务逻辑", responsibility_index)
            self.assertIn("数据访问", responsibility_index)
            self.assertIn("UIModule", responsibility_index["显示界面"])
            self.assertIn("ServiceModule", responsibility_index["处理业务逻辑"])
            self.assertIn("DataModule", responsibility_index["数据访问"])
        
        with open(self.indices_dir / "requirement_module_index.json", "r", encoding="utf-8") as f:
            requirement_module_index = json.load(f)
            self.assertIn("REQ-001", requirement_module_index)
            self.assertIn("REQ-002", requirement_module_index)
            self.assertIn("REQ-003", requirement_module_index)
            self.assertIn("REQ-004", requirement_module_index)
            self.assertIn("UIModule", requirement_module_index["REQ-001"])
            self.assertIn("UIModule", requirement_module_index["REQ-002"])
            self.assertIn("ServiceModule", requirement_module_index["REQ-002"])
            self.assertIn("ServiceModule", requirement_module_index["REQ-003"])
            self.assertIn("DataModule", requirement_module_index["REQ-003"])
            self.assertIn("DataModule", requirement_module_index["REQ-004"])
        
        with open(self.indices_dir / "cross_cutting_index.json", "r", encoding="utf-8") as f:
            cross_cutting_index = json.load(f)
            self.assertIn("安全", cross_cutting_index)
            self.assertIn("日志", cross_cutting_index)
            self.assertIn("性能", cross_cutting_index)
            self.assertIn("UIModule", cross_cutting_index["安全"])
            self.assertIn("UIModule", cross_cutting_index["日志"])
            self.assertIn("ServiceModule", cross_cutting_index["日志"])
            self.assertIn("ServiceModule", cross_cutting_index["性能"])
            self.assertIn("DataModule", cross_cutting_index["安全"])
            self.assertIn("DataModule", cross_cutting_index["性能"])
