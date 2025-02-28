import asyncio
import logging

from app.database import init_db
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init() -> None:
    logger.info("Creating initial database tables")
    try:
        await init_db()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def main() -> None:
    logger.info("Initializing database")
    asyncio.run(init())
    logger.info("Database initialization completed")

if __name__ == "__main__":
    main() 