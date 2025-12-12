# 1.0 首页模块API

> 创建人: 楼学之
> 更新人: 黄明峰
> 创建时间: 2025-12-01 19:48:08
> 更新时间: 2025-12-05 18:45:54

## 模块说明

首页模块提供首页内容展示相关的API接口。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范

## 目录Header参数

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |

## 目录Query参数

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

## 目录Body参数

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

## 目录认证信息

> API Key认证（X-API-Key Header）

---

# ❗️1.0首页_

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

