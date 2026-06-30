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
maintenant = datetime.now()
date_actuelle = maintenant.strftime("%d/%m/%Y à %Hh%M")

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
                            "description": "Valeur EXACTE avec accents requise (ex: 'Élevage')."
                        },
                        "poste": {"type": "string", "enum": liste_postes},
                        "situation_matrimoniale": {
                            "type": "string", 
                            "enum": ["Célibataire", "Marié(e)", "Veuf(ve)", "Divorcé(e)"], 
                            "description": "Valeur EXACTE requise avec accents."
                        },
                        "adresse_residentielle": {"type": "string"},
                        "telephone_perso": {"type": "string", "description": "Numero de telephone personnel (ex: +22177...)"},
                        "email_perso": {"type": "string", "description": "Email personnel de l'employe"},
                        "num_cni": {"type": "string", "description": "Numero de carte nationale d'identite"},
                        "lieu_naissance": {"type": "string"},
                        "num_securite_sociale": {"type": "string", "description": "Numero IPRES/CSS"},
                        "quartier": {"type": "string"},
                        "nom_banque": {"type": "string", "description": "Nom de la banque (ex: CBAO, BICIS)"},
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
            f"Tu es l'assistant RH intelligent de Jariniou. Tu gères les employés, les réunions et l'analyse de documents. Ne prends pas trop de temps pour répondre, l'utilisateur est une personne occupée.\n"
            f"Date et heure actuelles du serveur : {date_actuelle}\n\n"        
            f"RÈGLES GÉNÉRALES :\n"
            f"- Réponds en français, de manière professionnelle et sans emojis.\n"
            f"- Utilise des tableaux Markdown et mets les noms/matricules en **gras**.\n"
            f"- Ne divulgue les informations des employés que si explicitement demandé.\n\n"
            f"CRÉATION D'EMPLOYÉ :\n"
            f"- Collecte tous les champs nécessaires : {', '.join(champs_complets)}.\n"
            f"- Dates toujours en YYYY-MM-DD.\n"
            f"- Ne déclenche le formulaire que si tu as au minimum : nom, prénom, matricule, salaire, poste, département.\n"
            f"- Si des informations manquent et que l'utilisateur insiste, ouvre quand même le formulaire en signalant les champs manquants.\n\n"
            f"MODIFICATION D'EMPLOYÉ :\n"
            f"- Identifie l'employé via la liste fournie (nom, prénom ou matricule).\n"
            f"- Demande confirmation avant d'agir : récapitule les changements et attends un OUI explicite.\n"
            f"- Ne modifie que les champs mentionnés par l'utilisateur.\n\n"
            f"SUPPRESSION D'EMPLOYÉ :\n"
            f"- Propose toujours la désactivation (actif=false) en premier, en expliquant que cela préserve l'historique de paie.\n"
            f"- Si l'utilisateur insiste pour supprimer définitivement, demande une confirmation explicite avant d'agir.\n\n"
            f"RÉUNIONS :\n"
            f"- Collecte : sujet, participants (identifiés dans la liste), date/heure et lieu.\n"
            f"- Résous les UUIDs des participants depuis la liste fournie avant d'appeler l'outil.\n"
            f"- N'appelle jamais l'outil sans avoir au moins un UUID valide dans employe_ids.\n"
            f"- Si une réunion vient d'être créée dans cette conversation, ne la recrée PAS. Complète ou confirme simplement.\n"
            f"- Ne déclenche l'outil organiser_reunion qu'UNE SEULE FOIS par demande.\n\n"
            f"ANALYSE OCR :\n"
            f"- Si un document est fourni, extrais les informations et propose de pré-remplir le formulaire.\n\n"
            f"DONNÉES DISPONIBLES :\n"
            f"- Départements et postes : {infos_bdd}\n"
            f"- Employés actifs : {infos_employes}\n"
            f"- Résultat OCR : {payload.contexte}\n"
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
                "https://api.openai.com/v1/chat/completions", # URL OpenAI
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini", # Modèle OpenAI
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
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", 
                     "text": (
                            "Analyse ce document RH de manière extrêmement complète et minutieuse. "
                            "Tu dois extraire TOUTES les informations visibles sans exception et les lister en Markdown (Ce n'est pas la peine de préciser que tu les formates en Markdown) :\n"
                            "- Civilité, Nom, Prénom\n"
                            "- Matricule\n"
                            "- Date de naissance et Lieu de naissance\n"
                            "- Situation matrimoniale et Nombre d'enfants\n"
                            "- Numéro de CNI complet\n"
                            "- Numéro de Sécurité Sociale (IPRES/CSS)\n"
                            "- Adresse résidentielle détaillée, Ville et Quartier séparés\n"
                            "- Téléphone personnel et Email personnel\n"
                            "- Poste exact et Département exact\n"
                            "- Date d'embauche et Salaire de base (FCFA)\n"
                            "- Banque et RIB / IBAN complet.\n\n"
                            "Prends ton temps, sois exhaustif. Si l'information est écrite sur l'image, tu dois l'extraire."
                        )
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            reponse = await client.post(
                "https://api.openai.com/v1/chat/completions",
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