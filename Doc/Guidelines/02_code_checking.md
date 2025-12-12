# 代码检测说明

> 创建时间: 2025-12-07  
> 适用范围: 工业问答后端项目所有Python代码

## 概述

本文档说明如何使用代码检测工具对项目代码进行格式检查、静态分析和质量评估。项目使用 **Ruff** 作为主要的代码检测和格式化工具。

## 1. 工具介绍

### 1.1 Ruff

**Ruff** 是一个用 Rust 编写的极速 Python linter 和代码格式化工具，可以替代多个传统工具（如 Flake8、Black、isort 等）。

**特性**:
- ⚡ **极速**: 比传统工具快 10-100 倍
- 🔧 **多合一**: 集成 linting、格式化、导入排序等功能
- 📦 **零配置**: 开箱即用，合理的默认配置
- 🔌 **可扩展**: 支持插件和自定义规则

**项目配置**: `pyproject.toml`

```toml
[tool.ruff]
line-length = 100

[project.optional-dependencies]
dev = [
    "ruff>=0.4.8",
]
```

## 2. 安装和配置

### 2.1 安装 Ruff

```bash
# 安装开发依赖（包含Ruff）
pip install -e ".[dev]"

# 或单独安装
pip install ruff>=0.4.8
```

### 2.2 配置文件

项目使用 `pyproject.toml` 配置 Ruff：

```toml
[tool.ruff]
# 行长度限制
line-length = 100

# 选择要启用的规则集
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

# 忽略的规则
ignore = [
    "E501",  # 行长度（由formatter处理）
]

# 排除的目录
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]
```

## 3. 使用方法

### 3.1 检查代码

```bash
# 检查所有Python文件
ruff check .

# 检查特定文件或目录
ruff check app/
ruff check app/core/config.py

# 显示详细的错误信息
ruff check . --verbose

# 只显示错误，不显示警告
ruff check . --select E
```

### 3.2 自动修复

```bash
# 自动修复可修复的问题
ruff check . --fix

# 修复并显示修复的内容
ruff check . --fix --diff
```

### 3.3 格式化代码

```bash
# 格式化所有Python文件
ruff format .

# 格式化特定文件或目录
ruff format app/
ruff format app/core/config.py

# 预览格式化后的差异（不实际修改文件）
ruff format . --diff
```

### 3.4 检查并格式化

```bash
# 先检查，再格式化
ruff check . --fix
ruff format .
```

## 4. 常用命令

### 4.1 开发工作流

```bash
# 1. 检查代码问题
ruff check .

# 2. 自动修复可修复的问题
ruff check . --fix

# 3. 格式化代码
ruff format .

# 4. 再次检查确保没有问题
ruff check .
```

### 4.2 CI/CD 集成

在 CI/CD 流程中，使用以下命令确保代码质量：

```bash
# 检查代码（不自动修复，失败时退出）
ruff check . --output-format=github

# 检查代码格式（不自动修改，失败时退出）
ruff format . --check
```

### 4.3 预提交钩子

可以配置 Git 预提交钩子自动运行检查：

```bash
# .git/hooks/pre-commit
#!/bin/sh
ruff check . --fix
ruff format .
```

## 5. 规则说明

### 5.1 启用的规则集

项目启用了以下规则集：

| 规则集 | 说明 | 示例 |
|--------|------|------|
| **E** | pycodestyle errors | 语法错误、缩进错误 |
| **W** | pycodestyle warnings | 代码风格警告 |
| **F** | pyflakes | 未使用的导入、未定义的变量 |
| **I** | isort | 导入排序 |
| **N** | pep8-naming | 命名规范 |
| **UP** | pyupgrade | Python版本升级建议 |
| **B** | flake8-bugbear | 常见bug模式 |
| **C4** | flake8-comprehensions | 列表/字典推导式优化 |
| **SIM** | flake8-simplify | 代码简化建议 |

### 5.2 常见问题示例

#### 未使用的导入

```python
# ❌ 错误：未使用的导入
from fastapi import APIRouter, Depends, HTTPException

def my_function():
    return APIRouter()  # HTTPException未使用

# ✅ 修复后
from fastapi import APIRouter, Depends

def my_function():
    return APIRouter()
```

#### 导入排序

```python
# ❌ 错误：导入顺序不正确
from app.core.config import Settings
import time
from fastapi import APIRouter

# ✅ 修复后
import time

from fastapi import APIRouter

from app.core.config import Settings
```

#### 命名规范

```python
# ❌ 错误：类名不符合规范
class myClass:  # 应该是MyClass
    pass

# ✅ 修复后
class MyClass:
    pass
```

#### 代码简化

```python
# ❌ 错误：可以简化
if x is not None:
    if x > 0:
        return True

# ✅ 修复后
if x is not None and x > 0:
    return True
```

