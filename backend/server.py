from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Create the main app without a prefix
app = FastAPI(title="Application Synthèse Vocale AI")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define Models
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000, description="Texte à convertir en audio")
    voice: str = Field(default="onyx", description="Voix à utiliser")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Vitesse de lecture")

class TTSHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    voice: str
    speed: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration: Optional[float] = None

class TTSHistoryCreate(BaseModel):
    text: str
    voice: str
    speed: float
    duration: Optional[float] = None


# Routes
@api_router.get("/")
async def root():
    return {"message": "API Synthèse Vocale avec Intelligence AI"}

@api_router.get("/tts/voices")
async def get_voices():
    """Retourne la liste des voix disponibles"""
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy", "description": "Voix neutre et claire"},
            {"id": "echo", "name": "Echo", "description": "Voix masculine douce"},
            {"id": "fable", "name": "Fable", "description": "Voix narrative expressive"},
            {"id": "onyx", "name": "Onyx", "description": "Voix masculine profonde"},
            {"id": "nova", "name": "Nova", "description": "Voix féminine énergique"},
            {"id": "shimmer", "name": "Shimmer", "description": "Voix féminine douce"}
        ],
        "formats": ["mp3"],
        "speed_range": {"min": 0.25, "max": 4.0, "default": 1.0}
    }

@api_router.post("/tts/generate")
async def generate_speech(request: TTSRequest):
    """Génère un audio à partir du texte avec intelligence AI pour comprendre la ponctuation"""
    try:
        logger.info(f"Génération audio: voice={request.voice}, speed={request.speed}, text_length={len(request.text)}")
        
        # Appel à l'API OpenAI TTS
        response = openai_client.audio.speech.create(
            model="tts-1",  # Modèle avec latence réduite
            voice=request.voice,
            input=request.text,
            response_format="mp3",
            speed=request.speed
        )
        
        # Convertir la réponse en bytes
        audio_bytes = response.content
        logger.info(f"Audio généré avec succès: {len(audio_bytes)} bytes")
        
        # Retourner l'audio en streaming
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=synthese_vocale.mp3",
                "Content-Length": str(len(audio_bytes))
            }
        )
        
    except RateLimitError as e:
        logger.error(f"Limite de débit dépassée: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite de requêtes dépassée. Veuillez réessayer plus tard."
        )
    except AuthenticationError as e:
        logger.error(f"Erreur d'authentification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification avec l'API OpenAI"
        )
    except APIConnectionError as e:
        logger.error(f"Erreur de connexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de se connecter à l'API OpenAI"
        )
    except APIError as e:
        logger.error(f"Erreur API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération audio"
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite"
        )

@api_router.post("/tts/history", response_model=TTSHistory)
async def save_history(input: TTSHistoryCreate):
    """Sauvegarde une entrée dans l'historique"""
    history_obj = TTSHistory(**input.model_dump())
    
    doc = history_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.tts_history.insert_one(doc)
    return history_obj

@api_router.get("/tts/history", response_model=List[TTSHistory])
async def get_history():
    """Récupère l'historique des conversions"""
    history_items = await db.tts_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
    
    for item in history_items:
        if isinstance(item['timestamp'], str):
            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
    
    return history_items

@api_router.delete("/tts/history/{history_id}")
async def delete_history_item(history_id: str):
    """Supprime une entrée de l'historique"""
    result = await db.tts_history.delete_one({"id": history_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément d'historique non trouvé"
        )
    
    return {"message": "Élément supprimé avec succès"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TTS API"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()