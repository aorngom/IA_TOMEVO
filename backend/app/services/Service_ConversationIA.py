from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.Model_ConversationIA import ConversationIA, MessageIA
from typing import Optional
import uuid
from datetime import datetime

def obtenir_ou_creer_conversation(db: Session, session_id: str, premier_message: Optional[str] = None) -> ConversationIA:
    """
    Récupère une conversation existante par session_id.
    Si elle n'existe pas, la crée avec un titre basé sur le premier message.
    """
    conversation = db.query(ConversationIA).filter(
        ConversationIA.session_id == session_id
    ).first()

    if not conversation:
        titre = None
        if premier_message:
            # Titre = 50 premiers caractères du premier message, nettoyé
            titre = premier_message.strip()[:80]
            if len(premier_message.strip()) > 80:
                titre += "..."

        conversation = ConversationIA(
            session_id=session_id,
            titre=titre
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


def sauvegarder_messages(
    db: Session,
    session_id: str,
    message_user: str,
    message_assistant: str,
    action: Optional[str] = None
):
    """
    Sauvegarde la paire de messages (user + assistant) pour une session.
    Crée la conversation si elle n'existe pas encore.
    """
    try:
        conversation = obtenir_ou_creer_conversation(db, session_id, message_user)

        # Message utilisateur
        msg_user = MessageIA(
            conversation_id=conversation.id,
            role="user",
            content=message_user,
            action=None
        )
        db.add(msg_user)

        # Message assistant
        msg_assistant = MessageIA(
            conversation_id=conversation.id,
            role="assistant",
            content=message_assistant,
            action=action
        )
        db.add(msg_assistant)

        # Mettre à jour updated_at de la conversation
        from datetime import datetime
        conversation.updated_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ConversationIA] Erreur sauvegarde : {e}")


def obtenir_toutes_conversations(db: Session):
    """
    Retourne toutes les conversations avec le nombre de messages.
    Correction : Conversion des UUID en string pour éviter l'erreur 500 JSON.
    """
    conversations = (
        db.query(ConversationIA)
        .order_by(ConversationIA.updated_at.desc())
        .all()
    )

    result = []
    for conv in conversations:
        # On compte les messages liés
        nb = db.query(func.count(MessageIA.id)).filter(
            MessageIA.conversation_id == conv.id
        ).scalar()
        
        result.append({
            "id": str(conv.id), 
            "session_id": conv.session_id,
            "titre": conv.titre or "Conversation sans titre",
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "nombre_messages": nb or 0
        })
    return result



def obtenir_conversation_par_session(db: Session, session_id: str):
    """Retourne une conversation complète avec tous ses messages."""
    return (
        db.query(ConversationIA)
        .filter(ConversationIA.session_id == session_id)
        .first()
    )


def obtenir_conversation_par_id(db: Session, conversation_id: str):
    """
    Retourne une conversation complète par son ID (string ou UUID).
    """
    return (
        db.query(ConversationIA)
        .filter(ConversationIA.id == conversation_id)
        .first()
    )

def supprimer_conversation(db: Session, conversation_id) -> bool:
    conv = db.query(ConversationIA).filter(ConversationIA.id == conversation_id).first()
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True