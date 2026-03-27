import streamlit as st
import requests
import io
import random

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Chordly",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── THEME ────────────────────────────────────────────────────────────────────

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark = st.session_state.dark_mode

BG        = "#0d0d12" if dark else "#f5f5f7"
SURFACE   = "#13131a" if dark else "#ffffff"
BORDER    = "#2a2a3a" if dark else "#e0e0e0"
TEXT      = "#e8e8f0" if dark else "#111111"
MUTED     = "#6b6b80" if dark else "#888888"
CARD_BG   = "#1a1a24" if dark else "#f0f0f5"

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif;
}}
.stApp {{
    background: {BG};
    color: {TEXT};
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0 1.5rem 1.5rem 1.5rem !important; max-width: 100% !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {SURFACE} !important;
    border-right: 1px solid {BORDER} !important;
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding: 1rem !important;
}}

/* Sidebar labels */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label {{
    color: {MUTED} !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
}}

/* Selectbox */
div[data-testid="stSelectbox"] > div > div {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-size: 0.95rem !important;
}}

/* Buttons */
.stButton > button {{
    background: {TEXT} !important;
    color: {BG} !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.9rem 1.5rem !important;
    width: 100% !important;
    height: 3.2rem !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.15s !important;
}}
.stButton > button:hover {{
    opacity: 0.85 !important;
}}

/* Top bar */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 0.75rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.2rem;
}}
.app-name {{
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: {TEXT};
    font-family: 'Space Grotesk', sans-serif;
}}
.app-name span {{
    color: #00e5ff;
}}

/* Model card */
.model-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}}
.model-tag {{
    font-size: 0.65rem;
    font-family: 'Space Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: {MUTED};
    margin-bottom: 4px;
}}
.model-desc {{
    font-size: 0.9rem;
    color: {MUTED};
    line-height: 1.5;
}}
.model-strength {{
    font-size: 0.8rem;
    margin-top: 6px;
    font-weight: 600;
}}

/* Stats */
.stats-row {{
    display: flex;
    gap: 10px;
    margin: 0.8rem 0;
}}
.stat-box {{
    flex: 1;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 0.7rem;
    text-align: center;
}}
.stat-value {{
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: {TEXT};
    line-height: 1;
}}
.stat-label {{
    font-size: 0.65rem;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 3px;
}}

/* Chord strip */
.chord-strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0.6rem 0;
}}
.chord-pill-major {{
    background: rgba(0,229,255,0.1);
    border: 1px solid rgba(0,229,255,0.3);
    color: #00e5ff;
    padding: 5px 12px;
    border-radius: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
}}
.chord-pill-minor {{
    background: rgba(167,139,250,0.1);
    border: 1px solid rgba(167,139,250,0.3);
    color: #a78bfa;
    padding: 5px 12px;
    border-radius: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
}}

/* Section label */
.slabel {{
    font-size: 0.65rem;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-family: 'Space Mono', monospace;
    margin-bottom: 0.4rem;
    margin-top: 0.8rem;
}}

