import httpx
from typing import AsyncIterator, List, Optional
from app.voice.llm.base import BaseLLMProvider, LLMMessage, LLMResponse

class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM Provider via REST API.
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        if not api_key:
            raise ValueError("Gemini API Key is required for GeminiLLMProvider")
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def generate_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        contents = []
        for msg in messages:
            role = "user" if msg.role in ["user", "system"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        headers = {"Content-Type": "application/json"}
        url = f"{self.base_url}?key={self.api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "")
                    
            usage = data.get("usageMetadata", {}).get("totalTokenCount", 0)
            return LLMResponse(
                content=text,
                model=self.model,
                tokens_used=usage,
                finish_reason="stop"
            )

    async def stream_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        # Generate full response and stream words as generator
        resp = await self.generate_response(messages, system_prompt, temperature)
        words = resp.content.split(" ")
        for word in words:
            yield word + " "
