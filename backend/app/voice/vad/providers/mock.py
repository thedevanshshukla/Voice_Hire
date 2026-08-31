from app.voice.vad.base import BaseVADProvider, VADFrameResult, VADState

class MockVADProvider(BaseVADProvider):
    """
    Mock VAD Provider for automated unit testing and simulation.
    """
    def __init__(self, force_speech: bool = True):
        self.force_speech = force_speech
        self.frame_count = 0

    def process_frame(self, audio_frame: bytes, sample_rate: int = 16000) -> VADFrameResult:
        self.frame_count += 1
        return VADFrameResult(
            is_speech=self.force_speech,
            probability=0.95 if self.force_speech else 0.05,
            energy_level=0.08 if self.force_speech else 0.001,
            state=VADState.SPEECH_ONGOING if self.force_speech else VADState.SILENCE,
            speech_duration_ms=self.frame_count * 20.0 if self.force_speech else 0.0,
            silence_duration_ms=0.0 if self.force_speech else self.frame_count * 20.0
        )

    def reset(self):
        self.frame_count = 0
