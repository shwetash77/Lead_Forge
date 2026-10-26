import json

import httpx
import pytest

from app.config import Settings
from app.schemas import LeadIn
from app.scoring import _extract_json, score_lead, score_with_llm, score_with_rules


def make_lead(message: str) -> LeadIn:
    return LeadIn(name="Asha Verma", email="asha@example.com", message=message)


def test_rules_flag_spam():
    result = score_with_rules(make_lead("Buy cheap backlinks and SEO packages today"))
    assert result.is_spam is True
    assert result.score == 0


def test_rules_score_buying_intent_high():
    msg = "I want to enroll my daughter in the Python course starting next month. Budget is ₹15000."
    result = score_with_rules(make_lead(msg))
    assert result.is_spam is False
    assert result.score >= 6
    assert result.intent == "purchase enquiry"


def test_rules_score_vague_message_low():
    result = score_with_rules(make_lead("hello"))
    assert result.score <= 2


def test_extract_json_handles_surrounding_text():
    raw = 'Sure! Here you go:\n{"a": 1}\nHope that helps.'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_raises_without_object():
    with pytest.raises(ValueError):
        _extract_json("no json here")


def _llm_client(reply_text: str, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"content": [{"type": "text", "text": reply_text}]})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_llm_scoring_parses_valid_reply():
    reply = json.dumps(
        {
            "is_spam": False,
            "score": 9,
            "intent": "course enrollment",
            "summary": "Parent wants to enroll a child next month.",
            "suggested_reply": "Thanks! Here are the batch details.",
        }
    )
    settings = Settings()
    settings.anthropic_api_key = "test-key"
    result = score_with_llm(make_lead("I want to enroll"), settings, client=_llm_client(reply))
    assert result.score == 9
    assert result.intent == "course enrollment"


def test_llm_scoring_rejects_out_of_range_score():
    reply = json.dumps(
        {"is_spam": False, "score": 99, "intent": "x", "summary": "x", "suggested_reply": "x"}
    )
    settings = Settings()
    settings.anthropic_api_key = "test-key"
    with pytest.raises(Exception):
        score_with_llm(make_lead("hi there friend"), settings, client=_llm_client(reply))


def test_score_lead_falls_back_to_rules_when_llm_fails(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM down")

    monkeypatch.setattr("app.scoring.score_with_llm", boom)
    settings = Settings()
    settings.anthropic_api_key = "test-key"
    result, scorer = score_lead(make_lead("What is the price of the course?"), settings)
    assert scorer == "rules"
    assert result.score > 0


def test_score_lead_uses_rules_without_api_key():
    settings = Settings()
    settings.anthropic_api_key = ""
    _, scorer = score_lead(make_lead("What is the price of the course?"), settings)
    assert scorer == "rules"
