# Ingestion Pipeline Documentation

This document describes the automated ingestion pipeline that syncs content (blogs and case studies) from the [nom-content](https://github.com/divamtech/nom-content) repository to the NOM Chatbot's vector database.

## Architecture

1.  **Source of Truth**: All blogs and case studies are maintained in the `nom-content` GitHub repository.
2.  **Trigger**: A GitHub Action on the `nom-content` repo sends a webhook (POST) to the backend API.
3.  **Sync Logic**: 
    - The backend compares the latest commit SHA from GitHub with its stored `last_synced_commit`.
    - If they differ, it fetches all `.md` files, parses frontmatter, chunks the content, generates OpenAI embeddings (512-dim), and upserts them into `pgvector`.
4.  **Recovery**: If a webhook is missed (e.g., server was down), the backend automatically checks for updates every time it starts up.

## Configuration

The following environment variables are required in the `.env` file:

```env
# OpenAI
OPENAI_API_KEY=your_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Sync Webhook
SYNC_SECRET_TOKEN=your_random_secret_token

# GitHub (Optional, but recommended for rate limits)
GITHUB_TOKEN=your_github_pat
```

## Webhook Endpoint

- **URL**: `https://your-backend-url.com/api/v1/content/sync`
- **Method**: `POST`
- **Headers**:
    - `X-Sync-Token`: Must match `SYNC_SECRET_TOKEN`

## GitHub Action Example

Add this to `.github/workflows/sync.yml` in the `nom-content` repository:

```yaml
name: Sync to Chatbot

on:
  push:
    branches: [ main ]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Webhook
        run: |
          curl -X POST https://your-backend-url.com/api/v1/content/sync \
            -H "X-Sync-Token: ${{ secrets.SYNC_SECRET_TOKEN }}"
```

## Database Tables

The pipeline automatically creates/manages these tables:
- `website_embeddings`: Stores content, metadata, and the 512-dim vector.
- `sync_metadata`: Stores the `last_synced_commit` SHA to track state.

## Manual Trigger

You can manually trigger a sync by sending a POST request with the correct token:
```bash
curl -X POST http://localhost:8000/api/v1/content/sync -H "X-Sync-Token: your_secret"
```
