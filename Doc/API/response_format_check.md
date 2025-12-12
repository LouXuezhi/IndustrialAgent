# API响应格式检查报告

## 统一响应格式规范

### 成功响应格式
```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        // 具体数据字段
    },
    "timestamp": 1704067200  // Unix时间戳（可选）
}
```

### 错误响应格式
```javascript
{
    "code": 400,  // HTTP状态码或自定义错误码
    "message": "错误描述",
    "detail": "详细错误信息"  // 可选
}
```

## 已修正的接口

### Chat对话接口（7.0）
- ✅ 7.0 问答接口 (`POST /api/v1/ask`) ⭐ 已实现并统一格式

### 核心API接口（8.0）
- ✅ 8.1 文档摄取接口 (`POST /api/v1/docs/ingest`)
- ✅ 8.2 索引重建接口 (`POST /api/v1/docs/reindex`)
- ✅ 8.3 健康检查接口 (`GET /api/v1/admin/healthz`)
- ✅ 8.4 Ping接口 (`GET /api/v1/admin/ping`)

### 库管理接口（3.0）
- ✅ 3.1 库结构返回 (`GET /library`)
- ✅ 3.2 库删除 (`POST /library/deletedir`)
- ✅ 3.3 库添加 (`POST /library/createdir`)
- ✅ 3.4 库下载 (`POST /library/downloadlib`)
- ✅ 3.5 文件结构返回 (`POST /library`)
- ✅ 3.6 文件删除 (`POST /library/deletefile`)
- ✅ 3.7 文件添加 (`POST /library/uploadfile`)
- ✅ 3.8 文件下载 (`POST /library/downloadfile`)
- ✅ 3.9 文件向量化 (`POST /library/embedfile`)
- ✅ 3.10 文件查看 (`POST /library/checkfile`)
- ✅ 3.11 查看文件详情 (`POST /library/infofile`)

### 文档OCR接口（4.0）
- ✅ 4.1 上传文件 (`POST /fileocr/upload`)
- ✅ 4.2 归档文件 (`POST /fileocr/archive`)

### 回收站接口（6.0）
- ✅ 6.1 访问回收站 (`GET /trashbin/`)
- ✅ 6.2 文件结构返回 (`POST /trashbin/...`)

## 待检查的接口

以下接口响应示例为"暂无数据"，需要在实现时确保符合统一格式：

### 首页接口（1.0）
- ⚠️ 1.0 首页 (`GET /welcome`)
- ⚠️ 1.1 获取首页内容 (`GET /api/home/content`) - 已有响应但需检查格式

### 工作台接口（2.0）
- ⚠️ 2.1 产品手册 (`GET /desk/product-manuals`)
- ⚠️ 2.2.x 大模型agent相关接口
- ⚠️ 2.3 日历/日期 (`GET /desk/time/current`)
- ⚠️ 2.4 工厂状态监测 (`GET /desk/factory-status/overview`)
- ⚠️ 2.5 最近访问 (`GET /desk/users/recent-visits/{status}`)
- ⚠️ 2.6.x 自定义入口相关接口
- ⚠️ 2.7 知识库管理 (`GET /desk/knowledge`)

### Chat对话接口（7.0）
- ⚠️ 7.1 发送消息 (`GET /chat/send`)
- ⚠️ 7.2.1 新建对话 (`POST /chat/conversation/new`) - 已有响应但需检查格式
- ⚠️ 7.2.2 加载历史对话 (`GET /chat/conversation/list`)
- ⚠️ 7.2.3 加载对话历史 (`GET /chat/conversation/history`)
- ⚠️ 7.2.4 关闭对话 (`POST /chat/conversation/close`)
- ⚠️ 7.3 附件 (`GET /chat/attachment`)
- ⚠️ 7.4 重新生成 (`GET /chat/resend`)

### 开放平台接口（9.0）
- ⚠️ 9.1 获取平台信息 (`GET /api/open-platform/basic-info`)
- ⚠️ 9.2 SDK调用实例 (`GET /api/open-platform/sdk-example`)
- ⚠️ 9.3 获取网页嵌入码 (`GET /api/open-platform/embed-code`)

### 设置接口（10.0）
- ⚠️ 所有设置相关接口

## 修正要点

### 1. 成功响应
- ✅ 必须包含 `code: 0`
- ✅ 必须包含 `message: "success"`
- ✅ 数据必须放在 `data` 字段中
- ✅ 可选包含 `timestamp` 字段

