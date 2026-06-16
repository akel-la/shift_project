import asyncio
from datetime import timedelta

from httpx import AsyncClient

from app.core.security import create_token


class TestRegistration:


    async def test_register_employee_success(self, client: AsyncClient):
        """
        Успешная регистрация нового пользователя.
        """
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "password123",
                "role": "employee",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


    async def test_register_employee_with_short_password_fail(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "123",
                "role": "employee",
            },
        )
        assert response.status_code == 422


    async def test_register_with_admin_role_forbidden(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newadmin",
                "password": "password123",
                "role": "admin",
            },
        )
        assert response.status_code == 403


    async def test_register_duplicate_username_conflict(
        self, client: AsyncClient, employee_user
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                # В фикстуре employee_user и тут - одно и то же имя.
                "username": "employee",
                "password": "password123",
                "role": "employee",
            },
        )
        assert response.status_code == 409


class TestLogin:


    async def test_login_employee_success(self, client: AsyncClient, employee_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "emp123456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


    async def test_login_wrong_password(self, client: AsyncClient, employee_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "ghost",
                "password": "password",
            },
        )
        assert response.status_code == 401


class TestRefreshToken:


    async def test_refresh_token_success(self, client: AsyncClient, employee_user):
        """
        Проверка того, что в генератор токенов создает разные значения токенов
        при разных обращениях одного и того же пользователя.
        """
        # 1. Вход через username и password:
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "emp123456",
            },
        )

        # 2. Берем refresh_token:
        tokens = login_resp.json()
        refresh = tokens["refresh_token"]

        # 3. Пауза, чтобы изменилось время создания токена:
        await asyncio.sleep(1.1)

        # 4. Используя полученный refresh, отправляем запрос
        # на получение новых access_token и refresh_token:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh}
        )

        # 5. Получаем ответ и проверяем, что были сгенерированы
        # новые access_token и refresh_token:
        assert response.status_code == 200
        new_tokens = response.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]


    async def test_refresh_with_access_token_fails(
        self, client: AsyncClient, employee_user
    ):
        """
        Входим через username, password, получаем access и refresh токены.
        Делаем запрос, вместо access token передав refresh token - ожидаем ошибку.
        (Нужно проверять, что пришел токен нужного типа).
        """
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "emp123456",
            },
        )
        access = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": access  # передаём access вместо refresh
            },
        )
        assert response.status_code == 401


    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """
        Запрос на получение нового access token с неправильным
        refresh токеном - ожидаем ошибку.
        """
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid token"}
        )
        assert response.status_code == 401


class TestCurrentUser:


    async def test_get_me_employee(self, client: AsyncClient, employee_token):
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "employee"
        assert user["role"] == "employee"


    async def test_get_me_without_token(self, client: AsyncClient):
        """
        Делаем запрос без токена - ожидаем ошибку.
        """
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """
        Запрос с неправильным токеном - ожидаем ошибку.
        """
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid token"}
        )
        assert response.status_code == 401


    async def test_get_me_with_expired_token(self, client: AsyncClient, employee_user):
        """
        Создаем просроченный токен (seconds=-1) и делаем запрос - ожидаем ошибку.
        """
        expired_token = create_token(
            data={"sub": str(employee_user.id)},
            token_type="access",
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestUserEndpoints:


    async def test_get_own_profile(
        self, client: AsyncClient, employee_token, employee_user
    ):
        response = await client.get(
            f"/api/v1/users/{employee_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == employee_user.id


    async def test_get_other_profile_forbidden(
        self, client: AsyncClient, employee_token, admin_user
    ):
        """
        Сотрудник пытается получить профиль админа - ожидаем ошибку.
        """
        response = await client.get(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 403


    async def test_admin_get_any_profile(
        self, client: AsyncClient, admin_token, employee_user
    ):
        """
        Администратор может получить любой профиль.
        """
        response = await client.get(
            f"/api/v1/users/{employee_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == employee_user.id


    async def test_update_own_username(
        self, client: AsyncClient, employee_token, employee_user
    ):
        response = await client.put(
            f"/api/v1/users/{employee_user.id}",
            json={"username": "new_emp_name"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "new_emp_name"


    async def test_update_own_role_forbidden(
        self, client: AsyncClient, employee_token, employee_user
    ):
        """
        Пытаемся назначить себе роль администратора - ожидаем ошибку.
        """
        response = await client.put(
            f"/api/v1/users/{employee_user.id}",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 403


    async def test_admin_update_user_role(
        self, client: AsyncClient, admin_token, employee_user
    ):
        """
        Администратор может менять роли других пользователей.
        """
        response = await client.put(
            f"/api/v1/users/{employee_user.id}",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


    async def test_update_password_and_login(
        self, client: AsyncClient, employee_token, employee_user
    ):
        # Новый пароль:
        response = await client.put(
            f"/api/v1/users/{employee_user.id}",
            json={"password": "newpassword123"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 200

        # Старый пароль - больше не работает:
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "emp123456",
            },
        )
        assert login_resp.status_code == 401

        # Новый пароль - работает:
        login_resp2 = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "employee",
                "password": "newpassword123",
            },
        )
        assert login_resp2.status_code == 200


    async def test_delete_user_by_employee_forbidden(
        self, client: AsyncClient, employee_token, admin_user
    ):
        response = await client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 403


    async def test_delete_user_by_admin_success(
        self, client: AsyncClient, admin_token, employee_user
    ):
        # Удаляем пользователя:
        response = await client.delete(
            f"/api/v1/users/{employee_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        # Если пользователь удален - то мы больше не можем получить его:
        get_response = await client.get(
            f"/api/v1/users/{employee_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == 404
