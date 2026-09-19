"""AssemblyAI Realtime Speech-to-Text (streaming v3) for live mode.

Primary live path for this hackathon MVP:
  - assemblyai.streaming.v3.RealTimeTranscriber over wss://streaming.assemblyai.com/v3/ws
  - Default speech model: universal-streaming-multilingual (better for NG accents / code-switch)

Pragmatic Streamlit integration:
  - Text / uploaded-audio → transcript path always works when a key is set.
  - Optional short PCM microphone stream via stream_microphone() when pyaudio is available.
  - Full always-on Voice Agent loop is out of scope for this MVP; we use Realtime STT
    as the AssemblyAI voice surface and route intents to remittance tools.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from voice_remit.stt.base import TranscriptEvent

logger = logging.getLogger(__name__)


class AssemblyAILiveSTT:
    name = "assemblyai_realtime"

    def __init__(self, api_key: str, speech_model: str = "universal-streaming-multilingual"):
        if not api_key:
            raise ValueError("ASSEMBLYAI_API_KEY is required for live STT")
        self.api_key = api_key
        self.speech_model = speech_model

    def describe(self) -> str:
        return (
            f"AssemblyAI Realtime STT (streaming v3), speech_model={self.speech_model}. "
            "Typed text is accepted as a final turn; optional mic streaming via stream_microphone()."
        )

    def transcribe_text_input(self, text: str) -> TranscriptEvent:
        """Live mode still accepts typed turns (judges / no-mic demos)."""
        cleaned = " ".join(text.strip().split())
        return TranscriptEvent(text=cleaned, is_final=True, source="assemblyai")

    def transcribe_file(self, path: str) -> TranscriptEvent:
        """Prerecorded fallback using AssemblyAI Universal transcription."""
        import assemblyai as aai

        aai.settings.api_key = self.api_key
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcript = aai.Transcriber(config=config).transcribe(path)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(transcript.error or "AssemblyAI transcription failed")
        return TranscriptEvent(
            text=(transcript.text or "").strip(),
            is_final=True,
            source="assemblyai",
        )

    def stream_microphone(
        self,
        on_turn: Callable[[str, bool], None],
        sample_rate: int = 16000,
        max_seconds: float = 15.0,
    ) -> str:
        """Short realtime mic session → final transcript text.

        Requires `pyaudio` (optional dependency). Used by CLI live demos.
        """
        try:
            from assemblyai.streaming.v3 import (
                RealTimeEvents,
                RealTimeParameters,
                RealTimeTranscriber,
                RealTimeTranscriberOptions,
                TurnEvent,
            )
        except ImportError as e:
            raise RuntimeError(
                "assemblyai streaming.v3 not available — upgrade: pip install -U assemblyai"
            ) from e

        try:
            import pyaudio  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "pyaudio is required for microphone streaming. "
                "Install system portaudio + `pip install pyaudio`, or use typed input / file upload."
            ) from e

        finals: list[str] = []

        def _on_turn(_client, event: TurnEvent) -> None:
            text = (getattr(event, "transcript", None) or getattr(event, "text", "") or "").strip()
            if not text:
                return
            end_of_turn = bool(getattr(event, "end_of_turn", False) or getattr(event, "is_final", False))
            on_turn(text, end_of_turn)
            if end_of_turn:
                finals.append(text)

        client = RealTimeTranscriber(
            RealTimeTranscriberOptions(api_key=self.api_key),
        )
        client.on(RealTimeEvents.Turn, _on_turn)

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=3200,
        )

        client.connect(
            RealTimeParameters(
                sample_rate=sample_rate,
                speech_model=self.speech_model,
            )
        )

        import time

        deadline = time.time() + max_seconds
        try:
            while time.time() < deadline:
                data = stream.read(3200, exception_on_overflow=False)
                client.stream(data)
        finally:
            try:
                client.disconnect(terminate=True)
            except Exception:  # noqa: BLE001
                logger.exception("Error terminating AssemblyAI session")
            stream.stop_stream()
            stream.close()
            audio.terminate()

        return " ".join(finals).strip()


def is_live_sdk_importable() -> bool:
    try:
        import assemblyai  # noqa: F401

        return True
    except ImportError:
        return False
