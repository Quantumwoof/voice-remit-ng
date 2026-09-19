#!/usr/bin/env python3
"""Smoke test — must pass with DEMO_MODE=1 and no API key."""

from __future__ import annotations

import os
import sys

os.environ["DEMO_MODE"] = "1"
os.environ.pop("ASSEMBLYAI_API_KEY", None)

from voice_remit.agent import VoiceRemitAgent
from voice_remit.config import get_settings
from voice_remit.stt.factory import get_stt_backend
from voice_remit.stt.mock import MockSTT
from voice_remit.tools.remittance import RemittanceToolkit


def main() -> int:
    settings = get_settings()
    assert settings.demo_mode is True, "DEMO_MODE should be True"
    stt = get_stt_backend(settings)
    assert isinstance(stt, MockSTT), f"Expected MockSTT, got {type(stt)}"

    toolkit = RemittanceToolkit()
    fee = toolkit.fee_compare(200)
    assert fee.details["providers"], "fee_compare returned no providers"
    assert fee.details["providers"][0]["recipient_ngn"] > 0

    fx = toolkit.fx_check()
    assert "USD/NGN" in fx.details["pair"]

    send = toolkit.send_now_advice(150)
    assert send.details["suggested_provider"]

    checklist = toolkit.receive_checklist("bank")
    assert len(checklist.details["checklist"]) >= 5

    agent = VoiceRemitAgent(toolkit)
    phrases = MockSTT().canned_phrases()
    intents_seen = set()
    for phrase in phrases:
        event = stt.transcribe_text_input(phrase)
        reply = agent.route(event.text)
        assert reply.spoken, f"Empty spoken reply for: {phrase}"
        intents_seen.add(reply.intent)
        print(f"OK  [{reply.intent:18}] {phrase[:60]}")

    expected = {"fee_compare", "fx_check", "send_now_advice", "receive_checklist", "help"}
    missing = expected - intents_seen
    assert not missing, f"Missing intents: {missing}"

    print()
    print("Smoke test passed (DEMO_MODE).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
