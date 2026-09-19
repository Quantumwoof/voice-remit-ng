"""VoiceRemitNG — Streamlit demo UI (primary hackathon entrypoint)."""

from __future__ import annotations

import os

import streamlit as st

# Force demo unless user explicitly set live + key in env before launch.
os.environ.setdefault("DEMO_MODE", "1")

from voice_remit.agent import VoiceRemitAgent
from voice_remit.config import get_settings
from voice_remit.stt.factory import get_stt_backend
from voice_remit.stt.mock import MockSTT


st.set_page_config(
    page_title="VoiceRemitNG",
    page_icon="🇳🇬",
    layout="wide",
)

settings = get_settings()
stt = get_stt_backend(settings)
agent = VoiceRemitAgent()


def main() -> None:
    st.title("🇳🇬 VoiceRemitNG")
    st.caption(
        "AssemblyAI-powered voice / STT agent for Nigeria remittance help — "
        "lablab AssemblyAI Voice Agent Hackathon MVP"
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        mode = settings.mode_label
        if settings.demo_mode or not settings.assemblyai_api_key:
            st.info(f"**Mode:** {mode} — mock STT + remittance tools (no API key required).")
        else:
            st.success(f"**Mode:** {mode}")
        st.write(stt.describe())

    with col_b:
        st.metric("Corridor", "USD → NGN")
        st.metric("Focus", "Fees · FX · Timing · Receive")

    st.divider()

    left, right = st.columns([1, 1])

    with left:
        st.subheader("🎤 Talk to the agent")
        st.write(
            "Type what you'd say out loud, or pick a canned demo phrase. "
            "In live mode with `ASSEMBLYAI_API_KEY`, the same path accepts transcripts "
            "from AssemblyAI Realtime STT / file upload."
        )

        canned = MockSTT().canned_phrases()
        pick = st.selectbox("Demo phrase (judges)", ["— type your own —"] + canned)
        default_text = "" if pick.startswith("—") else pick
        user_text = st.text_area(
            "Your message (as if spoken)",
            value=default_text,
            height=100,
            placeholder="e.g. Compare fees for sending 500 dollars to my mum in Lagos",
        )

        uploaded = None
        if not settings.demo_mode and settings.assemblyai_api_key:
            uploaded = st.file_uploader(
                "Optional: upload audio for AssemblyAI prerecorded transcription",
                type=["wav", "mp3", "m4a", "ogg", "webm", "flac"],
            )

        go = st.button("Transcribe & advise", type="primary", use_container_width=True)

    with right:
        st.subheader("💡 Remittance answer")
        if "last_reply" not in st.session_state:
            st.session_state.last_reply = None

        if go:
            transcript = user_text.strip()
            source = stt.name

            if uploaded is not None and hasattr(stt, "transcribe_file"):
                import tempfile
                from pathlib import Path

                suffix = Path(uploaded.name).suffix or ".wav"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                try:
                    event = stt.transcribe_file(tmp_path)
                    transcript = event.text
                    source = event.source
                except Exception as exc:  # noqa: BLE001
                    st.error(f"AssemblyAI file transcription failed: {exc}")
                    transcript = transcript or ""
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

            if not transcript:
                st.warning("Enter a phrase or upload audio first.")
            else:
                event = stt.transcribe_text_input(transcript)
                reply = agent.route(event.text)
                st.session_state.last_reply = {
                    "source": source,
                    "reply": reply,
                }

        payload = st.session_state.last_reply
        if payload:
            reply = payload["reply"]
            st.markdown(f"**Heard ({payload['source']}):** _{reply.transcript}_")
            st.markdown(f"**Intent:** `{reply.intent}`")
            st.markdown(f"### {reply.tool.title}")
            st.markdown(reply.tool.summary)
            st.success(reply.spoken)
            st.caption(f"🇳🇬 {reply.tool.nigeria_tip}")

            details = reply.tool.details
            if "providers" in details:
                st.dataframe(details["providers"], use_container_width=True)
            elif "checklist" in details:
                for i, item in enumerate(details["checklist"], 1):
                    st.write(f"{i}. {item}")
            else:
                with st.expander("Raw tool details"):
                    st.json(details)
        else:
            st.write("Results appear here after you submit a phrase.")

    st.divider()
    with st.expander("How AssemblyAI is used"):
        st.markdown(
            """
**DEMO_MODE=1 (default):** Mock STT — no AssemblyAI calls.

**Live (`DEMO_MODE=0` + `ASSEMBLYAI_API_KEY`):**
1. **AssemblyAI Realtime Speech-to-Text** (`assemblyai.streaming.v3.RealTimeTranscriber`) —
   primary voice path for microphone streaming (CLI / optional mic).
2. **Prerecorded transcription** — Streamlit file upload → Universal model.
3. Intent routing is local (remittance tools). We document Realtime STT as the hackathon
   AssemblyAI surface; a full hosted Voice Agent loop can wrap the same tools later.

Default streaming speech model: `universal-streaming-multilingual` (Nigeria accents / code-switching).
            """
        )

    st.caption("MIT · VoiceRemitNG · Not financial advice — illustrative hackathon rates only.")


if __name__ == "__main__":
    main()