## 6. 集成到开发环境

### 6.1 VS Code

在 VS Code 中安装 Ruff 扩展：

1. 安装扩展: `charliermarsh.ruff`
2. 配置 `settings.json`:

```json
{
    "ruff.enable": true,
    "ruff.format.args": ["--line-length=100"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": true
    }
}
```

### 6.2 PyCharm

1. 安装 Ruff 插件
2. 配置外部工具：
   - **Program**: `ruff`
   - **Arguments**: `check $FilePath$ --fix`
   - **Working directory**: `$ProjectFileDir$`

### 6.3 命令行别名

在 `~/.bashrc` 或 `~/.zshrc` 中添加别名：

```bash
# 快速检查
alias rcheck='ruff check .'

# 快速修复
alias rfix='ruff check . --fix && ruff format .'

# 检查并格式化
alias rfmt='ruff format .'
```

## 7. 忽略特定规则

### 7.1 文件级别忽略

在文件顶部添加注释忽略整个文件：

```python
# ruff: noqa
# 或
# ruff: noqa: E501, F401
```

### 7.2 行级别忽略

在特定行添加注释：

```python
long_line = "This is a very long line that exceeds 100 characters"  # noqa: E501

unused_import = "test"  # noqa: F401
```

### 7.3 块级别忽略

```python
# ruff: noqa: E501
def long_function_with_many_parameters(
    param1, param2, param3, param4, param5
):
    pass
# ruff: noqa: E501
```

## 8. 性能优化

### 8.1 缓存

Ruff 自动缓存检查结果，提高后续检查速度。

### 8.2 并行检查

Ruff 默认使用多核并行检查，无需额外配置。

### 8.3 增量检查

只检查修改的文件：

```bash
# 检查Git暂存区的文件
ruff check $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

# 检查最近修改的文件
ruff check $(git diff HEAD --name-only | grep '\.py$')
```

## 9. 与其他工具集成

### 9.1 与 pytest 集成

在 `pytest.ini` 或 `pyproject.toml` 中配置：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# 在测试前运行Ruff检查
addopts = "--ruff"
```

### 9.2 与 pre-commit 集成

创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

安装 pre-commit:

```bash
pip install pre-commit
pre-commit install
```

## 10. 常见问题排查

### 10.1 检查未生效

```bash
# 检查Ruff版本
ruff --version

# 检查配置文件
ruff check . --config pyproject.toml --verbose

# 清除缓存
ruff clean
```

### 10.2 规则冲突

如果某个规则与项目需求冲突，可以在配置中忽略：

```toml
[tool.ruff]
ignore = [
    "E501",  # 忽略行长度检查
    "F401",  # 忽略未使用的导入
]
```

### 10.3 性能问题

```bash
# 检查特定目录（排除不需要检查的目录）
ruff check app/ --exclude "app/migrations"

# 只检查修改的文件
ruff check $(git diff --name-only | grep '\.py$')
```

## 11. 最佳实践

### 11.1 开发流程

1. **编写代码**: 按照代码规范编写代码
2. **提交前检查**: 运行 `ruff check . --fix && ruff format .`
3. **提交代码**: 确保所有检查通过
4. **CI/CD检查**: 在CI/CD中自动运行检查

### 11.2 团队协作

- **统一配置**: 所有开发者使用相同的 `pyproject.toml` 配置
- **定期检查**: 定期运行全面检查，修复所有问题
- **代码审查**: 在代码审查时关注代码质量问题

### 11.3 持续改进

- **逐步启用规则**: 可以逐步启用更多规则集
- **自定义规则**: 根据项目需求自定义规则
- **定期更新**: 定期更新 Ruff 版本，获取新功能和修复

## 12. 参考资源

- [Ruff 官方文档](https://docs.astral.sh/ruff/)
- [Ruff GitHub 仓库](https://github.com/astral-sh/ruff)
- [Ruff 规则列表](https://docs.astral.sh/ruff/rules/)
- [PEP 8 风格指南](https://peps.python.org/pep-0008/)

## 13. 检查清单

在提交代码前，确保：

- [ ] 运行 `ruff check .` 无错误
- [ ] 运行 `ruff format .` 格式化代码
- [ ] 所有类型提示正确
- [ ] 所有函数有文档字符串
- [ ] 导入顺序正确
- [ ] 命名符合规范
- [ ] 无未使用的导入和变量

## 14. 示例工作流

```bash
# 完整的代码检查工作流
#!/bin/bash

echo "🔍 Running Ruff check..."
ruff check . --fix

echo "✨ Formatting code..."
ruff format .

echo "🔍 Final check..."
ruff check .

echo "✅ All checks passed!"
```

将此脚本保存为 `scripts/check_code.sh`，在提交代码前运行。



