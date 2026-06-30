import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv  

# 1. Chargement de la configuration
load_dotenv()

# 2. Import des routes 
from app.routes.Route_Auth import router as auth_router
from app.routes.Route_Employes import router as employes_router
from app.routes.Route_FichesPaie import router as paie_router
from app.routes.Route_Ocr import router as ocr_router
# Nouveaux imports
from app.routes.Route_ConversationIA import router as conversation_router
from app.routes.Route_Reunion import router as reunion_router
from app.routes.Route_PaieIA import router as paie_ia_router
from app.services.Service_Scheduler import demarrer_scheduler, arreter_scheduler
app = FastAPI(title="Poulet App API", version="1.0.0")

# 3. Configuration du Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Inclusion des routeurs
app.include_router(auth_router, prefix="/auth", tags=["Authentification"])
app.include_router(employes_router, prefix="/employes", tags=["Employés"])
app.include_router(paie_router, prefix="/paie", tags=["Fiches de Paie"])
app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
app.include_router(conversation_router, prefix="/conversations-ia", tags=["Historique IA"])
app.include_router(reunion_router, prefix="/reunions", tags=["Réunions"])
app.include_router(paie_ia_router, prefix="/paie-ia")


@app.on_event("startup")
async def startup_event():
    if os.getenv("GROQ_API_KEY"):
        print("Configuration : Clé détectée.")
    else:
        print("Attention : Clé API manquante dans le fichier .env")
    demarrer_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    arreter_scheduler()

@app.get("/")
def racine():
    return {"message": "API Poulet App opérationnelle"}