"""Nigeria-focused remittance tools (fee compare, FX, send-now, receive checklist).

Rates and fees are illustrative hackathon mocks — not live market data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


LAGOS = ZoneInfo("Africa/Lagos")


@dataclass
class ToolResult:
    name: str
    title: str
    summary: str
    details: dict[str, Any]
    nigeria_tip: str


# Illustrative corridor data (USD → NGN) for demo / hackathon.
CORRIDORS = {
    "wise": {
        "name": "Wise",
        "fee_pct": 0.65,
        "flat_fee_usd": 1.20,
        "fx_markup_pct": 0.35,
        "eta": "minutes–1 business day",
        "receive": "Naira bank account",
    },
    "remitly": {
        "name": "Remitly",
        "fee_pct": 0.0,
        "flat_fee_usd": 3.99,
        "fx_markup_pct": 1.10,
        "eta": "minutes (Express) / 1–3 days (Economy)",
        "receive": "Bank / mobile money / cash pickup",
    },
    "worldremit": {
        "name": "WorldRemit",
        "fee_pct": 1.5,
        "flat_fee_usd": 0.0,
        "fx_markup_pct": 0.90,
        "eta": "minutes–same day",
        "receive": "Bank / mobile money",
    },
    "western_union": {
        "name": "Western Union",
        "fee_pct": 2.5,
        "flat_fee_usd": 4.99,
        "fx_markup_pct": 2.20,
        "eta": "minutes (cash) / 1–2 days (bank)",
        "receive": "Cash pickup / bank",
    },
    "sendwave": {
        "name": "Sendwave",
        "fee_pct": 0.0,
        "flat_fee_usd": 0.0,
        "fx_markup_pct": 1.80,
        "eta": "minutes",
        "receive": "Naira bank / mobile wallet",
    },
}

# Mid-market mock (illustrative). Live FX not fetched in DEMO.
MOCK_USD_NGN_MID = 1585.0


def _now_lagos() -> datetime:
    return datetime.now(LAGOS)


def parse_amount_usd(text: str, default: float = 200.0) -> float:
    """Pull a USD amount from free text, e.g. '$500', '500 dollars', 'send 100'."""
    patterns = [
        r"\$\s*([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:usd|dollars?|bucks)",
        r"(?:send|transfer|remit)\s+([\d,]+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return float(m.group(1).replace(",", ""))
    # bare number if present
    m = re.search(r"\b([\d]{2,6}(?:\.\d+)?)\b", text)
    if m:
        val = float(m.group(1))
        if 10 <= val <= 50000:
            return val
    return default


class RemittanceToolkit:
    """Tool pack the voice agent can call from transcribed intent."""

    def fee_compare(self, amount_usd: float = 200.0) -> ToolResult:
        mid = MOCK_USD_NGN_MID
        rows = []
        for key, c in CORRIDORS.items():
            fee = amount_usd * (c["fee_pct"] / 100.0) + c["flat_fee_usd"]
            effective_rate = mid * (1 - c["fx_markup_pct"] / 100.0)
            net_usd = max(amount_usd - fee, 0)
            naira = round(net_usd * effective_rate, 2)
            total_cost_pct = ((amount_usd * mid - naira) / (amount_usd * mid)) * 100
            rows.append(
                {
                    "provider": c["name"],
                    "key": key,
                    "fee_usd": round(fee, 2),
                    "effective_usd_ngn": round(effective_rate, 2),
                    "recipient_ngn": naira,
                    "total_cost_pct": round(total_cost_pct, 2),
                    "eta": c["eta"],
                    "receive": c["receive"],
                }
            )
        rows.sort(key=lambda r: r["recipient_ngn"], reverse=True)
        best = rows[0]
        summary = (
            f"For ${amount_usd:,.0f} USD → NGN, **{best['provider']}** currently puts the most "
            f"naira in the recipient's pocket (~₦{best['recipient_ngn']:,.0f}), "
            f"with ~{best['total_cost_pct']:.1f}% all-in cost vs mid-market."
        )
        return ToolResult(
            name="fee_compare",
            title=f"Fee & FX compare — ${amount_usd:,.0f} USD → NGN",
            summary=summary,
            details={"amount_usd": amount_usd, "mid_usd_ngn": mid, "providers": rows},
            nigeria_tip=(
                "Confirm the payout bank supports your corridor (GTBank, Access, UBA, Zenith, "
                "Opay, PalmPay are common). Always check the *guaranteed* naira amount before you pay."
            ),
        )

    def fx_check(self) -> ToolResult:
        mid = MOCK_USD_NGN_MID
        now = _now_lagos()
        # Illustrative day move
        day_change_pct = 0.42
        summary = (
            f"Illustrative mid-market **USD/NGN ≈ ₦{mid:,.0f}** "
            f"(Lagos {now.strftime('%Y-%m-%d %H:%M %Z')}). "
            f"Mock day move: +{day_change_pct:.2f}% — naira a touch stronger vs USD in this demo."
        )
        return ToolResult(
            name="fx_check",
            title="USD/NGN FX snapshot",
            summary=summary,
            details={
                "pair": "USD/NGN",
                "mid_market": mid,
                "day_change_pct": day_change_pct,
                "as_of": now.isoformat(),
                "note": "Hackathon mock — not a live feed. Wire a FX API for production.",
            },
            nigeria_tip=(
                "CBN official vs parallel (ABOKO/Nafex-style) rates can diverge. "
                "Remittance apps usually use their own retail rate — compare *naira received*, not headline FX alone."
            ),
        )

    def send_now_advice(self, amount_usd: float = 200.0) -> ToolResult:
        now = _now_lagos()
        weekday = now.weekday()  # Mon=0
        hour = now.hour
        banking_hours = 8 <= hour < 16 and weekday < 5
        weekend = weekday >= 5

        if banking_hours:
            urgency = "Good window"
            advice = (
                "Nigerian banks are in business hours — bank payouts and BVN/name checks clear faster. "
                "Express corridors (Sendwave, Remitly Express, Wise) are fine to fire now."
            )
        elif weekend:
            urgency = "Weekend — prefer wallets / cash"
            advice = (
                "Many NG bank rails slow on weekends. Prefer mobile money (Opay/PalmPay) or cash pickup "
                "if the recipient needs funds today; bank deposits may land Monday."
            )
        else:
            urgency = "After hours"
            advice = (
                "Outside Lagos banking hours. Instant wallet corridors still work; "
                "traditional bank credits may wait until the next clearing cycle."
            )

        compare = self.fee_compare(amount_usd)
        best = compare.details["providers"][0]
        summary = (
            f"**{urgency}** (Lagos {now.strftime('%a %H:%M')}). {advice} "
            f"Cheapest demo pick for ${amount_usd:,.0f}: **{best['provider']}** → ~₦{best['recipient_ngn']:,.0f}."
        )
        return ToolResult(
            name="send_now_advice",
            title="Send-now timing advice",
            summary=summary,
            details={
                "lagos_time": now.isoformat(),
                "banking_hours": banking_hours,
                "weekend": weekend,
                "suggested_provider": best["provider"],
                "amount_usd": amount_usd,
            },
            nigeria_tip=(
                "If sending for school fees or rent, confirm the landlord/school account name matches "
                "exactly — mismatched names are a top cause of failed NG payouts."
            ),
        )

    def receive_checklist(self, channel: str = "bank") -> ToolResult:
        channel = channel.lower().strip()
        items = [
            "Recipient full legal name (must match BVN / bank records)",
            "Correct 10-digit NUBAN account number (double-check digit by digit)",
            "Bank name + sort if required by the app",
            "Active phone number for SMS / OTP alerts",
            "Agree on who pays fees (sender vs deducted from payout)",
        ]
        if "wallet" in channel or "opay" in channel or "palm" in channel:
            items.extend(
                [
                    "Wallet provider (Opay, PalmPay, etc.) registered to recipient NIN/BVN",
                    "Wallet limit / KYC tier can receive the amount",
                ]
            )
            title = "Receive checklist — mobile wallet"
        elif "cash" in channel:
            items.extend(
                [
                    "Valid government ID for cash pickup (NIN slip, passport, driver's licence)",
                    "Pickup city / agent location and MTCN / reference code",
                    "Do not share the full reference over insecure channels",
                ]
            )
            title = "Receive checklist — cash pickup"
        else:
            items.extend(
                [
                    "Account is Naira (NGN), not USD domiciliary — unless you intend domiciliary",
                    "Recipient bank is on the corridor's supported list",
                ]
            )
            title = "Receive checklist — Naira bank transfer"

        summary = (
            "Before you hit send, walk through this Nigeria receive checklist with the recipient. "
            "Most failed remittances are bad account numbers or name mismatches — not FX."
        )
        return ToolResult(
            name="receive_checklist",
            title=title,
            summary=summary,
            details={"channel": channel, "checklist": items},
            nigeria_tip=(
                "Ask the recipient to send a bank app screenshot of account name + NUBAN — "
                "don't rely on WhatsApp voice notes for digits."
            ),
        )

    def help_menu(self) -> ToolResult:
        return ToolResult(
            name="help",
            title="What I can help with",
            summary=(
                "VoiceRemitNG helps Nigerian families and diaspora senders with remittance decisions. "
                "Try: fee compare, FX check, send-now advice, or receive checklist."
            ),
            details={
                "intents": [
                    "compare fees / cheapest way to send",
                    "what's the dollar to naira rate",
                    "should I send money now",
                    "checklist for receiving in Nigeria",
                ]
            },
            nigeria_tip="Speak naturally — e.g. 'Compare fees for sending 300 dollars to Lagos'.",
        )
