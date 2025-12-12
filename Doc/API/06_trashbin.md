# 6.0 回收站模块API

> 创建人: 楼学之
> 更新人: 黄明峰
> 创建时间: 2025-12-01 19:51:40
> 更新时间: 2025-12-05 18:45:54

## 模块说明

回收站模块提供回收站相关的API接口，支持查看已删除的文档库和文件。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范

---

# ❗️6.0回收站_

**接口状态**

> 开发中

**接口URL**

> http://localhost/trashbin

**请求方式**

> GET

**Content-Type**

> json

**请求Body参数**

```javascript
暂无数据
```

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

# 6.0回收站

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-06 11:47:49

> 更新时间: 2025-12-06 11:47:54

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

## 6.1回收站_访问回收站

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 18:00:56

> 更新时间: 2025-12-06 11:47:57

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/trashbin/

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
        "directorybin": [
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
        "filebin": [
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

* 失败(404)

```javascript
{
    "code": 404,
    "message": "Not found",
    "detail": "回收站为空或不存在"
}
```

**Query**

## 6.2回收站_文件结构返回

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 18:07:59

> 更新时间: 2025-12-06 11:48:05

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> 未填写

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

* 存在失败(404)

```javascript
{
    "code": 404,
    "message": "Not exist",
    "detail": "文档库不存在"
}
```

**Query**

