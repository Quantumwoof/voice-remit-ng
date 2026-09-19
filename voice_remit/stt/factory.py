"""Pick mock vs AssemblyAI backend from settings."""

from __future__ import annotations

from voice_remit.config import Settings, get_settings
from voice_remit.stt.mock import MockSTT


def get_stt_backend(settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.demo_mode or not settings.assemblyai_api_key:
        return MockSTT()
    from voice_remit.stt.assemblyai_live import AssemblyAILiveSTT

    return AssemblyAILiveSTT(
        api_key=settings.assemblyai_api_key,
        speech_model=settings.speech_model,
    )
