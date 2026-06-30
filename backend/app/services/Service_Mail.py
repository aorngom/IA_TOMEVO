import os
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional
import traceback


# ============================================================
# 1. CONFIGURATION SMTP
# ============================================================

def get_smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from": os.getenv("SMTP_FROM", "Jariniou Paie <noreply@jariniou.com>")
    }


# ============================================================
# 2. ENVOI MAIL GÉNÉRIQUE
# ============================================================

async def envoyer_mail(
    destinataire: str,
    sujet: str,
    corps_html: str,
    corps_texte: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    pdf_nom: Optional[str] = None
) -> dict:
    """
    Envoie un mail avec optionnellement un PDF en pièce jointe.
    Retourne {"succes": True/False, "detail": "..."}
    """
    smtp = get_smtp_config()

    if not smtp["user"] or not smtp["password"]:
        return {
            "succes": False,
            "detail": "Configuration SMTP manquante dans le fichier .env"
        }

    try:
        # Construction du message
        msg = MIMEMultipart("mixed")
        msg["From"] = smtp["from"]
        msg["To"] = destinataire
        msg["Subject"] = sujet

        # Corps du mail (HTML + fallback texte)
        corps = MIMEMultipart("alternative")
        if corps_texte:
            corps.attach(MIMEText(corps_texte, "plain", "utf-8"))
        corps.attach(MIMEText(corps_html, "html", "utf-8"))
        msg.attach(corps)

        # Pièce jointe PDF
        if pdf_bytes and pdf_nom:
            attachment = MIMEBase("application", "pdf")
            attachment.set_payload(pdf_bytes)
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f'attachment; filename="{pdf_nom}"'
            )
            msg.attach(attachment)

        # Envoi SMTP
        await aiosmtplib.send(
            msg,
            hostname=smtp["host"],
            port=465,
            username=smtp["user"],
            password=smtp["password"],
            use_tls=True
        )

        return {"succes": True, "detail": f"Mail envoyé à {destinataire}"}

    except Exception as e:
        traceback.print_exc()
        return {"succes": False, "detail": f"Erreur SMTP : {str(e)}"}


# ============================================================
# 3. TEMPLATE BULLETIN DE PAIE (HTML)
# ============================================================

