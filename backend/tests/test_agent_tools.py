from fastapi.testclient import TestClient

from app.main import app


def test_seed_and_log_interaction():
    with TestClient(app) as client:
        seeded = client.post("/api/seed")
        assert seeded.status_code == 200
        hcp_id = seeded.json()[0]["id"]

        response = client.post(
            "/api/interactions",
            json={
                "hcp_id": hcp_id,
                "channel": "in_person",
                "raw_notes": "Dr. Rao was interested in CardioFlow and asked for a follow-up next week.",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["summary"]
        assert "CardioFlow" in body["products_discussed"]


def test_agent_uses_tools():
    with TestClient(app) as client:
        seeded = client.post("/api/seed").json()
        hcp_id = seeded[0]["id"]
        response = client.post(
            "/api/agent/chat",
            json={
                "hcp_id": hcp_id,
                "message": "Log an in person visit: Dr was positive about GlucoTrack, requested access data, and asked us to schedule follow up next week.",
            },
        )
        assert response.status_code == 200
        event_names = [event["name"] for event in response.json()["tool_events"]]
        assert "log_interaction" in event_names
        assert "suggest_next_best_action" in event_names

