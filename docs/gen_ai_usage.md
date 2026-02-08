# Generative AI Usage

**Yes**, we implemented multiple generative AI models and APIs to power the core experience of UW-Crushes.

## How we used them:

1.  **Google Gemini 1.5 Flash (via API):**
    *   **How:** We used Gemini as the primary "brain" for our agents. All user speech is transcribed and sent to Gemini, which generates the character's response in real-time.
    *   **Why:** We chose Gemini 1.5 Flash specifically for its **ultra-low latency** and **massive context window**. In a voice conversation, speed is everything; Gemini allows our agents to reply almost instantly, preventing the "awkward silence" typical of older chatbots. The large context window also lets the agent "remember" details from earlier in the date.

2.  **Rime.ai (TTS API):**
    *   **How:** We integrated Rime's text-to-speech engine to convert the AI's text into audio.
    *   **Why:** Standard TTS sounds robotic. Rime was essential because it supports **generative audio fillers** (like "um," "uh," "loading...") and **non-verbal sounds** (laughter, sighs). This is critical for a "dating" simulator where tone and emotion convey more than words.

3.  **Inflection AI (Pi-3.1 via Custom Integration):**
    *   **How:** We built a custom connector to Inflection's Pi model to handle specific "emotional" sub-routines.
    *   **Why:** Pi is known for its high Emotional Intelligence (EQ). We use it when the conversation turns serious or when the user needs "emotional support," allowing the agent to switch from "flirty/funny" to "genuinely supportive."

4.  **OpenAI Whisper (via LiveKit):**
    *   **How:** Used for real-time Speech-to-Text (STT).
    *   **Why:** To accurately transcribe the user's voice, including student slang and technical terms, into text that the LLMs can process.
