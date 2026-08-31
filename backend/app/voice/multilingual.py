import re
from typing import Dict, Any, Tuple
from app.models.interview import InterviewLanguage

DEVANGARI_REGEX = re.compile(r"[\u0900-\u097F]")

HINGLISH_KEYWORDS = [
    "humne", "hamne", "karega", "karenge", "karna", "karte", "karti",
    "koshish", "kyunki", "kyonki", "hota", "hoti", "hote", "hai", "hain",
    "tha", "thi", "the", "matlab", "achha", "accha", "theek", "thik",
    "bhi", "lekin", "magar", "aur", "kaise", "kya", "kyu", "kyun",
    "karo", "kijiye", "raha", "rahi", "rahe", "hoga", "hogi", "honge"
]

class LanguageDetector:
    """
    Detects language and code-switching between English, Devanagari Hindi,
    and conversational Hinglish (Indian Tech standard).
    """

    @classmethod
    def detect_language(cls, text: str) -> Tuple[InterviewLanguage, float]:
        if not text or not text.strip():
            return InterviewLanguage.ENGLISH, 1.0

        clean_text = text.strip().lower()

        # 1. Check for Devanagari characters
        devanagari_chars = len(DEVANGARI_REGEX.findall(clean_text))
        if devanagari_chars > 3:
            return InterviewLanguage.HINDI, 0.95

        # 2. Check for Romanized Hinglish keywords
        words = re.findall(r"\b\w+\b", clean_text)
        if not words:
            return InterviewLanguage.ENGLISH, 1.0

        hinglish_matches = [w for w in words if w in HINGLISH_KEYWORDS]
        ratio = len(hinglish_matches) / float(len(words))

        if len(hinglish_matches) >= 2 or ratio >= 0.15:
            confidence = min(0.98, 0.6 + (len(hinglish_matches) * 0.1))
            return InterviewLanguage.HINGLISH, round(confidence, 2)

        return InterviewLanguage.ENGLISH, 0.90

    @classmethod
    def get_stt_language_config(cls, lang: InterviewLanguage) -> Dict[str, str]:
        if lang == InterviewLanguage.HINDI:
            return {"language": "hi", "model": "nova-2"}
        elif lang == InterviewLanguage.HINGLISH:
            return {"language": "multi", "model": "nova-2"}
        else:
            return {"language": "en-US", "model": "nova-2"}

    @classmethod
    def get_tts_model_config(cls, lang: InterviewLanguage) -> Dict[str, str]:
        if lang in [InterviewLanguage.HINDI, InterviewLanguage.HINGLISH]:
            return {
                "model_id": "eleven_multilingual_v2",
                "deepgram_model": "aura-asteria-en"
            }
        return {
            "model_id": "eleven_turbo_v2_5",
            "deepgram_model": "aura-helios-en"
        }
