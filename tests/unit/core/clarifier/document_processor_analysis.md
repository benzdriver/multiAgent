# document_processor.py 模块分析

## 模块概述
document_processor.py 是 core/clarifier 包中的组件，负责读取和分析文档，提取架构信息，并生成需求到架构的映射文档。该模块使用 LLM 进行文档分析和信息提取。

## 类和方法

### DocumentProcessor
主要类，提供文档处理功能。

**初始化方法：**
- `__init__(input_path=None, logger=None)`: 初始化文档处理器，设置输入路径和日志记录器。

**主要方法：**
- `read_all_markdown_files()`: 读取输入目录下的所有 Markdown 文件
- `analyze_all_documents(documents, llm_call)`: 分析所有文档并理解架构
- `extract_architecture_info(architecture_doc, llm_call)`: 从技术架构文档中提取架构信息
- `generate_mapping_doc(analysis, architecture_info, llm_call)`: 生成需求到架构的映射文档

## 依赖关系
- `Path` 从 pathlib 模块：用于文件路径操作
- `Dict`, `List`, `Optional` 从 typing 模块：用于类型注解
- `asyncio`：用于异步操作
- `json`：用于 JSON 序列化和反序列化
- `llm.llm_executor.run_prompt`：用于执行 LLM 提示并获取响应

## 工作流程
1. 初始化文档处理器，设置输入路径
2. 读取输入目录下的所有 Markdown 文件
3. 分析所有文档，提取架构信息
4. 生成需求到架构的映射文档

## 文件操作
- 读取输入目录下的 Markdown 文件
- 创建输入目录（如果不存在）
- 写入映射文档到输入目录

## 错误处理
- 使用 try/except 处理文件读取错误
- 记录错误信息到日志或打印到控制台

## LLM 交互
- 使用 LLM 分析文档内容
- 使用 LLM 提取架构信息
- 使用 LLM 生成映射文档

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试提供自定义参数初始化
   - 测试输入目录不存在的情况

2. **文件操作测试**
   - 测试 read_all_markdown_files 方法
   - 测试空目录的情况
   - 测试文件读取错误的情况

3. **文档分析测试**
   - 测试 analyze_all_documents 方法
   - 模拟 LLM 响应
   - 测试不同文档内容的情况

4. **架构信息提取测试**
   - 测试 extract_architecture_info 方法
   - 模拟 LLM 响应
   - 测试不同架构文档的情况

5. **映射文档生成测试**
   - 测试 generate_mapping_doc 方法
   - 模拟 LLM 响应
   - 测试文件写入操作

### 集成测试
1. **与 LLM 集成测试**
   - 测试文档分析和 LLM 的集成
   - 测试架构信息提取和 LLM 的集成
   - 测试映射文档生成和 LLM 的集成

2. **与文件系统集成测试**
   - 测试读取实际文件
   - 测试写入实际文件

3. **端到端测试**
   - 测试完整的文档处理流程
   - 从读取文件到生成映射文档

### 模拟依赖
- 使用 unittest.mock 模拟 LLM 调用
- 使用临时目录进行文件操作测试

### 测试边缘情况
- 空输入
- 错误输入
- LLM 调用失败
- 文件操作失败
