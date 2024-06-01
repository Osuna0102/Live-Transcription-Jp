from fastapi import FastAPI, Request, WebSocket, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from deepgram import Deepgram
from dotenv import load_dotenv
import os
import asyncio
import json
from typing import Dict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date
import requests
from app.routes import router
from app.settings import dg_client_key 


load_dotenv()
app = FastAPI()
dg_client = Deepgram(dg_client_key)


# Mount static files
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Set up CORS
origins = [
    "http://localhost:3000",  # Allow localhost for development
    "https://livetranscription.onrender.com",  # Allow your production site
    "http://livetranscription.onrender.com",  # Allow your production site over HTTP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)  # Include the router

@app.get("/")
async def index():
    return FileResponse('templates/index.html')