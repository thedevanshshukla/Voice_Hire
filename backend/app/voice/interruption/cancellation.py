import time
from typing import Optional, List, Callable
from app.core.logger import get_logger

logger = get_logger("voice.cancellation")

class InterruptedException(Exception):
    """Exception raised when an active token/TTS stream is interrupted by candidate barge-in."""
    pass

class CancellationToken:
    """
    Thread-safe and async cooperative cancellation token for stopping active LLM & TTS streams.
    """
    def __init__(self):
        self._is_cancelled: bool = False
        self._cancel_reason: Optional[str] = None
        self._cancelled_at: Optional[float] = None
        self._requested_at: Optional[float] = None
        self._callbacks: List[Callable[[], None]] = []

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def cancellation_latency_ms(self) -> float:
        if self._requested_at and self._cancelled_at:
            return round((self._cancelled_at - self._requested_at) * 1000.0, 2)
        return 0.0

    def cancel(self, reason: str = "barge_in"):
        if not self._is_cancelled:
            self._requested_at = time.perf_counter()
            self._is_cancelled = True
            self._cancel_reason = reason
            self._cancelled_at = time.perf_counter()
            
            logger.info("Cancellation token triggered", extra={
                "reason": reason,
                "cancellation_latency_ms": self.cancellation_latency_ms
            })
            
            # Execute registered abort callbacks
            for cb in self._callbacks:
                try:
                    cb()
                except Exception as e:
                    logger.warning(f"Error in cancellation callback: {e}")

    def on_cancel(self, callback: Callable[[], None]):
        """Register a callback to be called immediately upon cancellation."""
        if self._is_cancelled:
            callback()
        else:
            self._callbacks.append(callback)

    def raise_if_cancelled(self):
        if self._is_cancelled:
            raise InterruptedException(f"Stream cancelled due to: {self._cancel_reason}")

    def reset(self):
        self._is_cancelled = False
        self._cancel_reason = None
        self._cancelled_at = None
        self._requested_at = None
        self._callbacks.clear()
