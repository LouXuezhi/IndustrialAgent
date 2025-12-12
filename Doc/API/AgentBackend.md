# 全局公共参数

**全局Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥，用于身份验证（除健康检查接口外，其他接口都需要） |

**全局Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**全局Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**全局认证方式**

> API Key认证（通过X-API-Key Header传递）

**注意**: 除健康检查接口（`/api/v1/admin/healthz`、`/api/v1/admin/ping`、`/`）外，所有接口都需要在Header中传递`X-API-Key`。

# 统一响应格式规范

## 成功响应格式

所有成功响应统一使用以下格式：

```javascript
{
    "code": 0,              // 状态码，0表示成功
    "message": "success",   // 响应消息
    "data": {               // 响应数据（根据接口不同而变化）
        // 具体数据字段
    },
    "timestamp": 1704067200 // Unix时间戳（可选）
}
```

## 错误响应格式

所有错误响应统一使用以下格式：

```javascript
{
    "code": 400,            // HTTP状态码或自定义错误码
    "message": "错误描述",  // 错误消息
    "detail": "详细错误信息" // 可选的详细错误信息
}
```

## 常见状态码

| 状态码 | HTTP状态码 | 中文描述 |
| --- | ---- | ---- |
| 0 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权（API Key无效或缺失） |
| 403 | 403 | 无权限访问 |
| 404 | 404 | 资源不存在 |
| 422 | 422 | 请求体验证失败 |
| 500 | 500 | 服务器内部错误 |

# 状态码说明

| 状态码 | 中文描述 |
| --- | ---- |
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

# ❗️1.0首页_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:48:08

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/welcome

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

# 1.0首页_获取首页内容

> 创建人: 曾亚琦

> 更新人: 楼学之

> 创建时间: 2025-12-03 20:52:36

> 更新时间: 2025-12-11 00:31:52

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/api/home/content?lang=zh-CN

**请求方式**

> GET

**Content-Type**

> none

**请求Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| lang | zh-CN | string | 是 | 语言（不填默认中文） |

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
  "code": 0,
  "message": "success",
  "data": {
    "banner": {
      "title": "赋能工业数智化",
      "subtitle": "大模型 & Agent 一体化平台",
      "cta_buttons": [
        { "type": "trial", "text": "立即体验" },
        { "type": "manual", "text": "使用手册" }
      ]
    },
    "feature_cards": [
      {
        "id": 1,
        "title": "大模型赋能工业4.0",
        "description": "大模型带来新的赋能方式..."
      },
      {
        "id": 2,
        "title": "文档数字化，处理自动化",
        "description": "通过文档结构化和自动处理..."
      }
    ],
    "solution_cards": [
      {
        "id": "agent_build",
        "title": "Agent构建",
        "description": "使用图形化节点快速搭建 Agent 流程"
      },
      {
        "id": "kb_build",
        "title": "知识库构建",
        "description": "一键导入文档，构建企业知识库"
      },
      {
        "id": "flow_automation",
        "title": "流程自动化",
        "description": "连接业务系统，实现自动化流转"
      }
    ]
  }
}

```

* 失败(404)

```javascript
暂无数据
```

**Query**

# ❗️2.0工作台_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:46:57

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk

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

# 2.0工作台

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:54:10

> 更新时间: 2025-12-05 18:54:19

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

## 2.1工作台_产品手册

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:38:27

> 更新时间: 2025-12-05 18:54:22

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/product-manuals

**请求方式**

> GET

**Content-Type**

> json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 否 | - |

**请求Body参数**

```javascript
暂无数据
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
		"title": "非专而生战般一",
		"content": "Duis elit",
		"updateTime": "2007-04-29 00:31:07"
	},
	"timestamp": 1704067200
}
```

* 失败(404)

```javascript
{
	"code": 404,
	"message": "Not found",
	"detail": "资源不存在"
}
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 否 | - |

**Query**

## 2.2.1工作台_大模型agent_智能排产

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:45:50

> 更新时间: 2025-12-05 18:54:36

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/agents/smart-scheduling

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

## 2.2.2工作台_大模型agent_数据大屏

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:48:54

> 更新时间: 2025-12-05 18:54:38

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/agents/data-dashboard

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

## 2.2.3工作台_大模型agent_周报总结

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:55:54

> 更新时间: 2025-12-05 18:58:24

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/agents/weekly-report?week=

**请求方式**

> GET

**Content-Type**

> none

**请求Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| week | - | string | 是 | - |

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

## 2.2.4工作台_大模型agent_竞对动向

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:58:22

> 更新时间: 2025-12-05 18:59:35

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/agents/competitor-trends

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

## 2.2.5工作台_大模型agent_全部

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 19:00:17

> 更新时间: 2025-12-05 19:03:53

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/agents/all

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

## 2.3工作台_日历/日期

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:41:38

> 更新时间: 2025-12-05 19:05:05

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/time/current

