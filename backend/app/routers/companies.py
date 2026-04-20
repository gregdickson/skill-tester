from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company, CompanyBrain
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyOut, CompanyBrainOut

router = APIRouter()


@router.get("", response_model=list[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.name))
    return result.scalars().all()


@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(body: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(**body.model_dump())
    db.add(company)
    # Create empty brain
    brain = CompanyBrain(company_id=company.id)
    db.add(brain)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(company_id: UUID, body: CompanyUpdate, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/{company_id}/brain", response_model=CompanyBrainOut)
async def get_brain(company_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompanyBrain).where(CompanyBrain.company_id == company_id)
    )
    brain = result.scalars().first()
    if not brain:
        raise HTTPException(404, "Brain not found")
    return brain
