import asyncio
from sqlalchemy import text
from core.database import engine

async def main():
    async with engine.connect() as conn:
        # Alle Tabellen anzeigen
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
        tables = result.fetchall()
        print("Tables:", tables)

        # Beispiel: alle User anzeigen
        result = await conn.execute(text("SELECT * FROM users;"))
        users = result.fetchall()
        print("Users:", users)

asyncio.run(main())