**请求方式**

> GET

**Content-Type**

> none

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

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

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 2.4工作台_工厂状态监测

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:43:21

> 更新时间: 2025-12-05 19:05:29

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/factory-status/overview

**请求方式**

> GET

**Content-Type**

> json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**请求Body参数**

```javascript
暂无数据
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
		"agentAlerts": 65,
		"automationLogs": 60,
		"optimizationSuggestions": 59
	},
	"timestamp": 1704067200
}
```

* 失败(404)

```javascript
暂无数据
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 2.5工作台_最近访问

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:45:04

> 更新时间: 2025-12-05 19:05:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/users/recent-visits/{status}

**请求方式**

> GET

**Content-Type**

> none

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**路径变量**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| status | /api/workbench/factory/status | string | 是 | - |

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
	"code": 0,
	"message": "success",
	"data": [
		{
			"name": "阎平",
			"path": "magna"
		},
		{
			"name": "尹桂英",
			"path": "sed"
		},
		{
			"name": "郑霞",
			"path": "sint pariatur veniam sed"
		},
		{
			"name": "廖敏",
			"path": "aliquip labore"
		}
	],
	"timestamp": 1704067200
}
```

* 失败(404)

```javascript
暂无数据
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 2.6.1工作台_自定义入口_访问

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:46:35

> 更新时间: 2025-12-05 19:06:16

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/users/custom-entries/get

**请求方式**

> GET

**Content-Type**

> none

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

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

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 2.6.2工作台_自定义入口_添加

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 13:48:29

> 更新时间: 2025-12-05 19:06:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/users/custom-entries/add

**请求方式**

> POST

**Content-Type**

> json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**请求Body参数**

```javascript
{
	"name": "姚秀英",
	"url": "http://rslkcbltg.my/akiegru"
}
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
{
	"code": 404,
	"message": "Not found",
	"detail": "资源不存在"
}
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 2.7工作台_知识库管理

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 19:02:10

> 更新时间: 2025-12-05 19:03:48

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/desk/knowledge

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

# ❗️3.0库管理_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:49:04

> 更新时间: 2025-12-05 18:45:54

```text
# 库管理功能 路由组

![Screenshot 2025-12-02 at 16.14.12.png](https://img.cdn.apipost.cn/upload/user/363063963187482624/logo/bc8ff6d7-cdbd-4c4c-a1b8-bdbb767aa536.png "Screenshot 2025-12-02 at 16.14.12.png")
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

# ❗️4.0文档OCR_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:49:50

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

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

# ❗️5.0Agent流_

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-01 19:50:48

> 更新时间: 2025-12-07 22:10:38

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/agent

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

# ❗️6.0回收站_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:51:40

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

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

# ❗️7.0Chat对话_

> 创建人: 楼学之

> 更新人: 楼学之

> 创建时间: 2025-12-01 19:52:37

> 更新时间: 2025-12-06 11:48:01

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat

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

# 7.0Chat对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:52:27

> 更新时间: 2025-12-05 18:52:31

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

## 7.1Chat对话_发送消息

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:16:08

> 更新时间: 2025-12-05 19:07:40

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/send

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

## 7.2.1Chat对话_新建对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:19:05

> 更新时间: 2025-12-05 19:08:13

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/new

**请求方式**

> POST

**Content-Type**

> json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**请求Body参数**

```javascript
{
	"conversationName": "dolore Ut minim quis consequat"
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
		"conversationId": "aliqua aliquip occaecat ut",
		"conversationName": "eu",
		"createTime": "2000-02-10 02:36:00"
	},
	"timestamp": 1704067200
}
```

* 失败(404)

```javascript
暂无数据
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 7.2.2Chat对话_加载历史对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:19:55

> 更新时间: 2025-12-05 19:08:31

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/list

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

## 7.2.3Chat对话_加载对话历史

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:24:49

> 更新时间: 2025-12-05 19:08:53

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/history?conversationId=

**请求方式**

> GET

**Content-Type**

> none

**请求Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| conversationId | - | string | 是 | - |

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

## 7.2.4Chat对话_关闭对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 14:59:30

> 更新时间: 2025-12-05 19:10:40

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/close

**请求方式**

> POST

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

## 7.3Chat对话_附件

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 13:01:38

> 更新时间: 2025-12-05 19:09:48

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/attachment

**请求方式**

> GET

**Content-Type**

> form-data

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | multipart/form-data | string | 是 | - |

**请求Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| fileUrl | - | string | 是 | - |
| timestamp | - | string | 是 | - |

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

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | multipart/form-data | string | 是 | - |

**Query**

## 7.4Chat对话_重新生成

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 15:06:05

> 更新时间: 2025-12-05 19:10:22

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/resend

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

# ❗️8.0核心API接口_

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-01

> 更新时间: 2025-12-07

