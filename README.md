# VoiceRemitNG 🇳🇬

**AssemblyAI-powered voice / STT agent for Nigeria remittance help**

Built for the [lablab](https://lablab.ai) **AssemblyAI Voice Agent Hackathon**.

> Speak naturally (“Compare fees for sending $300 to Lagos”) → transcript → remittance tools
> (fee compare, FX check, send-now advice, receive checklist) → clear Nigeria-focused guidance.

MIT licensed · Demo works **without** an API key (`DEMO_MODE=1`).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Problem

Diaspora families send billions of dollars to Nigeria every year, but the experience is noisy:

- Opaque **fees vs FX markups** across Wise, Remitly, Sendwave, Western Union, etc.
- Confusion between **CBN / parallel / app retail** USD→NGN rates.
- Bad timing (weekends / after Lagos banking hours) delays bank payouts.
- Failed transfers from **wrong NUBAN**, name/BVN mismatch, or incomplete cash-pickup IDs.

Most “help” is blog posts or chatbots that don’t meet people where they already talk — **voice**.

## Solution

**VoiceRemitNG** is a lightweight voice agent:

1. **Hear** the user (mock STT in demo, **AssemblyAI Realtime Speech-to-Text** in live mode).
2. **Route** intent to Nigeria remittance tools.
3. **Answer** with spoken-style advice plus structured details (tables / checklists).

Primary UI: **Streamlit** (`app.py`). Optional: **CLI** (`cli.py`).

---

## How AssemblyAI is used

| Mode | AssemblyAI feature | When |
| --- | --- | --- |
| **DEMO** (`DEMO_MODE=1`) | None — **mock STT** | Default. Judges can run without a key. |
| **LIVE** (`DEMO_MODE=0` + key) | **Realtime STT** via `assemblyai.streaming.v3.RealTimeTranscriber` (WebSocket `wss://streaming.assemblyai.com/v3/ws`) | CLI `--mic` short sessions; same client ready for a full duplex agent. |
| **LIVE** | **Prerecorded / Universal transcription** | Streamlit audio file upload. |

**Speech model (live streaming default):** `universal-streaming-multilingual` — pragmatic for Nigerian accents and English↔Pidgin code-switching. Override with `ASSEMBLYAI_SPEECH_MODEL`.

**Not used in this MVP (documented for judges):** a full hosted AssemblyAI *Voice Agent* orchestration loop. We keep the hackathon scope honest: **Realtime STT is the wired AssemblyAI voice surface**; remittance “tools” are local Python functions the agent calls after each final turn. Those tools are shaped so they can be registered as Voice Agent tools later without rewriting product logic.

---

## Quick start (DEMO — no API key)

```bash
git clone https://github.com/Quantumwoof/voice-remit-ng.git
cd voice-remit-ng
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Smoke test (must pass offline)
DEMO_MODE=1 python smoke_test.py

# Streamlit demo UI
DEMO_MODE=1 streamlit run app.py

# CLI
DEMO_MODE=1 python cli.py "Compare fees for sending 300 dollars to Nigeria"
DEMO_MODE=1 python cli.py --list-demos
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Live mode (AssemblyAI)

```bash
cp .env.example .env
# Edit .env:
#   DEMO_MODE=0
#   ASSEMBLYAI_API_KEY=your_key_here

set -a && source .env && set +a
streamlit run app.py

# Optional: short mic session (needs pyaudio + PortAudio)
python cli.py --mic --seconds 12
```

Get a key at [assemblyai.com](https://www.assemblyai.com/). **Never commit `.env`.**

---

## Demo script for judges (≈3 minutes)

1. **Clone & smoke** — `DEMO_MODE=1 python smoke_test.py` → all intents green.
2. **Launch UI** — `DEMO_MODE=1 streamlit run app.py`.
3. **Fee compare** — select *“Compare fees for sending 300 dollars to Nigeria”* → show provider table (₦ received, all-in cost).
4. **FX check** — *“What's the dollar to naira rate right now?”* → mid-market mock + Nigeria tip on retail vs parallel rates.
5. **Send-now** — *“Should I send money now from London to Lagos?”* → Lagos-time banking window advice.
6. **Receive checklist** — *“Give me a checklist for receiving money in my GTBank account”* → NUBAN / BVN checklist.
7. **(Optional live)** — set `ASSEMBLYAI_API_KEY`, upload a short WAV, or `python cli.py --mic` to show Realtime STT.

Emphasize: **DEMO works offline**; live mode swaps mock STT for AssemblyAI without changing remittance tools.

---

## Project layout

```
voice-remit-ng/
├── app.py                 # Streamlit primary demo
├── cli.py                 # Optional CLI (+ --mic for live)
├── smoke_test.py          # DEMO_MODE regression
├── requirements.txt
├── .env.example
├── LICENSE                # MIT
├── docs/
│   ├── VoiceRemitNG-cover.png
│   └── VoiceRemitNG-slides.pdf
└── voice_remit/
    ├── agent.py           # Intent router
    ├── config.py          # DEMO_MODE / API key
    ├── stt/
    │   ├── mock.py
    │   └── assemblyai_live.py
    └── tools/
        └── remittance.py  # Fee · FX · send-now · checklist
```

## Remittance tools (Nigeria-focused)

| Tool | What it does |
| --- | --- |
| `fee_compare` | Illustrative all-in cost across major corridors; ranks by ₦ received |
| `fx_check` | Mock USD/NGN mid + Lagos timestamp + retail-rate tip |
| `send_now_advice` | Banking hours / weekend guidance in `Africa/Lagos` |
| `receive_checklist` | Bank / wallet / cash-pickup KYC & NUBAN checks |

Rates and fees are **hackathon mocks**, not live market data — not financial advice.

## Environment

| Variable | Meaning |
| --- | --- |
| `DEMO_MODE=1` | Mock STT (default if unset / no key) |
| `ASSEMBLYAI_API_KEY` | Enables live Realtime STT + file transcription |
| `ASSEMBLYAI_SPEECH_MODEL` | Optional streaming model override |

## License

MIT — see [LICENSE](LICENSE).
