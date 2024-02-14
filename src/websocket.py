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
        self.is_client = is_client
        self.uri = uri

        self.loop = asyncio.get_event_loop()
        self.server = None

        self.transcript = ""
        self.finished = False
        self.running = False

    async def _send_transcript(self, websocket):
        await websocket.send(json.dumps({"transcript": self.transcript, "finished": self.finished if self.transcript else False}))

    async def _update_clients(self, websocket, path):
        log.info("New Websocket client connected.")
        last_transcript = ""
        last_finished = False
        while self.running:
            try:
                if self.transcript != last_transcript or self.finished and not last_finished:
                    await self._send_transcript(websocket)
                    last_transcript = self.transcript
                    last_finished = self.finished
                await asyncio.sleep(self.update_rate)
            except (websockets.ConnectionClosed, websockets.ConnectionClosedError):
                log.info("Websocket Client disconnected.")
                break
            except Exception as e:
                log.error(f"WebSocket error: {e}.")
                break

    async def _connect_to_websocket(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    log.info("Connected to WebSocket server.")
                    last_transcript = ""
                    last_finished = False
                    while self.running:
                        if self.transcript != last_transcript or self.finished and not last_finished:
                            await self._send_transcript(websocket)
                            last_transcript = self.transcript
                            last_finished = self.finished
                        await asyncio.sleep(self.update_rate)
            except ConnectionRefusedError:
                log.error("Websocket Connection refused. Retrying in 5 seconds.")
            except (websockets.ConnectionClosed, websockets.ConnectionClosedError):
                log.error("WebSocket Connection closed. Retrying in 5 seconds.")
            except websockets.InvalidURI:
                log.error("WebSocket Invalid URI. Retrying in 5 seconds.")
            except Exception as e:
                log.error(f"WebSocket error: {e}. Retrying in 5 seconds.")
            await asyncio.sleep(5)

    def _start_server(self):
        self.server = websockets.serve(self._update_clients, "127.0.0.1", self.port)
        self.loop.run_until_complete(self.server)
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        
    def _stop_server(self):
        self.server.ws_server.close()
        self.loop.stop()
        self.thread.join()

    def _start_client(self):
        self.thread = Thread(target=self.loop.run_until_complete, args=(self._connect_to_websocket(),))
        self.thread.start()

    def _stop_client(self):
        self.thread.join()

    def start(self):
        self.running = True
        if self.is_client:
            self._start_client()
        else:
            self._start_server()
    
    def stop(self):
        self.running = False
        if self.is_client:
            self._stop_client()
        else:
            self._stop_server()

    def set_finished(self, finished):
        self.finished = finished

    def set_text(self, transcript):
        self.transcript = transcript
    
    def set_update_rate(self, rate):
        self.update_rate = rate
