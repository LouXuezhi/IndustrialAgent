# 代码规范指南

> 创建时间: 2025-12-07  
> 适用范围: 工业问答后端项目

## 文档说明

本目录包含工业问答后端项目的代码规范和检测说明文档，旨在确保代码质量、可读性和一致性。

## 文档结构

```
Doc/Guidelines/
├── README.md              # 本文档（索引）
├── 01_code_style.md      # 代码规范格式说明
└── 02_code_checking.md   # 代码检测说明
```

## 快速导航

### 1. [代码规范格式说明](./01_code_style.md)

详细说明项目的代码规范，包括：

- **代码格式**: 行长度、缩进、空行、引号
- **命名规范**: 变量、函数、类、模块命名
- **类型提示**: 完整的类型注解要求
- **文档字符串**: Docstring 格式和规范
- **导入规范**: 导入顺序和方式
- **异常处理**: 异常捕获和处理规范
- **异步编程**: async/await 使用规范
- **代码组织**: 文件结构和函数长度
- **注释规范**: 代码注释和TODO
- **测试规范**: 测试代码编写规范
- **最佳实践**: 可读性、性能、安全性

### 2. [代码检测说明](./02_code_checking.md)

说明如何使用代码检测工具，包括：

- **工具介绍**: Ruff 工具特性
- **安装配置**: 安装和配置方法
- **使用方法**: 检查、修复、格式化命令
- **规则说明**: 启用的规则集和常见问题
- **IDE集成**: VS Code、PyCharm 集成
- **CI/CD集成**: 持续集成配置
- **最佳实践**: 开发流程和团队协作

## 核心原则

### 1. 一致性

- 所有代码应遵循统一的风格和规范
- 使用自动化工具确保一致性

### 2. 可读性

- 代码应该易于理解和维护
- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串

### 3. 类型安全

- 所有函数必须包含类型提示
- 使用类型检查工具确保类型安全

### 4. 质量保证

- 使用自动化工具检查代码质量
- 在提交前运行代码检查
- 在CI/CD中自动运行检查

## 工具配置

### Ruff 配置

项目使用 Ruff 作为代码检测和格式化工具，配置在 `pyproject.toml` 中：

```toml
[tool.ruff]
line-length = 100
```

### 开发依赖

```bash
# 安装开发依赖（包含Ruff）
pip install -e ".[dev]"
```

## 快速开始

### 1. 检查代码

```bash
# 检查所有Python文件
ruff check .

# 自动修复可修复的问题
ruff check . --fix
```

### 2. 格式化代码

```bash
# 格式化所有Python文件
ruff format .
```

### 3. 完整检查

```bash
# 检查并格式化
ruff check . --fix
ruff format .
```

## 开发工作流

### 日常开发

1. **编写代码**: 按照代码规范编写代码
2. **本地检查**: 运行 `ruff check . --fix && ruff format .`
3. **提交代码**: 确保所有检查通过
4. **代码审查**: 在代码审查时关注代码质量

### 提交前检查

在提交代码前，运行以下命令：

```bash
# 检查代码
ruff check . --fix

# 格式化代码
ruff format .

# 再次检查确保没有问题
ruff check .
```

## 规则概览

### 启用的规则集

- **E**: pycodestyle errors
- **W**: pycodestyle warnings
- **F**: pyflakes
- **I**: isort (导入排序)
- **N**: pep8-naming (命名规范)
- **UP**: pyupgrade (Python版本升级)
- **B**: flake8-bugbear (常见bug)
- **C4**: flake8-comprehensions (推导式优化)
- **SIM**: flake8-simplify (代码简化)

### 关键规范

- **行长度**: 最大100字符
- **类型提示**: 所有函数必须包含类型提示
- **文档字符串**: 所有公共函数和类必须有文档字符串
- **导入顺序**: 标准库 → 第三方库 → 本地模块
- **命名规范**: 
  - 变量/函数: `snake_case`
  - 类: `PascalCase`
  - 常量: `UPPER_CASE`

## 常见问题

### Q: 如何忽略特定规则？

A: 在文件或行级别添加 `# noqa` 注释：

```python
long_line = "..."  # noqa: E501
```

### Q: 如何配置IDE自动格式化？

A: 参考 [代码检测说明](./02_code_checking.md#6-集成到开发环境) 中的IDE集成部分。

### Q: 如何自定义规则？

A: 在 `pyproject.toml` 的 `[tool.ruff]` 部分添加配置：

```toml
[tool.ruff]
select = ["E", "F", "I"]
ignore = ["E501"]
```

## 参考资源

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Ruff 官方文档](https://docs.astral.sh/ruff/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

## 更新日志

- **2025-12-07**: 初始版本，创建代码规范和检测说明文档

## 贡献指南

添加新的规范或更新现有规范时：

1. 更新相应的文档文件
2. 更新本README中的相关说明
3. 确保示例代码符合规范
4. 更新工具配置（如需要）



