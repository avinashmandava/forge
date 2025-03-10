from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.base import get_db
from app.schemas.crm import (
    Company, CompanyCreate,
    Contact, ContactCreate,
    Deal, DealCreate,
    Interaction, InteractionCreate
)
from app.services.ai_service import AIService
from app.models.crm import Company as CompanyModel
from app.models.crm import Contact as ContactModel
from app.models.crm import Deal as DealModel
from app.models.crm import Interaction as InteractionModel, DealStage
from sqlalchemy import select
from pydantic import BaseModel
import logging
import json

logger = logging.getLogger(__name__)

class InteractionText(BaseModel):
    text: str

router = APIRouter()
ai_service = AIService()

@router.post("/process-interaction/", response_model=Interaction)
async def process_interaction(
    interaction: InteractionText,
    db: AsyncSession = Depends(get_db)
):
    """Process a natural language interaction and extract CRM data."""
    try:
        # Extract entities from the text
        entities = await ai_service.extract_entities(interaction.text)
        logger.info(f"Extracted entities: {entities}")

        # Generate a summary
        summary = await ai_service.generate_interaction_summary(interaction.text)
        logger.info(f"Generated summary: {summary}")

        # Analyze sentiment and insights
        analysis = await ai_service.analyze_sentiment(interaction.text)
        logger.info(f"Sentiment analysis: {analysis}")

        # Try to find the contact based on extracted information
        contact_id = None
        if entities.get("contact_first_name") or entities.get("contact_last_name"):
            query = select(ContactModel)
            conditions = []

            if entities.get("contact_first_name"):
                conditions.append(ContactModel.first_name.ilike(f"%{entities['contact_first_name']}%"))
            if entities.get("contact_last_name"):
                conditions.append(ContactModel.last_name.ilike(f"%{entities['contact_last_name']}%"))

            if conditions:
                query = query.where(*conditions)
                result = await db.execute(query)
                contact = result.scalar_one_or_none()
                if contact:
                    contact_id = contact.id
                    logger.info(f"Found matching contact: {contact.first_name} {contact.last_name}")

        # Create interaction record
        combined_analysis = {
            **analysis,  # Include sentiment analysis
            **entities,  # Include extracted entities
        }

        db_interaction = InteractionModel(
            type="conversation",
            summary=summary,
            contact_id=contact_id,
            ai_analysis=json.dumps(combined_analysis)  # Store as proper JSON string
        )

        # If we found a deal value or stage, create/update a deal
        if entities.get("deal_value") or entities.get("deal_stage"):
            # Check if there's an existing deal for this contact
            if contact_id:
                result = await db.execute(
                    select(DealModel).where(DealModel.contact_id == contact_id)
                )
                deal = result.scalar_one_or_none()

                if not deal and entities.get("deal_value"):
                    # Create new deal
                    deal = DealModel(
                        title=f"Deal with {entities.get('company_name', 'Unknown Company')}",
                        value=float(str(entities["deal_value"]).replace("$", "").replace("k", "000")),
                        stage=DealStage.CONTACT_MADE,
                        contact_id=contact_id,
                        company_id=contact.company_id if contact else None
                    )
                    db.add(deal)
                    await db.flush()
                    db_interaction.deal_id = deal.id

        db.add(db_interaction)
        await db.commit()
        await db.refresh(db_interaction)

        return db_interaction
    except Exception as e:
        logger.error(f"Error processing interaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/companies/", response_model=Company)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Creating company with data: {company.dict()}")
        db_company = CompanyModel(**company.dict())
        db.add(db_company)
        await db.commit()
        await db.refresh(db_company)
        return db_company
    except Exception as e:
        logger.error(f"Error creating company: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contacts/", response_model=Contact)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Creating contact with data: {contact.dict()}")
        db_contact = ContactModel(**contact.dict())
        db.add(db_contact)
        await db.commit()
        await db.refresh(db_contact)
        return db_contact
    except Exception as e:
        logger.error(f"Error creating contact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deals/", response_model=Deal)
async def create_deal(
    deal: DealCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Creating deal with data: {deal.dict()}")
        db_deal = DealModel(**deal.dict())
        db.add(db_deal)
        await db.commit()
        await db.refresh(db_deal)
        return db_deal
    except Exception as e:
        logger.error(f"Error creating deal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/", response_model=List[Company])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(CompanyModel).offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing companies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contacts/", response_model=List[Contact])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(ContactModel).offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deals/", response_model=List[Deal])
async def list_deals(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(DealModel).offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing deals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/search/", response_model=List[Company])
async def search_companies(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(CompanyModel).where(CompanyModel.name == name)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error searching companies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactions/", response_model=List[Interaction])
async def list_interactions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(InteractionModel)
            .order_by(InteractionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing interactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
