import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.skip(reason="Requires running MongoDB with init_beanie")
def test_ask_missing_data_returns_clarification() -> None:
    response = client.post(
        "/api/v1/ask",
        json={
            "message": "Quiero reservar",
            "channel": "test",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["intent"] == "availability_check"
    assert body["requires_tool"] is False
    assert "necesito" in body["response"].lower()
