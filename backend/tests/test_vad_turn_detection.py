import pytest
import struct
from app.voice.vad.providers.energy import EnergyVADProvider
from app.voice.vad.turn_detector import TurnDetector, TurnStatus
from app.voice.vad.base import VADState

def generate_pcm_frame(amplitude: int = 0, num_samples: int = 320) -> bytes:
    """Generate 20ms of 16-bit PCM samples at 16kHz."""
    return struct.pack(f"<{num_samples}h", *([amplitude] * num_samples))

def test_energy_vad_speech_vs_silence():
    vad = EnergyVADProvider(energy_threshold=0.01)
    
    # 1. Silence Frame (amplitude 0)
    silence_frame = generate_pcm_frame(amplitude=0)
    res_silence = vad.process_frame(silence_frame)
    assert res_silence.is_speech is False
    assert res_silence.energy_level < 0.005

    # 2. Loud Speech Frame (amplitude 10000 / 32768 = ~0.30 RMS)
    speech_frame = generate_pcm_frame(amplitude=10000)
    res_speech = vad.process_frame(speech_frame)
    assert res_speech.is_speech is True
    assert res_speech.energy_level > 0.05

def test_turn_detector_short_thinking_pause():
    detector = TurnDetector(
        silence_threshold_ms=800,
        min_speech_duration_ms=200,
        max_pause_tolerance_ms=600
    )
    
    # 1. Candidate speaks for 400ms (20 frames x 20ms)
    speech_frame = generate_pcm_frame(amplitude=8000)
    for _ in range(20):
        res = detector.process_frame(speech_frame)
    assert res.status == TurnStatus.CANDIDATE_SPEAKING
    assert res.is_turn_complete is False

    # 2. Candidate temporarily pauses for 300ms (15 frames of silence)
    silence_frame = generate_pcm_frame(amplitude=0)
    for _ in range(15):
        res = detector.process_frame(silence_frame)
    # The detector must recognize this as a thinking pause without completing turn!
    assert res.status == TurnStatus.CANDIDATE_PAUSED
    assert res.is_turn_complete is False
    assert res.pause_count == 1

    # 3. Candidate resumes speech for 200ms
    for _ in range(10):
        res = detector.process_frame(speech_frame)
    assert res.status == TurnStatus.CANDIDATE_SPEAKING
    assert res.is_turn_complete is False

def test_turn_detector_terminal_answer_completion():
    detector = TurnDetector(
        silence_threshold_ms=800,
        min_speech_duration_ms=200
    )
    
    # 1. Candidate speaks for 600ms
    speech_frame = generate_pcm_frame(amplitude=8000)
    for _ in range(30):
        detector.process_frame(speech_frame)

    # 2. Candidate finishes answer -> Silence for 900ms (45 frames of 20ms)
    silence_frame = generate_pcm_frame(amplitude=0)
    completed_event = None
    for _ in range(45):
        res = detector.process_frame(silence_frame)
        if res.is_turn_complete:
            completed_event = res
            break
        
    assert completed_event is not None
    assert completed_event.status == TurnStatus.TURN_ENDPOINT
    assert completed_event.is_turn_complete is True
    assert completed_event.speech_duration_ms >= 600.0
    assert completed_event.endpointing_delay_ms >= 800.0

def test_turn_detector_rejects_brief_noise():
    detector = TurnDetector(
        silence_threshold_ms=800,
        min_speech_duration_ms=300 # Requires 300ms of speech
    )
    
    # Brief 40ms noise (2 frames)
    speech_frame = generate_pcm_frame(amplitude=8000)
    detector.process_frame(speech_frame)
    detector.process_frame(speech_frame)

    # Followed by silence
    silence_frame = generate_pcm_frame(amplitude=0)
    res = None
    for _ in range(45):
        res = detector.process_frame(silence_frame)

    # Should not trigger a completed turn
    assert res.is_turn_complete is False
