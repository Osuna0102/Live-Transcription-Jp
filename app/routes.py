from fastapi import APIRouter, FastAPI, Request, WebSocket, HTTPException, UploadFile, File, Form
from .services.transcription_service import websocket_endpoint, transcript
from .services.users_service import create_user, User

router = APIRouter()

@router.post("/users/")
async def create_user_endpoint(user: User):
    return create_user(user)

@router.websocket("/listen")
async def listen_route(websocket: WebSocket, language: str = 'ja'):
    await websocket_endpoint(websocket, language)

@router.post("/transcript")
async def transcript_route(file: UploadFile = File(...), language: str = Form(...)):
    return await transcript(file, language)