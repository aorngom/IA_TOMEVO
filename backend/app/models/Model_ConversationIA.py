import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.base_de_donnees import Base
from datetime import datetime


class ConversationIA(Base):
    __tablename__ = "conversation_ia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    titre = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("MessageIA", back_populates="conversation", cascade="all, delete-orphan", order_by="MessageIA.created_at")


class MessageIA(Base):
    __tablename__ = "message_ia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversation_ia.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)       # 'user' ou 'assistant'
    content = Column(Text, nullable=False)
    action = Column(String(50), nullable=True)      # 'OUVRIR_FORMULAIRE', 'REUNION_CREEE', None
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    conversation = relationship("ConversationIA", back_populates="messages")