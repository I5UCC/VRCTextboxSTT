import speech_recognition as sr
import numpy as np
from queue import Queue
from config import listener

class ListenHandler(object):
    def __init__(self, config: listener) -> None:
        self.config: listener = config
        self.rec = sr.Recognizer()
        self.rec.dynamic_energy_threshold = bool(self.config.dynamic_energy_threshold)
        self.rec.energy_threshold = self.config.energy_threshold
        self.rec.pause_threshold = self.config.pause_threshold
        self.source = sr.Microphone(sample_rate=16000, device_index=int(self.config.microphone_index) if self.config.microphone_index else None)
        self.data_queue = Queue()

    def listen_once(self) -> np.ndarray:
        """
        Listens once and returns the audio data as a np array.
        """

        with self.source:
            try:
                _audio = self.rec.listen(self.source, timeout=self.config.timeout_time)
            except sr.WaitTimeoutError:
                return None

            return self.raw_to_np(_audio.get_raw_data())
        
    def start_listen_background(self) -> None:
        """
        Listens in the background and puts the audio data into a queue.
        """
        def record_callback(_, audio:sr.AudioData) -> None:
            _data = audio.get_raw_data()
            self.data_queue.put(_data)

        self.stop_listening = self.rec.listen_in_background(self.source, record_callback, phrase_time_limit=self.config.phrase_time_limit)

    def stop_listen_background(self) -> None:
        self.stop_listening(wait_for_stop=False)
        self.clear_queue()

    def raw_to_np(self, raw_data:bytes) -> np.ndarray:
        return np.frombuffer(raw_data, np.int16).flatten().astype(np.float32) / 32768.0
    
    def clear_queue(self) -> None:
        self.data_queue.queue.clear()

    def get_energy_threshold(self) -> int:
        with self.source:
            _last = self.rec.energy_threshold
            self.rec.adjust_for_ambient_noise(self.source, 5)
            _value = round(self.rec.energy_threshold) + 20
            self.rec.energy_threshold = _last
            return _value