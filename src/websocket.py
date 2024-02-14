import asyncio
import websockets
import json
from threading import Thread
import logging

log = logging.getLogger(__name__)

class WebsocketHandler:
    def __init__(self, port, update_rate, is_client=False, uri="ws://localhost:8765"):
        self.port = port
        self.update_rate = update_rate
        self.transcript = ""
        self.last_transcript = ""
        self.finished = False
        self.running = False
        self.is_client = is_client
        self.clients = set()
        self.server = websockets.serve(self.update_clients, "127.0.0.1", self.port)
        self.uri = uri
        self.loop = asyncio.get_event_loop()

    async def send_transcript(self, websocket):
        if not self.transcript:
            self.finished = False

        await websocket.send(json.dumps({"transcript": self.transcript, "finished": self.finished}))

        if self.finished:
            await asyncio.sleep(0.6)
            self.finished = False
        self.last_transcript = self.transcript

    async def update_clients(self, websocket, path):
        log.info("New Websocket client connected.")
        self.clients.add(websocket)
        while self.running:
            if self.transcript != self.last_transcript or self.finished:
                for client in self.clients:
                    try:
                        await self.send_transcript(client)
                        await asyncio.sleep(self.update_rate)
                    except websockets.ConnectionClosed:
                        log.info("Client disconnected.")
                        self.clients.remove(client)
                        break
                if not self.clients:
                    await asyncio.sleep(2)

    async def connect_to_websocket(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    log.info("Connected to WebSocket server.")
                    while self.running:
                        try:
                            if self.transcript != self.last_transcript or self.finished:
                                await self.send_transcript(websocket)
                            await asyncio.sleep(self.update_rate)
                        except websockets.ConnectionClosed:
                            log.error("WebSocket connection closed. Retrying in 5 seconds.")
                            await asyncio.sleep(5)
                            break
            except ConnectionRefusedError:
                log.error("Websocket Connection refused. Retrying in 5 seconds.")
                await asyncio.sleep(5)

    def start(self):
        self.running = True
        if self.is_client:
            self.start_client()
        else:
            self.start_server()
    
    def stop(self):
        self.running = False
        if self.is_client:
            self.stop_client()
        else:
            self.stop_server()

    def start_server(self):
        self.loop.run_until_complete(self.server)
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        
    def stop_server(self):
        self.server.ws_server.close()
        self.loop.stop()
        self.thread.join()

    def start_client(self):
        self.thread = Thread(target=self.loop.run_until_complete, args=(self.connect_to_websocket(),))
        self.thread.start()

    def stop_client(self):
        self.thread.join()

    def set_finished(self, finished):
        self.finished = finished

    def set_text(self, transcript):
        self.transcript = transcript
    
    def set_update_rate(self, rate):
        self.update_rate = rate
