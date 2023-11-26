import asyncio
import websockets
from threading import Thread

class WebsocketHandler:
    def __init__(self, port):
        self.port = port
        self.transcript = ""
        self.last_transcript = ""
        self.running = False
        self.clients = set()
        self.server = websockets.serve(self.update_clients, "127.0.0.1", self.port)
        self.loop = asyncio.get_event_loop()

    def start(self):
        self.loop.run_until_complete(self.server)
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        self.running = True

    def stop(self):
        self.server.ws_server.close()
        self.loop.stop()
        self.running = False

    async def update_clients(self, websocket, path):
        print("New Websocket client connected.")
        self.clients.add(websocket)
        while True:
            if self.transcript != self.last_transcript:
                for client in self.clients:
                    try:
                        await client.send(self.transcript)
                    except Exception:
                        print("Client disconnected.")
                        self.clients.remove(client)
                        break
                self.last_transcript = self.transcript
            await asyncio.sleep(0.5)

    def set_text(self, transcript):
        self.transcript = transcript

if __name__ == "__main__":
    import random
    import time
    webs = WebsocketHandler(8765)
    webs.start()

    for i in range(10):
        webs.set_text("This is a test transcript." + str(random.randint(0, 10000)))
        time.sleep(0.5)
    
    webs.stop()