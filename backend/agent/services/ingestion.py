from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, List, Tuple
import httpx
import yaml
import tiktoken
import psycopg
from langchain_openai import OpenAIEmbeddings
from config import get_settings

logger = logging.getLogger(__name__)

def _normalize_database_url(database_url: str) -> str:
    """Normalize database URL for psycopg compatibility."""
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg://")
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg2://")
    return database_url

@dataclass
class DocumentChunk:
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None

class ContentIngestor:
    def __init__(self):
        self.settings = get_settings()
        self.embeddings_model = OpenAIEmbeddings(
            model=self.settings.openai_embedding_model,
            api_key=self.settings.openai_api_key,
            dimensions=512,
        )
        self.github_api_base = "https://api.github.com/repos/divamtech/nom-content"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.settings.github_token:
            self.headers["Authorization"] = f"token {self.settings.github_token}"
        
        self.token_limit = 500
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    async def setup_database(self):
        """Ensure tables exist with correct schema."""
        def _setup():
            db_url = _normalize_database_url(self.settings.database_url)
            with psycopg.connect(db_url, autocommit=True, prepare_threshold=None) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS sync_metadata (
                            key TEXT PRIMARY KEY,
                            value TEXT,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS website_embeddings (
                            id BIGSERIAL PRIMARY KEY,
                            content TEXT NOT NULL,
                            metadata JSONB,
                            embedding vector(512),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS website_embeddings_vector_idx 
                        ON website_embeddings USING hnsw (embedding vector_cosine_ops);
                    """)
        await asyncio.to_thread(_setup)

    async def get_latest_commit_sha(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.github_api_base}/commits/main", headers=self.headers)
            resp.raise_for_status()
            return resp.json()["sha"]

    async def fetch_files_from_github(self, path: str) -> list[dict[str, Any]]:
        """Fetch file list and content from GitHub."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.github_api_base}/contents/{path}", headers=self.headers)
            resp.raise_for_status()
            items = resp.json()
            
            results = []
            for item in items:
                if item["type"] == "file" and item["name"].endswith(".md"):
                    content_resp = await client.get(item["download_url"])
                    content_resp.raise_for_status()
                    results.append({
                        "name": item["name"],
                        "content": content_resp.text,
                        "path": item["path"],
                        "url": f"https://newtononmars.com/{path}/{item['name'].replace('.md', '')}"
                    })
            return results

    def parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        if not content.startswith("---"):
            return {}, content
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        try:
            metadata = yaml.safe_load(parts[1]) or {}
        except Exception:
            metadata = {}
        return metadata, parts[2].lstrip("\n")

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def chunk_content(self, body: str, metadata: dict[str, Any]) -> list[DocumentChunk]:
        chunks = []
        current_section = ""
        current_title = metadata.get("title", "")
        
        lines = body.split("\n")
        for line in lines:
            if line.startswith("## "):
                if current_section.strip():
                    chunks.extend(self._split_by_tokens(current_section, metadata, current_title))
                current_title = line.replace("## ", "").strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"
        
        if current_section.strip():
            chunks.extend(self._split_by_tokens(current_section, metadata, current_title))
        
        return chunks

    def _split_by_tokens(self, text: str, metadata: dict[str, Any], section_title: str) -> list[DocumentChunk]:
        chunks = []
        lines = text.split("\n")
        current_chunk = ""
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens > self.token_limit and current_chunk.strip():
                chunk_meta = metadata.copy()
                chunk_meta["section"] = section_title
                chunks.append(DocumentChunk(content=current_chunk.strip(), metadata=chunk_meta))
                current_chunk = ""
                current_tokens = 0
            
            current_chunk += line + "\n"
            current_tokens += line_tokens
            
        if current_chunk.strip():
            chunk_meta = metadata.copy()
            chunk_meta["section"] = section_title
            chunks.append(DocumentChunk(content=current_chunk.strip(), metadata=chunk_meta))
            
        return chunks

    async def embed_batch(self, chunks: list[DocumentChunk]):
        texts = [c.content for c in chunks]
        embeddings = await asyncio.to_thread(self.embeddings_model.embed_documents, texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

    async def sync_content(self, force: bool = False):
        await self.setup_database()
        
        try:
            current_sha = await self.get_latest_commit_sha()
        except Exception as e:
            logger.error(f"Failed to fetch latest commit from GitHub: {e}")
            return False

        def _get_last_sha():
            db_url = _normalize_database_url(self.settings.database_url)
            with psycopg.connect(db_url, prepare_threshold=None) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT value FROM sync_metadata WHERE key = 'last_synced_commit';")
                    row = cur.fetchone()
                    return row[0] if row else None

        last_sha = await asyncio.to_thread(_get_last_sha)

        if last_sha == current_sha and not force:
            logger.info("Content is already up to date.")
            return True

        logger.info(f"Syncing content from GitHub: {last_sha} -> {current_sha}")
        
        all_chunks = []
        for path_key in ["content/blogs", "content/case-studies"]:
            try:
                files = await self.fetch_files_from_github(path_key)
                for file in files:
                    meta, body = self.parse_frontmatter(file["content"])
                    meta["source_type"] = "blog" if "blogs" in path_key else "case_study"
                    meta["url"] = file["url"]
                    meta["file_path"] = file["path"]
                    
                    file_chunks = self.chunk_content(body, meta)
                    all_chunks.extend(file_chunks)
            except Exception as e:
                logger.error(f"Failed to fetch or process {path_key}: {e}")

        if not all_chunks:
            logger.info("No content found to sync.")
            return True

        # Delete old blogs/case studies before re-ingesting to avoid duplicates/stale data
        def _delete_old():
            db_url = _normalize_database_url(self.settings.database_url)
            with psycopg.connect(db_url, autocommit=True, prepare_threshold=None) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM website_embeddings WHERE metadata->>'source_type' IN ('blog', 'case_study');"
                    )
        await asyncio.to_thread(_delete_old)

        # Embed in batches
        batch_size = 20
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            await self.embed_batch(batch)
            
            def _upsert_batch():
                db_url = _normalize_database_url(self.settings.database_url)
                with psycopg.connect(db_url, autocommit=True, prepare_threshold=None) as conn:
                    with conn.cursor() as cur:
                        for chunk in batch:
                            cur.execute(
                                "INSERT INTO website_embeddings (content, metadata, embedding) VALUES (%s, %s, %s);",
                                (chunk.content, json.dumps(chunk.metadata), str(chunk.embedding))
                            )
            await asyncio.to_thread(_upsert_batch)
            logger.info(f"Ingested {min(i+batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

        # Update sync state
        def _update_sha():
            db_url = _normalize_database_url(self.settings.database_url)
            with psycopg.connect(db_url, autocommit=True, prepare_threshold=None) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO sync_metadata (key, value) VALUES ('last_synced_commit', %s)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
                    """, (current_sha,))
        await asyncio.to_thread(_update_sha)
        
        logger.info("Sync complete!")
        return True
