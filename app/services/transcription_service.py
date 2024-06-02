from fastapi import WebSocket, UploadFile, File, Form, FastAPI
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
from ..settings import dg_client_key

dg_client = Deepgram(dg_client_key)

load_dotenv()
app = FastAPI()
dg_client = Deepgram('498c7b7448f02c656e9b7a4aeb85aed5fc0225e3')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

async def websocket_endpoint(websocket: WebSocket, language: str = 'ja'):
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
        socket = await dg_client.transcription.live({'punctuate': True, 'diarize': True, 'filler_words': True, 'smart_format': True, 'interim_results': False, 'language': language})  # Set the language dynamically
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, get_transcript)
        while True:
            data = await websocket.receive_bytes()
            socket.send(data)
    except Exception as e:
        print(f"Error connecting to Deepgram: {e}")


async def transcript(file: UploadFile = File(...), language: str = Form(...)):
    audio_file = await file.read()
    print(f"Language: {language}")

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
        'language': language,
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
                # Check if 'paragraphs' key exists in the dictionary
                if 'paragraphs' in alternative:
                    # Iterate over the paragraphs
                    for paragraph in alternative['paragraphs']['paragraphs']:
                        # Iterate over the sentences
                        for sentence in paragraph['sentences']:
                            # Write the time, speaker, and text to the output buffer
                            output.append("[" + str(sentence['start']) + "] Speaker " + str(paragraph['speaker']) + ": " + sentence['text'] + "\n")
                else:
                    # Return the entire response from the Deepgram API
                    return data

        # Write the output to a file
        with open('transcript.txt', 'w', encoding='utf-8') as f:
            f.writelines(output)

        # Return the file as a download
        return FileResponse('transcript.txt', filename='transcript.txt', media_type='text/plain')

    else:
        return {"error": "Failed to transcribe"}, response.status_code
    

