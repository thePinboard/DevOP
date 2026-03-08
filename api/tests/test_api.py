import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
def app():
    from main import app
    return app

@pytest.mark.asyncio
async def test_get_users(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_user_duplicate(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/users", json={
            "username": "alice",
            "email": "alice@example.com"
        })
    assert response.status_code == 409
    assert "existiert bereits" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_get_user_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User nicht gefunden"

@pytest.mark.asyncio
async def test_get_progress(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/progress/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_progress_user_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/progress/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_certificate(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/certificate/1")
    assert response.status_code == 200
    data = response.json()
    assert "eligible" in data
    assert "completed_phases" in data

@pytest.mark.asyncio
async def test_get_certificate_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/certificate/99999")
    assert response.status_code == 404
