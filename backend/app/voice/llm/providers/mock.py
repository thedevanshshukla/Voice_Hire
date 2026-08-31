import asyncio
from typing import AsyncIterator, List, Optional
from app.voice.llm.base import BaseLLMProvider, LLMMessage, LLMResponse

class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM Provider for local development, simulation, and unit tests.
    """
    def __init__(self, default_reply: str = "Thank you for explaining. Let's move on to the next question regarding distributed architecture."):
        self.default_reply = default_reply

    async def generate_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        await asyncio.sleep(0.05)
        # Contextual mock behavior if user text is provided
        last_msg = messages[-1].content if messages else ""
        reply = f"I heard: '{last_msg}'. {self.default_reply}" if last_msg else self.default_reply
        return LLMResponse(
            content=reply,
            model="mock-voice-llm",
            tokens_used=42,
            finish_reason="stop"
        )

    async def stream_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        response = await self.generate_response(messages, system_prompt, temperature)
        tokens = response.content.split(" ")
        for token in tokens:
            await asyncio.sleep(0.02)
            yield token + " "
