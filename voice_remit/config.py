"""Runtime configuration for VoiceRemitNG."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    demo_mode: bool
    assemblyai_api_key: str | None
    speech_model: str

    @property
    def live_ready(self) -> bool:
        return bool(self.assemblyai_api_key) and not self.demo_mode

    @property
    def mode_label(self) -> str:
        if self.demo_mode:
            return "DEMO"
        if self.assemblyai_api_key:
            return "LIVE (AssemblyAI Realtime STT)"
        return "DEMO (no API key — falling back)"


def get_settings() -> Settings:
    api_key = os.getenv("ASSEMBLYAI_API_KEY", "").strip() or None
    # Default to demo when no key; DEMO_MODE=1 forces demo even with a key.
    demo_explicit = os.getenv("DEMO_MODE")
    if demo_explicit is None:
        demo_mode = api_key is None
    else:
        demo_mode = _truthy(demo_explicit, default=True)

    speech_model = os.getenv(
        "ASSEMBLYAI_SPEECH_MODEL",
        "universal-streaming-multilingual",
    ).strip()

    return Settings(
        demo_mode=demo_mode,
        assemblyai_api_key=api_key,
        speech_model=speech_model,
    )
