import pytest

pytestmark = pytest.mark.asyncio


# --- Хелперы для создания тестовых данных ---
async def create_user_and_get_token(client, email, phone):
    """Регистрирует пользователя и возвращает его токен."""
    await client.post(
        "/api/auth/register",
        json={"full_name": "Test", "email": email, "phone": phone, "password": "123", "birthday": "2000-01-01",
              "gender": "male"}
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"login_identifier": email, "password": "123"}
    )
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


async def create_event(client, token, is_team=True):
    """Создает событие и возвращает его ID."""
    event_data = {
        "title": f"Test Event Team={is_team}", "date": "2025-10-10", "is_team": is_team,
        "max_members": 10, "max_teams": 5 if is_team else None
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/events", json=event_data, headers=headers)
    assert response.status_code == 200  # У вас в коде сейчас 200, а не 201
    return response.json()["event_id"]


# --- Тесты ---
async def test_create_and_join_team(client):
    """Тест: 1. Капитан создает команду. 2. Другой юзер вступает в нее."""
    # 1. Создаем двух пользователей и событие
    captain_token = await create_user_and_get_token(client, "captain@test.com", "+1")
    member_token = await create_user_and_get_token(client, "member@test.com", "+2")
    event_id = await create_event(client, captain_token, is_team=True)

    # 2. Капитан создает команду
    headers_captain = {"Authorization": f"Bearer {captain_token}"}
    response = await client.post(
        f"/api/events/{event_id}/participate",
        json={"participant_type": "team", "team_name": "Super Coders"},
        headers=headers_captain
    )
    assert response.status_code == 201
    participation_id = response.json()["id"]

    # 3. Второй участник присоединяется к команде
    headers_member = {"Authorization": f"Bearer {member_token}"}
    response = await client.post(f"/api/participations/{participation_id}/join", headers=headers_member)
    assert response.status_code == 204

    # 4. Проверяем, что в команде теперь два человека
    response = await client.get(f"/api/events/{event_id}/participations")
    assert response.status_code == 200
    participations = response.json()
    assert len(participations) == 1
    assert len(participations[0]["members"]) == 2


async def test_leave_team(client):
    """Тест: Участник самостоятельно покидает команду."""
    # 1. Создаем капитана, участника и команду
    captain_token = await create_user_and_get_token(client, "c_leave@test.com", "+3")
    member_token = await create_user_and_get_token(client, "m_leave@test.com", "+4")
    event_id = await create_event(client, captain_token, is_team=True)

    # Капитан создает команду
    headers_captain = {"Authorization": f"Bearer {captain_token}"}
    resp = await client.post(f"/api/events/{event_id}/participate",
                             json={"participant_type": "team", "team_name": "Leavers"}, headers=headers_captain)
    p_id = resp.json()["id"]

    # Участник вступает
    headers_member = {"Authorization": f"Bearer {member_token}"}
    await client.post(f"/api/participations/{p_id}/join", headers=headers_member)

    # Получаем ID участника
    member_profile = await client.get("/api/users/me", headers=headers_member)
    member_id = member_profile.json()["id"]

    # 2. Участник покидает команду
    response = await client.delete(f"/api/participations/{p_id}/members/{member_id}", headers=headers_member)
    assert response.status_code == 204

    # 3. Проверяем, что в команде остался один человек (капитан)
    response = await client.get(f"/api/events/{event_id}/participations")
    assert len(response.json()[0]["members"]) == 1
