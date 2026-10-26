"""CRM sync (HubSpot contacts API). Best-effort: failures never block lead intake."""
import logging

import httpx

from app.config import Settings

log = logging.getLogger("leadforge.crm")

HUBSPOT_CONTACTS_URL = "https://api.hubapi.com/crm/v3/objects/contacts"


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def push_to_hubspot(lead, settings: Settings, client: httpx.Client | None = None) -> tuple[str, str]:
    """Create a contact in HubSpot. Returns (status, crm_id)."""
    if not settings.hubspot_token:
        return "skipped", ""
    if lead.is_spam:
        return "skipped", ""

    first, last = _split_name(lead.name)
    body = {
        "properties": {
            "email": lead.email,
            "firstname": first,
            "lastname": last,
            "phone": lead.phone,
            # Standard HubSpot field; the rest of the context goes in the note below.
            "hs_lead_status": "NEW" if lead.score < 7 else "OPEN",
        }
    }
    headers = {"Authorization": f"Bearer {settings.hubspot_token}"}
    owns_client = client is None
    client = client or httpx.Client(timeout=15)
    try:
        resp = client.post(HUBSPOT_CONTACTS_URL, json=body, headers=headers)
        if resp.status_code == 409:  # contact with this email already exists
            return "synced", ""
        resp.raise_for_status()
        return "synced", str(resp.json().get("id", ""))
    except Exception as exc:
        log.warning("HubSpot sync failed for lead %s: %s", lead.id, exc)
        return "failed", ""
    finally:
        if owns_client:
            client.close()
