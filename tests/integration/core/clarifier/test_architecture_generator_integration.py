import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
import os
from unittest.mock import AsyncMock, patch, MagicMock

from core.clarifier.architecture_generator import ArchitectureGenerator
from core.clarifier.requirement_analyzer import RequirementAnalyzer
from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.architecture_manager import ArchitectureManager

class TestArchitectureGeneratorIntegration:
    """ArchitectureGenerator 集成测试"""
    
    @pytest.fixture
    def setup_test_environment(self):
        """设置测试环境"""
        temp_dir = Path(tempfile.mkdtemp())
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        
        with open(input_dir / "requirements.md", "w", encoding="utf-8") as f:
            f.write("""
            
            
            1. 用户管理
               - 用户注册
               - 用户登录
               - 用户信息管理
               
            2. 内容管理
               - 内容创建
               - 内容编辑
               - 内容发布
               
            
            1. 性能
               - 系统响应时间不超过2秒
               - 支持1000并发用户
               
            2. 安全性
               - 数据加密
               - 权限控制
            """)
        
        requirement_analysis = {
            "functional_requirements": [
                {
                    "category": "用户管理",
                    "requirements": ["用户注册", "用户登录", "用户信息管理"]
                },
                {
                    "category": "内容管理",
                    "requirements": ["内容创建", "内容编辑", "内容发布"]
                }
            ],
            "non_functional_requirements": [
                {
                    "category": "性能",
                    "requirements": ["系统响应时间不超过2秒", "支持1000并发用户"]
                },
                {
                    "category": "安全性",
                    "requirements": ["数据加密", "权限控制"]
                }
            ]
        }
        
        architecture_analysis = {
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
                },
                {
                    "name": "业务层",
                    "responsibilities": ["业务逻辑"],
                    "components": ["用户服务", "内容服务"]
                },
                {
                    "name": "数据层",
                    "responsibilities": ["数据访问"],
                    "components": ["数据访问对象"]
                }
            ],
            "core_components": [
                {
                    "name": "用户服务",
                    "description": "处理用户相关业务逻辑",
                    "responsibilities": ["用户认证", "用户信息管理"],
                    "interfaces": ["用户API"]
                },
                {
                    "name": "内容服务",
                    "description": "处理内容相关业务逻辑",
                    "responsibilities": ["内容管理", "内容发布"],
                    "interfaces": ["内容API"]
                }
            ]
        }
        
        yield {
            "temp_dir": temp_dir,
            "input_dir": input_dir,
            "output_dir": output_dir,
            "requirement_analysis": requirement_analysis,
            "architecture_analysis": architecture_analysis
        }
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_architecture_generator_with_requirement_analyzer(self, setup_test_environment):
        """测试 ArchitectureGenerator 与 RequirementAnalyzer 的集成"""
        env = setup_test_environment
        
        llm_call_mock = AsyncMock()
        llm_call_mock.return_value = env["architecture_analysis"]
        
        requirement_analyzer = RequirementAnalyzer()
        
        with patch.object(requirement_analyzer, 'analyze_requirements', 
                         return_value=env["requirement_analysis"]):
            
            architecture_generator = ArchitectureGenerator()
            
            architecture_generator.output_dir = env["output_dir"] / "architecture"
            architecture_generator.output_dir.mkdir(parents=True, exist_ok=True)
            
            requirement_analysis = await requirement_analyzer.analyze_requirements(
                input_path=env["input_dir"],
                llm_call=llm_call_mock
            )
            
            architecture_analysis = await architecture_generator.analyze_architecture_needs(
                requirement_analysis=requirement_analysis,
                llm_call=llm_call_mock
            )
            
            assert architecture_analysis == env["architecture_analysis"]
            
            await architecture_generator.generate_architecture_documents(
                requirement_analysis=requirement_analysis,
                architecture_analysis=architecture_analysis,
                llm_call=llm_call_mock
            )
            
            assert (architecture_generator.output_dir / "01_architecture_overview.md").exists()
            assert (architecture_generator.output_dir / "02_detailed_design.md").exists()
            assert (architecture_generator.output_dir / "03_interfaces.md").exists()
            assert (architecture_generator.output_dir / "04_deployment.md").exists()
            
            await architecture_generator.save_architecture_state(
                requirement_analysis=requirement_analysis,
                architecture_analysis=architecture_analysis
            )
            
            assert (architecture_generator.output_dir / "architecture_state.json").exists()
            
            with open(architecture_generator.output_dir / "architecture_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
                assert state["requirement_analysis"] == requirement_analysis
                assert state["architecture_analysis"] == architecture_analysis
                assert "timestamp" in state
    
    @pytest.mark.asyncio
    async def test_architecture_generator_with_architecture_reasoner(self, setup_test_environment):
        """测试 ArchitectureGenerator 与 ArchitectureReasoner 的集成"""
        env = setup_test_environment
        
        llm_call_mock = AsyncMock()
        llm_call_mock.return_value = env["architecture_analysis"]
        
        architecture_generator = ArchitectureGenerator()
        
        architecture_generator.output_dir = env["output_dir"] / "architecture"
        architecture_generator.output_dir.mkdir(parents=True, exist_ok=True)
        
        architecture_analysis = await architecture_generator.analyze_architecture_needs(
            requirement_analysis=env["requirement_analysis"],
            llm_call=llm_call_mock
        )
        
        await architecture_generator.save_architecture_state(
            requirement_analysis=env["requirement_analysis"],
            architecture_analysis=architecture_analysis
        )
        
        architecture_manager = ArchitectureManager()
        architecture_reasoner = ArchitectureReasoner(architecture_manager=architecture_manager)
        
        with patch.object(architecture_reasoner, 'check_all_issues', 
                         return_value={"issues": []}):
            
            consistency_result = await architecture_reasoner.check_all_issues(
                architecture_analysis=architecture_analysis
            )
            
            assert "issues" in consistency_result
            assert isinstance(consistency_result["issues"], list)
    
    @pytest.mark.asyncio
    async def test_end_to_end_architecture_generation(self, setup_test_environment):
        """测试端到端的架构生成流程"""
        env = setup_test_environment
        
        llm_call_mock = AsyncMock()
        
        def llm_call_side_effect(*args, **kwargs):
            prompt = args[0] if args else kwargs.get("prompt", "")
            
            if "分析并确定适合该系统的架构模式" in prompt:
                return env["architecture_analysis"]
            elif "生成一个Markdown格式的架构概述文档" in prompt:
                return "# 架构概述\n\n这是一个测试架构概述文档。"
            elif "生成一个Markdown格式的详细设计文档" in prompt:
                return "# 详细设计\n\n这是一个测试详细设计文档。"
            elif "生成一个Markdown格式的接口文档" in prompt:
                return "# 接口文档\n\n这是一个测试接口文档。"
            elif "生成一个Markdown格式的部署文档" in prompt:
                return "# 部署文档\n\n这是一个测试部署文档。"
            else:
                return "默认响应"
        
        llm_call_mock.side_effect = llm_call_side_effect
        
        requirement_analyzer = RequirementAnalyzer()
        
        with patch.object(requirement_analyzer, 'analyze_requirements', 
                         return_value=env["requirement_analysis"]):
            
            architecture_generator = ArchitectureGenerator()
            
            architecture_generator.output_dir = env["output_dir"] / "architecture"
            architecture_generator.output_dir.mkdir(parents=True, exist_ok=True)
            
            requirement_analysis = await requirement_analyzer.analyze_requirements(
                input_path=env["input_dir"],
                llm_call=llm_call_mock
            )
            
            architecture_analysis = await architecture_generator.analyze_architecture_needs(
                requirement_analysis=requirement_analysis,
                llm_call=llm_call_mock
            )
            
            await architecture_generator.generate_architecture_documents(
                requirement_analysis=requirement_analysis,
                architecture_analysis=architecture_analysis,
                llm_call=llm_call_mock
            )
            
            await architecture_generator.save_architecture_state(
                requirement_analysis=requirement_analysis,
                architecture_analysis=architecture_analysis
            )
            
            architecture_manager = ArchitectureManager()
            architecture_reasoner = ArchitectureReasoner(architecture_manager=architecture_manager)
            
            with patch.object(architecture_reasoner, 'check_all_issues', 
                             return_value={"issues": []}):
                
                consistency_result = await architecture_reasoner.check_all_issues(
                    architecture_analysis=architecture_analysis
                )
                
                assert (architecture_generator.output_dir / "01_architecture_overview.md").exists()
                assert (architecture_generator.output_dir / "02_detailed_design.md").exists()
                assert (architecture_generator.output_dir / "03_interfaces.md").exists()
                assert (architecture_generator.output_dir / "04_deployment.md").exists()
                assert (architecture_generator.output_dir / "architecture_state.json").exists()
                
                with open(architecture_generator.output_dir / "01_architecture_overview.md", "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "架构概述" in content
                
                with open(architecture_generator.output_dir / "architecture_state.json", "r", encoding="utf-8") as f:
                    state = json.load(f)
                    assert state["requirement_analysis"] == requirement_analysis
                    assert state["architecture_analysis"] == architecture_analysis
                    assert "timestamp" in state
                
                assert "issues" in consistency_result
                assert isinstance(consistency_result["issues"], list)
