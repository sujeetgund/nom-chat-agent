"""
Ingest KB documents into pgvector for embedding-based retrieval.

Flow:
  1. Read all .md files from kb/
  2. Split by heading level (aim for ~500 tokens per chunk)
  3. Parse frontmatter for metadata
  4. Generate embeddings using HuggingFace
  5. Upsert into pgvector
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg
import tiktoken
import yaml

# Add parent directory to path to allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = PROJECT_ROOT / "kb"
TOKEN_LIMIT_PER_CHUNK = 500


@dataclass
class DocumentChunk:
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


def get_encoding():
    """Get tiktoken encoding for token counting."""
    try:
        return tiktoken.encoding_for_model("gpt-3.5-turbo")
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, encoding) -> int:
    """Count tokens in text."""
    try:
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown file."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        metadata = yaml.safe_load(parts[1]) or {}
    except Exception as e:
        logger.debug(f"Failed to parse frontmatter: {e}")
        metadata = {}

    body = parts[2].lstrip("\n")
    return metadata, body


def read_kb_files() -> list[tuple[Path, str, dict[str, Any]]]:
    """Read all markdown files from kb/ directory."""
    files: list[tuple[Path, str, dict[str, Any]]] = []

    for md_file in sorted(KB_DIR.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(content)

            files.append((md_file, body, metadata))
        except Exception as e:
            logger.warning(f"Failed to read {md_file}: {e}")

    return files


def _split_by_h2(
    content: str, metadata: dict[str, Any], encoding
) -> list[DocumentChunk]:
    """Split content by H2 headers."""
    chunks = []
    current_section = ""
    current_title = ""

    for line in content.split("\n"):
        if line.startswith("## "):
            # Save previous section
            if current_section.strip():
                # Further split by token limit
                section_chunks = _split_by_tokens(
                    current_section, metadata, encoding, current_title
                )
                chunks.extend(section_chunks)

            current_title = line.replace("## ", "").strip()
            current_section = ""
        else:
            current_section += line + "\n"

    # Save last section
    if current_section.strip():
        section_chunks = _split_by_tokens(
            current_section, metadata, encoding, current_title
        )
        chunks.extend(section_chunks)

    return chunks


def _split_services(
    content: str, metadata: dict[str, Any], encoding
) -> list[DocumentChunk]:
    """Split services.md by H2 sections with URL mapping."""
    chunks = []
    current_section = ""
    current_title = ""

    # URL mapping for services
    service_urls = {
        "AI Agents": "/services/ai-agents",
        "RAG Applications": "/services/rag-applications",
        "Chatbots": "/services/chatbots",
        "Data Extraction": "/services/data-extraction",
    }

    for line in content.split("\n"):
        if line.startswith("## "):
            # Save previous section
            if current_section.strip():
                section_metadata = metadata.copy()
                service_title = line.replace("## ", "").strip()
                if service_title in service_urls:
                    section_metadata["url"] = service_urls[service_title]
                section_chunks = _split_by_tokens(
                    current_section, section_metadata, encoding, current_title
                )
                chunks.extend(section_chunks)

            current_title = line.replace("## ", "").strip()
            current_section = ""
        else:
            current_section += line + "\n"

    # Save last section
    if current_section.strip():
        section_metadata = metadata.copy()
        service_title = current_title
        if service_title in service_urls:
            section_metadata["url"] = service_urls[service_title]
        section_chunks = _split_by_tokens(
            current_section, section_metadata, encoding, current_title
        )
        chunks.extend(section_chunks)

    return chunks


def _split_by_tokens(
    content: str, metadata: dict[str, Any], encoding, section_title: str = ""
) -> list[DocumentChunk]:
    """Split content by token limit."""
    chunks = []
    lines = content.split("\n")
    current_chunk = ""
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line, encoding)

        if (
            current_tokens + line_tokens > TOKEN_LIMIT_PER_CHUNK
            and current_chunk.strip()
        ):
            # Save current chunk
            chunk_metadata = metadata.copy()
            if section_title:
                chunk_metadata["section"] = section_title
            chunks.append(
                DocumentChunk(
                    content=current_chunk.strip(),
                    metadata=chunk_metadata,
                )
            )
            current_chunk = ""
            current_tokens = 0

        current_chunk += line + "\n"
        current_tokens += line_tokens

    # Save last chunk
    if current_chunk.strip():
        chunk_metadata = metadata.copy()
        if section_title:
            chunk_metadata["section"] = section_title
        chunks.append(
            DocumentChunk(
                content=current_chunk.strip(),
                metadata=chunk_metadata,
            )
        )

    return chunks


def split_by_heading(
    content: str, metadata: dict[str, Any], encoding, source_type: str = ""
) -> list[DocumentChunk]:
    """Split content by heading level and token limit."""
    if source_type == "service":
        return _split_services(content, metadata, encoding)
    else:
        return _split_by_h2(content, metadata, encoding)


async def embed_chunks(
    chunks: list[DocumentChunk], embeddings_model: HuggingFaceEmbeddings
) -> list[DocumentChunk]:
    """Generate embeddings for chunks."""
    texts = [chunk.content for chunk in chunks]

    # Embed in thread pool (HuggingFaceEmbeddings doesn't have async API)
    try:
        embedded_texts = await asyncio.to_thread(
            embeddings_model.embed_documents, texts
        )
        for chunk, emb in zip(chunks, embedded_texts):
            chunk.embedding = emb
    except Exception as e:
        logger.error(f"Failed to embed chunks: {e}")
        raise

    return chunks


async def upsert_into_pgvector(chunks: list[DocumentChunk], settings) -> None:
    """Upsert chunks into pgvector database."""
    conn = await asyncpg.connect(settings.database_url)

    try:
        # Prepare insert statement
        insert_query = """
            INSERT INTO website_embeddings (content, metadata, embedding)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING;
        """

        count = 0
        error_count = 0

        for chunk in chunks:
            if not chunk.embedding:
                logger.warning(f"Skipping chunk without embedding: {chunk.metadata}")
                continue

            try:
                # Convert metadata dict to JSON string for pgvector
                metadata_json = json.dumps(chunk.metadata)
                # Convert embedding list to string format: "[0.1, 0.2, ...]"
                embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"
                await conn.execute(
                    insert_query,
                    chunk.content,
                    metadata_json,
                    embedding_str,
                )
                count += 1
            except Exception as e:
                error_count += 1
                if error_count == 1:  # Log first error in detail
                    logger.error(
                        f"First upsert failed for {chunk.metadata.get('title', 'unknown')}: {e}"
                    )
                else:
                    logger.debug(f"Upsert error #{error_count}: {str(e)[:100]}")
                continue

        logger.info(f"Upserted {count} chunks into pgvector (errors: {error_count})")

    finally:
        await conn.close()


async def main() -> None:
    """Main ingestion pipeline."""
    settings = get_settings()
    encoding = get_encoding()

    # Initialize embeddings model
    embeddings_model = HuggingFaceEmbeddings(
        model_name=settings.hf_embedding_model,
        model_kwargs={"device": "cpu"},  # Use GPU if available
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info(f"Reading KB files from {KB_DIR}...")
    files = read_kb_files()
    logger.info(f"Found {len(files)} files")

    all_chunks: list[DocumentChunk] = []

    for file_path, content, metadata in files:
        logger.info(f"Processing {file_path.relative_to(PROJECT_ROOT)}...")
        source_type = metadata.get("source_type", "")
        chunks = split_by_heading(content, metadata, encoding, source_type)
        all_chunks.extend(chunks)
        logger.info(f"  \u2192 {len(chunks)} chunks")

    logger.info(f"Total chunks: {len(all_chunks)}")

    logger.info("Generating embeddings...")
    all_chunks = await embed_chunks(all_chunks, embeddings_model)

    logger.info("Upserting into pgvector...")
    await upsert_into_pgvector(all_chunks, settings)

    logger.info("Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(main())
