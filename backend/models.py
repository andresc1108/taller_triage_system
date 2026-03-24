from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class TriageLevel(Enum):
    IMMEDIATE = 1      # Rojo - Inmediato
    VERY_URGENT = 2    # Naranja - Muy urgente
    URGENT = 3         # Amarillo - Urgente
    LESS_URGENT = 4    # Verde - Poco urgente
    NON_URGENT = 5     # Azul - No urgente


TRIAGE_CONFIG = {
    TriageLevel.IMMEDIATE: {
        "name": "Inmediato",
        "color": "#E53E3E",
        "badge": "🔴",
        "max_wait_minutes": 0,
        "description": "Riesgo vital inmediato"
    },
    TriageLevel.VERY_URGENT: {
        "name": "Muy Urgente",
        "color": "#DD6B20",
        "badge": "🟠",
        "max_wait_minutes": 10,
        "description": "Riesgo vital potencial"
    },
    TriageLevel.URGENT: {
        "name": "Urgente",
        "color": "#D69E2E",
        "badge": "🟡",
        "max_wait_minutes": 60,
        "description": "Estado grave, estable"
    },
    TriageLevel.LESS_URGENT: {
        "name": "Poco Urgente",
        "color": "#38A169",
        "badge": "🟢",
        "max_wait_minutes": 120,
        "description": "Situación no urgente"
    },
    TriageLevel.NON_URGENT: {
        "name": "No Urgente",
        "color": "#3182CE",
        "badge": "🔵",
        "max_wait_minutes": 240,
        "description": "Sin riesgo vital"
    },
}


class PatientStatus(Enum):
    WAITING = "En espera"
    IN_ATTENTION = "En atención"
    DISCHARGED = "Dado de alta"
    TRANSFERRED = "Transferido"


@dataclass
class VitalSigns:
    heart_rate: Optional[int] = None          # bpm
    systolic_bp: Optional[int] = None         # mmHg
    diastolic_bp: Optional[int] = None        # mmHg
    temperature: Optional[float] = None       # °C
    oxygen_saturation: Optional[int] = None   # %
    respiratory_rate: Optional[int] = None    # rpm
    pain_level: int = 0                       # 0-10 (EVA)
    consciousness: str = "Alerta"             # AVPU


@dataclass
class Patient:
    name: str
    age: int
    gender: str
    chief_complaint: str
    vital_signs: VitalSigns
    symptoms: list = field(default_factory=list)
    medical_history: str = ""

    # Auto-assigned
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    arrival_time: datetime = field(default_factory=datetime.now)
    triage_level: Optional[TriageLevel] = None
    status: PatientStatus = PatientStatus.WAITING
    attention_start: Optional[datetime] = None
    discharge_time: Optional[datetime] = None
    notes: str = ""

    def to_dict(self):
        cfg = TRIAGE_CONFIG.get(self.triage_level, {}) if self.triage_level else {}
        wait = int((datetime.now() - self.arrival_time).total_seconds() / 60)
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "chief_complaint": self.chief_complaint,
            "symptoms": self.symptoms,
            "medical_history": self.medical_history,
            "triage_level": self.triage_level.value if self.triage_level else None,
            "triage_name": cfg.get("name", "Sin clasificar"),
            "triage_color": cfg.get("color", "#718096"),
            "triage_badge": cfg.get("badge", "⚪"),
            "triage_description": cfg.get("description", ""),
            "max_wait_minutes": cfg.get("max_wait_minutes", 0),
            "status": self.status.value,
            "arrival_time": self.arrival_time.strftime("%H:%M:%S"),
            "wait_minutes": wait,
            "notes": self.notes,
            "vital_signs": {
                "heart_rate": self.vital_signs.heart_rate,
                "systolic_bp": self.vital_signs.systolic_bp,
                "diastolic_bp": self.vital_signs.diastolic_bp,
                "temperature": self.vital_signs.temperature,
                "oxygen_saturation": self.vital_signs.oxygen_saturation,
                "respiratory_rate": self.vital_signs.respiratory_rate,
                "pain_level": self.vital_signs.pain_level,
                "consciousness": self.vital_signs.consciousness,
            }
        }
