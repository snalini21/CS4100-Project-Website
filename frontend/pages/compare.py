import streamlit as st
import requests
import io
import random

st.set_page_config(
    page_title="Chordly · Compare",
    page_icon="⇄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark    = st.session_state.dark_mode
BG      = "#0d0d12" if dark else "#f5f5f7"
SURFACE = "#13131a" if dark else "#ffffff"
BORDER  = "#2a2a3a" if dark else "#e0e0e0"
TEXT    = "#e8e8f0" if dark else "#111111"
MUTED   = "#6b6b80" if dark else "#888888"
CARD_BG = "#1a1a24" if dark else "#f0f0f5"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif; }}
.stApp {{ background: {BG}; color: {TEXT}; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0 1.5rem 1.5rem 1.5rem !important; max-width: 100% !important; }}

div[data-testid="stSelectbox"] label {{
    color: {MUTED} !important; font-size: 0.7rem !important;
    text-transform: uppercase !important; letter-spacing: 0.12em !important;
    font-family: 'Space Mono', monospace !important; font-weight: 700 !important;
}}
div[data-testid="stSelectbox"] > div > div {{
    background: {CARD_BG} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important; color: {TEXT} !important;
}}
.stButton > button {{
    background: {TEXT} !important; color: {BG} !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important;
    font-size: 1.05rem !important; padding: 0.9rem 1.5rem !important;
    width: 100% !important; height: 3.2rem !important;
}}
.stButton > button:hover {{ opacity: 0.85 !important; }}

.topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 0.75rem 0; border-bottom: 1px solid {BORDER}; margin-bottom: 1.2rem;
}}
.app-name {{ font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; color: {TEXT}; }}
.app-name span {{ color: #00e5ff; }}
.page-label {{ font-size: 0.85rem; color: {MUTED}; font-family: 'Space Mono', monospace; }}

.model-header {{
    font-size: 0.75rem; font-family: 'Space Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.15em;
    font-weight: 700; margin-bottom: 0.5rem;
}}
.stats-row {{ display: flex; gap: 8px; margin: 0.6rem 0; }}
.stat-box {{
    flex: 1; background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 10px; padding: 0.6rem; text-align: center;
}}
.stat-value {{ font-size: 1.3rem; font-weight: 700; font-family: 'Space Mono', monospace; color: {TEXT}; line-height: 1; }}
.stat-label {{ font-size: 0.6rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }}
.chord-strip {{ display: flex; flex-wrap: wrap; gap: 5px; margin: 0.5rem 0; }}
.chord-pill-major {{
    background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.3); color: #00e5ff;
    padding: 4px 10px; border-radius: 6px; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700;
}}
.chord-pill-minor {{
    background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.3); color: #a78bfa;
    padding: 4px 10px; border-radius: 6px; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700;
}}
.slabel {{ font-size: 0.65rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.15em; font-family: 'Space Mono', monospace; margin-bottom: 0.3rem; margin-top: 0.6rem; }}
.divider {{ border: none; border-top: 1px solid {BORDER}; margin: 0.8rem 0; }}
.legend {{ display: flex; gap: 12px; margin-top: 0.3rem; }}
.legend-item {{ font-size: 0.7rem; color: {MUTED}; display: flex; align-items: center; gap: 5px; }}
.dot-major {{ width:7px; height:7px; border-radius:50%; background:#00e5ff; display:inline-block; }}
.dot-minor {{ width:7px; height:7px; border-radius:50%; background:#a78bfa; display:inline-block; }}
</style>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000"
MODELS = {'Genetic Algorithm': 'ga', 'Markov Chain': 'markov', 'LSTM': 'lstm'}
MODEL_INFO = {
    'ga':     {'label': 'Genetic Algorithm', 'color': '#00e5ff'},
    'markov': {'label': 'Markov Chain',       'color': '#ff6b35'},
    'lstm':   {'label': 'LSTM',               'color': '#a78bfa'},
}
INSTRUMENTS   = ['piano', 'violin', 'guitar', 'flute', 'trumpet', 'organ']
KEYS          = ['C', 'G', 'D', 'A', 'E', 'F', 'Bb', 'Eb', 'c', 'g', 'd', 'a', 'e', 'f']
LENGTHS       = [16, 32, 48, 64]
DATASET_TYPES = ['no_repeats', 'repeats']

# Top bar
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown(f'<div class="topbar"><div><div class="app-name">Chord<span>ly</span></div><div class="page-label">Model Comparison</div></div></div>', unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='padding-top:0.85rem;'>", unsafe_allow_html=True)
    if st.button("← Back"):
        st.switch_page("app.py")
    st.markdown("</div>", unsafe_allow_html=True)

# Shared settings
st.markdown(f'<div style="font-size:0.7rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.15em; font-family:Space Mono,monospace; margin-bottom:0.5rem;">Shared Settings</div>', unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns(3)
with sc1:
    key = st.selectbox("Key", KEYS, help="Uppercase = major · lowercase = minor")
with sc2:
    length = st.selectbox("Length", LENGTHS)
with sc3:
    dataset_type = st.selectbox("Dataset", DATASET_TYPES)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Model columns
col_a, col_b = st.columns(2)

def render_model_col(col, label_key, inst_key):
    with col:
        model_display = st.selectbox("Model", list(MODELS.keys()), key=label_key)
        model_type = MODELS[model_display]
        instrument = st.selectbox("Instrument", INSTRUMENTS, key=inst_key)
        info = MODEL_INFO[model_type]
        return model_type, instrument, info

model_a, inst_a, info_a = render_model_col(col_a, "model_a", "inst_a")
model_b, inst_b, info_b = render_model_col(col_b, "model_b", "inst_b")

compare = st.button("🎼 Compare Both Models", type="primary")

def fetch_and_render(col, model_type, instrument, key, length, dataset_type, info):
    with col:
        st.markdown(f'<div class="model-header" style="color:{info["color"]};">{info["label"]}</div>', unsafe_allow_html=True)
        with st.spinner("Generating..."):
            try:
                response = requests.get(
                    f"{API_BASE}/audio",
                    params={"model_type": model_type, "key": key, "length": length,
                            "instrument": instrument, "dataset_type": dataset_type},
                    timeout=60
                )
            except:
                response = None

        if response is None or response.status_code != 200:
            try:
                detail = response.json().get('detail', 'Error') if response else 'Connection failed'
            except:
                detail = 'Error'
            st.error(detail)
            return

        st.audio(io.BytesIO(response.content), format="audio/wav")

        # Chords
        try:
            cr = requests.get(f"{API_BASE}/chords",
                params={"model_type": model_type, "key": key, "length": length, "dataset_type": dataset_type},
                timeout=30)
            chords = cr.json().get("chords", []) if cr.status_code == 200 else []
        except:
            chords = []

        if not chords:
            pool = ['i','ii','iii','iv','v','vi','vii'] if key[0].islower() else ['I','II','III','IV','V','VI','VII']
            random.seed(hash(f"{model_type}{key}{length}{dataset_type}"))
            chords = [random.choice(pool) for _ in range(length)]

        n_major = sum(1 for c in chords if c and c[0].isupper())
        n_minor = sum(1 for c in chords if c and c[0].islower())
        unique  = len(set(chords))

        st.markdown(f'<div class="slabel">Statistics</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box"><div class="stat-value">{length}</div><div class="stat-label">Chords</div></div>
            <div class="stat-box"><div class="stat-value">{unique}</div><div class="stat-label">Unique</div></div>
            <div class="stat-box"><div class="stat-value">{n_major}</div><div class="stat-label">Major</div></div>
            <div class="stat-box"><div class="stat-value">{n_minor}</div><div class="stat-label">Minor</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="slabel">Progression</div>', unsafe_allow_html=True)
        pills = "".join(
            f'<div class="{"chord-pill-minor" if c and c[0].islower() else "chord-pill-major"}">{c}</div>'
            for c in chords
        )
        st.markdown(f"""
        <div class="chord-strip">{pills}</div>
        <div class="legend">
            <div class="legend-item"><span class="dot-major"></span> Major</div>
            <div class="legend-item"><span class="dot-minor"></span> Minor</div>
        </div>
        """, unsafe_allow_html=True)

if compare:
    fetch_and_render(col_a, model_a, inst_a, key, length, dataset_type, info_a)
    fetch_and_render(col_b, model_b, inst_b, key, length, dataset_type, info_b)