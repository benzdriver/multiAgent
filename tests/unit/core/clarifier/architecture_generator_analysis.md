# architecture_generator.py 模块分析

## 模块概述
architecture_generator.py 是 core/clarifier 包中的组件，负责根据需求分析结果生成架构文档。该模块使用 LLM 进行架构需求分析和文档生成，并保存架构状态。

## 类和方法

### ArchitectureGenerator
主要类，提供架构文档生成功能。

**初始化方法：**
- `__init__(logger=None)`: 初始化架构生成器，设置输出目录和日志记录器。

**主要公共方法：**
- `analyze_architecture_needs(requirement_analysis, llm_call)`: 根据需求分析结果，分析架构需求
- `generate_architecture_documents(requirement_analysis, architecture_analysis, llm_call)`: 生成架构文档
- `save_architecture_state(requirement_analysis, architecture_analysis)`: 保存架构状态

**私有方法：**
- `_generate_architecture_overview(requirement_analysis, architecture_analysis, llm_call)`: 生成架构概述文档
- `_generate_detailed_design(requirement_analysis, architecture_analysis, llm_call)`: 生成详细设计文档
- `_generate_interface_documentation(architecture_analysis, llm_call)`: 生成接口文档
- `_generate_deployment_documentation(architecture_analysis, llm_call)`: 生成部署文档

## 依赖关系
- `Path` 从 pathlib 模块：用于文件路径操作
- `json`：用于 JSON 序列化和反序列化
- `Dict`, `List`, `Any`, `Callable`, `Awaitable` 从 typing 模块：用于类型注解
- `run_prompt` 从 llm.llm_executor 模块：用于执行 LLM 提示并获取响应
- `clean_code_output` 从 llm.prompt_cleaner 模块：用于清理 LLM 返回的代码输出
- `datetime` 从 datetime 模块：用于生成时间戳

## 工作流程
1. 初始化架构生成器，设置输出目录
2. 根据需求分析结果，分析架构需求
3. 生成架构文档，包括概述、详细设计、接口和部署文档
4. 保存架构状态

## 文件操作
- 创建输出目录
- 写入架构文档（Markdown 格式）
- 保存架构状态（JSON 格式）

## 错误处理
- 使用 try/except 处理 JSON 解析错误
- 记录错误信息到日志或打印到控制台
- 提供默认值和回退机制

## LLM 交互
- 使用 LLM 分析架构需求
- 使用 LLM 生成架构文档
- 处理 LLM 返回的不同格式（字符串或字典）

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试提供自定义参数初始化

2. **架构需求分析测试**
   - 测试 analyze_architecture_needs 方法
   - 模拟 LLM 响应
   - 测试 JSON 解析错误处理
   - 测试不同输入格式

3. **文档生成测试**
   - 测试 generate_architecture_documents 方法
   - 测试各个文档生成方法
   - 测试文件写入操作
   - 测试不同输入格式

4. **架构状态保存测试**
   - 测试 save_architecture_state 方法
   - 测试文件写入操作
   - 测试生成的 JSON 格式

### 集成测试
1. **与 LLM 集成测试**
   - 测试架构需求分析和 LLM 的集成
   - 测试文档生成和 LLM 的集成

2. **与文件系统集成测试**
   - 测试文件写入操作
   - 测试目录创建操作

3. **与其他模块集成测试**
   - 测试与 clarifier.py 的集成
   - 测试与 requirement_analyzer.py 的集成

4. **端到端测试**
   - 测试完整的架构文档生成流程
   - 测试从需求分析到架构文档生成的完整流程

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
