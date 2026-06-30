from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.config.base_de_donnees import get_db
from app.services.Service_PaieIA import (
    calculer_salaire_complet,
    sauvegarder_fiche_calculee,
    lancer_paie_masse
)
from app.services.Service_Mail import envoyer_bulletin_employe
import traceback

# INSTANCE GLOBALE DU SCHEDULER
scheduler = AsyncIOScheduler(timezone="Africa/Dakar")


# 1. TÂCHE PRINCIPALE : PAIE AUTOMATIQUE

async def tache_paie_automatique(mois: int, annee: int):
    """
    Tâche déclenchée automatiquement par le scheduler.
    1. Génère les fiches de paie pour tous les employés actifs
    2. Envoie les bulletins par mail
    3. Logue l'exécution dans log_paie
    """
    print(f"\n[SCHEDULER] Déclenchement paie automatique — {mois}/{annee}")
    db: Session = next(get_db())

    nb_generes = 0
    nb_mails = 0
    nb_erreurs = 0
    details = {"generes": [], "mails": [], "erreurs": []}

    try:
        # Récupérer tous les employés actifs
        employes = db.execute(text(
            "SELECT id FROM employe WHERE actif = TRUE"
        )).fetchall()

        for emp in employes:
            emp_id = str(emp[0])
            try:
                # Calcul du salaire
                calcul = calculer_salaire_complet(db, emp_id, mois, annee)

                # Sauvegarde fiche
                fiche_id = sauvegarder_fiche_calculee(db, calcul)
                nb_generes += 1
                details["generes"].append({
                    "employe": f"{calcul['prenom']} {calcul['nom']}",
                    "matricule": calcul["matricule"],
                    "fiche_id": fiche_id
                })

                # Envoi mail bulletin
                if calcul.get("email_perso"):
                    resultat_mail = await envoyer_bulletin_employe(calcul)
                    if resultat_mail["succes"]:
                        nb_mails += 1
                        details["mails"].append(calcul["email_perso"])

                        # Marquer la fiche comme envoyée
                        db.execute(text("""
                            UPDATE fiche_paie
                            SET est_envoyee = TRUE, date_envoi = NOW()
                            WHERE id = :fiche_id
                        """), {"fiche_id": fiche_id})
                        db.commit()

            except ValueError as e:
                if "existe déjà" in str(e):
                    pass  # Fiche déjà générée, on ignore silencieusement
                else:
                    nb_erreurs += 1
                    details["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})
            except Exception as e:
                nb_erreurs += 1
                details["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})
                traceback.print_exc()

        # Log de l'exécution
        _logger_execution(
            db=db,
            type_exec="automatique",
            mois=mois,
            annee=annee,
            nb_generes=nb_generes,
            nb_mails=nb_mails,
            nb_erreurs=nb_erreurs,
            details=details,
            declenche_par="scheduler"
        )

        print(
            f"[SCHEDULER] Terminé — "
            f"{nb_generes} fiches générées, "
            f"{nb_mails} mails envoyés, "
            f"{nb_erreurs} erreurs"
        )

    except Exception as e:
        traceback.print_exc()
        print(f"[SCHEDULER] Erreur critique : {str(e)}")
    finally:
        db.close()


# 2. LOGGER EXÉCUTIONS

def _logger_execution(
    db: Session,
    type_exec: str,
    mois: int,
    annee: int,
    nb_generes: int,
    nb_mails: int,
    nb_erreurs: int,
    details: dict,
    declenche_par: str
):
    """Enregistre l'exécution dans log_paie."""
    import json
    try:
        db.execute(text("""
            INSERT INTO log_paie (
                type_execution, periode_mois, periode_annee,
                nb_fiches_generees, nb_mails_envoyes, nb_erreurs,
                details, declenche_par
            ) VALUES (
                :type_exec, :mois, :annee,
                :nb_gen, :nb_mails, :nb_err,
                :details, :declenche_par
            )
        """), {
            "type_exec": type_exec,
            "mois": mois,
            "annee": annee,
            "nb_gen": nb_generes,
            "nb_mails": nb_mails,
            "nb_err": nb_erreurs,
            "details": json.dumps(details, ensure_ascii=False),
            "declenche_par": declenche_par
        })
        db.commit()
    except Exception as e:
        print(f"[SCHEDULER] Erreur log : {str(e)}")


# 3. LIRE LA CONFIG DEPUIS LA BDD

def lire_config_paie(db: Session) -> dict:
    """Lit la config du scheduler depuis config_paie."""
    config = db.execute(text("""
        SELECT jour_declenchement, heure_declenchement, actif
        FROM config_paie
        WHERE actif = TRUE
        LIMIT 1
    """)).fetchone()

    if not config:
        return {"jour": 28, "heure": 23, "minute": 0, "actif": True}

    heure_str = str(config[1])  # ex: "23:00:00"
    parties = heure_str.split(":")
    heure = int(parties[0])
    minute = int(parties[1]) if len(parties) > 1 else 0

    return {
        "jour": int(config[0]),
        "heure": heure,
        "minute": minute,
        "actif": bool(config[2])
    }

def verifier_rappels_wrapper():
    """Wrapper synchrone pour appeler la coroutine async depuis APScheduler."""
    import asyncio
    db: Session = next(get_db())
    try:
        asyncio.get_event_loop().run_until_complete(verifier_rappels(db))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(verifier_rappels(db))
    finally:
        db.close()


# 4. DÉMARRAGE DU SCHEDULER

def demarrer_scheduler():
    try:
        db: Session = next(get_db())
        config = lire_config_paie(db)
        db.close()

        if not config["actif"]:
            print("[SCHEDULER] Scheduler désactivé dans config_paie.")
            return

        _programmer_job_paie(
            jour=config["jour"],
            heure=config["heure"],
            minute=config["minute"]
        )

        # ── Job vérification rappels toutes les minutes ──
        scheduler.add_job(
            verifier_rappels_wrapper,
            trigger="interval",
            minutes=1,
            id="verifier_rappels",
            name="Vérification rappels IA",
            replace_existing=True
        )

        scheduler.start()
        print(
            f"[SCHEDULER] Démarré — Paie programmée le {config['jour']} "
            f"de chaque mois à {config['heure']:02d}h{config['minute']:02d}"
        )
        print("[SCHEDULER] Vérification rappels active — toutes les minutes.")

    except Exception as e:
        print(f"[SCHEDULER] Erreur au démarrage : {str(e)}")
        traceback.print_exc()

def arreter_scheduler():
    """Appelé au shutdown de FastAPI."""
    if scheduler.running:
        scheduler.shutdown()
        print("[SCHEDULER] Arrêté.")


# 5. PROGRAMMER / REPROGRAMMER LE JOB

def _programmer_job_paie(jour: int, heure: int, minute: int):
    """
    Programme (ou reprogramme) le job de paie automatique.
    """
    now = datetime.now()

    # Déterminer le mois cible (mois courant ou suivant selon le jour)
    if now.day > jour:
        # On est après le jour de paie → prochain mois
        if now.month == 12:
            mois_cible = 1
            annee_cible = now.year + 1
        else:
            mois_cible = now.month + 1
            annee_cible = now.year
    else:
        mois_cible = now.month
        annee_cible = now.year

    # Supprimer l'ancien job s'il existe
    if scheduler.get_job("paie_automatique"):
        scheduler.remove_job("paie_automatique")

    # Programmer le nouveau job
    scheduler.add_job(
        tache_paie_automatique,
        trigger=CronTrigger(
            day=jour,
            hour=heure,
            minute=minute,
            month="*"
        ),
        args=[mois_cible, annee_cible],
        id="paie_automatique",
        name="Paie automatique mensuelle",
        replace_existing=True,
        misfire_grace_time=3600  # 1h de tolérance si le serveur était éteint
    )

    print(
        f"[SCHEDULER] Job reprogrammé — "
        f"Cible : {mois_cible}/{annee_cible} "
        f"le {jour} à {heure:02d}h{minute:02d}"
    )


# 6. RECONFIGURATION VIA PROMPT IA

async def reconfigurer_planning(
    db: Session,
    jour: int,
    heure: int,
    minute: int
) -> dict:
    """
    Appelé par le tool de l'agent IA pour changer la date de déclenchement.
    Met à jour config_paie en BDD et reprogramme le scheduler.
    """
    try:
        # Validation
        if not (1 <= jour <= 28):
            return {"succes": False, "detail": "Le jour doit être entre 1 et 28."}
        if not (0 <= heure <= 23):
            return {"succes": False, "detail": "L'heure doit être entre 0 et 23."}
        if not (0 <= minute <= 59):
            return {"succes": False, "detail": "Les minutes doivent être entre 0 et 59."}

        # Mise à jour BDD
        db.execute(text("""
            UPDATE config_paie
            SET jour_declenchement = :jour,
                heure_declenchement = :heure,
                updated_at = NOW()
            WHERE actif = TRUE
        """), {
            "jour": jour,
            "heure": f"{heure:02d}:{minute:02d}:00"
        })
        db.commit()

        # Reprogrammer le scheduler
        _programmer_job_paie(jour=jour, heure=heure, minute=minute)

        return {
            "succes": True,
            "detail": (
                f"Planning mis à jour : paie déclenchée le {jour} "
                f"de chaque mois à {heure:02d}h{minute:02d}."
            )
        }

    except Exception as e:
        return {"succes": False, "detail": f"Erreur : {str(e)}"}


# 7. DÉCLENCHEMENT IMMÉDIAT (pour tests)

async def declencher_maintenant(
    db: Session,
    mois: int,
    annee: int,
    type_exec: str = "test"
) -> dict:
    """
    Déclenche la paie immédiatement sans attendre le scheduler.
    Utilisé pour les tests ou les lancements manuels via l'agent IA.
    """
    try:
        employes = db.execute(text(
            "SELECT id FROM employe WHERE actif = TRUE"
        )).fetchall()

        nb_generes = 0
        nb_mails = 0
        nb_erreurs = 0
        details = {"generes": [], "mails": [], "erreurs": []}

        for emp in employes:
            emp_id = str(emp[0])
            try:
                calcul = calculer_salaire_complet(db, emp_id, mois, annee)
                fiche_id = sauvegarder_fiche_calculee(db, calcul)
                nb_generes += 1
                details["generes"].append({
                    "employe": f"{calcul['prenom']} {calcul['nom']}",
                    "matricule": calcul["matricule"],
                    "net": calcul["salaire_net"],
                    "fiche_id": fiche_id
                })

                if calcul.get("email_perso"):
                    resultat_mail = await envoyer_bulletin_employe(calcul)
                    if resultat_mail["succes"]:
                        nb_mails += 1
                        details["mails"].append(calcul["email_perso"])
                        db.execute(text("""
                            UPDATE fiche_paie
                            SET est_envoyee = TRUE, date_envoi = NOW()
                            WHERE id = :fiche_id
                        """), {"fiche_id": fiche_id})
                        db.commit()

            except ValueError as e:
                if "existe déjà" in str(e):
                    details["erreurs"].append({
                        "employe_id": emp_id,
                        "erreur": str(e)
                    })
                    nb_erreurs += 1
                else:
                    nb_erreurs += 1
                    details["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})
            except Exception as e:
                nb_erreurs += 1
                details["erreurs"].append({"employe_id": emp_id, "erreur": str(e)})

        _logger_execution(
            db=db,
            type_exec=type_exec,
            mois=mois,
            annee=annee,
            nb_generes=nb_generes,
            nb_mails=nb_mails,
            nb_erreurs=nb_erreurs,
            details=details,
            declenche_par="agent_ia" if type_exec == "manuelle" else "test"
        )

        mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

        return {
            "succes": True,
            "periode": f"{mois_noms[mois - 1]} {annee}",
            "nb_generes": nb_generes,
            "nb_mails": nb_mails,
            "nb_erreurs": nb_erreurs,
            "details": details
        }

    except Exception as e:
        traceback.print_exc()
        return {"succes": False, "detail": str(e)}
    
# 8. RAPPELS PROGRAMMÉS

async def verifier_rappels(db: Session):
    """
    Vérifie les rappels en attente et déclenche les notifications/envois auto.
    Appelée toutes les minutes par le scheduler.
    """
    from datetime import timezone
    maintenant = datetime.now(timezone.utc)
    
    try:
        rappels = db.execute(text("""
            SELECT id, type, date_heure, message, action
            FROM rappel_ia
            WHERE statut = 'en_attente'
              AND date_heure <= :maintenant
        """), {"maintenant": maintenant}).fetchall()

        for r in rappels:
            rappel_id = str(r[0])
            type_rappel = r[1]
            message = r[3]
            action = r[4]

            print(f"[RAPPEL] Déclenchement — type={type_rappel} | message={message[:50]}...")

            if type_rappel == 'envoi_auto':
                # Envoi automatique sans confirmation
                try:
                    from app.services.Service_Mail import envoyer_mail_manuel
                    if action:
                        import json as _json
                        act = action if isinstance(action, dict) else _json.loads(action)
                        resultat = await envoyer_mail_manuel(
                            destinataire=act.get("destinataire"),
                            sujet=act.get("sujet"),
                            corps=act.get("corps")
                        )
                        if resultat["succes"]:
                            print(f"[RAPPEL] Mail envoyé automatiquement à {act.get('destinataire')}")
                        else:
                            print(f"[RAPPEL] Échec envoi mail : {resultat['detail']}")
                except Exception as e:
                    print(f"[RAPPEL] Erreur envoi auto : {str(e)}")

            elif type_rappel == 'rappel':
                # Juste une notification — l'utilisateur doit confirmer
                print(f"[RAPPEL] Notification prête pour l'utilisateur : {message[:80]}")

            # Marquer comme déclenché
            db.execute(text("""
                UPDATE rappel_ia
                SET statut = 'declenche'
                WHERE id = :id
            """), {"id": rappel_id})
            db.commit()
            print(f"[RAPPEL] ID {rappel_id} marqué comme déclenché.")

    except Exception as e:
        print(f"[RAPPEL] Erreur vérification : {str(e)}")