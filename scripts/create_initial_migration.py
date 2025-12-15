#!/usr/bin/env python3
"""
创建初始数据库迁移脚本。

此脚本会基于当前的数据库模型生成初始迁移。
如果数据库已经存在表，请先备份数据，然后：
1. 删除现有表
2. 运行此脚本生成迁移
3. 运行 alembic upgrade head 应用迁移

或者，如果数据库是空的，直接运行此脚本即可。
"""
import subprocess
import sys
from pathlib import Path

def main():
    """创建初始迁移"""
    project_root = Path(__file__).parent.parent
    
    print("🔄 生成初始数据库迁移...")
    print("")
    
    # 检查 alembic 是否已初始化
    alembic_dir = project_root / "alembic"
    if not alembic_dir.exists():
        print("❌ Alembic 未初始化，请先运行: alembic init alembic")
        sys.exit(1)
    
    # 生成迁移
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial schema"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ 迁移脚本生成成功！")
        print("")
        print("📝 下一步：")
        print("   1. 检查生成的迁移文件: alembic/versions/")
        print("   2. 确认 SQL 语句正确")
        print("   3. 执行迁移: alembic upgrade head")
        print("")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ 迁移生成失败:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Alembic 未安装，请运行: pip install alembic")
        sys.exit(1)

if __name__ == "__main__":
    main()

