import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud

pytestmark = pytest.mark.asyncio

async def test_read_users_superuser(
    client: AsyncClient, superuser_token_headers: dict
) -> None:
    response = await client.get("/api/v1/users/", headers=superuser_token_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0
    for user in users:
        assert "id" in user
        assert "email" in user
        assert "username" in user

async def test_read_users_normal_user(
    client: AsyncClient, normal_user: AsyncSession
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access users list
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 400
    assert "not enough privileges" in response.json()["detail"].lower()

async def test_read_user_me(
    client: AsyncClient, normal_user: AsyncSession
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get own user info
    response = await client.get("/api/v1/users/me/", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "user@aitrader.com"
    assert user_data["username"] == "normaluser"

async def test_update_user_me(
    client: AsyncClient, normal_user: AsyncSession
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update own user info
    data = {
        "username": "updateduser",
        "email": "updated@aitrader.com",
    }
    response = await client.put("/api/v1/users/me", headers=headers, json=data)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == data["email"]
    assert user_data["username"] == data["username"]

async def test_read_user_by_id(
    client: AsyncClient, normal_user: AsyncSession, superuser_token_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{normal_user.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == normal_user.id
    assert user_data["email"] == normal_user.email
    assert user_data["username"] == normal_user.username

async def test_update_user_superuser(
    client: AsyncClient, normal_user: AsyncSession, superuser_token_headers: dict
) -> None:
    data = {
        "username": "updatedbyadmin",
        "email": "updatedbyadmin@aitrader.com",
    }
    response = await client.put(
        f"/api/v1/users/{normal_user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == data["email"]
    assert user_data["username"] == data["username"] 