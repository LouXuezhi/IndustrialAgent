import asyncio
from pathlib import Path

import typer

from app.db.session import async_session
from app.rag.ingestion import DocumentIngestor

cli = typer.Typer(help="Document ingestion utility")


@cli.command()
def ingest(path: Path) -> None:
    async def _run() -> None:
        ingestor = DocumentIngestor()
        async with async_session() as session:
            report = await ingestor.ingest_file(path, session)
        typer.echo(f"Ingested {path} into document {report.document_id} ({report.chunk_count} chunks)")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()

