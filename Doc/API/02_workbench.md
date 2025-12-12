# 2.0 工作台模块API

> 创建人: 楼学之
> 更新人: 黄明峰
> 创建时间: 2025-12-01 19:46:57
> 更新时间: 2025-12-05 18:45:54

## 模块说明

工作台模块提供工作台相关的API接口，包括产品手册、大模型agent、工厂状态监测、知识库管理等功能。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范

---

# ❗️2.0工作台_

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

