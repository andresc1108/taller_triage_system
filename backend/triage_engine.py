"""
Motor de Triage basado en la Escala de Manchester (MTS).
Evalúa síntomas, signos vitales y factores de riesgo para
asignar automáticamente el nivel de prioridad 1-5.
"""

from .models import Patient, TriageLevel, VitalSigns


# ─────────────────────────────────────────────────────────
# REGLAS DE SIGNOS VITALES
# ─────────────────────────────────────────────────────────

def _evaluate_vital_signs(vs: VitalSigns) -> int:
    """
    Devuelve el nivel de triage más crítico detectado en signos vitales.
    1 = más crítico, 5 = menos crítico.
    """
    level = 5

    # Saturación de oxígeno
    if vs.oxygen_saturation is not None:
        if vs.oxygen_saturation < 85:
            level = min(level, 1)
        elif vs.oxygen_saturation < 90:
            level = min(level, 2)
        elif vs.oxygen_saturation < 94:
            level = min(level, 3)

    # Frecuencia cardíaca
    if vs.heart_rate is not None:
        if vs.heart_rate < 40 or vs.heart_rate > 150:
            level = min(level, 1)
        elif vs.heart_rate < 50 or vs.heart_rate > 130:
            level = min(level, 2)
        elif vs.heart_rate < 60 or vs.heart_rate > 100:
            level = min(level, 3)

    # Presión arterial sistólica
    if vs.systolic_bp is not None:
        if vs.systolic_bp < 80 or vs.systolic_bp > 220:
            level = min(level, 1)
        elif vs.systolic_bp < 90 or vs.systolic_bp > 180:
            level = min(level, 2)
        elif vs.systolic_bp < 100 or vs.systolic_bp > 160:
            level = min(level, 3)

    # Temperatura
    if vs.temperature is not None:
        if vs.temperature >= 41.0 or vs.temperature < 35.0:
            level = min(level, 1)
        elif vs.temperature >= 39.5 or vs.temperature < 35.5:
            level = min(level, 2)
        elif vs.temperature >= 38.5:
            level = min(level, 3)

    # Frecuencia respiratoria
    if vs.respiratory_rate is not None:
        if vs.respiratory_rate < 8 or vs.respiratory_rate > 30:
            level = min(level, 1)
        elif vs.respiratory_rate < 10 or vs.respiratory_rate > 25:
            level = min(level, 2)
        elif vs.respiratory_rate > 20:
            level = min(level, 3)

    # Nivel de consciencia (AVPU)
    consciousness_map = {
        "Alerta": 5,
        "Responde a voz": 3,
        "Responde a dolor": 2,
        "Inconsciente": 1,
    }
    level = min(level, consciousness_map.get(vs.consciousness, 5))

    # Dolor (EVA 0-10)
    if vs.pain_level >= 9:
        level = min(level, 2)
    elif vs.pain_level >= 7:
        level = min(level, 3)
    elif vs.pain_level >= 5:
        level = min(level, 4)

    return level


# ─────────────────────────────────────────────────────────
# REGLAS DE SÍNTOMAS / MOTIVO DE CONSULTA
# ─────────────────────────────────────────────────────────

# Palabras clave → nivel máximo de triage que activan
SYMPTOM_RULES = {
    1: [
        "paro", "paro cardiaco", "paro cardiorrespiratorio",
        "no respira", "sin pulso", "inconsciente",
        "convulsión activa", "shock", "anafilaxia",
        "hemorragia masiva", "politraumatismo grave",
        "quemadura mayor 30%", "ahogamiento",
        "trauma craneal severo", "apnea",
    ],
    2: [
        "dolor pecho", "infarto", "dificultad respiratoria severa",
        "accidente cerebrovascular", "stroke", "ictus",
        "hemoptisis", "hemorragia activa", "trauma ocular",
        "fractura expuesta", "quemadura", "intoxicación",
        "sobredosis", "crisis hipertensiva", "meningitis",
        "sepsis", "eclampsia", "diabetes descompensada",
        "deshidratación severa",
    ],
    3: [
        "vómito sangre", "dolor abdominal severo",
        "fiebre alta", "fractura", "herida profunda",
        "cefalea intensa", "mareo intenso", "trauma",
        "dolor lumbar agudo", "retención urinaria",
        "hiperglucemia", "hipoglucemia",
    ],
    4: [
        "vómito", "diarrea", "fiebre", "tos",
        "dolor leve", "mareo leve", "erupción cutánea",
        "conjuntivitis", "otitis", "faringitis",
        "esguince leve", "contusión leve",
    ],
    5: [
        "resfriado", "gripe leve", "revisión",
        "receta", "certificado", "control",
        "herida superficial", "dolor crónico estable",
    ],
}


def _evaluate_symptoms(chief_complaint: str, symptoms: list) -> int:
    """Evalúa síntomas y retorna el nivel más urgente detectado."""
    text = (chief_complaint + " " + " ".join(symptoms)).lower()
    for level in range(1, 6):
        keywords = SYMPTOM_RULES.get(level, [])
        if any(kw in text for kw in keywords):
            return level
    return 4  # Por defecto: poco urgente si no hay match


# ─────────────────────────────────────────────────────────
# FACTORES MODIFICADORES
# ─────────────────────────────────────────────────────────

def _apply_modifiers(base_level: int, patient: Patient) -> int:
    """Ajusta el nivel según factores de riesgo del paciente."""
    level = base_level

    # Edad extrema = incrementar urgencia
    if patient.age < 2 or patient.age > 85:
        level = max(1, level - 1)
    elif patient.age < 12 or patient.age > 75:
        level = max(1, level - 1) if level > 2 else level

    # Historial médico relevante
    history = patient.medical_history.lower()
    high_risk_conditions = [
        "diabetes", "hipertensión", "epoc", "asma", "insuficiencia cardiaca",
        "cáncer", "inmunosuprimido", "embarazo", "vihsida", "anticoagulado",
        "marcapasos", "trasplante", "diálisis",
    ]
    if any(cond in history for cond in high_risk_conditions):
        level = max(1, level - 1) if level > 2 else level

    return level


# ─────────────────────────────────────────────────────────
# MOTOR PRINCIPAL
# ─────────────────────────────────────────────────────────

def classify_patient(patient: Patient) -> TriageLevel:
    """
    Algoritmo de triage Manchester:
    1. Evalúa signos vitales
    2. Evalúa síntomas / motivo
    3. Toma el nivel más crítico (número más bajo)
    4. Aplica modificadores de riesgo
    """
    vital_level = _evaluate_vital_signs(patient.vital_signs)
    symptom_level = _evaluate_symptoms(patient.chief_complaint, patient.symptoms)

    # El nivel final es el más crítico de ambos
    raw_level = min(vital_level, symptom_level)

    # Aplicar modificadores
    final_level = _apply_modifiers(raw_level, patient)

    return TriageLevel(final_level)