/* Legend */
.legend {{
    display: flex;
    gap: 16px;
    margin-top: 0.4rem;
}}
.legend-item {{
    font-size: 0.75rem;
    color: {MUTED};
    display: flex;
    align-items: center;
    gap: 6px;
}}
.dot-major {{ width:8px; height:8px; border-radius:50%; background:#00e5ff; display:inline-block; }}
.dot-minor {{ width:8px; height:8px; border-radius:50%; background:#a78bfa; display:inline-block; }}

div[data-testid="stVerticalBlock"] > div {{ gap: 0.4rem; }}
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ───────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

MODELS = {
    'Genetic Algorithm': 'ga',
    'Markov Chain': 'markov',
    'LSTM': 'lstm',
}
MODEL_INFO = {
    'ga':     {'label': 'Genetic Algorithm', 'desc': 'Evolves progressions over generations using a music theory fitness function. No training data — pure theory.', 'strength': 'Theoretically sound', 'color': '#00e5ff'},
    'markov': {'label': 'Markov Chain',       'desc': 'Models chord transitions as conditional probabilities from observed sequences.', 'strength': 'Statistically authentic', 'color': '#ff6b35'},
    'lstm':   {'label': 'LSTM',               'desc': 'Learns deep sequential patterns using a recurrent neural network with long short-term memory.', 'strength': 'Context-aware generation', 'color': '#a78bfa'},
}

INSTRUMENTS  = ['piano', 'violin', 'guitar', 'flute', 'trumpet', 'organ']
KEYS         = ['C', 'G', 'D', 'A', 'E', 'F', 'Bb', 'Eb', 'c', 'g', 'd', 'a', 'e', 'f']
LENGTHS      = [16, 32, 48, 64]
DATASET_TYPES = ['no_repeats', 'repeats']

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{TEXT}; margin-bottom:1rem; padding-bottom:0.75rem; border-bottom:1px solid {BORDER};">⚙️ Configure</div>', unsafe_allow_html=True)

    model_display = st.selectbox("Model", list(MODELS.keys()))
    model_type    = MODELS[model_display]
    instrument    = st.selectbox("Instrument", INSTRUMENTS)
    key           = st.selectbox("Key", KEYS, help="Uppercase = major · lowercase = minor")
    length        = st.selectbox("Length", LENGTHS)
    dataset_type  = st.selectbox("Dataset", DATASET_TYPES)

    st.markdown("<br>", unsafe_allow_html=True)
    generate = st.button("🎹 Generate", type="primary")

# ─── TOP BAR ──────────────────────────────────────────────────────────────────

col_title, col_btns = st.columns([3, 1])
with col_title:
    st.markdown(f'<div class="topbar"><div class="app-name">Chord<span>ly</span></div></div>', unsafe_allow_html=True)

with col_btns:
    st.markdown("<div style='padding-top:0.85rem; display:flex; gap:8px;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⇄ Compare"):
            st.switch_page("pages/compare.py")
    with c2:
        toggle_label = "☀️" if dark else "🌙"
        if st.button(toggle_label):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── MODEL CARD ───────────────────────────────────────────────────────────────

info = MODEL_INFO[model_type]
st.markdown(f"""
<div class="model-card" style="border-left: 3px solid {info['color']};">
    <div class="model-tag">{info['label']}</div>
    <div class="model-desc">{info['desc']}</div>
    <div class="model-strength" style="color:{info['color']};">✦ {info['strength']}</div>
</div>
""", unsafe_allow_html=True)

# ─── OUTPUT ───────────────────────────────────────────────────────────────────

if generate:
    with st.spinner("Generating..."):
        try:
            response = requests.get(
                f"{API_BASE}/audio",
                params={"model_type": model_type, "key": key, "length": length,
                        "instrument": instrument, "dataset_type": dataset_type},
                timeout=60
            )
        except requests.exceptions.ConnectionError:
            response = None

    if response is None:
        st.error("Cannot connect to backend. Run: `python3 -m uvicorn main:app --reload`")
    elif response.status_code != 200:
        try:
            detail = response.json().get('detail', 'Unknown error')
        except:
            detail = response.text
        st.error(f"Error {response.status_code}: {detail}")
    else:
        # Audio player
        st.markdown(f'<div class="slabel">Audio</div>', unsafe_allow_html=True)
        st.audio(io.BytesIO(response.content), format="audio/wav")

        # Chord data — try /chords endpoint, fall back to simulated
        try:
            chord_resp = requests.get(
                f"{API_BASE}/chords",
                params={"model_type": model_type, "key": key,
                        "length": length, "dataset_type": dataset_type},
                timeout=30
            )
            chords = chord_resp.json().get("chords", []) if chord_resp.status_code == 200 else []
        except:
            chords = []

        # Fallback simulation
        if not chords:
            pool = ['i','ii','iii','iv','v','vi','vii'] if key[0].islower() else ['I','II','III','IV','V','VI','VII']
            random.seed(hash(f"{model_type}{key}{length}{dataset_type}"))
            chords = [random.choice(pool) for _ in range(length)]

        n_major = sum(1 for c in chords if c and c[0].isupper())
        n_minor = sum(1 for c in chords if c and c[0].islower())
        unique  = len(set(chords))

        # Stats
        st.markdown(f'<div class="slabel">Statistics</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box"><div class="stat-value">{length}</div><div class="stat-label">Chords</div></div>
            <div class="stat-box"><div class="stat-value">{unique}</div><div class="stat-label">Unique</div></div>
            <div class="stat-box"><div class="stat-value">{n_major}</div><div class="stat-label">Major</div></div>
            <div class="stat-box"><div class="stat-value">{n_minor}</div><div class="stat-label">Minor</div></div>
            <div class="stat-box"><div class="stat-value">{key}</div><div class="stat-label">Key</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Progression
        st.markdown(f'<div class="slabel">Progression</div>', unsafe_allow_html=True)
        pills = ""
        for c in chords:
            cls = "chord-pill-minor" if (c and c[0].islower()) else "chord-pill-major"
            pills += f'<div class="{cls}">{c}</div>'
        st.markdown(f"""
        <div class="chord-strip">{pills}</div>
        <div class="legend">
            <div class="legend-item"><span class="dot-major"></span> Major chord</div>
            <div class="legend-item"><span class="dot-minor"></span> Minor chord</div>
        </div>
        """, unsafe_allow_html=True)