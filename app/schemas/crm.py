from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.crm import DealStage

class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: int

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class DealBase(BaseModel):
    title: str
    stage: DealStage
    value: Optional[float] = None
    company_id: int
    contact_id: int
    description: Optional[str] = None
    expected_close_date: Optional[datetime] = None

class DealCreate(DealBase):
    pass

class Deal(DealBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class InteractionBase(BaseModel):
    type: str
    summary: str
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    ai_analysis: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class Interaction(InteractionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
