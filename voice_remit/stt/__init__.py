"""Speech-to-text backends: mock (DEMO) and AssemblyAI Realtime (live)."""

from voice_remit.stt.base import STTBackend, TranscriptEvent
from voice_remit.stt.mock import MockSTT
from voice_remit.stt.factory import get_stt_backend

__all__ = ["STTBackend", "TranscriptEvent", "MockSTT", "get_stt_backend"]
