import httpx
import json
from typing import AsyncIterator, List, Optional
from app.voice.llm.base import BaseLLMProvider, LLMMessage, LLMResponse

class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM Provider using direct chat completions API.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OpenAI API Key is required for OpenAILLMProvider")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def generate_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(self.base_url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {}).get("total_tokens", 0)
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=usage,
                finish_reason=choice.get("finish_reason", "stop")
            )

    async def stream_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
