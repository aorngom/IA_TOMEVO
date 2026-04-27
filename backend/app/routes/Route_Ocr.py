from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.config.base_de_donnees import get_db
from sqlalchemy.orm import Session
from app.services.Service_Ocr import preparer_donnees_formulaire
from app.services.Service_Reunion import creer_reunion
from app.services.Service_ConversationIA import sauvegarder_messages
from app.services.Service_Employe import modifier_employe, supprimer_employe
from app.schemas.Schema_Employe import EmployeModification
from app.schemas.Schema_Reunion import ReunionCreation
import json
from sqlalchemy import text
from typing import List, Optional
import httpx
import os
import base64
from io import BytesIO
from datetime import datetime

try:
    from pdf2image import convert_from_bytes
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

router = APIRouter(tags=["OCR / IA"])


class Message(BaseModel):
    role: str
    content: str


class ChatPayload(BaseModel):
    messages: List[Message]
    contexte: Optional[str] = ""
    session_id: Optional[str] = None


@router.post("/chat")
async def chat_document(payload: ChatPayload, db: Session = Depends(get_db)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Clé API Groq absente.")

    # RÉCUPÉRATION DES INFOS BDD 
    try:
        deps_raw = db.execute(text("SELECT nom FROM departement")).fetchall()
        liste_deps = [d[0] for d in deps_raw]
        postes_raw = db.execute(text("SELECT libelle FROM poste")).fetchall()
        liste_postes = [p[0] for p in postes_raw]
        employes_raw = db.execute(
            text("SELECT id, nom, prenom, matricule FROM employe WHERE actif = TRUE")
        ).fetchall()
        liste_employes = [
            {"id": str(e[0]), "nom": e[1], "prenom": e[2], "matricule": e[3]}
            for e in employes_raw
        ]
        infos_bdd = f"DEPARTEMENTS: {liste_deps} | POSTES: {liste_postes}"
        infos_employes = json.dumps(liste_employes, ensure_ascii=False)
    except Exception:
        liste_deps, liste_postes, liste_employes = [], [], []
        infos_bdd = "Erreur lecture BDD"
        infos_employes = "[]"

    champs_complets = [
        "nom", "prenom", "matricule", "salaire_base_contrat", "departement", "poste",
        "date_embauche", "date_naissance", "civilite", "situation_matrimoniale",
        "adresse_residentielle", "telephone", "email_personnel", "num_cni",
        "lieu_naissance", "num_securite_sociale", "quartier", "banque", "rib_iban"
    ]

    # OUTILS 
    tools = [
        {
            "type": "function",
            "function": {
                "name": "ouvrir_formulaire_employe",
                "description": "Pre-remplit le formulaire de creation d'un nouvel employe. Convertis TOUJOURS les dates en YYYY-MM-DD. Le champ 'nom' est OBLIGATOIRE et doit contenir le nom de famille. Ne jamais utiliser 'nome' a la place de 'nom'. Pour le departement, utiliser EXACTEMENT les valeurs de l'enum avec accents (ex: 'Élevage' et non 'Elevage').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nom": {"type": "string", "description": "Nom de famille de l'employe. OBLIGATOIRE."},
                        "prenom": {"type": "string"},
                        "matricule": {"type": "string"},
                        "civilite": {"type": "string", "enum": ["M.", "Mme", "Mlle"]},
                        "date_naissance": {"type": "string", "description": "Format YYYY-MM-DD"},
                        "salaire_base_contrat": {"type": "number"},
                        "date_embauche": {"type": "string", "description": "Format YYYY-MM-DD"},
                        "departement": {
                            "type": "string", 
                            "enum": liste_deps, 
                            "description": "Valeur EXACTE avec accents requise (ex: 'Élevage' et non 'Elevage')."
                        },
                       "poste": {"type": "string", "enum": liste_postes},
                        "situation_matrimoniale": {
                            "type": "string", 
                            "enum": ["Célibataire", "Marié(e)", "Veuf(ve)", "Divorcé(e)"], 
                            "description": "Valeur EXACTE requise avec accents."
                        },                         "adresse_residentielle": {"type": "string"},
                        "telephone": {"type": "string"},
                        "email_personnel": {"type": "string"},
                        "num_cni": {"type": "string"},
                        "lieu_naissance": {"type": "string"},
                        "num_securite_sociale": {"type": "string"},
                        "quartier": {"type": "string"},
                        "banque": {"type": "string"},
                        "rib_iban": {"type": "string"}
                    },
                    "required": ["nom", "prenom", "matricule", "salaire_base_contrat", "departement", "poste"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "modifier_employe",
                "description": (
                    "Modifie les informations d'un employe existant. "
                    "Identifie l'employe par son matricule ou nom/prenom dans la liste des employes actifs. "
                    "Ne modifie QUE les champs explicitement mentionnes par l'utilisateur. "
                    "Pour poste et departement, resous le libelle en UUID depuis la liste BDD."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string", "description": "UUID de l'employe a modifier"},
                        "nom_employe": {"type": "string", "description": "Nom complet pour confirmation"},
                        "modifications": {
                            "type": "object",
                            "properties": {
                                "nom": {"type": "string"},
                                "prenom": {"type": "string"},
                                "telephone_perso": {"type": "string"},
                                "adresse_residentielle": {"type": "string"},
                                "ville": {"type": "string"},
                                "quartier": {"type": "string"},
                                "situation_matrimoniale": {"type": "string", "enum": ["Célibataire", "Marié(e)", "Veuf(ve)", "Divorcé(e)"]},
                                "nombre_enfants": {"type": "integer"},
                                "nom_banque": {"type": "string"},
                                "rib_iban": {"type": "string"},
                                "poste_id": {"type": "string"},
                                "departement_id": {"type": "string"},
                                "salaire_base_contrat": {"type": "number"},
                                "actif": {"type": "boolean"}
                            }
                        }
                    },
                    "required": ["employe_id", "modifications"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "supprimer_employe",
                "description": (
                    "Ne declenche cet outil QUE si l'utilisateur a explicitement confirme la suppression. "
                    "Supprime definitivement un employe. "
                    "Si l'utilisateur demande juste de supprimer sans confirmer, demande une confirmation d'abord. "
                    "Rappelle que l'action est irreversible."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employe_id": {"type": "string", "description": "UUID de l'employe a supprimer"},
                        "nom_employe": {"type": "string", "description": "Nom complet pour confirmation"}
                    },
                    "required": ["employe_id", "nom_employe"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "organiser_reunion",
                "description": (
                    "Cree et enregistre une reunion avec les participants specifies. "
                    "Utilise cet outil des que l'utilisateur demande d'organiser ou planifier une reunion. "
                    "Le champ date_heure doit etre en ISO 8601."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sujet": {"type": "string"},
                        "date_heure": {"type": "string"},
                        "lieu": {"type": "string"},
                        "ordre_du_jour": {"type": "string"},
                        "employe_ids": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["sujet", "date_heure", "employe_ids"]
                }
            }
        }
    ]

    # SYSTEM PROMPT 
    system_prompt = (
        f"Tu es l'intelligence de gestion centrale de Jariniou.\n\n"
        f"1. ANALYSE MULTIMODALE : Tu analyses les images de documents. Ton role est d'extraire les donnees textuelles et numeriques.\n\n"
        f"2. DISCRETION : Reponds poliment aux salutations. Ne donne les infos BDD que si on te le demande precisement.\n\n"
        f"3. RECOLTE STRICTE : Verifie qu'il ne manque rien d'essentiel. "
        f"NE DECLENCHE PAS le formulaire tant que tu n'as pas recolte les informations necessaires, sauf demande explicite de l'utilisateur.\n\n"
        f"4. REUNIONS : Processus OBLIGATOIRE en 3 etapes :\n"
        f"   ETAPE 1 : Demande le sujet, les participants (nom ou matricule), la date/heure et le lieu si non precises.\n"
        f"   ETAPE 2 : Une fois TOUTES les infos collectees, resous les UUIDs des participants depuis la liste fournie.\n"
        f"   ETAPE 3 : Seulement quand tu as sujet + date_heure + au moins un employe_id valide, utilise l'outil 'organiser_reunion'.\n"
        f"   NE JAMAIS appeler organiser_reunion sans avoir un tableau employe_ids contenant des UUIDs valides.\n\n"
        f"Si des noms sont ambigus, liste les correspondances possibles et demande confirmation.\n\n"
        f"5. MODIFICATION EMPLOYE : Processus OBLIGATOIRE en 3 etapes :\n"
        f"   ETAPE 1 : Si l'utilisateur ne precise pas quel employe modifier, demande-lui le nom ou matricule.\n"
        f"   ETAPE 2 : Une fois l'employe identifie et les modifications precisees, recapitule les changements "
        f"et demande UNE CONFIRMATION EXPLICITE ('Confirmez-vous ces modifications ? Repondez OUI pour valider.').\n"
        f"   ETAPE 3 : Seulement apres que l'utilisateur dit OUI ou confirme, utilise l'outil 'modifier_employe'.\n"
        f"   NE JAMAIS modifier sans avoir obtenu confirmation explicite.\n\n"
        f"6. SUPPRESSION EMPLOYE : Processus OBLIGATOIRE en 3 etapes :\n"
        f"   ETAPE 1 : Si l'utilisateur ne precise pas quel employe supprimer, demande le nom ou matricule.\n"
        f"   ETAPE 2 : Une fois identifie, affiche le nom complet et demande UNE CONFIRMATION EXPLICITE "
        f"('Confirmez-vous la suppression de [NOM] ? Cette action est IRREVERSIBLE. Repondez OUI pour confirmer.').\n"
        f"   ETAPE 3 : Seulement apres OUI explicite, utilise l'outil 'supprimer_employe'.\n"
        f"   NE JAMAIS supprimer sans confirmation explicite.\n\n"
        f"7. QUALITE : Utilise des tableaux Markdown. Mets les noms et matricules en **gras**.\n\n"
        f"8. SERIEUX : Pas d'emojis. Tres poli et expert.\n\n"
        f"9. RECOLTE EXHAUSTIVE : Pour un dossier complet, tu as besoin de : {', '.join(champs_complets)}. "
        f"IMPORTANT: Formate toujours les dates en YYYY-MM-DD." 
        f"CONSIGNE CRITIQUE : Pour le departement et la situation matrimoniale, utilise TOUJOURS les accents. "
        f"Ecris 'Élevage' (avec É majuscule), 'Célibataire', 'Marié(e)', 'Divorcé(e)'. "
        f"Si une info manque, previens que l'ouverture se fera apres 5 secondes.\n\n"
        f"10. PROTECTION : Ne donne que Nom, Matricule et Poste par defaut pour les listes d'employes.\n\n"
        f"CONTEXTE ACTUEL :\n"
        f"- Connaissances BDD : {infos_bdd}\n"
        f"- Liste des employes actifs : {infos_employes}\n"
        f"- Analyse document (OCR) : {payload.contexte}"
        f"11. DESACTIVATION vs SUPPRESSION : Par defaut, quand on te demande de 'supprimer' un employe, "
        f"propose TOUJOURS en premier de le desactiver (actif = false) plutot que de le supprimer definitivement. "
        f"Explique que la desactivation preserve l'historique de paie. "
        f"Utilise l'outil 'modifier_employe' avec 'actif: false' pour desactiver. "
        f"Ne procede a la suppression physique que si l'utilisateur insiste explicitement apres avoir ete informe.\n\n"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in payload.messages:
        messages.append(msg.model_dump())

    dernier_message_user = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    #"model": "llama-3.1-8b-instant",
                    #"model": "llama-3.1-70b-versatile",
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                }
            )

            res_data = reponse.json()
            if "choices" not in res_data:
                print(f"ERREUR GROQ: {json.dumps(res_data, indent=2)}")
                return {"reponse": f"Erreur API Groq : {res_data.get('error', {}).get('message', str(res_data))}"}
            message_ia = res_data["choices"][0]["message"]

            if "tool_calls" in message_ia:
                tool_call = message_ia["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])

                #  CAS 1 : Créer un employé 
                if tool_name == "ouvrir_formulaire_employe":
                    try:
                        manquants = [c.replace('_', ' ') for c in champs_complets if not args.get(c)]
                        resultat_service = preparer_donnees_formulaire(db, args)
                        msg_ia = "TRES BIEN, JE PREPARE LE FORMULAIRE."
                        if manquants:
                            msg_ia += f" ATTENTION : Il faudra completer manuellement : {', '.join(manquants)}. Ouverture dans 5 secondes..."
                        else:
                            msg_ia += " Toutes les informations sont pretes ! Ouverture dans 5 secondes..."
                        if payload.session_id:
                            sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action="OUVRIR_FORMULAIRE")
                        return {
                            "action": "OUVRIR_FORMULAIRE",
                            "donnees": resultat_service["data"],
                            "reponse": msg_ia,
                            "delai_secondes": 5
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la preparation : {str(e)}"}

                #  CAS 2 : Modifier un employé 
                elif tool_name == "modifier_employe":
                    try:
                        employe_id = args.get("employe_id")
                        nom_employe = args.get("nom_employe", "l'employe")

                        # Si employe_id n'est pas un UUID valide, chercher par nom/matricule
                        def _est_uuid(val):
                            try:
                                import uuid
                                uuid.UUID(str(val))
                                return True
                            except:
                                return False

                        if employe_id and not _est_uuid(str(employe_id)):
                            # Essayer de trouver par nom ou matricule
                            nom_recherche = nom_employe or employe_id
                            result = db.execute(
                                text("""
                                    SELECT id FROM employe 
                                    WHERE LOWER(nom) = LOWER(:nom) 
                                       OR LOWER(CONCAT(prenom, ' ', nom)) = LOWER(:nom)
                                       OR LOWER(CONCAT(nom, ' ', prenom)) = LOWER(:nom)
                                       OR matricule = :nom
                                    LIMIT 1
                                """),
                                {"nom": nom_recherche}
                            ).scalar()
                            if result:
                                employe_id = str(result)
                            else:
                                return {"reponse": f"Impossible d'identifier l'employe '{nom_recherche}'. Merci de preciser le matricule exact."}

                        modifications_brutes = args.get("modifications", {})

                        # Résoudre poste si nom fourni au lieu d'UUID
                        if "poste" in modifications_brutes and "poste_id" not in modifications_brutes:
                            poste_id = db.execute(
                                text("SELECT id FROM poste WHERE libelle = :libelle"),
                                {"libelle": modifications_brutes.pop("poste")}
                            ).scalar()
                            if poste_id:
                                modifications_brutes["poste_id"] = str(poste_id)

                        # Résoudre département si nom fourni au lieu d'UUID
                        if "departement" in modifications_brutes and "departement_id" not in modifications_brutes:
                            dep_id = db.execute(
                                text("SELECT id FROM departement WHERE nom = :nom"),
                                {"nom": modifications_brutes.pop("departement")}
                            ).scalar()
                            if dep_id:
                                modifications_brutes["departement_id"] = str(dep_id)

                        schema_modif = EmployeModification(**modifications_brutes)
                        employe_modifie = modifier_employe(db, employe_id, schema_modif)

                        if not employe_modifie:
                            msg_ia = "Employe introuvable avec l'identifiant fourni."
                            if payload.session_id:
                                sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action=None)
                            return {"reponse": msg_ia}

                        champs_modifies = list(modifications_brutes.keys())
                        resume = ", ".join(champs_modifies)
                        msg_ia = (
                            f"Les informations de **{nom_employe}** ont ete mises a jour avec succes.\n\n"
                            f"**Champs modifies :** {resume}"
                        )
                        if payload.session_id:
                            sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action="EMPLOYE_MODIFIE")
                        return {
                            "action": "EMPLOYE_MODIFIE",
                            "employe_id": employe_id,
                            "nom_employe": nom_employe,
                            "champs_modifies": champs_modifies,
                            "reponse": msg_ia
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la modification : {str(e)}"}
                #  CAS 3 : Supprimer un employé 
                elif tool_name == "supprimer_employe":
                    try:
                        employe_id = args.get("employe_id")
                        nom_employe = args.get("nom_employe", "l'employe")
                        succes = supprimer_employe(db, employe_id)
                        if not succes:
                            msg_ia = "Impossible de trouver l'employe pour le supprimer."
                            if payload.session_id:
                                sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action=None)
                            return {"reponse": msg_ia}
                        msg_ia = f"L'employe **{nom_employe}** a ete supprime definitivement de la base de donnees."
                        if payload.session_id:
                            try:
                                sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action="EMPLOYE_SUPPRIME")
                            except Exception:
                                pass  
                        return {
                            "action": "EMPLOYE_SUPPRIME",
                            "employe_id": employe_id,
                            "nom_employe": nom_employe,
                            "reponse": msg_ia
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la suppression : {str(e)}"}

                # CAS 4 : Organiser une réunion 
                elif tool_name == "organiser_reunion":
                    try:
                        import uuid as uuid_lib
                        employe_ids_valides = []
                        for eid in args.get("employe_ids", []):
                            try:
                                employe_ids_valides.append(uuid_lib.UUID(eid))
                            except Exception:
                                pass
                        donnees_reunion = ReunionCreation(
                            sujet=args["sujet"],
                            date_heure=datetime.fromisoformat(args["date_heure"]),
                            lieu=args.get("lieu"),
                            ordre_du_jour=args.get("ordre_du_jour"),
                            employe_ids=employe_ids_valides
                        )
                        reunion_cree = creer_reunion(db, donnees_reunion)
                        noms_participants = []
                        for p in reunion_cree.participants:
                            if p.employe:
                                noms_participants.append(f"{p.employe.prenom} {p.employe.nom}")
                        msg_ia = (
                            f"La reunion a ete organisee avec succes.\n\n"
                            f"**Sujet :** {reunion_cree.sujet}\n"
                            f"**Date :** {reunion_cree.date_heure.strftime('%d/%m/%Y a %Hh%M')}\n"
                            f"**Lieu :** {reunion_cree.lieu or 'Non precise'}\n"
                            f"**Participants ({len(noms_participants)}) :** {', '.join(noms_participants) if noms_participants else 'Aucun'}\n"
                        )
                        if reunion_cree.ordre_du_jour:
                            msg_ia += f"**Ordre du jour :** {reunion_cree.ordre_du_jour}"
                        if payload.session_id:
                            sauvegarder_messages(db, payload.session_id, dernier_message_user, msg_ia, action="REUNION_CREEE")
                        return {
                            "action": "REUNION_CREEE",
                            "reunion": {
                                "id": str(reunion_cree.id),
                                "sujet": reunion_cree.sujet,
                                "date_heure": reunion_cree.date_heure.isoformat(),
                                "lieu": reunion_cree.lieu,
                                "participants": noms_participants
                            },
                            "reponse": msg_ia
                        }
                    except Exception as e:
                        return {"reponse": f"Erreur lors de la creation de la reunion : {str(e)}"}

            #  CAS PAR DÉFAUT 
            reponse_texte = message_ia["content"]
            if payload.session_id and dernier_message_user:
                sauvegarder_messages(db, payload.session_id, dernier_message_user, reponse_texte, action=None)
            return {"reponse": reponse_texte}

    except Exception as e:
            import traceback
            traceback.print_exc()  # ← ajoute cette ligne
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyser")
async def analyser_document(fichier: UploadFile = File(...)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Cle API Groq absente.")
    contenu = await fichier.read()
    if fichier.content_type == "application/pdf":
        if not PDF_SUPPORT:
            return JSONResponse(status_code=400, content={"detail": "Support PDF non installe."})
        try:
            pages = convert_from_bytes(contenu, first_page=1, last_page=1)
            img_byte_arr = BytesIO()
            pages[0].save(img_byte_arr, format='JPEG')
            image_b64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur conversion PDF : {str(e)}")
    else:
        image_b64 = base64.b64encode(contenu).decode("utf-8")
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyse ce document RH. Si c'est pour un employe, extrais Nom, Prenom, Matricule, Poste, Departement, Salaire, Dates, Adresse, CNI, Telephone et RIB."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            data = reponse.json()
            if reponse.status_code != 200:
                return JSONResponse(status_code=reponse.status_code, content=data)
            return {"texte": data["choices"][0]["message"]["content"]}
    except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))