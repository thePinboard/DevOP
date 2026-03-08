import asyncio
from sqlalchemy import text
from core.database import engine

async def main():
    async with engine.begin() as conn:
        # SQL-Statement als 'text' umwandeln
        await conn.execute(
            text("ALTER TABLE progress ALTER COLUMN step DROP NOT NULL;")
        )
        print("Spalte 'step' ist jetzt nullable.")

asyncio.run(main())
