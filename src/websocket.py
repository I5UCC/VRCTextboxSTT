import asyncio
import websockets
import json
from threading import Thread
import logging

log = logging.getLogger(__name__)

class WebsocketHandler:
    """
    A class that handles WebSocket communication.

    Args:
        port (int): The port number to listen to.
        update_rate (float): The rate at which to update clients or send transcripts.
        is_client (bool, optional): Whether the instance is a client or a server. Defaults to False.
        uri (str, optional): The URI to connect to as a client. Defaults to "ws://localhost:8765".

    Methods:
        _send_transcript(self, websocket) -> None:
        _handle_client_updates(self, websocket, path) -> None:
        _maintain_websocket_connection(self) -> None:
        _start_server(self) -> None:
        _stop_server(self) -> None:
        _start_client(self) -> None:
        _stop_client(self) -> None:
        start(self) -> None:
        stop(self) -> None:
        set_finished(self, finished) -> None:
        set_text(self, transcript) -> None:
        set_update_rate(self, rate) -> None:

    Attributes:
        port (int): The port number to listen to.
        update_rate (float): The rate at which to update clients or send transcripts.
        is_client (bool): Whether the instance is a client or a server.
        uri (str): The URI to connect to as a client.
        loop (asyncio.AbstractEventLoop): The event loop for asynchronous operations.
        server (websockets.WebSocketServer): The WebSocket server instance.
        transcript (str): The current transcript to send.
        finished (bool): Indicates if the transcript is finished.
        running (bool): Indicates if the WebSocket communication is running.
    """
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

    async def _send_transcript(self, websocket) -> None:
        """
        Sends the transcript and finished status to the specified websocket.

        Args:
            websocket: The WebSocket connection to send the transcript to.

        Returns:
            None
        """
        await websocket.send(json.dumps({"transcript": self.transcript, "finished": self.finished if self.transcript else False}))

    async def _handle_client_updates(self, websocket, path) -> None:
        """
        Handles updates for a connected websocket client.
        Can be multiple coroutines running at the same time.

        Args:
            websocket: The WebSocket connection object.
            path: The path of the WebSocket connection.

        Returns:
            None
        """
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

    async def _maintain_websocket_connection(self) -> None:
        """
        Maintains the WebSocket connection for the client.

        Returns:
            None
        """
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

    def _start_server(self) -> None:
        """
        Starts the WebSocket server and runs it indefinitely.
        """
        self.server = websockets.serve(self._handle_client_updates, "127.0.0.1", self.port)
        self.loop.run_until_complete(self.server)
        self.thread = Thread(target=self.loop.run_forever)
        self.thread.start()
        
    def _stop_server(self) -> None:
        """
        Stops the WebSocket server.
        """
        self.server.ws_server.close()
        self.loop.stop()
        self.thread.join()

    def _start_client(self) -> None:
        """
        Starts the WebSocket client in a separate thread.
        """
        self.thread = Thread(target=self.loop.run_until_complete, args=(self._maintain_websocket_connection(),))
        self.thread.start()

    def _stop_client(self) -> None:
        """
        Stops the client by joining the thread.
        """
        self.thread.join()

    def start(self) -> None:
        """
        Starts the WebSocket connection depending on whether the instance is a client or a server.
        """
        self.running = True
        if self.is_client:
            self._start_client()
        else:
            self._start_server()
    
    def stop(self) -> None:
        """
        Stops the WebSocket connection depending on whether the instance is a client or a server.
        """
        self.running = False
        if self.is_client:
            self._stop_client()
        else:
            self._stop_server()

    def set_finished(self, finished) -> None:
        """
        Sets the finished status of the transcript.
        """
        self.finished = finished

    def set_text(self, transcript) -> None:
        """
        Sets the transcript to send.
        """
        self.transcript = transcript
    
    def set_update_rate(self, rate) -> None:
        """
        Sets the update rate.
        """
        self.update_rate = rate
