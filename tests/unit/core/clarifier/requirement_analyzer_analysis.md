# requirement_analyzer.py 模块分析

## 模块概述
requirement_analyzer.py 是 core/clarifier 包中的核心组件，负责分析需求文档、生成需求摘要，以及提取细粒度架构模块。该模块使用 LLM 进行需求分析和模块提取，并生成结构化的输出。

## 类和方法

### RequirementAnalyzer
主要类，提供需求分析和模块提取功能。

**初始化方法：**
- `__init__(output_dir="data/output", logger=None)`: 初始化需求分析器，设置输出目录和日志记录器。

**主要公共方法：**
- `analyze_requirements(content, llm_call)`: 分析需求文档内容，生成结构化的需求分析结果
- `generate_requirement_summary(requirement_analysis, llm_call=None)`: 生成需求摘要文档
- `analyze_granular_modules(content, llm_call, architecture_layers=None)`: 分析文档内容，提取细粒度模块

**私有方法：**
- `_generate_simple_summary(requirement_analysis)`: 生成简单的需求摘要文档
- `_save_granular_modules(modules)`: 保存提取的细粒度模块

## 依赖关系
- `os`, `json`: 用于文件操作和 JSON 处理
- `Path` 从 pathlib 模块：用于文件路径操作
- `Dict`, `Any`, `Callable`, `Awaitable`, `List`, `Optional` 从 typing 模块：用于类型注解
- `run_prompt` 从 core.llm.llm_executor 模块：用于执行 LLM 提示并获取响应
- `clean_code_output` 从 core.llm.prompt_cleaner 模块：用于清理 LLM 返回的代码输出

## 工作流程
1. 初始化需求分析器，设置输出目录
2. 分析需求文档内容，生成结构化的需求分析结果
3. 生成需求摘要文档
4. 分析文档内容，提取细粒度模块
5. 保存提取的细粒度模块

## 文件操作
- 创建输出目录
- 写入需求摘要文档
- 保存细粒度模块到 JSON 文件
- 创建模块目录结构

## 错误处理
- 使用 try/except 处理 LLM 调用错误
- 使用 try/except 处理 JSON 解析错误
- 使用 try/except 处理文件操作错误
- 提供默认值和回退机制

## LLM 交互
- 使用 LLM 分析需求文档
- 使用 LLM 生成需求摘要
- 使用 LLM 提取细粒度模块

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试提供自定义参数初始化

2. **需求分析测试**
   - 测试 analyze_requirements 方法
   - 模拟 LLM 响应
   - 测试 JSON 解析错误处理
   - 测试 LLM 调用错误处理

3. **需求摘要生成测试**
   - 测试 generate_requirement_summary 方法
   - 测试 _generate_simple_summary 方法
   - 测试有 LLM 调用和无 LLM 调用的情况
   - 测试文件写入操作

4. **模块提取测试**
   - 测试 analyze_granular_modules 方法
   - 测试不同架构层级的情况
   - 测试 JSON 解析错误处理
   - 测试 LLM 调用错误处理

5. **模块保存测试**
   - 测试 _save_granular_modules 方法
   - 测试目录创建
   - 测试文件写入
   - 测试错误处理

### 集成测试
1. **与 LLM 集成测试**
   - 测试需求分析和 LLM 的集成
   - 测试需求摘要生成和 LLM 的集成
   - 测试模块提取和 LLM 的集成

2. **与文件系统集成测试**
   - 测试文件写入操作
   - 测试目录创建操作

3. **与其他模块集成测试**
   - 测试与 clarifier.py 的集成
   - 测试与 architecture_manager.py 的集成

4. **端到端测试**
   - 测试完整的需求分析流程
   - 测试完整的模块提取流程

### 模拟依赖
- 使用 unittest.mock 模拟 LLM 调用
- 使用 unittest.mock 模拟文件操作
- 使用临时目录进行文件操作测试

### 测试边缘情况
- 空输入
- 错误输入
- LLM 调用失败
- JSON 解析错误
- 文件操作失败
