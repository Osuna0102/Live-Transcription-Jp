from flask import Flask, render_template
from deepgram import Deepgram
import os
import asyncio
from aiohttp import web, WSMsgType
from aiohttp_wsgi import WSGIHandler
import json
from firebase_admin import credentials, firestore, initialize_app
from datetime import date

app = Flask('aioflask')
dg_client = Deepgram('498c7b7448f02c656e9b7a4aeb85aed5fc0225e3')
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

@app.route('/')
def index():
    return render_template('index.html')

async def socket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    today = date.today().strftime("%Y-%m-%d")
    transcription_doc_ref = db.collection("transcriptions").document(today)
    data_collection_ref = db.collection("Data").document(today)
    transcription_doc = transcription_doc_ref.get()
    if not transcription_doc.exists:
        transcription_doc_ref.set({'transcriptions': []})
        transcription_doc = transcription_doc_ref.get()

    async def get_transcript(data):
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
            if transcript:
                await ws.send_str(transcript)
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
        socket = await dg_client.transcription.live({'punctuate': True, 'diarize': True, 'filler_words': True, 'smart_format': True, 'interim_results': False, 'language': 'en'})
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, get_transcript)
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == WSMsgType.ERROR:
                print(f'WebSocket Error: {ws.exception()}')
    except Exception as e:
        print(f"Error connecting to Deepgram: {e}")

if __name__ == "__main__" or os.environ.get("APP_ENV") == "heroku":
    aio_app = web.Application()
    wsgi = WSGIHandler(app)
    aio_app.router.add_route('*', '/{path_info: *}', wsgi.handle_request)
    aio_app.router.add_route('GET', '/transcribe', socket)
    web.run_app(aio_app, port=int(os.environ.get("PORT", 5000)))
