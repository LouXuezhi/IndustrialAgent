# 3.0 库管理模块API（JWT + 私人/群组库）

> 所有受保护接口需 Bearer JWT：`Authorization: Bearer <access_token>`

## 模块说明
- 结构：User/Group → Library → Document
- 隔离：每库独立存储与向量集合（Chroma：`library_<library_id>`；默认库 `library_default`）
- 权限现状：`owner_type=user` 已校验仅库所有者可操作；`owner_type=group` 预留，成员校验待实现
- 参考：`00_common.md`、`../Modules/06_document_library.md`

---

## 3.1 创建库 `POST /api/v1/docs/libraries`
- 认证：Bearer JWT
- Body:
  - `name` (str, required)
  - `description` (str, optional)
  - `owner_type` (enum `user|group`, default `user`)
  - `owner_id` (uuid, optional；当 owner_type=user 且提供时必须等于当前用户；group 预留)
- 行为：创建库，向量集合名 `library_<library_id>`
- 响应：`StandardResponse<LibraryResponse>`

## 3.2 列出库 `GET /api/v1/docs/libraries`
- 认证：Bearer JWT
- Query:
  - `owner_id` (uuid, optional，默认当前用户)
  - `owner_type` (enum `user|group`, default `user`)
- 仅允许查询当前用户的 user 库；group 查询待成员校验实现
- 响应：`StandardResponse<List<LibraryResponse>>`

## 3.3 获取库详情 `GET /api/v1/docs/libraries/{library_id}`
- 认证：Bearer JWT
- 仅库所属用户可查看（group 校验待实现）
- 响应：`StandardResponse<LibraryResponse>`

## 3.4 更新库 `PUT /api/v1/docs/libraries/{library_id}`
- 认证：Bearer JWT
- Body:
  - `name` (str, optional)
  - `description` (str, optional)
- 仅库所属用户可修改
- 响应：`StandardResponse<LibraryResponse>`

## 3.5 删除库 `DELETE /api/v1/docs/libraries/{library_id}`
- 认证：Bearer JWT
- 仅库所属用户可删；删除时尝试删除对应 Chroma collection（best-effort）
- 响应：`StandardResponse<{ "deleted": true }>`

## 3.6 文档摄取 `POST /api/v1/docs/ingest`
- 认证：Bearer JWT
- Form-Data:
  - `file` (UploadFile, required)
  - `library_id` (uuid, optional；指定则需库权限；未指定存入默认库)
- 行为：写入 DB（Document/Chunk）并写入库向量集合
- 响应：`StandardResponse<IngestResponse>`（含 `document_id`, `chunks`, `library_id`）

## 3.7 重建索引占位 `POST /api/v1/docs/reindex`
- 认证：Bearer JWT
- 响应：`StandardResponse<{ "status": "queued" }>`

---

## 数据结构
- `LibraryResponse`: `id`, `name`, `owner_id`, `owner_type`, `description`, `vector_collection_name`
- `IngestResponse`: `document_id`, `chunks`, `library_id|null`

---

## 权限与扩展
- user 库：仅库所有者可管理/摄取。
- group 库：已接入群组成员校验
  - 创建库：group owner/admin
  - 列表/详情/摄取：owner/admin/member
  - 更新/删除：owner/admin
- 后续可扩展：成员角色更细粒度、库分享策略、删除库时级联删除库内文档与向量数据。

# ❗️3.0库管理_

**接口状态**

> 开发中

**接口URL**

> http://localhost/library

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

# 3.0库管理

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-06 11:45:06

> 更新时间: 2025-12-06 11:45:35

```text
暂无描述
```

**目录Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录认证信息**

> 继承父级

**Query**

## 3.1库管理_库结构返回

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-02 10:24:58

