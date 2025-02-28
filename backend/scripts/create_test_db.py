import asyncio
import asyncpg
from app.config import settings

async def create_test_db():
    # Connect to default database
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database='postgres'
    )
    
    try:
        # Try to create the test database
        await conn.execute(f'CREATE DATABASE {settings.TEST_DB}')
        print(f"Test database '{settings.TEST_DB}' created successfully")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f"Test database '{settings.TEST_DB}' already exists")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_db()) 