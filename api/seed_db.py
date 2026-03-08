import asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from core.database import engine
from models import User, Progress

async def main():
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Prüfen, ob der Test-User bereits existiert
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            # User anlegen
            user = User(username="testuser", email="test@example.com")
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"User '{user.username}' erstellt mit ID {user.id}")
        else:
            print(f"User '{user.username}' existiert bereits mit ID {user.id}")

        # Prüfen, ob Progress-Einträge schon existieren
        result = await session.execute(
            select(Progress).where(Progress.user_id == user.id)
        )
        progress_entries = result.scalars().all()

        if not progress_entries:
            # Beispiel-Fortschritt anlegen
            progress1 = Progress(user_id=user.id, phase="Phase 1", step=1, completed=True)
            progress2 = Progress(user_id=user.id, phase="Phase 1", step=2, completed=False)
            session.add_all([progress1, progress2])
            await session.commit()
            print(f"{len([progress1, progress2])} Progress-Einträge für User '{user.username}' erstellt")
        else:
            print(f"Progress-Einträge für User '{user.username}' existieren bereits")

        # Prüfen: alle User anzeigen
        result = await session.execute(select(User))
        users = result.scalars().all()
        print("Alle User in der DB:", users)

asyncio.run(main())
