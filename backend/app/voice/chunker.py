import re
from typing import AsyncIterator, List

class SentenceBoundaryChunker:
    """
    Buffers streaming LLM text tokens and splits them into natural sentence & clause chunks.
    This enables streaming TTS synthesis on early clauses before full LLM completion.
    """
    def __init__(self, min_clause_words: int = 4):
        self.min_clause_words = min_clause_words
        self.buffer = ""
        # Sentence ending punctuation
        self.sentence_split_regex = re.compile(r'([.!?:\n]+)')

    async def process_stream(self, token_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for token in token_stream:
            self.buffer += token
            
            # Check for sentence split
            parts = self.sentence_split_regex.split(self.buffer)
            if len(parts) >= 3:
                # We have at least one complete sentence: parts[0] + parts[1]
                sentence = (parts[0] + parts[1]).strip()
                self.buffer = "".join(parts[2:])
                if sentence:
                    yield sentence

        # Flush remaining buffer at stream end
        remaining = self.buffer.strip()
        if remaining:
            self.buffer = ""
            yield remaining
