"""LeadForge API: receive a lead, score it, store it, sync it to the CRM."""
import hmac
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crm, scoring
from app.config import Settings, get_settings
from app.db import Lead, SessionLocal, init_db
from app.schemas import LeadIn, LeadOut

log = logging.getLogger("leadforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LeadForge", version="0.1.0", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(
    x_api_key: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key:  # auth disabled for local development
        return
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def sync_to_crm(lead_id: int) -> None:
    """Background task: push the lead to the CRM and record the outcome."""
    settings = get_settings()
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if lead is None:
            return
        lead.crm_status, lead.crm_id = crm.push_to_hubspot(lead, settings)
        db.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/leads", response_model=LeadOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_lead(
    payload: LeadIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    result, scorer = scoring.score_lead(payload, settings)
    lead = Lead(
        **payload.model_dump(),
        is_spam=result.is_spam,
        score=result.score,
        intent=result.intent,
        summary=result.summary,
        suggested_reply=result.suggested_reply,
        scored_by=scorer,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    background.add_task(sync_to_crm, lead.id)
    return lead


@app.get("/leads", response_model=list[LeadOut], dependencies=[Depends(require_api_key)])
def list_leads(
    min_score: int = Query(0, ge=0, le=10),
    include_spam: bool = False,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Lead).where(Lead.score >= min_score)
    if not include_spam:
        stmt = stmt.where(Lead.is_spam.is_(False))
    stmt = stmt.order_by(Lead.score.desc(), Lead.created_at.desc()).limit(limit)
    return db.scalars(stmt).all()


@app.get("/leads/{lead_id}", response_model=LeadOut, dependencies=[Depends(require_api_key)])
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
