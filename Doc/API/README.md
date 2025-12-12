# API文档索引

本文档索引提供了所有API模块文档的导航和快速参考。

## 文档结构

```
Doc/api/
├── README.md              # 本文档（API文档索引）
├── 00_common.md          # 公共文档（全局参数、响应格式规范）
├── 01_home.md            # 首页模块API
├── 02_workbench.md       # 工作台模块API
├── 03_library.md         # 库管理模块API
├── 04_ocr.md             # 文档OCR模块API
├── 05_agent_flow.md      # Agent流模块API
├── 06_trashbin.md        # 回收站模块API
├── 07_chat.md            # Chat对话模块API
├── 08_core_api.md        # 核心API接口模块 ⭐（已实现）
├── 09_open_platform.md   # 开放平台模块API
└── 10_settings.md        # 设置模块API
```

## 文档说明

- 所有模块文档都引用了 [00_common.md](./00_common.md) 公共文档
- 核心API接口模块（08_core_api.md）已实现，其他模块处于开发中
- 响应格式已统一，所有接口遵循统一的响应格式规范

## 快速导航

### 公共文档

- **[00_common.md](./00_common.md)** - 公共文档
  - 全局公共参数（Header、Query、Body）
  - 统一响应格式规范
  - 常见状态码说明

### 功能模块API

1. **[01_home.md](./01_home.md)** - 首页模块
   - 获取首页内容

2. **[02_workbench.md](./02_workbench.md)** - 工作台模块
   - 产品手册
   - 大模型agent（智能排产、数据大屏、周报总结、竞对动向）
   - 日历/日期
   - 工厂状态监测
   - 最近访问
   - 自定义入口
   - 知识库管理

3. **[03_library.md](./03_library.md)** - 库管理模块
   - 库结构返回
   - 库删除、添加、下载
   - 文件结构返回
   - 文件删除、添加、下载
   - 文件向量化
   - 文件查看、详情

4. **[04_ocr.md](./04_ocr.md)** - 文档OCR模块
   - 上传文件
   - 归档文件

5. **[05_agent_flow.md](./05_agent_flow.md)** - Agent流模块
   - Agent流程相关接口

6. **[06_trashbin.md](./06_trashbin.md)** - 回收站模块
   - 访问回收站
   - 文件结构返回

7. **[07_chat.md](./07_chat.md)** - Chat对话模块 ⭐
   - **问答接口** (`POST /api/v1/ask`) ⭐ 已实现
   - 发送消息
   - 新建对话
   - 加载历史对话
   - 加载对话历史
   - 关闭对话
   - 附件
   - 重新生成

8. **[08_core_api.md](./08_core_api.md)** - 核心API接口模块 ⭐
   - 文档摄取接口 (`POST /api/v1/docs/ingest`)
   - 索引重建接口 (`POST /api/v1/docs/reindex`)
   - 健康检查接口 (`GET /api/v1/admin/healthz`)
   - Ping接口 (`GET /api/v1/admin/ping`)

9. **[09_open_platform.md](./09_open_platform.md)** - 开放平台模块
   - 获取平台信息
   - SDK调用实例
   - 获取网页嵌入码

10. **[10_settings.md](./10_settings.md)** - 设置模块
   - 设置相关接口

## 使用说明

### 查看公共文档

在查看任何模块API文档前，建议先阅读 [00_common.md](./00_common.md) 了解：
- 全局公共参数（如X-API-Key）
- 统一响应格式规范
- 常见状态码

### 查看模块文档

每个模块文档包含：
- 模块概述
- 目录级参数（Header、Query、Body）
- 目录认证信息
- 具体接口定义（请求参数、响应示例、错误处理）

### 响应格式

所有接口响应遵循统一格式：
- **成功**: `{"code": 0, "message": "success", "data": {...}, "timestamp": ...}`
- **错误**: `{"code": 400+, "message": "...", "detail": "..."}`

详细说明请参考 [00_common.md](./00_common.md)。

## 接口状态说明

- **已实现**: 接口已开发完成，可直接使用
- **开发中**: 接口正在开发，响应示例可能为占位数据

## 认证说明

除以下接口外，所有接口都需要在Header中传递 `X-API-Key`：
- `GET /api/v1/admin/healthz` - 健康检查
- `GET /api/v1/admin/ping` - Ping
- `GET /` - 根路径

## 更新日志

- 2025-12-07: 按模块拆分API文档，统一响应格式
- 2025-12-07: 创建API文档索引

## 相关文档

- [模块文档](../Modules/README.md) - 系统模块设计文档
- [响应格式检查](../API/response_format_check.md) - 响应格式检查报告

