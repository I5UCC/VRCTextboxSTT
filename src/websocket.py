import asyncio
import websockets
import json
from threading import Thread
import logging

log = logging.getLogger(__name__)

class WebsocketHandler:
    def __init__(self, port, is_client=False, uri="ws://localhost:8765"):
        self.port = port
        self.transcript = ""
        self.last_transcript = ""
        self.finished = False
        self.running = False
        self.is_client = is_client
        self.clients = set()
        self.server = websockets.serve(self.update_clients, "127.0.0.1", self.port)
        self.uri = uri
        self.loop = asyncio.get_event_loop()

    def start(self):
        if self.is_client:
            self.start_client()
        else:
            self.start_server()
        self.running = True
    
    def stop(self):
        if self.is_client:
            self.stop_client()
        else:
            self.stop_server()
        self.running = False

    async def update_clients(self, websocket, path):
        log.info("New Websocket client connected.")
        self.clients.add(websocket)
        while True:
            if self.transcript != self.last_transcript or (self.transcript == self.last_transcript and self.finished):
                for client in self.clients:
                    try:
                        if not self.transcript:
                            self.finished = False
                        
                        await client.send(json.dumps({"transcript": self.transcript, "finished": self.finished}))
                        
                        if self.finished:
                            await asyncio.sleep(1)
                            self.finished = False
                        self.last_transcript = self.transcript
                        await asyncio.sleep(0.3)
                    except Exception:
                        log.info("Client disconnected.")
                        self.clients.remove(client)
                        break

    async def connect_to_websocket(self):
        async with websockets.connect(self.uri) as websocket:
            log.info("Connected to WebSocket server.")
            self.running = True
            while self.running:
                try:
                    if self.transcript != self.last_transcript or (self.transcript == self.last_transcript and self.finished):
                        if not self.transcript:
                            self.finished = False

                        await websocket.send(json.dumps({"transcript": self.transcript, "finished": self.finished}))

                        if self.finished:
                            await asyncio.sleep(1)
                            self.finished = False
                        self.last_transcript = self.transcript
                    await asyncio.sleep(0.3)
                except websockets.ConnectionClosed:
                    log.info("WebSocket connection closed.")
                    self.running = False

    def start_server(self):
        self.loop.run_until_complete(self.server)
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        
    def stop_server(self):
        self.server.ws_server.close()
        self.loop.stop()

    def start_client(self):
        self.thread = Thread(target=self.loop.run_until_complete, args=(self.connect_to_websocket(),))
        self.thread.start()

    def stop_client(self):
        self.thread.join()

    def set_finished(self, finished):
        self.finished = finished

    def set_text(self, transcript):
        self.transcript = transcript
