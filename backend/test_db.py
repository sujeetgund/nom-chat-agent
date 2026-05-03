import asyncio
import asyncpg
from config import get_settings


async def check_table():
    settings = get_settings()
    conn = await asyncpg.connect(settings.database_url)
    try:
        # Check if table exists
        result = await conn.fetchval("SELECT to_regclass('public.website_embeddings')")
        print(f"Table exists: {result}")

        # Get table schema
        schema = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'website_embeddings'
            ORDER BY ordinal_position
        """)
        print("Table schema:")
        for row in schema:
            print(f"  {row[0]}: {row[1]}")

        # Check row count
        count = await conn.fetchval("SELECT COUNT(*) FROM website_embeddings")
        print(f"Current rows in table: {count}")

    finally:
        await conn.close()


asyncio.run(check_table())
