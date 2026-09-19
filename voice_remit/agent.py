"""Intent router: transcript → remittance tool → spoken-style reply."""

from __future__ import annotations

import re
from dataclasses import dataclass

from voice_remit.tools.remittance import RemittanceToolkit, ToolResult, parse_amount_usd


@dataclass
class AgentReply:
    transcript: str
    intent: str
    tool: ToolResult
    spoken: str


class VoiceRemitAgent:
    """Lightweight voice agent for Nigeria remittance help."""

    def __init__(self, toolkit: RemittanceToolkit | None = None):
        self.toolkit = toolkit or RemittanceToolkit()

    def route(self, transcript: str) -> AgentReply:
        text = transcript.strip()
        lower = text.lower()
        amount = parse_amount_usd(text)

        if self._match(lower, ["help", "what can you", "menu", "capabilities"]):
            tool = self.toolkit.help_menu()
            intent = "help"
        elif self._match(
            lower,
            [
                "checklist",
                "receive",
                "receiving",
                "account number",
                "nuban",
                "pick up",
                "pickup",
                "cash",
                "gtbank",
                "opay",
            ],
        ):
            channel = "cash" if any(w in lower for w in ("cash", "pick up", "pickup", "western")) else (
                "wallet" if any(w in lower for w in ("opay", "palmpay", "wallet", "mobile money")) else "bank"
            )
            tool = self.toolkit.receive_checklist(channel)
            intent = "receive_checklist"
        elif self._match(
            lower,
            ["rate", "fx", "exchange", "dollar to naira", "usd/ngn", "naira rate", "how much is the dollar"],
        ):
            tool = self.toolkit.fx_check()
            intent = "fx_check"
        elif self._match(
            lower,
            ["send now", "should i send", "timing", "when should", "good time", "right now"],
        ):
            tool = self.toolkit.send_now_advice(amount)
            intent = "send_now_advice"
        elif self._match(
            lower,
            [
                "fee",
                "fees",
                "compare",
                "cheapest",
                "cost",
                "how much to send",
                "remitly",
                "wise",
                "sendwave",
                "transfer",
                "send",
            ],
        ):
            tool = self.toolkit.fee_compare(amount)
            intent = "fee_compare"
        else:
            tool = self.toolkit.help_menu()
            intent = "fallback_help"

        spoken = self._to_spoken(tool)
        return AgentReply(transcript=text, intent=intent, tool=tool, spoken=spoken)

    @staticmethod
    def _match(text: str, keywords: list[str]) -> bool:
        return any(k in text for k in keywords)

    @staticmethod
    def _to_spoken(tool: ToolResult) -> str:
        # Strip markdown for a more natural voice reply.
        summary = re.sub(r"\*\*([^*]+)\*\*", r"\1", tool.summary)
        return f"{summary} Tip: {tool.nigeria_tip}"
