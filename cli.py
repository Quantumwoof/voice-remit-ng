#!/usr/bin/env python3
"""Optional CLI for VoiceRemitNG (DEMO or live)."""

from __future__ import annotations

import argparse
import os
import sys

os.environ.setdefault("DEMO_MODE", "1")

from voice_remit.agent import VoiceRemitAgent
from voice_remit.config import get_settings
from voice_remit.stt.factory import get_stt_backend
from voice_remit.stt.mock import MockSTT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VoiceRemitNG CLI")
    parser.add_argument("text", nargs="*", help="Utterance to process")
    parser.add_argument("--list-demos", action="store_true", help="Show canned DEMO phrases")
    parser.add_argument("--mic", action="store_true", help="Live mic via AssemblyAI Realtime STT")
    parser.add_argument("--seconds", type=float, default=12.0, help="Mic listen duration")
    args = parser.parse_args(argv)

    settings = get_settings()
    stt = get_stt_backend(settings)
    agent = VoiceRemitAgent()

    print(f"Mode: {settings.mode_label}")
    print(stt.describe())
    print()

    if args.list_demos:
        for p in MockSTT().canned_phrases():
            print(f"  • {p}")
        return 0

    transcript = " ".join(args.text).strip()

    if args.mic:
        if settings.demo_mode or not settings.assemblyai_api_key:
            print("Mic requires DEMO_MODE=0 and ASSEMBLYAI_API_KEY", file=sys.stderr)
            return 2
        if not hasattr(stt, "stream_microphone"):
            print("Backend does not support microphone streaming", file=sys.stderr)
            return 2

        print(f"Listening ~{args.seconds}s … speak now")
        partials: list[str] = []

        def on_turn(text: str, final: bool) -> None:
            tag = "FINAL" if final else "partial"
            print(f"  [{tag}] {text}")
            if final:
                partials.append(text)

        transcript = stt.stream_microphone(on_turn, max_seconds=args.seconds) or " ".join(partials)

    if not transcript:
        print("Usage: python cli.py \"Compare fees for sending 200 dollars\"")
        print("       python cli.py --list-demos")
        return 1

    event = stt.transcribe_text_input(transcript)
    reply = agent.route(event.text)
    print(f"Heard: {reply.transcript}")
    print(f"Intent: {reply.intent}")
    print(f"Title: {reply.tool.title}")
    print(reply.spoken)
    print(f"Tip: {reply.tool.nigeria_tip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
