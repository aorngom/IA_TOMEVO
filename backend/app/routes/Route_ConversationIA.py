from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.base_de_donnees import get_db
from app.services.Service_ConversationIA import (
    obtenir_toutes_conversations,
    obtenir_conversation_par_id,
    obtenir_conversation_par_session,
    supprimer_conversation
)
import uuid

router = APIRouter(tags=["Historique IA"])

@router.get("/")
def liste_conversations(db: Session = Depends(get_db)):
    """
    Liste toutes les conversations en vue résumée (avec nombre_messages).
    C'est la route appelée par Service_ConversationIA.listerToutes()
    """
    try:
        return obtenir_toutes_conversations(db)
    except Exception as e:
        print(f"Erreur liste_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
def conversation_par_session(session_id: str, db: Session = Depends(get_db)):
    """Récupère une conversation complète par session_id."""
    conv = obtenir_conversation_par_session(db, session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    return {
        "id": conv.id,
        "session_id": conv.session_id,
        "titre": conv.titre or "Conversation sans titre",
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "action": m.action,
                "created_at": m.created_at
            }
            for m in conv.messages
        ]
    }


@router.get("/{conversation_id}")
def detail_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Récupère une conversation complète par UUID.
    Note: On utilise 'str' ici pour éviter les crashs de conversion automatique, 
    le service se chargera de la recherche.
    """
    conv = obtenir_conversation_par_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    return {
        "id": conv.id,
        "session_id": conv.session_id,
        "titre": conv.titre or "Conversation sans titre",
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "action": m.action,
                "created_at": m.created_at
            }
            for m in conv.messages
        ]
    }


@router.delete("/{conversation_id}")
def supprimer(conversation_id: str, db: Session = Depends(get_db)):
    """Supprime une conversation et ses messages associés."""
    ok = supprimer_conversation(db, conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return {"message": "Conversation supprimée avec succès"}