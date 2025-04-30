# MultiAgent 架构澄清与生成系统

## 环境准备

1. **克隆项目并进入目录**
   ```bash
   git clone <your-repo-url>
   cd multiAgent
   ```

2. **建议使用 Python 虚拟环境**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **安装依赖**
   ```bash
y   pip install -r requirements.txt
   ```

## 运行后端（FastAPI）

```bash
uvicorn webui.app:app --reload
```

- 默认监听 http://127.0.0.1:8000
- WebUI 静态页面位于 `webui/static/index.html`，可直接浏览器访问或通过 Nginx/VSCode Live Server 代理

## 运行 Clarifier CLI

```bash
python run_clarifier_new.py
```

## 主要目录说明

- `core/clarifier/`：Clarifier 业务主流程与架构推理
- `core/llm/`：LLM 封装与统一调用接口
- `webui/`：FastAPI 后端与前端静态页面
- `data/`：输入输出数据与持久化

## 环境变量

- 请在根目录下配置 `.env` 文件，至少包含：
  ```env
  OPENAI_API_KEY=sk-xxxxxx
  ```

## 常见问题
- 如遇依赖问题，请确保 Python 版本 >= 3.8，且已激活虚拟环境
- 如需自定义 LLM、数据路径等，可修改相关配置文件或源码

---
如有问题欢迎提 issue 或联系开发者。
