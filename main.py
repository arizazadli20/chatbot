"""
Psychological Research WhatsApp Bot (FastAPI + Twilio + Gemini 3.8 Flash)
========================================================================

HOW TO RUN:
1. Ensure your Gemini API Key is set in your terminal:
   export GEMINI_API_KEY="your_actual_api_key_here"

2. Install dependencies:
   pip install fastapi uvicorn python-multipart twilio google-genai

3. Start the FastAPI server with uvicorn:
   uvicorn main:app --reload --port 8000

4. Expose your local port via ngrok:
   ngrok http 8000

5. Configure Twilio WhatsApp Sandbox:
   - Go to Twilio Console -> Messaging -> Try it out -> Send a WhatsApp message.
   - In "Sandbox Settings", set "WHEN A MESSAGE COMES IN" to:
     URL: https://<your-ngrok-subdomain>.ngrok-free.app/chat
     HTTP Method: POST
"""

import os
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
from google.genai import types

# ==============================================================================
# 1. INITIALIZATION & SYSTEM PROMPT
# ==============================================================================
app = FastAPI(title="Psychological Research WhatsApp Bot")

# Initialize Gemini Client (reads GEMINI_API_KEY from environment)
client = genai.Client()

SYSTEM_PROMPT = """You are an empathetic, reflective virtual companion designed for daily 10-15 minute emotional check-ins. Your primary goal is to help users process their daily emotions, track mood changes, and practice self-reflection, serving as an accessible mental health tool for those who cannot attend traditional therapy.

CORE BEHAVIORS:
1. Daily Reflection Focus: Start conversations by gently asking how their day was or what their dominant emotion is right now. Encourage them to compare their current feelings to previous days.
2. Encouraging Self-Discovery: Instead of giving direct advice, use Socratic questioning. Ask "How did that make you feel?" or "What do you think is the root cause of that emotion?" to help them analyze their own thoughts.
3. Experience Tracking: Implicitly help them notice the value of the session. Use phrases like "As you write this out, how does it feel to put these thoughts into words?" to prepare them for our future research surveys about the AI vs. Therapy experience.
4. Pacing: Keep your responses concise and digestible. Do not overwhelm the user. End your turn with exactly ONE open-ended, thought-provoking question to keep the 15-minute session flowing.

STRICT BOUNDARIES:
1. AI Transparency: Clearly but gently remind them (when appropriate) that you are an AI self-reflection tool, NOT a replacement for a human therapist.
2. No Diagnosis: NEVER diagnose, label their condition, or prescribe treatments. Focus entirely on their emotional state in the present moment.

CRISIS PROTOCOL (SAFETY LAYER):
If the user mentions suicide, self-harm, or severe psychological breakdown, completely drop the conversational persona and output EXACTLY this text in Azerbaijani:
"Çox üzr istəyirəm ki, bu cür çətinliklərdən keçirsiniz. Bir süni intellekt olaraq mən psixoterapiyanı əvəz edə və sizə lazım olan təcili köməyi edə bilmərəm. Zəhmət olmasa dərhal 112 Fövqəladə Hallar nömrəsinə zəng edin və ya peşəkar dəstək alın. Həyatınız dəyərlidir və kömək almaq mümkündür."

LANGUAGE AND TONE:
You MUST communicate exclusively in Azerbaijani. Your tone should be extremely warm, patient, non-judgmental, and highly professional yet accessible."""

# ==============================================================================
# 2. IN-MEMORY SESSION MANAGEMENT
# ==============================================================================
# Maps sender phone number (e.g., 'whatsapp:+99450XXXXXXX') to active Gemini chat session
user_sessions: dict[str, any] = {}

def get_or_create_session(user_id: str):
    """Retrieves an existing chat session or creates a new one for a new user."""
    if user_id not in user_sessions:
        user_sessions[user_id] = client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
    return user_sessions[user_id]

# ==============================================================================
# 3. TWILIO WEBHOOK ENDPOINT
# ==============================================================================
@app.post("/chat")
def handle_incoming_whatsapp(
    Body: str = Form(default=""),
    From: str = Form(default="")
):
    """
    Twilio Webhook endpoint called on incoming WhatsApp messages.
    Parses 'Body' and 'From' from Twilio's POST request and returns TwiML XML.
    """
    incoming_text = Body.strip()
    sender_phone = From.strip()

    twiml_response = MessagingResponse()

    # Handle empty message payloads
    if not incoming_text:
        twiml_response.message("Zəhmət olmasa bir mesaj yazın.")
        return Response(content=str(twiml_response), media_type="application/xml")

    try:
        # Retrieve or initialize the user's isolated conversation session
        chat_session = get_or_create_session(sender_phone)

        # Generate complete non-streamed response for WhatsApp
        gemini_response = chat_session.send_message(incoming_text)
        reply_text = gemini_response.text.strip()

    except Exception as e:
        print(f"[API Error for {sender_phone}]: {e}")
        reply_text = (
            "Bağışlayın, sistemdə müvəqqəti xəta baş verdi. "
            "Zəhmət olmasa bir qədər sonra yenidən cəhd edin."
        )

    # Wrap reply in Twilio Messaging XML format
    twiml_response.message(reply_text)
    return Response(content=str(twiml_response), media_type="application/xml")

# ==============================================================================
# 4. HEALTH CHECK / ROOT ENDPOINT
# ==============================================================================
@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Psychological Research WhatsApp Bot (Twilio + Gemini 3.8 Flash)",
        "active_sessions": len(user_sessions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
