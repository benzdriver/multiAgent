# clarifier.py 模块分析

## 模块概述
clarifier.py 是 core/clarifier 包中的核心组件，作为整个需求澄清和架构设计过程的主要协调器。该模块提供了文件解析和交互式两种工作模式，负责协调需求分析、架构生成、深度推理和模块集成等功能。

## 类和方法

### Clarifier
主要类，提供需求澄清和架构设计功能。

**初始化方法：**
- `__init__(data_dir="data", llm_chat=None)`: 初始化需求澄清器，设置数据目录和LLM聊天接口。

**主要公共方法：**
- `start()`: 启动需求澄清器，是整个流程的入口点
- `deep_clarification(requirement_analysis=None)`: 执行深度需求澄清
- `deep_reasoning(requirement_analysis=None, architecture_analysis=None)`: 执行深度架构推理
- `integrate_legacy_modules(input_path="data/input", output_path="data/output")`: 集成legacy clarifier的功能
- `generate_granular_modules(input_path="data/input", output_path="data/output")`: 生成细粒度架构模块
- `continue_from_user()`: 从用户输入继续执行

**私有方法：**
- `_file_based_clarification()`: 基于文件的需求澄清
- `_interactive_clarification()`: 交互式需求澄清
- `_read_all_markdown_files(input_path=None)`: 读取输入文件夹中的所有Markdown文件
- `run_llm(prompt, **kwargs)`: 运行LLM，使用llm_executor中的run_prompt函数

**主函数：**
- `main()`: 创建Clarifier实例并启动

## 依赖关系
- `RequirementAnalyzer`: 用于分析需求
- `ArchitectureGenerator`: 用于生成架构文档
- `ArchitectureManager`: 用于管理架构状态
- `ArchitectureReasoner`: 用于架构推理和问题检测
- `MultiDimensionalIndexGenerator`: 用于生成多维度索引
- `run_prompt`: 用于执行LLM提示并获取响应
- `Logger`: 用于日志记录
- 标准库: pathlib, typing, asyncio, json, os, glob

## 工作流程
1. 用户启动程序，选择工作模式（文件解析或交互式）
2. 系统读取输入文档，分析需求
3. 生成需求摘要文档
4. 分析架构需求，生成架构文档
5. 用户可以选择进行深度需求澄清或深度架构推理
6. 系统可以集成legacy模块或生成细粒度架构模块

## 文件操作
- 读取输入文件夹中的Markdown文件
- 生成需求摘要文档
- 生成架构文档
- 保存深度澄清和推理结果
- 保存架构状态和问题报告

## 错误处理
- 使用try/except处理文件操作错误
- 使用try/except处理LLM调用错误
- 使用try/except处理JSON解析错误
- 提供默认值和回退机制

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试提供自定义参数初始化

2. **文件操作测试**
   - 测试 _read_all_markdown_files 方法
   - 测试文件不存在的情况
   - 测试文件读取错误的情况

3. **LLM交互测试**
   - 测试 run_llm 方法
   - 模拟LLM响应
   - 测试错误处理

4. **深度澄清和推理测试**
   - 测试 deep_clarification 方法
   - 测试 deep_reasoning 方法
   - 测试没有需求数据的情况

5. **模块生成和集成测试**
   - 测试 integrate_legacy_modules 方法
   - 测试 generate_granular_modules 方法
   - 测试模块处理错误的情况

### 集成测试
1. **与RequirementAnalyzer集成测试**
   - 测试需求分析流程
   - 测试需求摘要生成

2. **与ArchitectureGenerator集成测试**
   - 测试架构需求分析
   - 测试架构文档生成

3. **与ArchitectureManager集成测试**
   - 测试模块处理
   - 测试架构状态管理

4. **与ArchitectureReasoner集成测试**
   - 测试架构问题检测
   - 测试问题报告生成

5. **与MultiDimensionalIndexGenerator集成测试**
   - 测试多维度索引生成

6. **端到端测试**
   - 测试完整的文件解析流程
   - 测试细粒度模块生成流程

### 模拟依赖
- 使用unittest.mock模拟RequirementAnalyzer
- 使用unittest.mock模拟ArchitectureGenerator
- 使用unittest.mock模拟ArchitectureManager
- 使用unittest.mock模拟ArchitectureReasoner
- 使用unittest.mock模拟MultiDimensionalIndexGenerator
- 使用unittest.mock模拟LLM响应
- 使用临时目录进行文件操作测试

### 测试边缘情况
- 空输入
- 错误输入
- LLM调用失败
- 文件操作失败
- JSON解析错误
