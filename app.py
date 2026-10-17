import streamlit as st
import os
import json
import uuid
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types

# ==============================================================================
# FEATURE 4: BACKEND DATA ARCHITECTURE (SQLITE3)
# ==============================================================================
DB_PATH = "research_data.db"

def init_db():
    """Initializes SQLite database and creates the research sessions table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            initial_mood TEXT NOT NULL,
            chat_history TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_session(session_id: str, initial_mood: str, messages: list):
    """Saves or updates the session record with serialized chat history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        history_json = json.dumps(messages, ensure_ascii=False)
        cursor.execute("""
            INSERT INTO sessions (session_id, timestamp, initial_mood, chat_history)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                timestamp = excluded.timestamp,
                chat_history = excluded.chat_history
        """, (session_id, timestamp, initial_mood, history_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error]: {e}")

# Initialize database on startup
init_db()

# ==============================================================================
# PAGE CONFIGURATION & SYSTEM PROMPT
# ==============================================================================
st.set_page_config(
    page_title="Refleksiya Məkanı | Psixoloji Tədqiqat Platforması",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded"
)

SYSTEM_PROMPT = """You are an empathetic, reflective virtual companion designed for daily 10-15 minute emotional check-ins. Your primary goal is to help users process their daily emotions, track mood changes, and practice self-reflection, serving as an accessible mental health tool for those who cannot attend traditional therapy.

CORE BEHAVIORS:
1. Daily Reflection Focus: Start conversations by gently asking how their day was or what their dominant emotion is right now. Encourage them to compare their current feelings to previous days.
2. Encouraging Self-Discovery: Instead of giving direct advice, use Socratic questioning.
3. Pacing: Keep your responses concise. End your turn with exactly ONE open-ended question.

STRICT BOUNDARIES:
1. AI Transparency: Clearly but gently remind them that you are an AI, NOT a human therapist.
2. No Diagnosis: NEVER diagnose or prescribe treatments.

CRISIS PROTOCOL (SAFETY LAYER):
If the user mentions suicide or self-harm, stop regular conversation immediately and output EXACTLY this text in Azerbaijani:
"Çox üzr istəyirəm ki, bu cür çətinliklərdən keçirsiniz. Bir süni intellekt olaraq mən psixoterapiyanı əvəz edə və sizə lazım olan təcili köməyi edə bilmərəm. Zəhmət olmasa dərhal 112 Fövqəladə Hallar nömrəsinə zəng edin və ya peşəkar dəstək alın. Həyatınız dəyərlidir və kömək almaq mümkündür."

LANGUAGE:
ALWAYS reply in Azerbaijani. Be warm, patient, and non-judgmental."""

# ==============================================================================
# FEATURE 2: CUSTOM THERAPEUTIC UI (CSS)
# ==============================================================================
st.markdown("""
<style>
    /* =========================================================================
       1. HIDE UNNECESSARY STREAMLIT CHROME (NATIVE APP FEEL)
       ========================================================================= */
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    header[data-testid="stHeader"], header {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}

    /* =========================================================================
       2. VIEWPORT & CONTAINER: MAXIMIZE SCREEN REAL ESTATE ON MOBILE
       ========================================================================= */
    .stApp {
        background-color: #F8FAF9;
        color: #2D3748;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
        max-width: 760px;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.85rem !important;
            padding-bottom: 5.5rem !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
        }
    }

    /* =========================================================================
       3. MOOD TRACKER CARD & RESPONSIVE EMOJI BUTTONS
       ========================================================================= */
    .mood-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 28px 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #E8EFEA;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    @media (max-width: 768px) {
        .mood-card {
            padding: 22px 14px;
            margin-top: 10px;
            margin-bottom: 16px;
        }
    }

    /* Flexbox wrapper for 5 emoji columns with graceful wrapping */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        gap: 10px !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 calc(20% - 12px) !important;
        min-width: 62px !important;
        padding: 0 !important;
    }

    @media (max-width: 480px) {
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 calc(33.33% - 10px) !important;
            min-width: 76px !important;
        }
    }

    /* Emoji / Action buttons touch styling */
    div.stButton > button {
        border-radius: 16px !important;
        border: 1px solid #DCE6DF !important;
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        padding: 12px 6px !important;
        font-weight: 500 !important;
        min-height: 52px !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
        font-size: 0.95rem !important;
    }
    div.stButton > button:hover, div.stButton > button:active {
        border-color: #48BB78 !important;
        color: #22543D !important;
        background-color: #F0FFF4 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.12) !important;
    }

    /* =========================================================================
       4. MESSAGING APP CHAT BUBBLES (iMESSAGE / WHATSAPP FEEL)
       ========================================================================= */
    div[data-testid="stChatMessage"] {
        border-radius: 20px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid #E8ECE9 !important;
        background-color: #FFFFFF !important;
        max-width: 92% !important;
        word-break: break-word !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stChatMessage"] {
            padding: 12px 14px !important;
            border-radius: 18px !important;
            font-size: 0.95rem !important;
        }
    }

    /* Model (AI) messages: clean white/light-gray */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    div[data-testid="stChatMessage"]:has([aria-label*="model"]),
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #FFFFFF !important;
        border-color: #E8ECE9 !important;
        margin-right: auto !important;
        border-bottom-left-radius: 4px !important;
    }

    /* User messages: light therapeutic green/blue */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    div[data-testid="stChatMessage"]:has([aria-label*="user"]),
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #E7F6EC !important;
        border-color: #D3ECD9 !important;
        margin-left: auto !important;
        border-bottom-right-radius: 4px !important;
    }

    /* =========================================================================
       5. INPUT FIELD: ANCHORED AT BOTTOM & MOBILE KEYBOARD RESILIENT
       ========================================================================= */
    div[data-testid="stBottom"] {
        background-color: #F8FAF9 !important;
        padding-top: 8px !important;
        padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px)) !important;
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 100 !important;
    }

    div[data-testid="stChatInput"] {
        border-radius: 24px !important;
        border: 1px solid #DCE6DF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        background-color: #FFFFFF !important;
        margin-bottom: 4px !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: #48BB78 !important;
        box-shadow: 0 0 0 2px rgba(72, 187, 120, 0.18) !important;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #F3F7F4;
        border-right: 1px solid #E2ECE5;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "initial_mood" not in st.session_state:
    st.session_state.initial_mood = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# ==============================================================================
# FEATURE 3: RESEARCH & SURVEY SIDEBAR
# ==============================================================================
with st.sidebar:
    st.header("🌿 Tədqiqat və Məxfilik")
    st.markdown(
        """
        Bu platforma **10-15 dəqiqəlik gündəlik emosional refleksiya** 
        və özünüdərk üçün nəzərdə tutulmuş akademik araşdırma alətidir. 
        Məqsəd ənənəvi psixoterapiya ilə süni intellekt əsaslı refleksiya alətlərinin 
        təsirini və istifadəçi təcrübəsini müqayisə etməkdir.

        🔒 **Məxfilik Zəmanəti:**  
        Bütün toplanan məlumatlar **tamamilə anonimdir**. Heç bir ad, əlaqə vasitəsi 
        və ya şəxsi identifikasiya məlumatı yadda saxlanılmır.
        """
    )
    st.divider()

    st.markdown(
        f"""
        **Anonim Sessiya ID:**  
        `{st.session_state.session_id[:8]}...`  

        **Qeydə Alınmış Əhval:**  
        *{st.session_state.initial_mood if st.session_state.initial_mood else "Hələ seçilməyib"}*
        """
    )
    st.divider()

    st.link_button(
        "📝 Təcrübəni Bölüş",
        "https://forms.gle/placeholder_research_survey",
        use_container_width=True,
        help="Sessiyanı tamamladıqdan sonra təcrübənizi bölüşərək elmi məqaləmizə dəstək olun."
    )

    if st.session_state.initial_mood:
        st.write("")
        if st.button("🔄 Yeni Sessiya Başlat", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.initial_mood = None
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.rerun()

# ==============================================================================
# FEATURE 1: PRE-CHAT MOOD TRACKER & CONDITIONAL CHAT UNLOCK
# ==============================================================================
if st.session_state.initial_mood is None:
    st.markdown(
        """
        <div class="mood-card">
            <h1 style="font-size: 2.2rem; margin-bottom: 8px;">🌱 Xoş Gəlmisiniz</h1>
            <p style="color: #718096; font-size: 1.15rem; margin-top: 0; margin-bottom: 24px;">
                Gündəlik emosional check-in və özünüdərk məkanı
            </p>
            <h3 style="color: #2D3748; font-weight: 600; margin-bottom: 12px;">
                Bu gün özünüzü necə hiss edirsiniz?
            </h3>
            <p style="color: #A0AEC0; font-size: 0.95rem; margin-bottom: 8px;">
                Söhbətə başlamaq üçün hisslərinizi ən yaxşı ifadə edən emojini seçin:
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5 emoji buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    mood_buttons = [
        (col1, "😢", "Kədərli", "😢 Kədərli"),
        (col2, "😕", "Narahat", "😕 Narahat"),
        (col3, "😐", "Neytral", "😐 Neytral"),
        (col4, "🙂", "Yaxşı", "🙂 Yaxşı"),
        (col5, "🤩", "Əla", "🤩 Əla"),
    ]

    for col, emoji_icon, label, mood_key in mood_buttons:
        with col:
            if st.button(f"{emoji_icon}\n\n{label}", use_container_width=True, key=f"btn_{label}"):
                st.session_state.initial_mood = mood_key

                # Initialize Gemini chat session with required model & system prompt
                try:
                    client = genai.Client()
                    st.session_state.client = client
                    st.session_state.chat_session = client.chats.create(
                        model="gemini-3.8-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )

                    # Hidden first prompt: passes initial mood for AI contextualization
                    hidden_context_prompt = (
                        f"[SİSTEM KONTEKSTİ]: İstifadəçi bu gün öz əhvalını belə qiymətləndirdi: '{mood_key}'. "
                        f"Zəhmət olmasa bu hissi empatiya və anlayışla qarşıla, "
                        f"gününün necə keçdiyini soruşaraq zərif və dəstəkləyici şəkildə söhbətə başla."
                    )
                    opening_response = st.session_state.chat_session.send_message(hidden_context_prompt)
                    st.session_state.messages.append({"role": "model", "content": opening_response.text.strip()})

                    # Persist initial session record to SQLite
                    save_session(
                        st.session_state.session_id,
                        st.session_state.initial_mood,
                        st.session_state.messages
                    )
                    st.rerun()

                except Exception as e:
                    st.error(f"Bağlantı xətası: {e}. Zəhmət olmasa 'export GEMINI_API_KEY' mühit dəyişənini yoxlayın.")

# ==============================================================================
# CHAT INTERFACE & ZERO-LATENCY STREAMING
# ==============================================================================
else:
    st.markdown("<h2 style='margin-bottom: 2px;'>🌿 Virtual Refleksiya Yoldaşı</h2>", unsafe_allow_html=True)
    st.caption(f"Bugünkü qeydə alınmış əhvalınız: **{st.session_state.initial_mood}** • Bura sizin üçün təhlükəsiz və mühakiməsiz məkandır.")

    # Render ongoing conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input & word-by-word streaming generator logic
    if prompt := st.chat_input("Düşüncələrinizi və ya hisslərinizi bölüşün..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("model"):
            try:
                # Use send_message_stream for word-by-word generation
                response_stream = st.session_state.chat_session.send_message_stream(prompt)

                # Generator to yield text chunks for Streamlit
                def stream_data():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text

                # Write stream to the UI and capture the full response
                full_response = st.write_stream(stream_data())

                # Append the completed message to the session history
                st.session_state.messages.append({"role": "model", "content": full_response})

                # Automatically persist updated conversation to SQLite
                save_session(
                    st.session_state.session_id,
                    st.session_state.initial_mood,
                    st.session_state.messages
                )

            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")
