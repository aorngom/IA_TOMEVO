from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class MessageIAReponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    action: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationIAReponse(BaseModel):
    id: uuid.UUID
    session_id: str
    titre: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageIAReponse] = []

    class Config:
        from_attributes = True


class ConversationIAResume(BaseModel):
    """Version allégée sans les messages, pour la liste"""
    id: uuid.UUID
    session_id: str
    titre: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    nombre_messages: int = 0

    class Config:
        from_attributes = True