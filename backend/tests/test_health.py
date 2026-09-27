"""
Smoke tests for the Aegis gateway.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint_has_credit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert "NIKHIL CHARY SRIRAMOJU" in response.json()["designed_and_developed_by"]


@pytest.mark.asyncio
async def test_languages_endpoint_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/execute/languages", headers={"Authorization": "Bearer invalid"})
    assert response.status_code in (401, 403)
