# 潜在合并冲突

## webui/app.py
- 我们的分支添加了前端资源挂载点 `/assets` 和新的API端点 `/api/get_global_state`
- main分支重构了API系统，将路由移至单独的文件中
- 主要冲突点:
  - 根路由 `/` 的处理方式
  - 静态文件挂载
  - 全局状态API端点

## 解决方案
合并时需要保留两个分支的功能:
1. 保留main分支的API路由重构
2. 保留feature分支的前端资源挂载和新API端点
3. 确保根路由指向新的React前端