def generer_html_bulletin(calcul: dict) -> str:
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    periode = f"{mois_noms[calcul['periode_mois'] - 1]} {calcul['periode_annee']}"
    devise = calcul.get("devise", "FCFA")

    def fmt(val):
        return f"{float(val or 0):,.0f}".replace(",", " ")

    # Construire les lignes gains
    lignes_gains = f"""
        <tr><td>Salaire de base</td>
            <td class="montant gain">{fmt(calcul['salaire_base'])} {devise}</td></tr>
    """
    if calcul.get("prime_transport", 0) > 0:
        lignes_gains += f"""
        <tr><td>Prime de transport</td>
            <td class="montant gain">{fmt(calcul['prime_transport'])} {devise}</td></tr>
        """
    if calcul.get("prime_logement", 0) > 0:
        lignes_gains += f"""
        <tr><td>Prime de logement</td>
            <td class="montant gain">{fmt(calcul['prime_logement'])} {devise}</td></tr>
        """
    if calcul.get("prime_autres", 0) > 0:
        lignes_gains += f"""
        <tr><td>Autres primes</td>
            <td class="montant gain">{fmt(calcul['prime_autres'])} {devise}</td></tr>
        """
    if calcul.get("retenue_absence", 0) > 0:
        lignes_gains += f"""
        <tr><td>Retenue absences ({calcul.get('jours_absence', 0)} jour(s))</td>
            <td class="montant retenue">-{fmt(calcul['retenue_absence'])} {devise}</td></tr>
        """

    # Construire les lignes retenues
    lignes_retenues = ""
    if calcul.get("ipres_salariale", 0) > 0:
        lignes_retenues += f"""
        <tr><td>IPRES part salariale</td>
            <td class="montant retenue">-{fmt(calcul['ipres_salariale'])} {devise}</td></tr>
        """
    if calcul.get("ir", 0) > 0:
        lignes_retenues += f"""
        <tr><td>Impôt sur le Revenu</td>
            <td class="montant retenue">-{fmt(calcul['ir'])} {devise}</td></tr>
        """

    # Construire les cotisations patronales
    lignes_patronales = ""
    if calcul.get("ipres_patronale", 0) > 0:
        lignes_patronales += f"""
        <tr><td>IPRES part patronale</td>
            <td class="montant" style="color:#27ae60">{fmt(calcul['ipres_patronale'])} {devise}</td></tr>
        """
    if calcul.get("css_pf", 0) > 0:
        lignes_patronales += f"""
        <tr><td>CSS Prestations familiales</td>
            <td class="montant" style="color:#27ae60">{fmt(calcul['css_pf'])} {devise}</td></tr>
        """
    if calcul.get("css_at", 0) > 0:
        lignes_patronales += f"""
        <tr><td>CSS Accidents du travail</td>
            <td class="montant" style="color:#27ae60">{fmt(calcul['css_at'])} {devise}</td></tr>
        """
    if calcul.get("cfe", 0) > 0:
        lignes_patronales += f"""
        <tr><td>Contribution forfaitaire</td>
            <td class="montant" style="color:#27ae60">{fmt(calcul['cfe'])} {devise}</td></tr>
        """

    entete_patronal = ""
    if lignes_patronales:
        entete_patronal = """
        <tr><td colspan="2" style="background:#f0fff4; font-weight:bold;
            font-size:11px; color:#27ae60; padding:6px 12px;">
            COTISATIONS PATRONALES (informatives)
        </td></tr>
        """

    # Note de changement
    note_html = ""
    if calcul.get("note_changement"):
        note_html = f"""
        <div style="margin-top:20px; padding:12px; background:#fff8e1;
                    border-left:4px solid #f59e0b; border-radius:4px; font-size:12px;">
            <strong>Note :</strong> {calcul['note_changement']}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 13px;
                color: #1a1a1a; margin: 0; padding: 20px; }}
        .header {{ background: #1a5276; color: white;
                   padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 20px; }}
        .header p {{ margin: 4px 0 0; font-size: 12px; opacity: 0.85; }}
        .infos {{ display: flex; gap: 20px; padding: 16px;
                  background: #f8f9fa; border: 1px solid #dee2e6; }}
        .infos-bloc {{ flex: 1; }}
        .infos-bloc h3 {{ margin: 0 0 8px; font-size: 11px;
                          text-transform: uppercase; color: #6c757d; }}
        .infos-bloc p {{ margin: 2px 0; font-size: 13px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th {{ background: #1a5276; color: white; padding: 8px 12px;
              text-align: left; font-size: 12px; }}
        td {{ padding: 7px 12px; border-bottom: 1px solid #f0f0f0; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .montant {{ text-align: right; font-weight: bold; }}
        .retenue {{ color: #c0392b; }}
        .gain {{ color: #1a5276; }}
        .total-row {{ background: #1a5276 !important; color: white; font-weight: bold; }}
        .total-row td {{ padding: 10px 12px; }}
        .net-row {{ background: #27ae60 !important; color: white;
                    font-weight: bold; font-size: 15px; }}
        .net-row td {{ padding: 12px; }}
        .footer {{ margin-top: 20px; font-size: 11px; color: #6c757d;
                   text-align: center; padding-top: 12px;
                   border-top: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Bulletin de Paie</h1>
        <p>Période : {periode} &nbsp;|&nbsp; Généré le {datetime.now().strftime('%d/%m/%Y')}</p>
    </div>

    <div class="infos">
        <div class="infos-bloc">
            <h3>Employé</h3>
            <p><strong>{calcul['prenom']} {calcul['nom']}</strong></p>
            <p>Matricule : {calcul['matricule']}</p>
            <p>Poste : {calcul.get('poste', '—')}</p>
            <p>Département : {calcul.get('departement', '—')}</p>
        </div>
        <div class="infos-bloc">
            <h3>Contrat</h3>
            <p>Type : {calcul.get('type_contrat', '—')}</p>
            <p>Pays : {calcul.get('pays', '—')}</p>
        </div>
        <div class="infos-bloc">
            <h3>Période</h3>
            <p><strong>{periode}</strong></p>
            <p>Devise : {devise}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Libellé</th>
                <th style="text-align:right">Montant ({devise})</th>
            </tr>
        </thead>
        <tbody>
            <tr><td colspan="2" style="background:#eaf4fb; font-weight:bold;
                font-size:11px; color:#1a5276; padding:6px 12px;">
                ÉLÉMENTS DE RÉMUNÉRATION
            </td></tr>
            {lignes_gains}
            <tr class="total-row">
                <td>Salaire Brut</td>
                <td class="montant">{fmt(calcul['salaire_brut'])} {devise}</td>
            </tr>
            <tr><td colspan="2" style="background:#fdf2f2; font-weight:bold;
                font-size:11px; color:#c0392b; padding:6px 12px;">
                RETENUES SALARIALES
            </td></tr>
            {lignes_retenues}
            {entete_patronal}
            {lignes_patronales}
        </tbody>
    </table>

    <table style="margin-top:8px;">
        <tbody>
            <tr class="net-row">
                <td>NET À PAYER</td>
                <td class="montant" style="text-align:right; font-size:18px;">
                    {fmt(calcul['salaire_net'])} {devise}
                </td>
            </tr>
        </tbody>
    </table>

    {note_html}

    <div class="footer">
        Ce bulletin de paie est confidentiel. Conservez-le soigneusement.<br>
        Généré automatiquement par le système Jariniou.
    </div>
</body>
</html>"""


