import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime

from backend import (
    Patient, VitalSigns, TriageLevel, PatientStatus,
    TRIAGE_CONFIG, HospitalQueue
)

# ─────────────────────────────────────────────────────────
# CONFIG & STATE
# ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ER Triage System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "queue" not in st.session_state:
    st.session_state.queue = HospitalQueue()

queue: HospitalQueue = st.session_state.queue

# ─────────────────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;700&display=swap');

:root {
    --bg: #0a0f1e;
    --surface: #111827;
    --surface2: #1a2235;
    --border: #1e2d45;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --text: #e2e8f0;
    --muted: #64748b;
    --red: #ef4444;
    --orange: #f97316;
    --yellow: #eab308;
    --green: #22c55e;
    --blue: #3b82f6;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background-color: var(--bg) !important; }

h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.metric-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 0.75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.patient-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border-left: 4px solid;
    transition: all 0.2s;
}
.patient-card:hover { border-color: var(--accent); }

.triage-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
}

.overdue-warning {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.8rem;
    color: #fca5a5;
    margin-top: 8px;
}

.vital-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 12px;
}
.vital-item {
    background: var(--surface2);
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
}
.vital-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent);
}
.vital-label {
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
}

.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin-bottom: 16px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select,
.stTextArea textarea {
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}

/* Buttons */
.stButton button {
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    border: none !important;
    color: white !important;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

.stTabs [data-baseweb="tab-list"] {
    background-color: var(--surface) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--surface2) !important;
    color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def triage_color(level: TriageLevel) -> str:
    return TRIAGE_CONFIG[level]["color"]

def render_patient_card(patient: Patient, stats: dict, show_actions: bool = True):
    cfg = TRIAGE_CONFIG[patient.triage_level] if patient.triage_level else {}
    color = cfg.get("color", "#718096")
    badge = cfg.get("badge", "⚪")
    name = cfg.get("name", "Sin clasificar")
    wait = int((datetime.now() - patient.arrival_time).total_seconds() / 60)
    overdue = patient.id in stats.get("overdue_patients", [])

    card_html = f"""
    <div class="patient-card" style="border-left-color: {color};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-weight:700; font-size:1.05rem;">{patient.name}</span>
                <span style="color:#64748b; font-size:0.85rem; margin-left:10px;">
                    {patient.age} años · {patient.gender}
                </span>
            </div>
            <div style="display:flex; gap:8px; align-items:center;">
                <span class="triage-badge" style="background:{color}22; color:{color}; border:1px solid {color}44;">
                    {badge} {name}
                </span>
                <span style="font-family:monospace; font-size:0.75rem; color:#64748b;">
                    #{patient.id}
                </span>
            </div>
        </div>
        <div style="margin-top:8px; font-size:0.9rem; color:#94a3b8;">
            📋 {patient.chief_complaint}
        </div>
        <div style="margin-top:6px; font-size:0.8rem; color:#64748b;">
            🕐 Llegó: {patient.arrival_time.strftime('%H:%M')} · Espera: <b style="color:#e2e8f0;">{wait} min</b>
        </div>
        {"<div class='overdue-warning'>⚠️ Tiempo de espera EXCEDIDO — Requiere atención inmediata</div>" if overdue else ""}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    if show_actions:
        cols = st.columns([1, 1, 1, 2])
        with cols[0]:
            if patient.status == PatientStatus.WAITING:
                if st.button("▶ Atender", key=f"atend_{patient.id}", type="primary"):
                    queue.start_attention(patient.id)
                    st.rerun()
        with cols[1]:
            if patient.status == PatientStatus.IN_ATTENTION:
                if st.button("✓ Alta", key=f"alta_{patient.id}"):
                    queue.discharge_patient(patient.id)
                    st.rerun()
        with cols[2]:
            if st.button("🗑 Eliminar", key=f"del_{patient.id}"):
                queue.delete_patient(patient.id)
                st.rerun()

# ─────────────────────────────────────────────────────────
# SIDEBAR – REGISTRO DE PACIENTE
# ─────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 24px;">
        <div style="font-size:2rem;">🏥</div>
        <div style="font-family:'IBM Plex Mono',monospace; font-weight:600; color:#00d4ff; font-size:1rem;">
            ER TRIAGE
        </div>
        <div style="font-size:0.7rem; color:#64748b;">Sistema de Urgencias</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Registrar Paciente</div>', unsafe_allow_html=True)

    with st.form("registro_paciente", clear_on_submit=True):
        # ── Datos básicos ──
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
        with col2:
            edad = st.number_input("Edad", min_value=0, max_value=120, value=35)

        genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
        motivo = st.text_input("Motivo de consulta", placeholder="Ej: Dolor pecho intenso")

        sintomas_raw = st.text_area(
            "Síntomas adicionales (separados por coma)",
            placeholder="Ej: náuseas, sudoración, dificultad respiratoria",
            height=80
        )
        historial = st.text_area("Antecedentes médicos", placeholder="Ej: Diabetes tipo 2, hipertensión", height=60)

        st.markdown('<div class="section-header" style="margin-top:16px;">Signos Vitales</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            fc = st.number_input("FC (bpm)", min_value=0, max_value=300, value=0)
            pa_sis = st.number_input("PA sistólica", min_value=0, max_value=300, value=0)
            temp = st.number_input("Temperatura (°C)", min_value=0.0, max_value=45.0, value=0.0, step=0.1)
        with c2:
            spo2 = st.number_input("SpO₂ (%)", min_value=0, max_value=100, value=0)
            pa_dia = st.number_input("PA diastólica", min_value=0, max_value=200, value=0)
            fr = st.number_input("FR (rpm)", min_value=0, max_value=60, value=0)

        dolor = st.slider("Dolor EVA (0-10)", 0, 10, 0)
        consciencia = st.selectbox("Consciencia (AVPU)", ["Alerta", "Responde a voz", "Responde a dolor", "Inconsciente"])

        submitted = st.form_submit_button("⚡ Registrar y Clasificar", type="primary", use_container_width=True)

    if submitted and nombre and motivo:
        vs = VitalSigns(
            heart_rate=fc if fc > 0 else None,
            systolic_bp=pa_sis if pa_sis > 0 else None,
            diastolic_bp=pa_dia if pa_dia > 0 else None,
            temperature=temp if temp > 0 else None,
            oxygen_saturation=spo2 if spo2 > 0 else None,
            respiratory_rate=fr if fr > 0 else None,
            pain_level=dolor,
            consciousness=consciencia
        )
        sintomas = [s.strip() for s in sintomas_raw.split(",") if s.strip()]
        patient = Patient(
            name=nombre, age=edad, gender=genero,
            chief_complaint=motivo, vital_signs=vs,
            symptoms=sintomas, medical_history=historial
        )
        registered = queue.register_patient(patient)
        cfg = TRIAGE_CONFIG[registered.triage_level]
        st.success(f"✅ Paciente registrado · Triage: {cfg['badge']} {cfg['name']}")
    elif submitted:
        st.error("Por favor completa nombre y motivo de consulta.")

# ─────────────────────────────────────────────────────────
# HEADER PRINCIPAL
# ─────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
    <div>
        <h1 style="margin:0; font-size:1.8rem; background:linear-gradient(90deg,#00d4ff,#7c3aed);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            SALA DE URGENCIAS
        </h1>
        <div style="font-size:0.8rem; color:#64748b; font-family:'IBM Plex Mono',monospace;">
            Sistema de Triage · Escala de Manchester
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

stats = queue.get_statistics()

# ─────────────────────────────────────────────────────────
# MÉTRICAS
# ─────────────────────────────────────────────────────────

m1, m2, m3, m4, m5 = st.columns(5)
metrics = [
    (m1, stats["total"], "Total pacientes"),
    (m2, stats["waiting"], "En espera"),
    (m3, stats["active"], "En atención"),
    (m4, stats["discharged"], "Alta/Transferidos"),
    (m5, f"{stats['avg_wait_minutes']} min", "Espera promedio"),
]
for col, val, label in metrics:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# Alertas de espera excedida
if stats["overdue_patients"]:
    st.markdown(f"""
    <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.5);
                border-radius:10px; padding:12px 18px; margin:16px 0;">
        🚨 <b>{len(stats["overdue_patients"])} paciente(s)</b> han excedido el tiempo máximo de espera según su triage.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# DISTRIBUCIÓN DE TRIAGE
