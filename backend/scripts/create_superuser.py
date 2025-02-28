import asyncio
import logging
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user
from app.database import AsyncSessionLocal
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_superuser() -> None:
    """Create a superuser interactively."""
    print("Creating superuser account...")
    
    # Get user input
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")
    
    if password != confirm_password:
        logger.error("Passwords don't match")
        return
    
    try:
        async with AsyncSessionLocal() as db:
            db_session: AsyncSession = db
            
            # Check if user already exists
            existing_user = await user.get_by_email(db_session, email=email)
            if existing_user:
                logger.error("User with this email already exists")
                return
                
            existing_user = await user.get_by_username(db_session, username=username)
            if existing_user:
                logger.error("User with this username already exists")
                return
            
            # Create superuser
            user_in = UserCreate(
                email=email,
                username=username,
                password=password,
                is_superuser=True,
            )
            await user.create(db_session, obj_in=user_in)
            logger.info(f"Superuser {username} created successfully")
            
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
        raise

def main() -> None:
    """Main function to run the script."""
    try:
        asyncio.run(create_superuser())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Failed to create superuser: {e}")
        raise

if __name__ == "__main__":
    main()