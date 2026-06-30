Fichiers importants — Partie RH (Gestion des Employés)

Route_Ocr.py
C'est la porte d'entrée de l'assistant RH. Quand un responsable discute avec l'IA pour créer un employé, modifier ses informations, organiser une réunion ou analyser un document scanné, c'est ce fichier qui reçoit le message et déclenche les bonnes actions. Les fonctions qui interviennent sont chat_document et analyser_document.


Service_Employe.py
Ce fichier contient toutes les actions possibles sur un employé : le créer, le modifier, le supprimer ou le désactiver. Il est appelé aussi bien par l'assistant IA que par les formulaires classiques de l'interface. Les fonctions qui interviennent sont obtenir_tous_employes, obtenir_employe_par_id, creer_employe, modifier_employe et supprimer_employe.


Service_Ocr.py
Ce fichier analyse les documents uploadés (image ou PDF d'une fiche employé) et prépare les données extraites pour pré-remplir le formulaire de création. C'est lui qui fait le lien entre ce que l'IA lit dans le document et ce que le formulaire attend. La fonction qui intervient est preparer_donnees_formulaire.


Service_Reunion.py
Ce fichier gère la création des réunions. Quand l'IA comprend qu'un utilisateur veut organiser une réunion, elle appelle ce fichier pour l'enregistrer en base de données avec les participants, la date et le lieu. La fonction qui intervient est creer_reunion.


Service_ConversationIA.py
Ce fichier sauvegarde l'historique des conversations avec l'assistant RH. Chaque échange entre l'utilisateur et l'IA est enregistré pour garder une trace des actions effectuées. La fonction qui intervient est sauvegarder_messages.


Schema_Employe.py
Ce fichier définit exactement quelles informations sont attendues pour créer ou modifier un employé. Il protège la base de données en s'assurant que les données reçues sont complètes et au bon format. Les fonctions qui interviennent sont EmployeCreation, EmployeModification et EmployeReponse.


Schema_Reunion.py
Ce fichier définit les informations attendues pour créer une réunion : sujet, date, lieu, participants. Les fonctions qui interviennent sont ReunionCreation et ReunionReponse.


Page_GestionEmployes.jsx
C'est la page principale de gestion des employés dans l'interface. Elle affiche la liste des employés, permet de rechercher, filtrer par département, voir le détail d'un employé et ouvrir l'assistant IA RH. Les fonctions qui interviennent sont Page_GestionEmployes et AgentGRHPanel.


Page_OCR.jsx (ou page Traitement)
C'est la page qui permet d'uploader un document RH (fiche employé scannée) pour que l'IA l'analyse et propose de créer l'employé automatiquement avec les informations extraites. Les fonctions qui interviennent sont Page_Ocr et handleUpload.











Fichiers importants — Partie Paie

Route_PaieIA.py
C'est la porte d'entrée de l'assistant paie. Quand un utilisateur pose une question sur la paie dans l'interface, c'est ce fichier qui reçoit le message, comprend ce que l'utilisateur veut faire et déclenche les bonnes actions (calculer un salaire, générer une fiche, envoyer un mail, programmer la paie). Les fonctions qui interviennent sont chat_paie, get_notifications et marquer_notification_lue.


Route_FichesPaie.py
Ce fichier gère la création et la consultation des fiches de paie depuis le formulaire manuel, sans passer par l'IA. Quand un responsable clique sur "Générer une fiche", c'est ce fichier qui est appelé. Les fonctions qui interviennent sont liste_fiches, detail_fiche, fiches_par_employe, creer et supprimer.


Service_PaieIA.py
C'est le moteur de calcul des salaires. Il lit les règles de cotisations et d'impôts depuis la base de données — si les règles changent ou si l'entreprise change de pays, on met à jour la base de données et le calcul s'adapte automatiquement sans toucher au code. Il calcule le salaire brut, les cotisations IPRES, l'impôt sur le revenu et le salaire net. Les fonctions qui interviennent sont get_config_pays, calculer_salaire_complet, calculer_salaire_generique, sauvegarder_fiche_calculee, lancer_paie_masse, analyser_fiches_mois, detecter_irregularites, statistiques_masse_salariale et comparer_mois.


Service_Mail.py
Ce fichier s'occupe de tout ce qui est envoi d'emails. Il génère le bulletin de paie en format HTML et l'envoie à l'employé par mail. L'IA peut aussi s'en servir pour envoyer des mails rédigés à la demande. Les fonctions qui interviennent sont envoyer_mail, generer_html_bulletin, envoyer_bulletin_employe, envoyer_mail_manuel et envoyer_bulletins_masse.


Service_Scheduler.py
Ce fichier programme le déclenchement automatique de la paie chaque mois à une date et heure configurables. Il peut aussi gérer des rappels : l'utilisateur peut demander à l'IA de lui envoyer une notification ou un mail automatique à une heure précise. Les fonctions qui interviennent sont demarrer_scheduler, arreter_scheduler, tache_paie_automatique, declencher_maintenant, reconfigurer_planning et verifier_rappels.


Schema_FichePaie.py
Ce fichier définit les informations attendues quand on crée une fiche de paie. Il garantit que le formulaire n'envoie jamais de salaire calculé à la main — seuls l'employé, le mois et l'année sont fournis, le reste est calculé automatiquement. Les fonctions qui interviennent sont FichePaieCreation et FichePaieReponse.


Page_ListeFichesPaie.jsx
C'est la page principale des fiches de paie dans l'interface. Elle affiche la liste des fiches, les statistiques de masse salariale, les filtres de recherche, le formulaire de génération manuelle et le bouton pour ouvrir l'assistant IA paie. Elle gère aussi l'affichage des notifications en temps réel. Les fonctions qui interviennent sont AgentPaiePanel, BoutonAgentPaie, Form_AjoutFiche et Page_ListeFichesPaie.


Service_PaieIA.js
Ce fichier fait le lien entre l'interface utilisateur et le backend pour tout ce qui concerne l'assistant paie. Il envoie les messages de l'utilisateur, convertit les fichiers uploadés en base64 et récupère les notifications. Les fonctions qui interviennent sont chat, fichierVersBase64, getNotifications et marquerLue.