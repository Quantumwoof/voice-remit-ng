"""STT backend interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TranscriptEvent:
    text: str
    is_final: bool
    source: str  # "mock" | "assemblyai"


class STTBackend(Protocol):
    name: str

    def transcribe_text_input(self, text: str) -> TranscriptEvent:
        """Treat typed text as a final transcript (UI / CLI path)."""
        ...

    def describe(self) -> str:
        ...
