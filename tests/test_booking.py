import datetime

from httpx import AsyncClient


class TestBookingCreation:
    async def test_create_booking_success(
        self, client: AsyncClient, employee_token, test_slot
    ):
        """
        Сотрудник может создать бронирование.
        """
        response = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=1)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slot_id"] == test_slot.id
        assert "id" in data

    async def test_create_booking_past_date_fails(
        self, client: AsyncClient, employee_token, test_slot
    ):
        """
        Бронирование на прошедшую дату запрещено.
        """
        response = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": "2020-01-01",
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 422

    async def test_create_booking_duplicate_slot_and_date_fails(
        self,
        client: AsyncClient,
        employee_token,
        test_slot,
    ):
        """
        Нельзя забронировать один и тот же слот на ту же дату дважды.
        """
        date = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()

        # Первое бронирование:
        first_response = await client.post(
            "/api/v1/bookings",
            json={"slot_id": test_slot.id, "booking_date": date},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert first_response.status_code == 201

        # Второе бронирование - должна быть ошибка:
        second_response = await client.post(
            "/api/v1/bookings",
            json={"slot_id": test_slot.id, "booking_date": date},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert second_response.status_code == 409

    async def test_create_booking_nonexistent_slot(
        self, client: AsyncClient, employee_token
    ):
        """
        Создание бронирования на несуществующий слот.
        """
        response = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": 9999,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=1)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 404


class TestBookingRetrieval:
    async def test_get_own_booking(
        self, client: AsyncClient, employee_token, test_slot
    ):
        """Сотрудник видит своё бронирование."""
        create_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=3)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        booking_id = create_resp.json()["id"]
        response = await client.get(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == booking_id

    async def test_get_other_booking_forbidden(
        self, client: AsyncClient, employee_token, admin_token, test_slot
    ):
        """Сотрудник не может просматривать чужое бронирование."""
        # Администратор создаёт бронь (от своего имени)
        admin_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=4)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        booking_id = admin_resp.json()["id"]
        # Сотрудник пытается прочитать
        response = await client.get(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 403

    async def test_admin_can_view_any_booking(
        self, client: AsyncClient, employee_token, admin_token, test_slot
    ):
        """Администратор может просматривать любые брони."""
        emp_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=5)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        booking_id = emp_resp.json()["id"]
        response = await client.get(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == booking_id

    async def test_get_all_bookings_filter(
        self,
        client: AsyncClient,
        employee_token,
        admin_token,
        test_slot,
    ):
        """
        Фильтрация бронирований по дате/комнате.
        """
        date = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()

        # Создадим бронирование сотрудником:
        create_slot = await client.post(
            "/api/v1/bookings",
            json={"slot_id": test_slot.id, "booking_date": date},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert create_slot.json()["booking_date"] == date, (
            f"Проблема в сериализации даты: "
            f"{create_slot.json()['booking_date']} != {date}"
        )
        assert create_slot.status_code == 201, (
            f"Не получилось создать слот: {create_slot.text}"
        )

        # Администратор получает все бронирования на дату:
        response = await client.get(
            f"/api/v1/bookings?date={date}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1, (
            f"Администратор не получил информацию о бронировании {response.text}"
        )

        # Сотрудник видит только свои (даже если запросит все):
        response_emp = await client.get(
            "/api/v1/bookings",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response_emp.status_code == 200

        # Бронирование сотрудника - одно, должно быть в списке:
        assert any(
            b["user_id"] == response_emp.json()[0]["user_id"]
            for b in response_emp.json()
        )


class TestBookingDeletion:
    async def test_delete_own_booking(
        self, client: AsyncClient, employee_token, test_slot
    ):
        """Сотрудник может отменить свою бронь."""
        create_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=7)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        booking_id = create_resp.json()["id"]
        response = await client.delete(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 204

    async def test_delete_other_booking_forbidden(
        self, client: AsyncClient, employee_token, admin_token, test_slot
    ):
        """Сотрудник не может отменить чужую бронь."""
        admin_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=8)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        booking_id = admin_resp.json()["id"]
        response = await client.delete(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert response.status_code == 403

    async def test_admin_delete_any_booking(
        self, client: AsyncClient, employee_token, admin_token, test_slot
    ):
        """Администратор может отменить любое бронирование."""
        emp_resp = await client.post(
            "/api/v1/bookings",
            json={
                "slot_id": test_slot.id,
                "booking_date": (
                    datetime.date.today() + datetime.timedelta(days=9)
                ).isoformat(),
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        booking_id = emp_resp.json()["id"]
        response = await client.delete(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204
