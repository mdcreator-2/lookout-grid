from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker, async_session
from collections.abc import AsyncGenerator
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

async_session_factory = async_sessionmaker(
    engine, 
    class_=async_session,
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()