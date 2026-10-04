from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.session import get_db
from backend.models import Lab
from backend.schemas.catalog import LabOut, SubjectOut
from config.labs import SUBJECTS

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects() -> list[SubjectOut]:
    labels = {"ADS": "Algorithms & Data Structures", "PP1": "PP1", "PP2": "PP2"}
    return [SubjectOut(code=s, label=labels.get(s, s)) for s in SUBJECTS]


@router.get("/labs", response_model=list[LabOut])
async def list_labs(
    subject: str = Query(..., pattern="^(ADS|PP1|PP2)$"),
    session: AsyncSession = Depends(get_db),
) -> list[LabOut]:
    result = await session.execute(
        select(Lab)
        .where(Lab.subject == subject, Lab.is_active.is_(True))
        .options(selectinload(Lab.languages))
        .order_by(Lab.lab_number)
    )
    return list(result.scalars().all())
