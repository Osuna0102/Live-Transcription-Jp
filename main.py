from flask import Flask, render_template
from deepgram import Deepgram
from dotenv import load_dotenv
import os
import asyncio
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
import json
from typing import Dict, Callable


load_dotenv()

app = Flask('aioflask')

dg_client = Deepgram('498c7b7448f02c656e9b7a4aeb85aed5fc0225e3')

async def process_audio(fast_socket: web.WebSocketResponse):
    async def get_transcript(data: Dict) -> None:
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']

        
            if transcript:
                await fast_socket.send_str(transcript)
            
            #data recieved on a variable
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8').decode('utf-8')
            #print(json_data)

            if 'alternatives' in data['channel'] and data['channel']['alternatives']:
                confidence = data['channel']['alternatives'][0]['confidence']
                if 'words' in data['channel']['alternatives'][0] and data['channel']['alternatives'][0]['words']:
                    start = data['channel']['alternatives'][0]['words'][0]['start']
                    end = data['channel']['alternatives'][0]['words'][0]['end']
                    # Print values
                    print(f"Confidence: {confidence}")
                    print(f"Start: {start}")
                    print(f"End: {end}")
                else:
                    print("")
            else:
                print("No alternatives found in the JSON data.")

    deepgram_socket = await connect_to_deepgram(get_transcript)

    return deepgram_socket

async def connect_to_deepgram(transcript_received_handler: Callable[[Dict], None]) -> str:
    try:
        socket = await dg_client.transcription.live({'punctuate': True,'diarize': True,'filler_words': True, 'smart_format': True, 'interim_results': False, 'language': 'ja'})
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)

        return socket
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')

@app.route('/')
def index():
    return render_template('index.html')

async def socket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request) 

    deepgram_socket = await process_audio(ws)

    while True:
        data = await ws.receive_bytes()
        deepgram_socket.send(data)

  

if __name__ == "__main__":
       aio_app = web.Application()
       wsgi = WSGIHandler(app)
       aio_app.router.add_route('*', '/{path_info: *}', wsgi.handle_request)
       aio_app.router.add_route('GET', '/listen', socket)
       asyncio.run(web.run_app(aio_app, port=5555))