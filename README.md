# Psychological Research Virtual Companion Chatbot

An empathetic, reflective AI companion designed for daily 10-15 minute emotional check-ins and academic research, comparing AI-guided self-reflection to traditional psychotherapy. Built with Google Gemini 3.8 Flash and communicating strictly in Azerbaijani.

## Project Structure

- `app.py`: Streamlit-based web platform with a mobile-first UI, pre-chat mood tracker, research survey sidebar, real-time response streaming, and SQLite anonymous session logging.
- `main.py`: FastAPI backend acting as a Twilio Webhook to deploy the companion as a 24/7 WhatsApp bot.
- `chatbot.py`: Terminal-based interactive chat interface for quick local testing.
- `requirements.txt`: Python dependencies.

## Key Features

1. **Pre-Chat Mood Tracker**: Evaluates user state (`😢`, `😕`, `😐`, `🙂`, `🤩`) before starting the session and contextually primes the AI's greeting.
2. **Mobile-First Responsive UI**: Styled like native messaging apps (iMessage/WhatsApp) with pastel aesthetics and keyboard-resilient layout.
3. **Research Data Architecture**: Automatically logs anonymous sessions (`session_id`, `timestamp`, `initial_mood`, and serialized `chat_history`) into `research_data.db` (SQLite).
4. **Safety & Crisis Protocol**: Built-in emergency pivot in Azerbaijani directing users to the 112 Emergency Hotline upon detecting crisis keywords.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Gemini API Key
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. Run Applications

- **Streamlit Web Platform**:
  ```bash
  streamlit run app.py
  ```

- **WhatsApp Bot (FastAPI + Twilio)**:
  ```bash
  uvicorn main:app --reload --port 8000
  ```

- **CLI Terminal Chat**:
  ```bash
  python3 chatbot.py
  ```