# ============================================================
# 4. ENVOI BULLETIN À UN EMPLOYÉ
# ============================================================

async def envoyer_bulletin_employe(calcul: dict) -> dict:
    """
    Génère le HTML du bulletin et l'envoie par mail à l'employé.
    """
    email = calcul.get("email_perso")
    if not email:
        return {
            "succes": False,
            "detail": f"Pas d'email pour {calcul['prenom']} {calcul['nom']}"
        }

    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    periode = f"{mois_noms[calcul['periode_mois'] - 1]} {calcul['periode_annee']}"
    devise = calcul.get("devise", "FCFA")

    sujet = f"Votre bulletin de paie — {periode}"

    corps_html = generer_html_bulletin(calcul)

    corps_texte = (
        f"Bonjour {calcul['prenom']} {calcul['nom']},\n\n"
        f"Veuillez trouver ci-joint votre bulletin de paie pour {periode}.\n\n"
        f"Salaire brut  : {calcul['salaire_brut']:,.0f} {devise}\n"
        f"Net à payer   : {calcul['salaire_net']:,.0f} {devise}\n\n"
    )

    if calcul.get("note_changement"):
        corps_texte += f"Note : {calcul['note_changement']}\n\n"

    corps_texte += (
        "Ce bulletin est confidentiel. Conservez-le soigneusement.\n\n"
        "Cordialement,\nLe service RH — Jariniou"
    )

    # Tentative génération PDF (optionnel, selon weasyprint installé)
    pdf_bytes = None
    pdf_nom = None
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=corps_html).write_pdf()
        pdf_nom = f"bulletin_{calcul['matricule']}_{calcul['periode_mois']:02d}{calcul['periode_annee']}.pdf"
    except Exception:
        # Si weasyprint échoue, on envoie juste le HTML sans PDF joint
        pass

    return await envoyer_mail(
        destinataire=email,
        sujet=sujet,
        corps_html=corps_html,
        corps_texte=corps_texte,
        pdf_bytes=pdf_bytes,
        pdf_nom=pdf_nom
    )


# ============================================================
# 5. MAIL MANUEL (rédigé par l'IA, confirmé par l'humain)
# ============================================================

async def envoyer_mail_manuel(
    destinataire: str,
    sujet: str,
    corps: str
) -> dict:
    """
    Envoie un mail manuel rédigé par l'agent IA après confirmation humaine.
    """
    corps_html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; font-size:14px;
                 color:#1a1a1a; padding:24px; max-width:600px; margin:auto;">
        <div style="border-top: 4px solid #1a5276; padding-top: 20px;">
            {corps.replace(chr(10), '<br>')}
        </div>
        <div style="margin-top:32px; padding-top:16px; border-top:1px solid #dee2e6;
                    font-size:12px; color:#6c757d;">
            Ce message a été envoyé via le système Jariniou.
        </div>
    </body>
    </html>
    """
    return await envoyer_mail(
        destinataire=destinataire,
        sujet=sujet,
        corps_html=corps_html,
        corps_texte=corps
    )


# ============================================================
# 6. ENVOI MASSE (tous les employés d'un mois)
# ============================================================

async def envoyer_bulletins_masse(calculs: list[dict]) -> dict:
    """
    Envoie les bulletins à tous les employés d'une liste de calculs.
    """
    resultats = {"envoyes": [], "echecs": []}

    for calcul in calculs:
        resultat = await envoyer_bulletin_employe(calcul)
        if resultat["succes"]:
            resultats["envoyes"].append({
                "employe": f"{calcul['prenom']} {calcul['nom']}",
                "email": calcul.get("email_perso")
            })
        else:
            resultats["echecs"].append({
                "employe": f"{calcul['prenom']} {calcul['nom']}",
                "raison": resultat["detail"]
            })

    return {
        "nb_envoyes": len(resultats["envoyes"]),
        "nb_echecs": len(resultats["echecs"]),
        "detail": resultats
    }