# ─────────────────────────────────────────────────────────

st.markdown('<div class="section-header">Distribución por Nivel de Triage</div>', unsafe_allow_html=True)
triage_cols = st.columns(5)
for i, (level_val, info) in enumerate(stats["triage_distribution"].items()):
    with triage_cols[i]:
        st.markdown(f"""
        <div style="background:{info['color']}15; border:1px solid {info['color']}44;
                    border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:1.8rem;">{info['badge']}</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:1.5rem;
                        font-weight:700; color:{info['color']};">{info['count']}</div>
            <div style="font-size:0.7rem; color:#94a3b8;">{info['name']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# TABS: COLA, EN ATENCIÓN, HISTORIAL
# ─────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    f"⏳ En Espera ({stats['waiting']})",
    f"⚕️ En Atención ({stats['active']})",
    f"📋 Historial ({stats['discharged']})"
])

with tab1:
    waiting = queue.get_waiting_patients()
    if not waiting:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#475569;">
            <div style="font-size:2rem; margin-bottom:8px;">✅</div>
            <div>No hay pacientes en espera</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for p in waiting:
            render_patient_card(p, stats)

with tab2:
    active = queue.get_active_patients()
    if not active:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#475569;">
            <div style="font-size:2rem; margin-bottom:8px;">🏥</div>
            <div>No hay pacientes en atención</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for p in active:
            render_patient_card(p, stats)

with tab3:
    discharged = queue.get_discharged_patients()
    if not discharged:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#475569;">
            <div style="font-size:2rem; margin-bottom:8px;">📂</div>
            <div>Sin pacientes en historial</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for p in discharged:
            cfg = TRIAGE_CONFIG[p.triage_level] if p.triage_level else {}
            color = cfg.get("color", "#718096")
            badge = cfg.get("badge", "⚪")
            name = cfg.get("name", "Sin clasificar")
            st.markdown(f"""
            <div class="patient-card" style="border-left-color:{color}; opacity:0.75;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:600;">{p.name}</span>
                    <span class="triage-badge" style="background:{color}22; color:{color}; border:1px solid {color}44;">
                        {badge} {name}
                    </span>
                </div>
                <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">
                    {p.chief_complaint} · {p.status.value}
                    {f"· Alta: {p.discharge_time.strftime('%H:%M')}" if p.discharge_time else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Auto-refresh cada 30 segundos
st.markdown("""
<script>
setTimeout(function() { window.location.reload(); }, 30000);
</script>
""", unsafe_allow_html=True)
