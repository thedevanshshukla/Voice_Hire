from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = "stop"

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for Large Language Model (LLM) Providers.
    """
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Generate a complete response from the LLM.
        """
        pass

    @abstractmethod
    async def stream_response(
        self, 
        messages: List[LLMMessage], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from the LLM.
        """
        pass
