import speech_recognition as sr
import numpy as np
from queue import Queue
from config import listener_config
import traceback
import logging

log = logging.getLogger(__name__)

class ListenHandler(object):
    def __init__(self, config: listener_config) -> None:
        self.config: listener_config = config
        self.rec = sr.Recognizer()
        self.source = sr.Microphone(sample_rate=16000)
        self.data_queue = Queue()
        self.set_config(config)

    def set_config(self, config: listener_config):
        self.config = config

        self.rec.dynamic_energy_threshold = bool(self.config.dynamic_energy_threshold)
        self.rec.energy_threshold = self.config.energy_threshold
        self.rec.pause_threshold = self.config.pause_threshold
        self.source.device_index = int(self.config.microphone_index) if self.config.microphone_index else None

    def listen_once(self) -> np.ndarray:
        """
        Listens once and returns the audio data as a np array.
        """

        with self.source:
            try:
                _audio = self.rec.listen(self.source, timeout=self.config.timeout_time)
            except sr.WaitTimeoutError:
                return None
            except Exception:
                log.error("Error listening: ")
                log.error(traceback.format_exc())
                return None

            return _audio.get_raw_data()
        
    def start_listen_background(self) -> None:
        """
        Listens in the background and puts the audio data into a queue.
        """
        def record_callback(_, audio:sr.AudioData) -> None:
            try:
                _data = audio.get_raw_data()
                self.data_queue.put(_data)
            except Exception:
                log.error("Error in record callback data: ")
                log.error(traceback.format_exc())

        try:
            self.stop_listening = self.rec.listen_in_background(self.source, record_callback, phrase_time_limit=self.config.phrase_time_limit)
        except Exception:
            log.error("Error starting background listener: ")
            log.error(traceback.format_exc())

    def stop_listen_background(self) -> None:
        try:
            self.stop_listening()
        except Exception:
            log.error("Error stopping listening: ")
            log.error(traceback.format_exc())
        try:
            self.clear_queue()
        except Exception:
            log.error("Error clearing queue: ")
            log.error(traceback.format_exc())

    def raw_to_np(self, raw_data:bytes) -> np.ndarray:
        """Convert raw audio from signed 16-bit integer to signed 16-bit float and return as np array."""
        try:
            return np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0
        except Exception:
            log.error("Error converting raw data to np: ")
            log.error(traceback.format_exc())
            return None
    
    def clear_queue(self) -> None:
        try:
            self.data_queue.queue.clear()
        except Exception:
            log.error("Error clearing queue: ")
            log.error(traceback.format_exc())

    def get_energy_threshold(self) -> int:
        try:
            with self.source:
                _last = self.rec.energy_threshold
                self.rec.adjust_for_ambient_noise(self.source, 5)
                _value = round(self.rec.energy_threshold) + 100
                self.rec.energy_threshold = _last
                return _value
        except Exception:
            log.error("Error getting energy threshold: ")
            log.error(traceback.format_exc())
            return 200