> 更新时间: 2025-12-06 11:45:42

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 2,
        "directories": [
            {
                "dirname": "dir1",
                "filenum": 2,
                "embedednum": 2,
                "size": "132.2MB",
                "creator": "xusun000"
            },
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 3,
                "size": "43.5MB",
                "creator": "xusun001"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 查找失败(204)

```javascript
{
    "code": 204,
    "message": "Empty space",
    "detail": "空空间返回"
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "未登录或无权限"
}
```

**Query**

## 3.2库管理_库删除

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-02 16:36:03

> 更新时间: 2025-12-06 11:45:56

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/deletedir

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "dirname":"dir1"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 1,
        "directories": [
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 3,
                "size": "43.5MB",
                "creator": "xusun001"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文档库不存在"
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

**Query**

## 3.3库管理_库添加

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-02 16:57:17

> 更新时间: 2025-12-06 11:45:46

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/createdir

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "dirname":"dir1"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 2,
        "directories": [
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 4,
                "size": "43.5MB",
                "creator": "xusun001"
            },
            {
                "dirname": "dir1",
                "filenum": 0,
                "embedednum": 0,
                "size": "0",
                "creator": "xusun001"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

**Query**

## 3.4库管理_库下载

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 15:29:36

> 更新时间: 2025-12-06 11:46:04

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/downloadlib

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "dirname":"dir1"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
//返回文件
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Download failed",
    "detail": "下载失败，文档库不存在"
}
```

**Query**

## 3.5库管理_文件结构返回

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 15:48:51

> 更新时间: 2025-12-06 11:46:07

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "dirname":"dir1"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirname": "dir1",
        "filenum": 2,
        "files": [
            {
                "filename": "F1.txt",
                "filetype": "text/plain",
                "size": "1.2MB",
                "embeded": "yes",
                "creator": "xusun01"
            },
            {
                "filename": "F2.pdf",
                "filetype": "application/pdf",
                "size": "1.7MB",
                "embeded": "yes",
                "creator": "xusun01"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文档库不存在"
}
```

**Query**

## 3.6库管理_文件删除

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 15:46:17

> 更新时间: 2025-12-06 11:46:14

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/deletefile

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "filepath":"/dir1/f1.txt"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 2,
        "directories": [
            {
                "dirname": "dir1",
                "filenum": 1,
                "embedednum": 1,
                "size": "32.2MB",
                "creator": "xusun000"
            },
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 3,
                "size": "43.5MB",
                "creator": "xusun001"
            }
        ],
        "dirname": "dir1",
        "filenum": 1,
        "files": [
            {
                "filename": "F2.pdf",
                "filetype": "application/pdf",
                "size": "1.7MB",
                "embeded": "yes",
                "creator": "xusun01"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文档不存在"
}
```

**Query**

## 3.7库管理_文件添加

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 16:26:47

> 更新时间: 2025-12-06 11:46:16

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/uploadfile

**请求方式**

> POST

**Content-Type**

> form-data

**请求Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| filepath | /dir1/f1 | string | 是 | - |
| file | - | file | 是 | - |

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirnum": 2,
        "directories": [
            {
                "dirname": "dir1",
                "filenum": 2,
                "embedednum": 2,
                "size": "132.2MB",
                "creator": "xusun000"
            },
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 3,
                "size": "43.5MB",
                "creator": "xusun001"
            }
        ],
        "dirname": "dir1",
        "filenum": 2,
        "files": [
            {
                "filename": "F1.txt",
                "filetype": "text/plain",
                "size": "1.2MB",
                "embeded": "yes",
                "creator": "xusun01"
            },
            {
                "filename": "F2.pdf",
                "filetype": "application/pdf",
                "size": "1.7MB",
                "embeded": "yes",
                "creator": "xusun01"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文档库不存在"
}
```

**Query**

## 3.8库管理_文件下载

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 16:40:25

> 更新时间: 2025-12-06 11:46:21

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/downloadfile

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "filepath":"/dir1/f1.txt"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
//文件返回
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文件不存在"
}
```

**Query**

## 3.9库管理_文件向量化

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 16:56:35

> 更新时间: 2025-12-06 11:46:26

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/embedfile

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "filepath":"/dir1/f1.txt",
    "rewrite":"yes"// default -> no
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "dirname": "dir1",
        "directories": [
            {
                "dirname": "dir1",
                "filenum": 2,
                "embedednum": 2,
                "size": "132.2MB",
                "creator": "xusun000"
            },
            {
                "dirname": "dir2",
                "filenum": 4,
                "embedednum": 3,
                "size": "43.5MB",
                "creator": "xusun001"
            }
        ],
        "filenum": 2,
        "files": [
            {
                "filename": "F1.txt",
                "filetype": "text/plain",
                "size": "1.2MB",
                "embeded": "yes",
                "creator": "xusun01"
            },
            {
                "filename": "F2.pdf",
                "filetype": "application/pdf",
                "size": "1.7MB",
                "embeded": "yes",
                "creator": "xusun01"
            }
        ]
    },
    "timestamp": 1704067200
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文件不存在"
}
```

* 未复写向量化(400)

```javascript
{
    "code": 400,
    "message": "Already embedded",
    "detail": "文件已向量化，如需重新向量化请设置rewrite为yes"
}
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

**Query**

## 3.10库管理_文件查看

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 17:10:31

> 更新时间: 2025-12-06 11:46:28

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/checkfile

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "filepath":"/dir1/f1.txt"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
//返回文件
```

* 权限失败(403)

```javascript
{
    "code": 403,
    "message": "No access",
    "detail": "无权限访问"
}
```

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文件不存在"
}
```

**Query**

## 3.11库管理_查看文件详情

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 17:14:59

> 更新时间: 2025-12-06 11:46:31

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/library/infofile

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
{
    "filepath":"/dir1/f1.txt"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
    "filename":"f1.txt",
    "dirname":"dir1",
    "filetype":"text/plain", //MIME Type
    "size":"12.5MB",
    "creator":"xusun01",
    "embeded":"yes",
    "access":"rwe",//read write embeded "r_e" "_re" 
    "created_at":"1764753812",
    "modified_at":"1764753854"
}
```

* 失败(404)

```javascript
暂无数据
```

**Query**

