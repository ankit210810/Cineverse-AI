"""AI Movie Assistant Page for Cineverse AI.

Features:
- Animated AI sparkle logo matching reference design
- Voice System (Speech-to-Text voice recognition + Text-to-Speech read-aloud)
- Direct hybrid AI recommendation query execution
- Interactive movie recommendation cards
"""

import streamlit as st
from ui.components import render_hero, render_movie_card, render_html
from services.assistant_service import get_assistant


def render_assistant_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    # Header with animated AI logo matching reference image
    render_html("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid rgba(140, 92, 255, 0.2);">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: linear-gradient(135deg, #0A1414 0%, #101F1E 100%); border: 1px solid rgba(255, 215, 0, 0.5); border-radius: 9999px; padding: 8px 18px; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 0 16px rgba(64, 217, 232, 0.3);">
                    <span class="ai-sparkle-animated" style="font-size: 1.2rem;">✨</span>
                    <span style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">Cineverse AI</span>
                </div>
                <div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF;">Conversational Cinematic Companion</div>
                    <div style="font-size: 0.85rem; color: #A0A5BA;">Powered by local Sequential Transformers & Bayesian Popularity</div>
                </div>
            </div>
            <div class="voice-wave-wrap" title="Voice System Ready">
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
            </div>
        </div>
    """)

    assistant = get_assistant()

    # Session chat history init
    if "assistant_messages" not in st.session_state:
        st.session_state["assistant_messages"] = [
            {
                "role": "assistant",
                "content": f"Hello {display_name}! I'm your Cineverse AI cinematic companion. Ask me with your voice or text for movie ideas, hidden gems, or specific moods tonight!",
                "movies": []
            }
        ]

    # Voice Input Bar
    v_col1, v_col2 = st.columns([1.2, 3])
    with v_col1:
        st.components.v1.html("""
            <div style="font-family: sans-serif; display: flex; align-items: center; gap: 8px;">
                <button id="micBtn" style="
                    background: linear-gradient(135deg, #1A1F38 0%, #25234A 100%);
                    border: 1px solid #40D9E8;
                    border-radius: 20px;
                    color: #FFFFFF;
                    padding: 8px 14px;
                    font-size: 12px;
                    font-weight: 700;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    box-shadow: 0 0 10px rgba(64, 217, 232, 0.3);
                ">
                    <span id="micIcon">🎙️</span> <span id="micLabel">Speak Prompt</span>
                </button>
                <span id="voiceStatus" style="font-size: 11px; color: #A0A5BA;"></span>
            </div>

            <script>
                const micBtn = document.getElementById('micBtn');
                const micLabel = document.getElementById('micLabel');
                const voiceStatus = document.getElementById('voiceStatus');
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

                if (!SpeechRecognition) {
                    micLabel.innerText = 'Voice Unsupported';
                    micBtn.disabled = true;
                } else {
                    const recognition = new SpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = 'en-US';
                    let isRecording = false;

                    micBtn.addEventListener('click', () => {
                        if (!isRecording) {
                            try {
                                recognition.start();
                                isRecording = true;
                                micBtn.style.background = 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)';
                                micLabel.innerText = 'Listening...';
                                voiceStatus.innerText = 'Speak now';
                            } catch (e) {
                                console.log(e);
                            }
                        } else {
                            recognition.stop();
                            isRecording = false;
                            micBtn.style.background = 'linear-gradient(135deg, #1A1F38 0%, #25234A 100%)';
                            micLabel.innerText = 'Speak Prompt';
                            voiceStatus.innerText = '';
                        }
                    });

                    recognition.onresult = (event) => {
                        const transcript = event.results[0][0].transcript;
                        voiceStatus.innerText = 'Heard: "' + transcript + '"';
                        isRecording = false;
                        micBtn.style.background = 'linear-gradient(135deg, #1A1F38 0%, #25234A 100%)';
                        micLabel.innerText = 'Speak Prompt';

                        try {
                            const parentDoc = window.parent.document;
                            const chatInputs = parentDoc.querySelectorAll('textarea, input[data-testid="stChatInputTextArea"]');
                            if (chatInputs && chatInputs.length > 0) {
                                const input = chatInputs[chatInputs.length - 1];
                                input.value = transcript;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.focus();
                            }
                        } catch(err) {
                            console.error('Parent dispatch error:', err);
                        }
                    };

                    recognition.onerror = (event) => {
                        voiceStatus.innerText = 'Error: ' + event.error;
                        isRecording = false;
                        micBtn.style.background = 'linear-gradient(135deg, #1A1F38 0%, #25234A 100%)';
                        micLabel.innerText = 'Speak Prompt';
                    };

                    recognition.onend = () => {
                        isRecording = false;
                        micBtn.style.background = 'linear-gradient(135deg, #1A1F38 0%, #25234A 100%)';
                        micLabel.innerText = 'Speak Prompt';
                    };
                }
            </script>
        """, height=44)

    with v_col2:
        st.caption("🎙️ **Voice System Online**: Tap 'Speak Prompt' to speak your query aloud, or click 🔊 Listen on any response.")

    # Quick Inquiries Chips
    render_html("<div style='font-size: 0.85rem; color: #A0A5BA; margin: 12px 0 8px 0;'>Quick Inquiries:</div>")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    prompt_to_submit = None
    with q_col1:
        if st.button("🍿 Recommend for tonight", use_container_width=True, key="btn_q1"):
            prompt_to_submit = "Recommend a movie for tonight."
    with q_col2:
        if st.button("🌀 Mind-bending like Inception", use_container_width=True, key="btn_q2"):
            prompt_to_submit = "Suggest a mind-bending thriller like Inception."
    with q_col3:
        if st.button("🚀 Epic Sci-Fi adventure", use_container_width=True, key="btn_q3"):
            prompt_to_submit = "Suggest an epic sci-fi adventure."
    with q_col4:
        if st.button("🛋️ Funny and relaxing", use_container_width=True, key="btn_q4"):
            prompt_to_submit = "Show me something funny and relaxing."

    # Render previous messages
    for idx, msg in enumerate(st.session_state["assistant_messages"]):
        with st.chat_message(msg["role"], avatar="✨" if msg["role"] == "assistant" else "👤"):
            st.write(msg["content"])

            # Voice output for AI messages
            if msg["role"] == "assistant":
                clean_speech_text = msg["content"].replace('"', '\\"').replace('\n', ' ')
                st.components.v1.html(f"""
                    <div style="display: flex; gap: 8px;">
                        <button onclick="
                            window.speechSynthesis.cancel();
                            const u = new SpeechSynthesisUtterance('{clean_speech_text[:280]}');
                            u.rate = 1.0;
                            u.pitch = 1.0;
                            window.speechSynthesis.speak(u);
                        " style="
                            background: rgba(140, 92, 255, 0.15);
                            border: 1px solid rgba(140, 92, 255, 0.4);
                            border-radius: 12px;
                            color: #D8C5FF;
                            padding: 4px 10px;
                            font-size: 11px;
                            cursor: pointer;
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                        ">
                            🔊 Listen
                        </button>
                        <button onclick="window.speechSynthesis.cancel();" style="
                            background: rgba(255, 255, 255, 0.05);
                            border: 1px solid rgba(255, 255, 255, 0.15);
                            border-radius: 12px;
                            color: #A0A5BA;
                            padding: 4px 8px;
                            font-size: 11px;
                            cursor: pointer;
                        ">
                            ⏹️ Stop
                        </button>
                    </div>
                """, height=30)

            if msg.get("movies"):
                cols = st.columns(min(len(msg["movies"]), 4))
                for i, m in enumerate(msg["movies"][:4]):
                    with cols[i]:
                        render_movie_card(m, user_id=user_id, show_explanation=False, key_prefix=f"chat_{idx}_{i}")

    # Chat Input
    user_input = st.chat_input("Ask Cineverse AI or use the microphone above...", key="main_assistant_chat_input")
    active_prompt = prompt_to_submit or user_input

    if active_prompt:
        st.session_state["assistant_messages"].append({
            "role": "user",
            "content": active_prompt
        })

        with st.spinner("Analyzing recommendations..."):
            res = assistant.answer_query(active_prompt, user_id=user_id)
            st.session_state["assistant_messages"].append({
                "role": "assistant",
                "content": res["intro"],
                "movies": res.get("movies", [])
            })

        st.rerun()

    st.caption("Engine Transparency: Cineverse AI assistant queries our local recommendation engines (Transformers, Matrix Factorization, and Bayesian Popularity) without relying on external third-party chat APIs.")
