import os
import sys
import argparse
import asyncio
import json
import logging
from pathlib import Path
import time
from typing import Dict

# --- 1. 路径补丁 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# --- 2. 导入依赖 ---
from rag.ingestion import DocumentIngestor
# 🌟 新增导入：用于重建数据库连接
from langchain_chroma import Chroma
from vectorDB.Chroma import embedding_model

# --- 3. 配置常量与日志 ---
STATE_FILE = os.path.join(project_root, "ingestion_state.json")
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.html', '.htm', '.txt', '.md'}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_state() -> Dict[str, float]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: Dict[str, float]):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存状态失败: {e}")


async def main():
    parser = argparse.ArgumentParser(description="RAG 文档批量入库工具")
    parser.add_argument("dir", help="文档所在的目录路径")
    parser.add_argument("--mode", choices=["full", "update"], default="update",
                        help="模式：full (全量重建) / update (增量更新)")
    args = parser.parse_args()

    source_dir = Path(args.dir)
    if not source_dir.exists():
        logger.error(f"❌ 目录不存在: {source_dir}")
        return

    # --- 4. 初始化 ---
    logger.info("🏗️  正在初始化文档处理器...")
    ingestor = DocumentIngestor()

    # --- 5. 模式处理 ---
    state = {}
    if args.mode == "full":
        logger.warning("⚠️  [全量模式] 正在清空向量数据库...")
        try:
            # 1. 删除旧集合
            ingestor.vector_db.delete_collection()
            logger.info("✅ 数据库已清空。")

            # 🌟 关键修复：删除后必须重新连接/创建集合，否则原来的对象会失效
            logger.info("🔄 正在重新初始化数据库连接...")
            ingestor.vector_db = Chroma(
                persist_directory="./chroma_store",
                collection_name="industrial_qa_docs",
                embedding_function=embedding_model
            )

        except Exception as e:
            logger.error(f"清空数据库失败: {e}")

        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    else:
        state = load_state()
        logger.info(f"🔄 [增量模式] 加载了 {len(state)} 条历史记录")

    # --- 6. 扫描 ---
    logger.info(f"📂 正在扫描目录: {source_dir}")
    files_to_process = []

    for file_path in source_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            abs_path = str(file_path.absolute())
            current_mtime = file_path.stat().st_mtime

            should_process = False
            reason = ""

            if args.mode == "full":
                should_process = True
            elif abs_path not in state:
                should_process = True
                reason = "新文件"
            elif current_mtime > state[abs_path]:
                should_process = True
                reason = "内容更新"

            if should_process:
                files_to_process.append((file_path, abs_path, current_mtime, reason))

    logger.info(f"📊 扫描完成: 发现 {len(files_to_process)} 个文件需要处理")

    # --- 7. 执行 ---
    success_count = 0
    fail_count = 0

    for i, (file_path, abs_path, mtime, reason) in enumerate(files_to_process):
        prefix = f"[{i + 1}/{len(files_to_process)}]"
        logger.info(f"{prefix} 处理中 ({reason}): {file_path.name}")

        try:
            # 调用处理逻辑 (session 传 None)
            report = await ingestor.ingest_file(file_path, session=None)

            if report.status == "success":
                logger.info(f"   ✅ 成功 | ID: {str(report.document_id)[:8]}... | Chunks: {report.chunk_count}")
                state[abs_path] = mtime
                save_state(state)
                success_count += 1
            else:
                logger.error(f"   ❌ 失败 | 原因: {report.error}")
                fail_count += 1

        except Exception as e:
            logger.error(f"   ❌ 系统异常: {e}")
            fail_count += 1

    logger.info("=" * 40)
    logger.info(f"🎉 批处理结束 | 成功: {success_count} | 失败: {fail_count}")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())