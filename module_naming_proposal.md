# 模块命名规范优化提案

## 当前命名规范分析

当前的模块命名规范使用 `{ComponentType} - {Domain}` 或 `{ComponentType}_-_{Domain}` 格式，例如：
- "UI Components - Documents"
- "Controllers_-_Authentication"
- "Layout Components - Forms"
- "Pages_-_Workspace"

### 存在的问题

1. **层级不明确**：虽然每个模块在 `full_summary.json` 中有明确的 `layer` 属性（如 "Presentation"、"Business"），但这在模块名称中并不可见
2. **组件类型与层级混淆**：当前命名中的组件类型（如 "UI Components"、"Controllers"）与层级概念（如 "Presentation"、"Business"）存在重叠但不完全一致
3. **不符合现代前端项目组织方式**：现代前端项目通常使用目录结构来反映架构层级，而不是在文件名中编码这些信息

## 建议的命名规范

### 方案一：目录结构反映层级和领域

```
src/
├── presentation/           # 表现层
│   ├── components/         # UI组件
│   │   ├── workspace/      # 工作区域相关组件
│   │   │   └── Button.tsx
│   │   └── documents/      # 文档相关组件
│   │       └── DocumentCard.tsx
│   └── layouts/            # 布局组件
│       └── forms/          # 表单相关布局
│           └── FormLayout.tsx
├── pages/                  # 页面组件
│   ├── workspace/          # 工作区页面
│   │   └── Dashboard.tsx
│   └── documents/          # 文档相关页面
│       └── DocumentList.tsx
├── business/               # 业务层
│   └── controllers/        # 控制器
│       └── authentication/ # 认证相关控制器
│           └── AuthController.ts
└── data/                   # 数据层
    └── services/           # 服务
        └── documents/      # 文档相关服务
            └── DocumentService.ts
```

### 方案二：保留当前命名但添加层级前缀

如果需要保持与现有系统的兼容性，可以考虑在当前命名前添加层级前缀：

```
Presentation.UI_Components.Workspace
Presentation.Layout_Components.Forms
Presentation.Pages.Workspace
Business.Controllers.Authentication
```

## 优势比较

### 方案一优势
- 符合现代前端项目组织方式
- 通过目录结构直观反映层级关系
- 提高代码可发现性和可维护性
- 简化文件命名，更加简洁明了

### 方案二优势
- 与现有系统保持一定兼容性
- 在不改变文件结构的情况下提高命名清晰度
- 便于在过渡期间逐步迁移

## 建议实施方案

建议采用**方案一**，通过目录结构反映层级和领域，这更符合现代前端项目的最佳实践。

实施步骤：
1. 创建新的目录结构
2. 逐步迁移现有模块到新结构
3. 更新相关引用和依赖
4. 更新文档和开发指南

这种方案虽然前期工作量较大，但长期来看将大大提高项目的可维护性和开发效率。
