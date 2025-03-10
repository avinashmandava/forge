from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
import enum

class DealStage(enum.Enum):
    LEAD = "lead"
    CONTACT_MADE = "contact_made"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    industry = Column(String)
    website = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    position = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="contacts")
    deals = relationship("Deal", back_populates="contact")
    interactions = relationship("Interaction", back_populates="contact")

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    stage = Column(Enum(DealStage))
    value = Column(Float)
    company_id = Column(Integer, ForeignKey("companies.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expected_close_date = Column(DateTime(timezone=True))

    company = relationship("Company", back_populates="deals")
    contact = relationship("Contact", back_populates="deals")
    interactions = relationship("Interaction", back_populates="deal")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # email, call, meeting, etc.
    summary = Column(Text)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    deal_id = Column(Integer, ForeignKey("deals.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_analysis = Column(Text)  # Store AI-generated insights

    contact = relationship("Contact", back_populates="interactions")
    deal = relationship("Deal", back_populates="interactions")
