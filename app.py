"""
Sistema de Triage y Flujo de Sala de Urgencias
Frontend : Streamlit
Backend  : Python — Escala de Manchester (MTS)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime

from backend import (
    Patient, VitalSigns, TriageLevel, PatientStatus,
    TRIAGE_CONFIG, HospitalQueue
)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="TriageER — Sistema de Urgencias",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "queue" not in st.session_state:
    st.session_state.queue = HospitalQueue()
if "discharge_notes" not in st.session_state:
    st.session_state.discharge_notes = {}

queue: HospitalQueue = st.session_state.queue

# ══════════════════════════════════════════════════════════
# SVG ICONS
# ══════════════════════════════════════════════════════════

ICONS = {
    "hospital":    '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/><line x1="12" y1="5" x2="12" y2="9"/><line x1="10" y1="7" x2="14" y2="7"/></svg>',
    "user":        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "clock":       '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "alert":       '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "alert_sm":    '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "heart":       '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "activity":    '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "thermometer": '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
    "droplet":     '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    "wind":        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>',
    "check":       '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "search":      '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "bar_chart":   '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>',
    "file":        '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "users":       '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "hourglass":   '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></svg>',
    "stethoscope": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></svg>',
    "archive":     '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>',
    "avg_wait":    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
}

TRIAGE_COLORS = {
    1: {"color": "#DC2626", "label": "Inmediato"},
    2: {"color": "#EA580C", "label": "Muy Urgente"},
    3: {"color": "#CA8A04", "label": "Urgente"},
    4: {"color": "#16A34A", "label": "Poco Urgente"},
    5: {"color": "#2563EB", "label": "No Urgente"},
}

def triage_dot(color: str, size: int = 9) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="5" fill="{color}"/></svg>'

# ══════════════════════════════════════════════════════════
# CSS — Azul y blanco, semántico, responsive, VisBug-ready
# ══════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --blue-900:#1e3a5f; --blue-800:#1e40af; --blue-700:#1d4ed8;
    --blue-600:#2563eb; --blue-500:#3b82f6; --blue-400:#60a5fa;
    --blue-100:#dbeafe; --blue-50:#eff6ff;
    --white:#ffffff;
    --gray-50:#f8fafc;  --gray-100:#f1f5f9; --gray-200:#e2e8f0;
    --gray-400:#94a3b8; --gray-600:#475569; --gray-800:#1e293b;
    --red:#DC2626; --orange:#EA580C; --yellow:#CA8A04; --green:#16A34A;
    --shadow-sm:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.05);
    --shadow-md:0 4px 12px rgba(0,0,0,.08),0 2px 4px rgba(0,0,0,.05);
    --radius:10px; --radius-sm:6px;
}

html, body, [class*="css"] {
    font-family:'Inter',system-ui,sans-serif !important;
    background-color:var(--gray-50) !important;
    color:var(--gray-800) !important;
}
.stApp { background-color:var(--gray-50) !important; }
h1,h2,h3,h4 { font-family:'Inter',sans-serif; font-weight:700; color:var(--blue-900); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color:var(--blue-900) !important;
    border-right:none !important;
    box-shadow:2px 0 12px rgba(0,0,0,.15) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color:rgba(255,255,255,.9) !important; }
[data-testid="stSidebar"] label { color:rgba(255,255,255,.7) !important; font-size:.82rem !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background:rgba(255,255,255,.1) !important;
    border:1px solid rgba(255,255,255,.2) !important;
    color:var(--white) !important;
    border-radius:var(--radius-sm) !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder { color:rgba(255,255,255,.4) !important; }

.sidebar-logo {
    display:flex; align-items:center; gap:12px;
    padding:18px 4px 22px;
    border-bottom:1px solid rgba(255,255,255,.15);
    margin-bottom:18px;
}
.sidebar-logo-icon {
    width:40px; height:40px; background:var(--blue-600);
    border-radius:10px; display:flex; align-items:center;
    justify-content:center; flex-shrink:0; color:var(--white);
}
.sidebar-logo-title { font-weight:700; font-size:.95rem; color:var(--white); line-height:1.2; }
.sidebar-logo-sub   { font-size:.68rem; color:rgba(255,255,255,.55); }
.sidebar-section-label {
    font-size:.65rem; font-weight:600; text-transform:uppercase;
    letter-spacing:.1em; color:rgba(255,255,255,.45);
    margin-bottom:8px; margin-top:4px;
}

/* ── Section label ── */
.section-label {
    font-size:.7rem; font-weight:600; text-transform:uppercase;
    letter-spacing:.08em; color:var(--gray-400);
    margin-bottom:10px; padding-bottom:6px;
    border-bottom:1px solid var(--gray-200);
    display:flex; align-items:center; gap:6px;
}

/* ── Main header card ── */
.main-header {
    background:var(--white); border:1px solid var(--gray-200);
    border-radius:var(--radius); padding:18px 22px;
    margin-bottom:18px; box-shadow:var(--shadow-sm);
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:12px;
}
.main-header-left { display:flex; align-items:center; gap:14px; }
.main-header-icon {
    width:46px; height:46px; background:var(--blue-600);
    border-radius:12px; display:flex; align-items:center;
    justify-content:center; flex-shrink:0; color:var(--white);
}
.main-title    { font-size:1.35rem; font-weight:800; color:var(--blue-900); margin:0; line-height:1.2; }
.main-subtitle { font-size:.76rem; color:var(--gray-400); margin-top:2px; }

/* ── Service status badge ── */
.status-badge {
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 12px; border-radius:20px;
    font-size:.74rem; font-weight:600;
}
.status-normal  { background:#dcfce7; color:#15803d; }
.status-alto    { background:#fef9c3; color:#854d0e; }
.status-critico { background:#fef2f2; color:var(--red); }

/* ── Alert banners ── */
.alert-critical {
    background:#fef2f2; border:1.5px solid var(--red);
    border-radius:var(--radius); padding:14px 18px;
    margin-bottom:16px;
    display:flex; align-items:flex-start; gap:12px;
    animation:pulse-alert 2s ease-in-out infinite;
}
.alert-critical-icon  { color:var(--red); flex-shrink:0; margin-top:1px; }
.alert-critical-title { font-weight:700; color:var(--red); font-size:.88rem; }
.alert-critical-body  { font-size:.8rem; color:#7f1d1d; margin-top:3px; }
.alert-service {
    background:#fffbeb; border:1px solid #ca8a04;
    border-radius:var(--radius); padding:11px 16px;
    margin-bottom:16px;
    display:flex; align-items:center; gap:10px;
    font-size:.84rem; font-weight:500; color:#78350f;
}
@keyframes pulse-alert {
    0%,100% { box-shadow:0 0 0 0 rgba(220,38,38,.2); }
    50%      { box-shadow:0 0 0 6px rgba(220,38,38,0); }
}

/* ── Metric row ── */
.metric-row { display:flex; gap:12px; margin-bottom:18px; flex-wrap:wrap; }
.metric-card {
    flex:1 1 130px; background:var(--white);
    border:1px solid var(--gray-200); border-radius:var(--radius);
    padding:16px 18px; box-shadow:var(--shadow-sm);
    position:relative; overflow:hidden; min-width:110px;
}
.metric-card-accent {
    position:absolute; top:0; left:0; right:0; height:3px;
    background:var(--blue-600);
}
.metric-card-icon {
    width:34px; height:34px; background:var(--blue-50);
    border-radius:8px; display:flex; align-items:center;
    justify-content:center; margin-bottom:8px; color:var(--blue-600);
}
.metric-value {
    font-family:'JetBrains Mono',monospace;
    font-size:1.9rem; font-weight:700; color:var(--blue-900); line-height:1;
}
.metric-label {
    font-size:.7rem; font-weight:500; color:var(--gray-400);
    text-transform:uppercase; letter-spacing:.06em; margin-top:4px;
}

/* ── Triage distribution ── */
.triage-bar-wrap { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.triage-bar-item {
    flex:1 1 90px; background:var(--white);
    border:1px solid var(--gray-200); border-radius:var(--radius);
    padding:12px 14px; box-shadow:var(--shadow-sm);
    display:flex; align-items:center; gap:10px;
}
.triage-dot-lg { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.triage-bar-count {
    font-family:'JetBrains Mono',monospace;
    font-size:1.4rem; font-weight:700;
}
.triage-bar-name { font-size:.68rem; color:var(--gray-400); margin-top:1px; }

/* ── Chart card ── */
.chart-card {
    background:var(--white); border:1px solid var(--gray-200);
    border-radius:var(--radius); padding:18px 20px;
    box-shadow:var(--shadow-sm); margin-bottom:18px;
}
.chart-title {
    font-size:.82rem; font-weight:700; color:var(--blue-900);
    margin-bottom:12px; display:flex; align-items:center; gap:7px;
}

/* ── Patient cards ── */
.patient-card {
    background:var(--white); border:1px solid var(--gray-200);
    border-left:4px solid; border-radius:var(--radius);
    padding:15px 18px; margin-bottom:10px;
    box-shadow:var(--shadow-sm);
    transition:box-shadow .15s ease;
}
.patient-card:hover { box-shadow:var(--shadow-md); }
.patient-card-header {
    display:flex; justify-content:space-between;
    align-items:flex-start; flex-wrap:wrap; gap:8px;
}
.patient-name     { font-weight:700; font-size:.98rem; color:var(--gray-800);
                     display:flex; align-items:center; gap:5px; }
.patient-meta     { font-size:.8rem; color:var(--gray-400); margin-top:2px; }
.patient-complaint{ font-size:.86rem; color:var(--gray-600); margin-top:6px; }
.patient-footer   { display:flex; align-items:center; gap:14px; margin-top:7px; flex-wrap:wrap; }
.patient-time     { font-size:.76rem; color:var(--gray-400);
                     display:flex; align-items:center; gap:4px; }
.patient-wait     { font-family:'JetBrains Mono',monospace; font-weight:600; color:var(--gray-800); }
.triage-badge {
    display:inline-flex; align-items:center; gap:5px;
    padding:3px 10px; border-radius:20px;
    font-size:.71rem; font-weight:600; white-space:nowrap;
}
.patient-id {
    font-family:'JetBrains Mono',monospace; font-size:.68rem;
    color:var(--gray-400); background:var(--gray-100);
    padding:2px 7px; border-radius:4px;
}
.overdue-tag {
    background:#fef2f2; border:1px solid #fca5a5;
    border-radius:var(--radius-sm); padding:5px 10px;
    font-size:.76rem; font-weight:600; color:var(--red);
    display:flex; align-items:center; gap:5px; margin-top:8px;
}

/* ── Vital signs ── */
.vitals-grid {
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(90px,1fr));
    gap:7px; margin-top:10px;
}
.vital-item {
    background:var(--gray-50); border:1px solid var(--gray-100);
    border-radius:var(--radius-sm); padding:7px 8px; text-align:center;
}
.vital-value {
    font-family:'JetBrains Mono',monospace;
    font-size:.95rem; font-weight:700; color:var(--blue-700);
}
.vital-label {
    font-size:.6rem; font-weight:500; color:var(--gray-400);
    text-transform:uppercase; letter-spacing:.04em;
    display:flex; align-items:center; justify-content:center;
    gap:3px; margin-top:2px;
}

/* ── Empty state ── */
.empty-state { text-align:center; padding:48px 20px; color:var(--gray-400); }
.empty-state-icon { margin-bottom:10px; }
.empty-state-text { font-size:.88rem; }

/* ── Inputs ── */
.stTextInput input,.stNumberInput input,
.stSelectbox select,.stTextArea textarea {
    border:1px solid var(--gray-200) !important;
    border-radius:var(--radius-sm) !important;
    background:var(--white) !important;
    color:var(--gray-800) !important;
    font-size:.87rem !important;
}
.stTextInput input:focus,.stNumberInput input:focus,
.stTextArea textarea:focus {
    border-color:var(--blue-500) !important;
    box-shadow:0 0 0 3px rgba(59,130,246,.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius:var(--radius-sm) !important;
    font-weight:600 !important; font-size:.82rem !important;
    transition:all .15s !important;
    border:1px solid var(--gray-200) !important;
    background:var(--white) !important; color:var(--gray-800) !important;
}
.stButton > button:hover {
    border-color:var(--blue-400) !important; color:var(--blue-700) !important;
}
.stButton > button[kind="primary"] {
    background:var(--blue-600) !important;
    border-color:var(--blue-600) !important;
    color:var(--white) !important;
}
.stButton > button[kind="primary"]:hover { background:var(--blue-700) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:var(--white) !important;
    border:1px solid var(--gray-200) !important;
    border-radius:var(--radius) !important;
    padding:4px !important; gap:4px !important;
    box-shadow:var(--shadow-sm) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius:var(--radius-sm) !important;
    font-size:.82rem !important; font-weight:500 !important;
    color:var(--gray-600) !important; padding:8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background:var(--blue-600) !important; color:var(--white) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu,footer,header { visibility:hidden; }

/* ── Responsive ── */
@media (max-width:768px) {
    .metric-row { gap:8px; }
    .metric-card { padding:12px 14px; }
    .metric-value { font-size:1.5rem; }
    .triage-bar-wrap { gap:6px; }
    .patient-card { padding:12px 14px; }
    .main-title { font-size:1.1rem; }
    .vitals-grid { grid-template-columns:repeat(2,1fr); }
    .main-header { padding:14px 16px; }
}
@media (max-width:480px) {
    .triage-bar-wrap,.metric-row { flex-direction:column; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

def service_load_status(stats: dict) -> tuple:
    n1 = stats["triage_distribution"].get(1, {}).get("count", 0)
    n2 = stats["triage_distribution"].get(2, {}).get("count", 0)
    w  = stats["waiting"]
    if n1 >= 2 or (n1 >= 1 and n2 >= 2):
        return "status-critico", "Carga CRÍTICA"
    if w >= 5 or n2 >= 2:
        return "status-alto", "Carga ALTA"
    return "status-normal", "Carga Normal"


def render_vitals_html(vs: VitalSigns) -> str:
    items = []
    if vs.heart_rate:
        items.append((f"{vs.heart_rate}", "bpm", ICONS["heart"]))
    if vs.systolic_bp:
        bp = f"{vs.systolic_bp}/{vs.diastolic_bp or '?'}"
        items.append((bp, "mmHg", ICONS["droplet"]))
    if vs.temperature:
        items.append((f"{vs.temperature}°", "Temp", ICONS["thermometer"]))
    if vs.oxygen_saturation:
        items.append((f"{vs.oxygen_saturation}%", "SpO2", ICONS["activity"]))
    if vs.respiratory_rate:
        items.append((f"{vs.respiratory_rate}", "rpm", ICONS["wind"]))
    if vs.pain_level > 0:
        items.append((f"{vs.pain_level}/10", "Dolor", ICONS["alert_sm"]))
    if not items:
        return ""
    html = '<div class="vitals-grid">'
    for val, lbl, icon in items:
        html += f'<div class="vital-item"><div class="vital-value">{val}</div><div class="vital-label">{icon} {lbl}</div></div>'
    html += "</div>"
    return html


def render_patient_card(patient: Patient, stats: dict, show_actions: bool = True):
    level = patient.triage_level.value if patient.triage_level else 5
    tc    = TRIAGE_COLORS.get(level, TRIAGE_COLORS[5])
    color = tc["color"]
    label = tc["label"]
    wait  = int((datetime.now() - patient.arrival_time).total_seconds() / 60)
    overdue = patient.id in stats.get("overdue_patients", [])

    overdue_html = f'<div class="overdue-tag" role="alert">{ICONS["alert_sm"]} Tiempo máximo de espera EXCEDIDO</div>' if overdue else ""
    vitals_html  = render_vitals_html(patient.vital_signs)
    consciencia  = patient.vital_signs.consciousness
    consc_html   = f'<span class="patient-time">{ICONS["clock"]} Consc.: <strong class="patient-wait">{consciencia}</strong></span>' if consciencia != "Alerta" else ""

    st.markdown(f"""
    <article class="patient-card" style="border-left-color:{color};" aria-label="Tarjeta paciente {patient.name}">
        <div class="patient-card-header">
            <div>
                <div class="patient-name">{ICONS["user"]} {patient.name}</div>
                <div class="patient-meta">{patient.age} años &middot; {patient.gender}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <span class="triage-badge" style="background:{color}18;color:{color};border:1px solid {color}33;"
                      aria-label="Nivel triage {label}">
                    {triage_dot(color, 8)} {label}
                </span>
                <span class="patient-id" aria-label="ID {patient.id}">#{patient.id}</span>
            </div>
        </div>
        <p class="patient-complaint">{patient.chief_complaint}</p>
        <div class="patient-footer">
            <span class="patient-time">{ICONS["clock"]} Llegó: <strong class="patient-wait">{patient.arrival_time.strftime("%H:%M")}</strong></span>
            <span class="patient-time">Espera: <strong class="patient-wait">{wait} min</strong></span>
            {consc_html}
        </div>
        {vitals_html}
        {overdue_html}
    </article>
    """, unsafe_allow_html=True)

    if show_actions:
        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        with c1:
            if patient.status == PatientStatus.WAITING:
                if st.button("Atender", key=f"atend_{patient.id}", type="primary"):
                    queue.start_attention(patient.id)
                    st.rerun()
        with c2:
            if patient.status == PatientStatus.IN_ATTENTION:
                if st.button("Dar alta", key=f"alta_{patient.id}"):
                    notes = st.session_state.discharge_notes.get(patient.id, "")
                    queue.discharge_patient(patient.id, notes=notes)
                    st.rerun()
        with c3:
            if st.button("Eliminar", key=f"del_{patient.id}"):
                queue.delete_patient(patient.id)
                st.rerun()

        if patient.status == PatientStatus.IN_ATTENTION:
            note = st.text_input(
                "Notas del médico",
                key=f"note_{patient.id}",
                placeholder="Diagnóstico, tratamiento aplicado, observaciones...",
                label_visibility="collapsed",
            )
            st.session_state.discharge_notes[patient.id] = note

# ══════════════════════════════════════════════════════════
# SIDEBAR — Registro
# ══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">{ICONS["hospital"]}</div>
        <div>
            <div class="sidebar-logo-title">TriageER</div>
            <div class="sidebar-logo-sub">Sistema de Urgencias Hospitalarias</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sidebar-section-label">Registro de Paciente</p>', unsafe_allow_html=True)

    with st.form("form_registro", clear_on_submit=True):
        nombre = st.text_input("Nombre completo", placeholder="Ej: María García")
        c1, c2 = st.columns(2)
        with c1:
            edad = st.number_input("Edad", min_value=0, max_value=120, value=35)
        with c2:
            genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])

        motivo      = st.text_input("Motivo de consulta", placeholder="Ej: Dolor de pecho")
        sint_raw    = st.text_area("Síntomas adicionales (coma)", placeholder="Ej: náuseas, sudoración", height=68)
        historial   = st.text_area("Antecedentes médicos", placeholder="Ej: Diabetes, hipertensión", height=52)

        st.markdown('<p class="sidebar-section-label" style="margin-top:14px;">Signos Vitales</p>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            fc   = st.number_input("FC (bpm)",      min_value=0, max_value=300, value=0)
            pa_s = st.number_input("PA sistólica",  min_value=0, max_value=300, value=0)
            temp = st.number_input("Temp (°C)",     min_value=0.0, max_value=45.0, value=0.0, step=0.1)
        with c2:
            spo2 = st.number_input("SpO₂ (%)",     min_value=0, max_value=100, value=0)
            pa_d = st.number_input("PA diastólica", min_value=0, max_value=200, value=0)
            fr   = st.number_input("FR (rpm)",      min_value=0, max_value=60,  value=0)

        dolor = st.slider("Dolor EVA (0–10)", 0, 10, 0)
        consc = st.selectbox("Consciencia (AVPU)",
                    ["Alerta", "Responde a voz", "Responde a dolor", "Inconsciente"])

        submitted = st.form_submit_button("Registrar y Clasificar", type="primary", use_container_width=True)

    if submitted:
        if nombre and motivo:
            vs = VitalSigns(
                heart_rate        = fc   if fc   > 0   else None,
                systolic_bp       = pa_s if pa_s > 0   else None,
                diastolic_bp      = pa_d if pa_d > 0   else None,
                temperature       = temp if temp > 0.0 else None,
                oxygen_saturation = spo2 if spo2 > 0   else None,
                respiratory_rate  = fr   if fr   > 0   else None,
                pain_level        = dolor,
                consciousness     = consc,
            )
            sintomas = [s.strip() for s in sint_raw.split(",") if s.strip()]
            patient  = Patient(
                name=nombre, age=edad, gender=genero,
                chief_complaint=motivo, vital_signs=vs,
                symptoms=sintomas, medical_history=historial,
            )
            reg = queue.register_patient(patient)
            lvl = reg.triage_level.value if reg.triage_level else 5
            tc  = TRIAGE_COLORS.get(lvl, TRIAGE_COLORS[5])
            st.success(f"Registrado — Triage: {tc['label']}")
        else:
            st.error("Completa nombre y motivo de consulta.")

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

stats = queue.get_statistics()
svc_class, svc_text = service_load_status(stats)

# ── Header ──
st.markdown(f"""
<header class="main-header" role="banner">
    <div class="main-header-left">
        <div class="main-header-icon" aria-hidden="true">{ICONS["stethoscope"]}</div>
        <div>
            <h1 class="main-title">Sala de Urgencias</h1>
            <p class="main-subtitle">Sistema de Triage &middot; Escala de Manchester &middot; {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
    </div>
    <span class="status-badge {svc_class}" role="status" aria-live="polite">{svc_text}</span>
</header>
""", unsafe_allow_html=True)

# ── Alertas ──
n1 = stats["triage_distribution"].get(1, {}).get("count", 0)
overdue_count = len(stats["overdue_patients"])

if n1 > 0:
    names_lvl1 = [p.name for p in queue.get_waiting_patients() if p.triage_level == TriageLevel.IMMEDIATE]
    names_str  = ", ".join(names_lvl1) if names_lvl1 else "en atención actualmente"
    st.markdown(f"""
    <div class="alert-critical" role="alert" aria-live="assertive">
        <div class="alert-critical-icon">{ICONS["alert"]}</div>
        <div>
            <div class="alert-critical-title">ALERTA &mdash; {n1} paciente(s) NIVEL INMEDIATO (Rojo)</div>
            <div class="alert-critical-body">Atención requerida en 0 minutos &mdash; {names_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if overdue_count > 0 and n1 == 0:
    st.markdown(f"""
    <div class="alert-service" role="alert" aria-live="polite">
        {ICONS["alert"]}
        <span><strong>{overdue_count} paciente(s)</strong> han excedido el tiempo máximo de espera según su nivel de triage.</span>
    </div>
    """, unsafe_allow_html=True)

# ── Métricas ──
st.markdown(f"""
<div class="metric-row" role="region" aria-label="Resumen estadístico">
    <div class="metric-card">
        <div class="metric-card-accent"></div>
        <div class="metric-card-icon" aria-hidden="true">{ICONS["users"]}</div>
        <div class="metric-value">{stats["total"]}</div>
        <div class="metric-label">Total pacientes</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-accent"></div>
        <div class="metric-card-icon" aria-hidden="true">{ICONS["hourglass"]}</div>
        <div class="metric-value">{stats["waiting"]}</div>
        <div class="metric-label">En espera</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-accent"></div>
        <div class="metric-card-icon" aria-hidden="true">{ICONS["stethoscope"]}</div>
        <div class="metric-value">{stats["active"]}</div>
        <div class="metric-label">En atención</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-accent"></div>
        <div class="metric-card-icon" aria-hidden="true">{ICONS["archive"]}</div>
        <div class="metric-value">{stats["discharged"]}</div>
        <div class="metric-label">Alta / Transferidos</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-accent"></div>
        <div class="metric-card-icon" aria-hidden="true">{ICONS["avg_wait"]}</div>
        <div class="metric-value">{stats["avg_wait_minutes"]}</div>
        <div class="metric-label">Espera prom. (min)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Distribución triage ──
st.markdown(f'<div class="section-label">{ICONS["bar_chart"]} Distribución por nivel de triage</div>', unsafe_allow_html=True)

triage_html = '<div class="triage-bar-wrap" role="list" aria-label="Niveles de triage">'
for lv in range(1, 6):
    tc   = TRIAGE_COLORS[lv]
    cnt  = stats["triage_distribution"].get(lv, {}).get("count", 0)
    triage_html += f"""
    <div class="triage-bar-item" role="listitem" aria-label="{tc['label']}: {cnt} pacientes">
        <div class="triage-dot-lg" style="background:{tc['color']};" aria-hidden="true"></div>
        <div>
            <div class="triage-bar-count" style="color:{tc['color']};">{cnt}</div>
            <div class="triage-bar-name">{tc['label']}</div>
        </div>
    </div>"""
triage_html += "</div>"
st.markdown(triage_html, unsafe_allow_html=True)

# ── Gráfica ──
chart_data = pd.DataFrame({
    "Nivel": [TRIAGE_COLORS[v]["label"] for v in range(1, 6)],
    "Pacientes": [stats["triage_distribution"].get(v, {}).get("count", 0) for v in range(1, 6)],
})
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown(f'<div class="chart-title">{ICONS["bar_chart"]} Pacientes por nivel — vista gráfica</div>', unsafe_allow_html=True)
st.bar_chart(chart_data.set_index("Nivel"), color="#2563eb", height=190)
st.markdown("</div>", unsafe_allow_html=True)

# ── Búsqueda ──
st.markdown(f'<div class="section-label">{ICONS["search"]} Buscar paciente</div>', unsafe_allow_html=True)
search = st.text_input("Buscar paciente", placeholder="Nombre o ID del paciente...", label_visibility="collapsed")

def filter_patients(patients, q):
    if not q:
        return patients
    ql = q.lower()
    return [p for p in patients if ql in p.name.lower() or ql in p.id.lower()]

# ── Tabs ──
tab1, tab2, tab3 = st.tabs([
    f"En Espera  ({stats['waiting']})",
    f"En Atención  ({stats['active']})",
    f"Historial  ({stats['discharged']})",
])

with tab1:
    patients = filter_patients(queue.get_waiting_patients(), search)
    if not patients:
        st.markdown(f'<div class="empty-state"><div class="empty-state-icon">{ICONS["check"]}</div><p class="empty-state-text">No hay pacientes en espera{" con ese criterio" if search else ""}</p></div>', unsafe_allow_html=True)
    else:
        for p in patients:
            render_patient_card(p, stats)

with tab2:
    patients = filter_patients(queue.get_active_patients(), search)
    if not patients:
        st.markdown(f'<div class="empty-state"><div class="empty-state-icon">{ICONS["stethoscope"]}</div><p class="empty-state-text">No hay pacientes en atención{" con ese criterio" if search else ""}</p></div>', unsafe_allow_html=True)
    else:
        for p in patients:
            render_patient_card(p, stats)

with tab3:
    patients = filter_patients(queue.get_discharged_patients(), search)
    if not patients:
        st.markdown(f'<div class="empty-state"><div class="empty-state-icon">{ICONS["file"]}</div><p class="empty-state-text">Sin registros en historial{" con ese criterio" if search else ""}</p></div>', unsafe_allow_html=True)
    else:
        for p in patients:
            lv    = p.triage_level.value if p.triage_level else 5
            tc    = TRIAGE_COLORS.get(lv, TRIAGE_COLORS[5])
            color = tc["color"]
            label = tc["label"]
            alta  = f" &middot; Alta: {p.discharge_time.strftime('%H:%M')}" if p.discharge_time else ""
            notes_html = f'<p style="font-size:.8rem;color:var(--gray-600);margin-top:5px;"><strong>Notas:</strong> {p.notes}</p>' if p.notes else ""
            st.markdown(f"""
            <article class="patient-card" style="border-left-color:{color};opacity:.82;" aria-label="Historial {p.name}">
                <div class="patient-card-header">
                    <div>
                        <div class="patient-name">{p.name}</div>
                        <div class="patient-meta">{p.age} años &middot; {p.gender}</div>
                    </div>
                    <span class="triage-badge" style="background:{color}18;color:{color};border:1px solid {color}33;">
                        {triage_dot(color, 8)} {label}
                    </span>
                </div>
                <p class="patient-complaint">{p.chief_complaint} &middot; {p.status.value}{alta}</p>
                {notes_html}
            </article>
            """, unsafe_allow_html=True)

# Auto-refresh 30 s
st.markdown("<script>(function(){setTimeout(function(){window.location.reload();},30000);})();</script>", unsafe_allow_html=True)