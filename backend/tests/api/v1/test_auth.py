import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models import User

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient, db: AsyncSession) -> None:
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
    }
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["email"] == data["email"]
    assert json_response["username"] == data["username"]
    assert "id" in json_response
    user = await crud.user.get_by_email(db, email=data["email"])
    assert user is not None
    assert user.email == data["email"]

async def test_register_existing_email(
    client: AsyncClient, normal_user: User
) -> None:
    data = {
        "email": "user@aitrader.com",  # Same as normal_user fixture
        "username": "newuser",
        "password": "testpass123",
    }
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 400
    assert "email already exists" in response.json()["detail"].lower()

async def test_register_existing_username(
    client: AsyncClient, normal_user: User
) -> None:
    data = {
        "email": "new@aitrader.com",
        "username": "testuser",  # Same as normal_user fixture
        "password": "testpass123",
    }
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 400
    assert "username already exists" in response.json()["detail"].lower()

async def test_login_success(client: AsyncClient, normal_user: User) -> None:
    data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    response = await client.post("/api/v1/auth/login", data=data)
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

async def test_login_wrong_password(
    client: AsyncClient, normal_user: AsyncSession
) -> None:
    data = {
        "username": "user@aitrader.com",
        "password": "wrongpass",
    }
    response = await client.post("/api/v1/auth/login", data=data)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

async def test_login_wrong_email(client: AsyncClient) -> None:
    data = {
        "username": "wrong@aitrader.com",
        "password": "user123",
    }
    response = await client.post("/api/v1/auth/login", data=data)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower() 