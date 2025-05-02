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
   pip install -r requirements.txt
   ```

## 使用说明

### 启动应用

始终使用以下命令启动应用以确保使用最新的前端UI:

```bash
python -m webui.app
```

- 默认监听 http://0.0.0.0:8080
- WebUI 使用React前端实现，位于 `webui/frontend/` 目录，构建后的页面通过 `http://localhost:8080` 访问

### 清除浏览器缓存

如果UI显示不正确或看到旧版UI，请运行:

```bash
python clear_browser_cache.py
```

此脚本将引导您清除浏览器缓存并重启应用。

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