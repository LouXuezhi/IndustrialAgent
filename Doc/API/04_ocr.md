# 4.0 文档OCR模块API

> 创建人: 楼学之
> 更新人: 黄明峰
> 创建时间: 2025-12-01 19:49:50
> 更新时间: 2025-12-05 18:45:54

## 模块说明

文档OCR模块提供文档OCR识别和归档相关的API接口。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范

---

# ❗️4.0文档OCR_

**接口状态**

> 开发中

**接口URL**

> http://localhost/fileocr

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

# 4.0文档OCR

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-06 11:46:56

> 更新时间: 2025-12-06 11:47:01

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

## 4.1文档OCR_上传文件

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 17:35:31

> 更新时间: 2025-12-06 11:47:05

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/fileocr/upload

**请求方式**

> POST

**Content-Type**

> form-data

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
//返回OCR文件
```

* OCR失败(404)

```javascript
{
    "code": 404,
    "message": "OCR failed",
    "detail": "OCR处理失败"
}
```

**Query**

## 4.2文档OCR_归档文件

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-03 17:44:28

> 更新时间: 2025-12-07 22:10:36

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/fileocr/archive

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

**Query**

