from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:Riad108515@localhost:5432/Agile_project"

# Create the database engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Sessionmaker for asynchronous sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get the database session
async def get_db():
    async with SessionLocal() as session:
        yield session
