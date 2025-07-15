import pytest

# Маркер для асинхронных тестов
pytestmark = pytest.mark.asyncio


async def test_register_user_success(client):
    """Тест успешной регистрации пользователя."""
    response = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+79991234567",
            "password": "password123",
            "birthday": "2000-01-01",
            "gender": "male",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data


async def test_register_user_conflict(client):
    """Тест на ошибку при регистрации с уже существующим email."""
    # Сначала успешно регистрируем
    await client.post(
        "/api/auth/register",
        json={
            "full_name": "Conflict User", "email": "conflict@example.com",
            "phone": "+79997654321", "password": "password123",
            "birthday": "2000-01-01", "gender": "female",
        },
    )
    # Пытаемся зарегистрировать снова с тем же email
    response = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Another User", "email": "conflict@example.com",
            "phone": "+79991112233", "password": "password456",
            "birthday": "2001-02-02", "gender": "male",
        },
    )
    assert response.status_code == 409


async def test_login_success(client):
    """Тест успешного входа."""
    # Регистрируем пользователя, чтобы было кем логиниться
    email = "login_success@example.com"
    password = "password123"
    await client.post(
        "/api/auth/register",
        json={
            "full_name": "Login User", "email": email, "phone": "+79001112233",
            "password": password, "birthday": "2000-01-01", "gender": "male",
        },
    )
    # Пытаемся войти
    response = await client.post(
        "/api/auth/login",
        json={"login_identifier": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_failure(client):
    """Тест неудачного входа с неверным паролем."""
    response = await client.post(
        "/api/auth/login",
        json={"login_identifier": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