### 2. 错误响应
- ✅ 必须包含 `code` 字段（HTTP状态码或自定义错误码）
- ✅ 必须包含 `message` 字段（错误描述）
- ✅ 可选包含 `detail` 字段（详细错误信息）
- ✅ 统一使用 `detail` 而不是 `details`

### 3. 数据类型统一
- ✅ 数字类型统一为数字（不是字符串），如 `"filenum": 2` 而不是 `"filenum": "2"`
- ✅ 移除注释（如 `//MIME Type`）
- ✅ 统一字段命名（如 `embedednum` 保持原样，但建议后续统一为 `embedded_num`）

## 检查清单

在实现新接口或更新现有接口时，请确保：

- [ ] 成功响应包含 `code: 0`、`message: "success"`、`data` 字段
- [ ] 错误响应包含 `code`、`message`、`detail` 字段
- [ ] 所有数据字段放在 `data` 对象中
- [ ] 数字类型使用数字而不是字符串
- [ ] 移除代码注释
- [ ] 错误消息使用英文，detail可以使用中文
- [ ] 时间戳使用Unix时间戳（整数）

## 示例对比

### ❌ 旧格式（不符合规范）
```javascript
{
    "message": "success",
    "dirnum": "2",
    "directories": [...]
}
```

### ✅ 新格式（符合规范）
```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 2,
        "directories": [...]
    },
    "timestamp": 1704067200
}
```

### ❌ 旧错误格式（不符合规范）
```javascript
{
    "message": "fail",
    "detail": "NoAccess"
}
```

### ✅ 新错误格式（符合规范）
```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

## 注意事项

1. **文件下载接口**：返回文件流时，可能不需要JSON格式，但错误响应仍需使用统一格式
2. **特殊状态码**：如204（空空间）等特殊状态码，也需要使用统一格式
3. **向后兼容**：如果已有前端在使用旧格式，需要考虑兼容性或版本迁移

## 已修正的接口详情

### 工作台接口（2.0）
- ✅ 2.1 产品手册 (`GET /desk/product-manuals`) - 修正code和message
- ✅ 2.4 工厂状态监测 (`GET /desk/factory-status/overview`) - 修正code和msg字段
- ✅ 2.5 最近访问 (`GET /desk/users/recent-visits/{status}`) - 修正code和message
- ✅ 2.6.2 自定义入口_添加 (`POST /desk/users/custom-entries/add`) - 修正错误响应格式

### 首页接口（1.0）
- ✅ 1.1 获取首页内容 (`GET /api/home/content`) - 统一message为"success"

### Chat对话接口（7.0）
- ✅ 7.2.1 新建对话 (`POST /chat/conversation/new`) - 修正code和timestamp格式

## 检查结果总结

### ✅ 已完全符合规范的接口
所有有具体响应数据的接口都已修正为统一格式：
- 成功响应：`{"code": 0, "message": "success", "data": {...}, "timestamp": ...}`
- 错误响应：`{"code": 400+, "message": "...", "detail": "..."}`

### ⚠️ 待实现的接口
以下接口响应示例为"暂无数据"，需要在实现时确保符合统一格式：
- 大部分工作台接口（2.2.x, 2.3, 2.6.1, 2.7等）
- Chat对话接口（7.1, 7.2.2, 7.2.3, 7.2.4, 7.3, 7.4）
- 开放平台接口（9.1, 9.2, 9.3）
- 设置接口（10.0）

## 修正要点总结

1. **成功响应code统一为0**：所有成功响应使用`code: 0`
2. **成功响应message统一为"success"**：统一使用`message: "success"`而不是"ok"或其他
3. **数据统一放在data字段**：所有业务数据放在`data`对象中
4. **错误响应包含code字段**：错误响应必须包含正确的HTTP状态码
5. **统一使用detail字段**：错误详情统一使用`detail`而不是`details`
6. **数字类型统一**：数字字段使用数字类型而不是字符串
7. **移除注释**：移除JSON中的注释（如`//MIME Type`）
8. **timestamp格式统一**：使用Unix时间戳（整数）而不是字符串

## 更新日期

- 2025-12-07: 完成核心API接口和库管理接口的响应格式统一
- 2025-12-07: 完成工作台、首页、Chat对话等接口的响应格式统一
- 2025-12-07: 创建响应格式检查报告

