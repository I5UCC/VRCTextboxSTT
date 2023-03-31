import torch
import numpy as np
from helper import log
import traceback

class VADHandler(object):
        def __init__(self, cache_path, device_str = "cuda:0") -> None:
                self.cache_path = cache_path
                self.device = device_str
                torch.hub.set_dir(self.cache_path)
                self.model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                        model='silero_vad',
                                        force_reload=False)
                (self.get_speech_timestamps,
                _,
                _,
                _,
                self.collect_chunks) = self.utils
                self.model.to(self.device)

        def apply(self, np_audio: np.ndarray) -> np.ndarray:
                """Apply voice activity detection to a numpy array of float32 audio data."""
        
                log.info("Applying VAD...")

                try:
                        torch_audio = torch.from_numpy(np_audio).to(self.device)

                        speech_timestamps = self.get_speech_timestamps(torch_audio, model=self.model, speech_pad_ms=100)

                        chunks = self.collect_chunks(speech_timestamps, torch_audio)

                        return chunks.cpu().detach().numpy()
                except Exception:
                        log.error("failed to apply VAD:")
                        log.error(traceback.format_exc())
                        return np_audio
