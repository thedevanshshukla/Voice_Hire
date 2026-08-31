import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import InterviewConfig, InterviewLanguage, InterviewRole, InterviewStage
from app.voice.multilingual import LanguageDetector
from app.interview.prompt_builder import InterviewPromptBuilder

def test_language_detection_english():
    text = "We configured consistent hashing across our Redis cluster with a 15-second TTL."
    lang, conf = LanguageDetector.detect_language(text)
    assert lang == InterviewLanguage.ENGLISH
    assert conf >= 0.85

def test_language_detection_devanagari_hindi():
    text = "हमने पोस्टग्रेस एसक्यूएल और काफ्का का उपयोग करके डिस्ट्रीब्यूटेड आर्किटेक्चर बनाया था।"
    lang, conf = LanguageDetector.detect_language(text)
    assert lang == InterviewLanguage.HINDI
    assert conf >= 0.90

def test_language_detection_hinglish():
    text = "Humne Redis cache use kiya tha kyunki database pe queries bahut slow chal rahi thi aur latency badh rahi thi."
    lang, conf = LanguageDetector.detect_language(text)
    assert lang == InterviewLanguage.HINGLISH
    assert conf >= 0.70

def test_stt_tts_provider_language_config():
    stt_hi = LanguageDetector.get_stt_language_config(InterviewLanguage.HINDI)
    assert stt_hi["language"] == "hi"

    stt_hinglish = LanguageDetector.get_stt_language_config(InterviewLanguage.HINGLISH)
    assert stt_hinglish["language"] == "multi"

    tts_hi = LanguageDetector.get_tts_model_config(InterviewLanguage.HINDI)
    assert tts_hi["model_id"] == "eleven_multilingual_v2"

def test_prompt_builder_hinglish_directive():
    config = InterviewConfig(role=InterviewRole.BACKEND, language=InterviewLanguage.HINGLISH)
    prompt = InterviewPromptBuilder.build_system_prompt(
        config=config,
        candidate_name="Rahul",
        stage=InterviewStage.CORE_CONCEPTS,
        current_language=InterviewLanguage.HINGLISH
    )
    assert "LANGUAGE DIRECTIVE" in prompt
    assert "Hinglish" in prompt
    assert "strictly in English" in prompt

@pytest.mark.asyncio
async def test_api_detect_language_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/voice/detect-language", json={
            "text": "Humne PostgreSQL me indexes create kiya tha taaki query fast ho jaye."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["detected_language"] in ["Hinglish", "Hindi"]
        assert data["confidence"] > 0.6