```text
核心API接口，包括问答、文档管理、系统管理等基础功能
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1

**请求方式**

> 多种（GET/POST）

**Content-Type**

> application/json / multipart/form-data

**认证方式**

> API Key (X-API-Key Header)

**Query**

# 8.0核心API接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
核心API接口定义，包括问答、文档管理、系统管理等基础功能
```

**目录Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥（除健康检查接口外） |

**目录Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录认证信息**

> API Key认证（X-API-Key Header）

## 8.1核心API_问答接口

> ⚠️ **已迁移**: 此接口已整合到 [Chat对话模块](./07_chat.md#70-chat对话_问答接口)

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07



**接口状态**

> 已迁移

**接口URL**

> http://localhost/api/v1/ask

**新文档位置**: [7.0 Chat对话_问答接口](./07_chat.md#70-chat对话_问答接口)

**Query**

## 8.2核心API_文档摄取接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
上传并摄取文档到知识库，支持PDF、DOCX、TXT等格式
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/docs/ingest

**请求方式**

> POST

**Content-Type**

> multipart/form-data

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |
| Content-Type | multipart/form-data | string | 是 | 请求内容类型 |

**请求Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| file | (文件) | file | 是 | 上传的文件（PDF、DOCX、TXT等） |
| library_id | lib-123 | string | 可选 | 文档库ID，不指定则使用默认文档库 |

**认证方式**

> API Key认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "document_id": "doc-789",
        "library_id": "lib-123",
        "chunks": 15,
        "title": "设备维护手册.pdf",
        "file_size": 1024000,
        "file_type": "application/pdf"
    },
    "timestamp": 1704067200
}
```

* 失败(401) - API Key无效

```javascript
{
    "code": 401,
    "message": "Invalid or missing API key",
    "detail": "API Key缺失或无效"
}
```

* 失败(400) - 文件格式不支持

```javascript
{
    "code": 400,
    "message": "Unsupported file type",
    "detail": "不支持的文件格式，仅支持PDF、DOCX、TXT等格式"
}
```

* 失败(500) - 服务器内部错误

```javascript
{
    "code": 500,
    "message": "Internal server error",
    "detail": "文档处理失败"
}
```

**Query**

## 8.3核心API_索引重建接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
触发全量索引重建（异步任务）
```

**接口状态**

> 已实现（占位实现）

**接口URL**

> http://localhost/api/v1/docs/reindex

**请求方式**

> POST

**Content-Type**

> application/json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |
| Content-Type | application/json | string | 是 | 请求内容类型 |

**请求Body参数**

```javascript
{
    "library_id": "lib-123"  // string, 可选, 文档库ID，不指定则重建所有文档库的索引
}
```

**认证方式**

> API Key认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "status": "queued",
        "task_id": "task-123",
        "estimated_time": 300
    },
    "timestamp": 1704067200
}
```

* 失败(401) - API Key无效

```javascript
{
    "code": 401,
    "message": "Invalid or missing API key",
    "detail": "API Key缺失或无效"
}
```

* 失败(500) - 服务器内部错误

```javascript
{
    "code": 500,
    "message": "Internal server error",
    "detail": "索引重建任务创建失败"
}
```

**Query**

## 8.4核心API_健康检查接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
系统健康检查端点，用于Kubernetes/Docker健康检查、负载均衡器健康探测
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/admin/healthz

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 无需认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "status": "healthy",
        "timestamp": 1704067200,
        "service": "Industrial QA Backend",
        "version": "0.1.0"
    },
    "timestamp": 1704067200
}
```

* 失败(503) - 服务不健康

```javascript
{
    "code": 503,
    "message": "Service unhealthy",
    "detail": "数据库连接失败"
}
```

**Query**

## 8.5核心API_Ping接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
简单连通性测试接口
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/admin/ping

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 无需认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "message": "pong"
    },
    "timestamp": 1704067200
}
```

**Query**

# ❗️9.0开放平台_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:53:02

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/api

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

# 9.0开放平台

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:51:24

> 更新时间: 2025-12-05 18:51:33

```text
开放平台相关接口
```

**目录Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |

**目录Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录认证信息**

> API Key认证

**Query**

## 9.1开放平台_获取平台信息

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 15:33:54

> 更新时间: 2025-12-05 19:11:51

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/api/open-platform/basic-info

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

## 9.2开放平台_sdk调用实例

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 15:36:03

> 更新时间: 2025-12-05 19:11:25

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/api/open-platform/sdk-example?language=

**请求方式**

> GET

**Content-Type**

> none

**请求Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| language | - | string | 是 | - |

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

## 9.3开放平台_获取网页嵌入码

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 15:40:32

> 更新时间: 2025-12-05 19:11:35

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/api/open-platform/embed-code

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

# ❗️10.0设置_

> 创建人: 楼学之

> 更新人: 黄明峰

> 创建时间: 2025-12-01 19:53:53

> 更新时间: 2025-12-05 18:45:54

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/settings

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
