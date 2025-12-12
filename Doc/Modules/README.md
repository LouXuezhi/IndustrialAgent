# 模块文档索引

本文档索引提供了所有模块文档的导航和快速参考。

## 文档结构

### 核心架构文档

1. **[00_overview.md](./00_overview.md)** - 项目模块总览
   - 架构图参考
   - 核心模块划分
   - 模块间通信概览
   - 数据流示例
   - 权限模型

### API层文档

2. **[01_api_layer.md](./01_api_layer.md)** - API层模块文档
   - 问答接口 (`/ask`)
   - 文档管理接口 (`/docs`)
   - 管理接口 (`/admin`)
   - 安全机制
   - 错误处理

### Agent层文档

3. **[02_agent_layer.md](./02_agent_layer.md)** - Agent层模块文档
   - QA Agent核心实现
   - 工具系统
   - 用户上下文管理
   - 角色与Prompt关联

### RAG层文档

4. **[03_rag_layer.md](./03_rag_layer.md)** - RAG层模块文档
   - RAG Pipeline
   - 混合检索器（支持多文档库）
   - 提示模板管理（角色相关）
   - 文档摄取
   - 响应评估

### 数据库层文档

5. **[04_database_layer.md](./04_database_layer.md)** - 数据库层模块文档
   - 数据模型（User, Group, DocumentLibrary, Document等）
   - CRUD操作
   - 会话管理
   - 数据库迁移

### 核心层文档

6. **[05_core_layer.md](./05_core_layer.md)** - 核心层模块文档
   - 配置管理
   - 安全验证
   - 日志配置
   - 邮件发送服务（阿里云邮件推送）

### 文档库模块文档

7. **[06_document_library.md](./06_document_library.md)** - 文档库模块文档
   - 文档库数据模型（私人库、群组库）
   - 文档库服务（CRUD、权限检查）
   - 文档存储管理
   - 权限检查
   - 与RAG模块集成

### 用户管理模块文档

8. **[07_user_management.md](./07_user_management.md)** - 用户管理模块文档
   - 用户、群组、权限数据模型
   - 认证服务（JWT、API Key）
   - 邮箱验证服务（基于阿里云邮件推送）
   - 权限检查服务（RBAC）
   - 角色定义和管理
   - 角色与Prompt关联

### 模块通信协议文档

9. **[08_module_communication.md](./08_module_communication.md)** - 模块间通信协议文档
   - API → Agent通信
   - Agent → RAG Pipeline通信
   - RAG Pipeline → Retriever通信
   - Retriever → Document Library Service通信
   - 错误处理和异常传递
   - 数据一致性保证

### 数据隔离文档

10. **[09_data_isolation.md](./09_data_isolation.md)** - 数据隔离和Agent记忆隔离文档
    - 两层结构说明（Group/User → Library → Document）
    - 数据完全隔离机制
    - Agent记忆隔离机制
    - 实现检查清单
    - 测试建议

## 快速查找指南

### 按功能查找

- **用户认证和授权**: [07_user_management.md](./07_user_management.md)
- **文档库管理**: [06_document_library.md](./06_document_library.md)
- **问答流程**: [02_agent_layer.md](./02_agent_layer.md) + [03_rag_layer.md](./03_rag_layer.md)
- **API接口**: [01_api_layer.md](./01_api_layer.md)
- **数据库设计**: [04_database_layer.md](./04_database_layer.md)
- **模块间通信**: [08_module_communication.md](./08_module_communication.md)

### 按角色查找

- **开发者**: 从 [00_overview.md](./00_overview.md) 开始，然后查看各模块详细文档
- **架构师**: 重点关注 [00_overview.md](./00_overview.md) 和 [08_module_communication.md](./08_module_communication.md)
- **DBA**: 重点关注 [04_database_layer.md](./04_database_layer.md)
- **前端开发者**: 重点关注 [01_api_layer.md](./01_api_layer.md)

## 关键概念索引

### 权限和角色

- **角色定义**: [07_user_management.md#角色定义](./07_user_management.md#角色定义)
- **权限模型**: [00_overview.md#权限模型](./00_overview.md#权限模型)
- **角色与Prompt关联**: [02_agent_layer.md#角色与Prompt关联](./02_agent_layer.md#角色与Prompt关联)

### 文档库

- **两层结构**: [09_data_isolation.md#两层结构](./09_data_isolation.md#两层结构)
- **私人文档库**: [06_document_library.md#DocumentLibrary文档库表](./06_document_library.md#DocumentLibrary文档库表)
- **群组文档库**: [06_document_library.md#DocumentLibrary文档库表](./06_document_library.md#DocumentLibrary文档库表)
- **文档库权限**: [06_document_library.md#权限检查](./06_document_library.md#权限检查)
- **数据隔离**: [09_data_isolation.md](./09_data_isolation.md)
- **Agent记忆隔离**: [09_data_isolation.md#Agent记忆隔离机制](./09_data_isolation.md#Agent记忆隔离机制)

### 数据流

- **问答流程**: [00_overview.md#完整问答流程](./00_overview.md#完整问答流程)
- **文档上传流程**: [00_overview.md#文档上传流程](./00_overview.md#文档上传流程)
- **模块通信**: [08_module_communication.md](./08_module_communication.md)

## 数据模型关系图

**两层结构**:
```
私人库结构:
User
  └── Library (DocumentLibrary, type=PRIVATE)
      └── Document
          └── Chunk

群组库结构:
Group
  └── Library (DocumentLibrary, type=GROUP)
      └── Document
          └── Chunk
```

**详细关系**:
```
User (用户)
├── owned_libraries (拥有的私人文档库, type=PRIVATE)
├── group_memberships (群组成员关系)
└── feedback (反馈记录)

Group (群组)
├── members (群组成员)
└── libraries (群组文档库, type=GROUP, owner_id指向Group)

DocumentLibrary (文档库)
├── documents (文档列表, 直接包含)
├── owner_id (根据type指向User或Group)
└── vector_collection_name (独立的向量集合名称)

Document (文档)
├── library_id (所属文档库, 必填)
├── owner (所有者)
└── chunks (文档块)

Chunk (文档块)
└── document (所属文档)
```

**重要说明**:
- 只有两层结构：Group/User → Library → Document
- 不需要GroupLibrary关联表
- Library直接包含Document（通过Document.library_id）
- 每个Library有独立的向量集合（vector_collection_name）
- 不同Library之间的数据完全隔离

## 更新日志

- **2024-01-XX**: 初始版本，包含所有核心模块文档
- **2024-01-XX**: 添加文档库模块和用户管理模块文档
- **2024-01-XX**: 添加模块间通信协议文档
- **2024-01-XX**: 细化权限系统和角色配置
- **2024-01-XX**: 明确两层结构（Group/User → Library → Document）
- **2024-01-XX**: 添加数据隔离和Agent记忆隔离文档

## 贡献指南

添加新模块文档时：
1. 创建新的模块文档文件（如 `09_new_module.md`）
2. 在本索引文件中添加链接和描述
3. 更新相关模块文档中的交叉引用
4. 更新 [00_overview.md](./00_overview.md) 中的模块列表

