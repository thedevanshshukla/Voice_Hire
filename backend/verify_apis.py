import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx
from pymongo import MongoClient

# Load environment variables
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", "").strip("\"' ")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/voicehire")

async def verify_openai():
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("your-") or OPENAI_API_KEY == "sk-...":
        return "[SKIPPED] (Not configured)"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            if res.status_code == 200:
                return "[SUCCESS] (Valid API Key)"
            else:
                return f"[FAILED] (HTTP {res.status_code}: {res.text[:100]})"
    except Exception as e:
        return f"[ERROR] ({str(e)})"

async def verify_gemini():
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your-") or GEMINI_API_KEY.startswith("AIzaSy..."):
        return "[SKIPPED] (Not configured)"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return "[SUCCESS] (Valid API Key)"
            else:
                return f"[FAILED] (HTTP {res.status_code}: {res.text[:100]})"
    except Exception as e:
        return f"[ERROR] ({str(e)})"

async def verify_deepgram():
    if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY.startswith("your-"):
        return "[SKIPPED] (Not configured)"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
            )
            if res.status_code == 200:
                return "[SUCCESS] (Valid API Key)"
            else:
                return f"[FAILED] (HTTP {res.status_code}: {res.text[:100]})"
    except Exception as e:
        return f"[ERROR] ({str(e)})"

async def verify_elevenlabs():
    if not ELEVEN_LABS_API_KEY or ELEVEN_LABS_API_KEY.startswith("your-"):
        return "[SKIPPED] (Not configured)"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": ELEVEN_LABS_API_KEY}
            )
            if res.status_code == 200:
                voices = res.json().get("voices", [])
                return f"[SUCCESS] (Valid API Key - {len(voices)} voices available)"
            else:
                return f"[FAILED] (HTTP {res.status_code}: {res.text[:100]})"
    except Exception as e:
        return f"[ERROR] ({str(e)})"

async def verify_livekit():
    if not LIVEKIT_API_KEY or LIVEKIT_API_KEY in ["devkey", "your-api-key"] or not LIVEKIT_API_SECRET or LIVEKIT_API_SECRET in ["secret", "your-api-secret"]:
        return "[SKIPPED] (Default/mock credentials configured)"
    try:
        from livekit.api import AccessToken, VideoGrants
        token = (
            AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
            .with_identity("verify-agent")
            .with_grants(VideoGrants(room_join=True, room="test-room"))
            .to_jwt()
        )
        return f"[SUCCESS] (Valid JWT Key/Secret Generated, Host: {LIVEKIT_URL})"
    except Exception as e:
        return f"[ERROR] ({str(e)})"

def verify_mongodb():
    if not MONGODB_URI or MONGODB_URI.startswith("your-"):
        return "[SKIPPED] (Not configured)"
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000, tlsAllowInvalidCertificates=True)
        # Send a ping to verify connection
        client.admin.command('ping')
        dbs = client.list_database_names()
        # Mask sensitive credentials in URI for display
        clean_uri = MONGODB_URI.split("@")[-1] if "@" in MONGODB_URI else MONGODB_URI
        return f"[SUCCESS] (Connected to MongoDB at {clean_uri})"
    except Exception as e:
        return f"[FAILED] ({str(e)})"

async def main():
    print("=" * 60)
    print(" VoiceHire API & Database Credentials Verification")
    print("=" * 60)

    results = await asyncio.gather(
        verify_openai(),
        verify_gemini(),
        verify_deepgram(),
        verify_elevenlabs(),
        verify_livekit()
    )

    mongo_result = verify_mongodb()

    print(f"OpenAI API:      {results[0]}")
    print(f"Gemini API:      {results[1]}")
    print(f"Deepgram API:    {results[2]}")
    print(f"ElevenLabs API:  {results[3]}")
    print(f"LiveKit:         {results[4]}")
    print(f"MongoDB:         {mongo_result}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
