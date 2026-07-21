"""
main.py
-------

API FastAPI LegalAI

Expose le moteur RAG pour une interface web.

Endpoint :

POST /chat
Input:  {"question": "Mon employeur peut-il me licencier ?"}
Output: {"answer": "..."}
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter dossier parent
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Import du moteur RAG
try:
    from models.rag import ask_legal_ai
    logger.info("✅ RAG importé avec succès")
except ImportError as e:
    logger.error(f"❌ Erreur d'import RAG : {e}")
    # Fallback si le chemin est différent
    try:
        from rag import ask_legal_ai
        logger.info("✅ RAG importé depuis le dossier courant")
    except ImportError:
        logger.error("❌ Impossible d'importer le RAG")
        sys.exit(1)

# ==============================
# APPLICATION
# ==============================

app = FastAPI(
    title="LegalAI API",
    description="Chatbot juridique droit du travail malgache",
    version="1.0"
)

# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# MODELE REQUETE
# ==============================

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    status: str = "success"

# ==============================
# ROUTES
# ==============================

@app.get("/")
def home():
    return {
        "message": "LegalAI API fonctionne",
        "endpoints": {
            "POST /chat": "Poser une question juridique",
            "GET /health": "Vérifier l'état du service"
        }
    }

@app.get("/health")
def health_check():
    """Vérifie que le RAG est bien chargé."""
    try:
        # Test rapide avec une question vide pour vérifier que tout fonctionne
        test_result = ask_legal_ai("test")
        return {
            "status": "healthy",
            "rag_loaded": True,
            "groq_available": True
        }
    except Exception as e:
        logger.error(f"❌ Health check échoué : {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/chat", response_model=QuestionResponse)
def chat(request: QuestionRequest):
    """
    Endpoint principal pour poser une question juridique.
    
    Args:
        request: QuestionRequest avec le champ 'question'
    
    Returns:
        QuestionResponse: La question et la réponse générée
    """
    if not request.question or request.question.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="La question ne peut pas être vide"
        )
    
    logger.info(f"📝 Question reçue : {request.question}")
    
    try:
        answer = ask_legal_ai(request.question)
        logger.info(f"✅ Réponse générée avec succès ({len(answer)} caractères)")
        
        return QuestionResponse(
            question=request.question,
            answer=answer
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur : {str(e)}"
        )

# ==============================
# GESTIONNAIRE D'ERREURS GLOBAL
# ==============================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP Exception : {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Exception non gérée : {exc}")
    return {
        "error": "Une erreur inattendue s'est produite",
        "status_code": 500
    }

# ==============================
# LANCEMENT EN MODE DEV
# ==============================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("🚀 LegalAI API - Démarrage")
    print("="*50)
    print(f"📂 Dossier racine : {ROOT_DIR}")
    print(f"🌐 Serveur : http://localhost:8000")
    print(f"📖 Documentation : http://localhost:8000/docs")
    print("="*50 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )