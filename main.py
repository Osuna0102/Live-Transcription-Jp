from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
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

load_dotenv()
app = FastAPI()
dg_client = Deepgram('498c7b7448f02c656e9b7a4aeb85aed5fc0225e3')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Mount static files
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Set up CORS
origins = [
    "http://localhost:3000",  # Allow localhost for development
    "https://livetranscription.onrender.com",  # Allow your production site
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def index():
    return FileResponse('templates/index.html')

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

@app.post("/transcript")
async def transcript(file: UploadFile = File(...)):
    audio_file = await file.read()

    # API Key
    api_key = '03414a05e387a8776d9b819cb038a8ec6511c49e'

    # Prepare the headers
    headers = {
        'Authorization': 'Token ' + api_key,
        'Content-Type': file.content_type,
    }

    # Prepare the query parameters
    query = {
        'model': 'nova-2',
        'smart_format': 'true',
        'diarize': 'true',
        'language': 'es',
    }

    # Send the request
    response = requests.post('https://api.deepgram.com/v1/listen', params=query, headers=headers, data=audio_file)

    if response.status_code == 200:
        # Decode the JSON response
        data = json.loads(response.text)

        # Start output buffering
        output = []

        # Print the overall confidence
        output.append("Overall Confidence: " + str(data['results']['channels'][0]['alternatives'][0]['confidence'] * 100) + "%\n")

        # Iterate over the channels
        for channel in data['results']['channels']:
            # Iterate over the alternatives
            for alternative in channel['alternatives']:
                # Iterate over the paragraphs
                for paragraph in alternative['paragraphs']['paragraphs']:
                    # Iterate over the sentences
                    for sentence in paragraph['sentences']:
                        # Write the time, speaker, and text to the output buffer
                        output.append("[" + str(sentence['start']) + "] Speaker " + str(paragraph['speaker']) + ": " + sentence['text'] + "\n")

        # Write the output to a file
        with open('transcript.txt', 'w') as f:
            f.writelines(output)

        # Return the file as a download
        return FileResponse('transcript.txt', filename='transcript.txt', media_type='text/plain')

    else:
        return {"error": "Failed to transcribe"}, response.status_code