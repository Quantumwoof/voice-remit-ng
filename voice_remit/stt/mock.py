"""Mock STT for DEMO_MODE — no API key required."""

from __future__ import annotations

from voice_remit.stt.base import TranscriptEvent


class MockSTT:
    name = "mock"

    def transcribe_text_input(self, text: str) -> TranscriptEvent:
        cleaned = " ".join(text.strip().split())
        return TranscriptEvent(text=cleaned, is_final=True, source="mock")

    def describe(self) -> str:
        return (
            "Mock STT (DEMO_MODE): typed or canned phrases are treated as final transcripts. "
            "No microphone or AssemblyAI key required."
        )

    def canned_phrases(self) -> list[str]:
        return [
            "Compare fees for sending 300 dollars to Nigeria",
            "What's the dollar to naira rate right now?",
            "Should I send money now from London to Lagos?",
            "Give me a checklist for receiving money in my GTBank account",
            "How do I pick up cash from Western Union in Abuja?",
            "Help — what can you do?",
        ]
