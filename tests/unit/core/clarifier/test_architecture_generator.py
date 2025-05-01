import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import json
import os
import shutil
import tempfile
from core.clarifier.architecture_generator import ArchitectureGenerator

class TestArchitectureGenerator:
    """ArchitectureGenerator 单元测试"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """测试前准备工作和测试后清理工作"""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('core.clarifier.architecture_generator.Path', return_value=Path(self.temp_dir)):
            self.generator = ArchitectureGenerator()
        
        self.generator.output_dir = Path(self.temp_dir)
        
        self.requirement_analysis = {
            "functional_requirements": ["需求1", "需求2"],
            "non_functional_requirements": ["性能", "安全性"]
        }
        
        self.architecture_analysis = {
            "architecture_pattern": {
                "name": "分层架构",
                "rationale": "适合企业应用",
                "advantages": ["清晰", "易于维护"],
                "challenges": ["性能开销"]
            },
            "layers": [
                {
                    "name": "表现层",
                    "responsibilities": ["用户界面"],
                    "components": ["Web UI"]
                }
            ]
        }
        
        yield
        
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        with patch('core.clarifier.architecture_generator.Path', return_value=Path(self.temp_dir)):
            generator = ArchitectureGenerator()
            
        assert Path(self.temp_dir).exists()
        assert generator.logger is None
        
        logger_mock = MagicMock()
        with patch('core.clarifier.architecture_generator.Path', return_value=Path(self.temp_dir)):
            generator = ArchitectureGenerator(logger=logger_mock)
        assert generator.logger == logger_mock
    
    @pytest.mark.asyncio
    @patch('core.clarifier.architecture_generator.clean_code_output')
    async def test_analyze_architecture_needs_success(self, mock_clean_code):
        """测试成功分析架构需求"""
        llm_call_mock = AsyncMock(return_value=self.architecture_analysis)
        
        mock_clean_code.return_value = lambda x: x
        
        result = await self.generator.analyze_architecture_needs(
            self.requirement_analysis, llm_call_mock
        )
        
        assert result == self.architecture_analysis
        
        llm_call_mock.assert_called_once()
        for key, value in self.requirement_analysis.items():
            assert f'"{key}"' in llm_call_mock.call_args[0][0]
            for item in value:
                assert f'"{item}"' in llm_call_mock.call_args[0][0]
    
    @pytest.mark.asyncio
    @patch('core.clarifier.architecture_generator.clean_code_output')
    async def test_analyze_architecture_needs_with_logger(self, mock_clean_code):
        """测试带日志记录器的架构需求分析"""
        logger_mock = MagicMock()
        self.generator.logger = logger_mock
        
        llm_call_mock = AsyncMock(return_value=self.architecture_analysis)
        
        mock_clean_code.return_value = lambda x: x
        
        result = await self.generator.analyze_architecture_needs(
            self.requirement_analysis, llm_call_mock
        )
        
        assert result == self.architecture_analysis
        
        logger_mock.log.assert_any_call("\n🔍 正在分析架构需求...", role="system")
        logger_mock.log.assert_any_call(f"LLM响应：{str(self.architecture_analysis)[:200]}...", role="llm_response")
    
    @pytest.mark.asyncio
    @patch('core.clarifier.architecture_generator.clean_code_output')
    async def test_analyze_architecture_needs_json_error(self, mock_clean_code):
        """测试 JSON 解析错误的情况"""
        llm_call_mock = AsyncMock(return_value="非 JSON 字符串")
        
        mock_clean_code.return_value = lambda x: x
        
        result = await self.generator.analyze_architecture_needs(
            self.requirement_analysis, llm_call_mock
        )
        
        assert result == "非 JSON 字符串"
    
    @pytest.mark.asyncio
    async def test_generate_architecture_documents(self):
        """测试生成架构文档"""
        llm_call_mock = AsyncMock(return_value="文档内容")
        
        with patch.object(self.generator, '_generate_architecture_overview', AsyncMock()) as mock_overview, \
             patch.object(self.generator, '_generate_detailed_design', AsyncMock()) as mock_design, \
             patch.object(self.generator, '_generate_interface_documentation', AsyncMock()) as mock_interface, \
             patch.object(self.generator, '_generate_deployment_documentation', AsyncMock()) as mock_deployment:
            
            await self.generator.generate_architecture_documents(
                self.requirement_analysis, self.architecture_analysis, llm_call_mock
            )
            
            mock_overview.assert_called_once_with(self.requirement_analysis, self.architecture_analysis, llm_call_mock)
            mock_design.assert_called_once_with(self.requirement_analysis, self.architecture_analysis, llm_call_mock)
            mock_interface.assert_called_once_with(self.architecture_analysis, llm_call_mock)
            mock_deployment.assert_called_once_with(self.architecture_analysis, llm_call_mock)
    
    @pytest.mark.asyncio
    async def test_generate_architecture_overview(self):
        """测试生成架构概述文档"""
        llm_call_mock = AsyncMock(return_value="架构概述文档内容")
        
        await self.generator._generate_architecture_overview(
            self.requirement_analysis, self.architecture_analysis, llm_call_mock
        )
        
        overview_file = self.generator.output_dir / "01_architecture_overview.md"
        assert overview_file.exists()
        
        with open(overview_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "架构概述文档内容"
        
        llm_call_mock.assert_called_once()
        for key, value in self.requirement_analysis.items():
            assert f'"{key}"' in llm_call_mock.call_args[0][0]
            for item in value:
                assert f'"{item}"' in llm_call_mock.call_args[0][0]
        
        assert f'"{self.architecture_analysis["architecture_pattern"]["name"]}"' in llm_call_mock.call_args[0][0]
        assert f'"{self.architecture_analysis["architecture_pattern"]["rationale"]}"' in llm_call_mock.call_args[0][0]
        for advantage in self.architecture_analysis["architecture_pattern"]["advantages"]:
            assert f'"{advantage}"' in llm_call_mock.call_args[0][0]
        for challenge in self.architecture_analysis["architecture_pattern"]["challenges"]:
            assert f'"{challenge}"' in llm_call_mock.call_args[0][0]
        for layer in self.architecture_analysis["layers"]:
            assert f'"{layer["name"]}"' in llm_call_mock.call_args[0][0]
            for resp in layer["responsibilities"]:
                assert f'"{resp}"' in llm_call_mock.call_args[0][0]
            for comp in layer["components"]:
                assert f'"{comp}"' in llm_call_mock.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_generate_detailed_design(self):
        """测试生成详细设计文档"""
        llm_call_mock = AsyncMock(return_value="详细设计文档内容")
        
        await self.generator._generate_detailed_design(
            self.requirement_analysis, self.architecture_analysis, llm_call_mock
        )
        
        design_file = self.generator.output_dir / "02_detailed_design.md"
        assert design_file.exists()
        
        with open(design_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "详细设计文档内容"
        
        llm_call_mock.assert_called_once()
        for key, value in self.requirement_analysis.items():
            assert f'"{key}"' in llm_call_mock.call_args[0][0]
            for item in value:
                assert f'"{item}"' in llm_call_mock.call_args[0][0]
        
        assert f'"{self.architecture_analysis["architecture_pattern"]["name"]}"' in llm_call_mock.call_args[0][0]
        assert f'"{self.architecture_analysis["architecture_pattern"]["rationale"]}"' in llm_call_mock.call_args[0][0]
        for advantage in self.architecture_analysis["architecture_pattern"]["advantages"]:
            assert f'"{advantage}"' in llm_call_mock.call_args[0][0]
        for challenge in self.architecture_analysis["architecture_pattern"]["challenges"]:
            assert f'"{challenge}"' in llm_call_mock.call_args[0][0]
        for layer in self.architecture_analysis["layers"]:
            assert f'"{layer["name"]}"' in llm_call_mock.call_args[0][0]
            for resp in layer["responsibilities"]:
                assert f'"{resp}"' in llm_call_mock.call_args[0][0]
            for comp in layer["components"]:
                assert f'"{comp}"' in llm_call_mock.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_generate_interface_documentation(self):
        """测试生成接口文档"""
        llm_call_mock = AsyncMock(return_value="接口文档内容")
        
        await self.generator._generate_interface_documentation(
            self.architecture_analysis, llm_call_mock
        )
        
        interface_file = self.generator.output_dir / "03_interfaces.md"
        assert interface_file.exists()
        
        with open(interface_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "接口文档内容"
        
        llm_call_mock.assert_called_once()
        assert f'"{self.architecture_analysis["architecture_pattern"]["name"]}"' in llm_call_mock.call_args[0][0]
        assert f'"{self.architecture_analysis["architecture_pattern"]["rationale"]}"' in llm_call_mock.call_args[0][0]
        for advantage in self.architecture_analysis["architecture_pattern"]["advantages"]:
            assert f'"{advantage}"' in llm_call_mock.call_args[0][0]
        for challenge in self.architecture_analysis["architecture_pattern"]["challenges"]:
            assert f'"{challenge}"' in llm_call_mock.call_args[0][0]
        for layer in self.architecture_analysis["layers"]:
            assert f'"{layer["name"]}"' in llm_call_mock.call_args[0][0]
            for resp in layer["responsibilities"]:
                assert f'"{resp}"' in llm_call_mock.call_args[0][0]
            for comp in layer["components"]:
                assert f'"{comp}"' in llm_call_mock.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_generate_deployment_documentation(self):
        """测试生成部署文档"""
        llm_call_mock = AsyncMock(return_value="部署文档内容")
        
        await self.generator._generate_deployment_documentation(
            self.architecture_analysis, llm_call_mock
        )
        
        deployment_file = self.generator.output_dir / "04_deployment.md"
        assert deployment_file.exists()
        
        with open(deployment_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "部署文档内容"
        
        llm_call_mock.assert_called_once()
        assert f'"{self.architecture_analysis["architecture_pattern"]["name"]}"' in llm_call_mock.call_args[0][0]
        assert f'"{self.architecture_analysis["architecture_pattern"]["rationale"]}"' in llm_call_mock.call_args[0][0]
        for advantage in self.architecture_analysis["architecture_pattern"]["advantages"]:
            assert f'"{advantage}"' in llm_call_mock.call_args[0][0]
        for challenge in self.architecture_analysis["architecture_pattern"]["challenges"]:
            assert f'"{challenge}"' in llm_call_mock.call_args[0][0]
        for layer in self.architecture_analysis["layers"]:
            assert f'"{layer["name"]}"' in llm_call_mock.call_args[0][0]
            for resp in layer["responsibilities"]:
                assert f'"{resp}"' in llm_call_mock.call_args[0][0]
            for comp in layer["components"]:
                assert f'"{comp}"' in llm_call_mock.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_save_architecture_state(self):
        """测试保存架构状态"""
        await self.generator.save_architecture_state(
            self.requirement_analysis, self.architecture_analysis
        )
        
        state_file = self.generator.output_dir / "architecture_state.json"
        assert state_file.exists()
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            assert state["requirement_analysis"] == self.requirement_analysis
            assert state["architecture_analysis"] == self.architecture_analysis
            assert "timestamp" in state
    
    @pytest.mark.asyncio
    async def test_dict_to_string_conversion(self):
        """测试字典到字符串的转换"""
        llm_call_mock = AsyncMock(return_value={"content": "文档内容"})
        
        await self.generator._generate_architecture_overview(
            self.requirement_analysis, self.architecture_analysis, llm_call_mock
        )
        
        overview_file = self.generator.output_dir / "01_architecture_overview.md"
        assert overview_file.exists()
        
        with open(overview_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '"content": "文档内容"' in content
