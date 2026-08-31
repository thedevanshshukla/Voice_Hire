import asyncio
from typing import Optional
from livekit.api import AccessToken, VideoGrants
from app.config import settings
from app.core.logger import get_logger
from app.voice.pipeline import BasicVoicePipeline

logger = get_logger("agent.worker")

def generate_livekit_token(room_name: str, identity: str, name: Optional[str] = None) -> str:
    """
    Generate a signed JWT AccessToken for connecting to a LiveKit Room.
    """
    grant = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )
    
    token = (
        AccessToken(api_key=settings.LIVEKIT_API_KEY, api_secret=settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(name or identity)
        .with_grants(grant)
    )
    
    return token.to_jwt()

class VoiceAgentWorker:
    """
    Voice Agent Worker managing realtime session handling and conversation processing.
    """
    def __init__(self, room_name: str, pipeline: Optional[BasicVoicePipeline] = None):
        self.room_name = room_name
        self.pipeline = pipeline or BasicVoicePipeline()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self.is_running = True
        logger.info(f"VoiceAgentWorker started for room {self.room_name}", extra={"room": self.room_name})

    async def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info(f"VoiceAgentWorker stopped for room {self.room_name}", extra={"room": self.room_name})
