from fastapi import FastAPI, WebSocket
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

load_dotenv()
app = FastAPI()
dg_client = Deepgram('498c7b7448f02c656e9b7a4aeb85aed5fc0225e3')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.get("/")
def index():
    return {"message": "Hello, World!"}

@app.websocket("/listen")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    today = date.today().strftime("%Y-%m-%d")
    transcription_doc_ref = db.collection("transcriptions").document(today)
    data_collection_ref = db.collection("Data").document(today)
    transcription_doc = transcription_doc_ref.get()
    if not transcription_doc.exists:
        transcription_doc_ref.set({'transcriptions': []})
        transcription_doc = transcription_doc_ref.get()

    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
            if transcript:
                await websocket.send_text(transcript)
                if 'alternatives' in data['channel'] and data['channel']['alternatives']:
                    confidence = data['channel']['alternatives'][0]['confidence']
                    if 'words' in data['channel']['alternatives'][0] and data['channel']['alternatives'][0]['words']:
                        start = data['channel']['alternatives'][0]['words'][0]['start']
                        end = data['channel']['alternatives'][0]['words'][0]['end']
                        transcription_doc_data = transcription_doc.to_dict().get('transcriptions', [])
                        transcription_doc_data.append(transcript)
                        transcription_doc_ref.update({'transcriptions': firestore.ArrayUnion([transcript])})
                        if not data_collection_ref.get().exists:
                            data_collection_ref.set({
                                'start': [start],
                                'end': [end],
                                'confidence': [confidence],
                            })
                        else:
                            data_collection_ref.update({
                                'start': firestore.ArrayUnion([start]),
                                'end': firestore.ArrayUnion([end]),
                                'confidence': firestore.ArrayUnion([confidence]),
                            })
                        print("Session:", today)
                        print("Transcription:", transcript)
                        print("Start:", start)
                        print("End:", end)
                        print("Confidence:", confidence)
                        print("-----------------------------")
                    else:
                        print("")
                else:
                    print("No alternatives found in the JSON data.")
    try:
        socket = await dg_client.transcription.live({'punctuate': True, 'diarize': True, 'filler_words': True, 'smart_format': True, 'interim_results': False, 'language': 'ja'})  # Set the default language to English
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, get_transcript)
        while True:
            data = await websocket.receive_bytes()
            socket.send(data)
    except Exception as e:
        print(f"Error connecting to Deepgram: {e}")
