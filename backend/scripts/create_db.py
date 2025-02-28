import asyncio
import asyncpg
from app.config import settings

async def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to default database
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database='postgres'
        )
        
        # Check if database exists
        result = await conn.fetchrow(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.POSTGRES_DB
        )
        
        if not result:
            # Create database if it doesn't exist
            await conn.execute(f'CREATE DATABASE {settings.POSTGRES_DB}')
            print(f"Database '{settings.POSTGRES_DB}' created successfully")
        else:
            print(f"Database '{settings.POSTGRES_DB}' already exists")
            
    except Exception as e:
        print(f"Error creating database: {e}")
        raise
    finally:
        await conn.close()

def main():
    """Main function to run the script."""
    asyncio.run(create_database())

if __name__ == "__main__":
    main() 