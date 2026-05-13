from fastapi.testclient import TestClient

from app.main import app


def test_run_debate_returns_mock_without_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/debate/run",
        json={"topic": "AI 是否会取代程序员", "rounds": 2, "style": "serious"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "AI 是否会取代程序员"
    assert data["mock"] is True
    assert len(data["messages"]) == 4
    assert data["judge"]["winner"] in {"affirmative", "negative", "draw"}

