from sqlalchemy.orm import Session, joinedload
from app.models.Model_Reunion import Reunion, ParticipantReunion
from app.models.Model_Employe import Employe
from app.schemas.Schema_Reunion import ReunionCreation, ReunionModification
import uuid
 
 
def obtenir_toutes_reunions(db: Session):
    return (
        db.query(Reunion)
        .options(joinedload(Reunion.participants).joinedload(ParticipantReunion.employe))
        .order_by(Reunion.date_heure.desc())
        .all()
    )
 
 
def obtenir_reunion_par_id(db: Session, reunion_id: uuid.UUID):
    return (
        db.query(Reunion)
        .options(joinedload(Reunion.participants).joinedload(ParticipantReunion.employe))
        .filter(Reunion.id == reunion_id)
        .first()
    )
 
 
def creer_reunion(db: Session, donnees: ReunionCreation):
    reunion = Reunion(
        sujet=donnees.sujet,
        date_heure=donnees.date_heure,
        lieu=donnees.lieu,
        ordre_du_jour=donnees.ordre_du_jour,
    )
    db.add(reunion)
    db.flush()  # Pour avoir l'id avant le commit
 
    for emp_id in donnees.employe_ids:
        employe = db.query(Employe).filter(Employe.id == emp_id).first()
        if employe:
            participant = ParticipantReunion(
                reunion_id=reunion.id,
                employe_id=emp_id,
                presence_confirmee=False
            )
            db.add(participant)
 
    db.commit()
    db.refresh(reunion)
    return obtenir_reunion_par_id(db, reunion.id)
 
 
def modifier_reunion(db: Session, reunion_id: uuid.UUID, donnees: ReunionModification):
    reunion = db.query(Reunion).filter(Reunion.id == reunion_id).first()
    if not reunion:
        return None
 
    if donnees.sujet is not None:
        reunion.sujet = donnees.sujet
    if donnees.date_heure is not None:
        reunion.date_heure = donnees.date_heure
    if donnees.lieu is not None:
        reunion.lieu = donnees.lieu
    if donnees.ordre_du_jour is not None:
        reunion.ordre_du_jour = donnees.ordre_du_jour
 
    if donnees.employe_ids is not None:
        # Supprimer anciens participants
        db.query(ParticipantReunion).filter(ParticipantReunion.reunion_id == reunion_id).delete()
        for emp_id in donnees.employe_ids:
            employe = db.query(Employe).filter(Employe.id == emp_id).first()
            if employe:
                db.add(ParticipantReunion(
                    reunion_id=reunion_id,
                    employe_id=emp_id,
                    presence_confirmee=False
                ))
 
    db.commit()
    return obtenir_reunion_par_id(db, reunion_id)
 
 
def supprimer_reunion(db: Session, reunion_id: uuid.UUID):
    reunion = db.query(Reunion).filter(Reunion.id == reunion_id).first()
    if not reunion:
        return False
    db.delete(reunion)
    db.commit()
    return True
 
 
def confirmer_presence(db: Session, reunion_id: uuid.UUID, employe_id: uuid.UUID):
    participant = db.query(ParticipantReunion).filter(
        ParticipantReunion.reunion_id == reunion_id,
        ParticipantReunion.employe_id == employe_id
    ).first()
    if not participant:
        return None
    participant.presence_confirmee = True
    db.commit()
    return participant
 