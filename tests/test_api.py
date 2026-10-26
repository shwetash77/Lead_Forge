import httpx

from app import crm
from app.config import Settings
from app.db import Lead

GOOD_LEAD = {
    "name": "Asha Verma",
    "email": "asha@example.com",
    "phone": "+91-9000000000",
    "message": (
        "I want to enroll my daughter in the Python course next month. "
        "Budget is 15000 rupees. What is the fee?"
    ),
}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_lead_scores_and_stores(client):
    resp = client.post("/leads", json=GOOD_LEAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["score"] >= 6
    assert body["is_spam"] is False
    assert body["scored_by"] == "rules"
    assert client.get(f"/leads/{body['id']}").json()["email"] == "asha@example.com"


def test_spam_lead_is_stored_but_hidden_by_default(client):
    spam = {**GOOD_LEAD, "message": "Cheap SEO and backlinks, guaranteed ranking"}
    created = client.post("/leads", json=spam).json()
    assert created["is_spam"] is True
    assert client.get("/leads").json() == []
    assert len(client.get("/leads?include_spam=true").json()) == 1


def test_leads_sorted_by_score_descending(client):
    client.post("/leads", json={**GOOD_LEAD, "message": "hello there my friend"})
    client.post("/leads", json=GOOD_LEAD)
    scores = [lead["score"] for lead in client.get("/leads").json()]
    assert scores == sorted(scores, reverse=True)


def test_min_score_filter(client):
    client.post("/leads", json={**GOOD_LEAD, "message": "hello there my friend"})
    client.post("/leads", json=GOOD_LEAD)
    results = client.get("/leads?min_score=6").json()
    assert len(results) == 1


def test_validation_rejects_bad_email(client):
    resp = client.post("/leads", json={**GOOD_LEAD, "email": "not-an-email"})
    assert resp.status_code == 422


def test_validation_rejects_empty_message(client):
    resp = client.post("/leads", json={**GOOD_LEAD, "message": ""})
    assert resp.status_code == 422


def test_unknown_lead_returns_404(client):
    assert client.get("/leads/9999").status_code == 404


def test_api_key_required_when_configured(client, monkeypatch):
    monkeypatch.setenv("LEADFORGE_API_KEY", "secret123")
    assert client.post("/leads", json=GOOD_LEAD).status_code == 401
    assert client.post("/leads", json=GOOD_LEAD, headers={"x-api-key": "wrong"}).status_code == 401
    ok = client.post("/leads", json=GOOD_LEAD, headers={"x-api-key": "secret123"})
    assert ok.status_code == 201


def test_crm_skipped_without_token(client):
    lead_id = client.post("/leads", json=GOOD_LEAD).json()["id"]
    assert client.get(f"/leads/{lead_id}").json()["crm_status"] == "skipped"


def _lead_obj(**overrides) -> Lead:
    data = dict(
        id=1, name="Asha Verma", email="asha@example.com", phone="", message="hi",
        is_spam=False, score=8,
    )
    data.update(overrides)
    return Lead(**data)


def _hubspot_client(status: int, payload: dict | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer tok"
        return httpx.Response(status, json=payload or {})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_hubspot_success_returns_contact_id():
    settings = Settings()
    settings.hubspot_token = "tok"
    status, crm_id = crm.push_to_hubspot(_lead_obj(), settings, client=_hubspot_client(201, {"id": "501"}))
    assert (status, crm_id) == ("synced", "501")


def test_hubspot_duplicate_contact_counts_as_synced():
    settings = Settings()
    settings.hubspot_token = "tok"
    status, _ = crm.push_to_hubspot(_lead_obj(), settings, client=_hubspot_client(409))
    assert status == "synced"


def test_hubspot_failure_is_reported_not_raised():
    settings = Settings()
    settings.hubspot_token = "tok"
    status, _ = crm.push_to_hubspot(_lead_obj(), settings, client=_hubspot_client(500))
    assert status == "failed"


def test_spam_is_never_sent_to_crm():
    settings = Settings()
    settings.hubspot_token = "tok"
    status, _ = crm.push_to_hubspot(_lead_obj(is_spam=True), settings, client=_hubspot_client(201))
    assert status == "skipped"
