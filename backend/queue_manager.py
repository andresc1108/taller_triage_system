"""
Gestor de cola de pacientes y estado del hospital.
Maneja el flujo completo desde registro hasta alta.
"""

from datetime import datetime
from typing import Dict, List, Optional
import threading

from .models import Patient, PatientStatus, TriageLevel, TRIAGE_CONFIG
from .triage_engine import classify_patient


class HospitalQueue:
    """
    Cola de urgencias con prioridad basada en Triage Manchester.
    Thread-safe para uso con Streamlit.
    """

    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        self._lock = threading.Lock()

    # ─────────────────────────────────────────────────────
    # REGISTRO
    # ─────────────────────────────────────────────────────

    def register_patient(self, patient: Patient) -> Patient:
        """Registra un paciente y aplica triage automáticamente."""
        with self._lock:
            patient.triage_level = classify_patient(patient)
            self._patients[patient.id] = patient
        return patient

    # ─────────────────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────────────────

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self._patients.get(patient_id)

    def get_all_patients(self) -> List[Patient]:
        """Retorna todos los pacientes ordenados por prioridad y tiempo de espera."""
        with self._lock:
            patients = list(self._patients.values())

        # Ordenar: primero por nivel de triage (1=más urgente), luego por hora de llegada
        return sorted(
            patients,
            key=lambda p: (
                p.triage_level.value if p.triage_level else 99,
                p.arrival_time
            )
        )

    def get_waiting_patients(self) -> List[Patient]:
        return [p for p in self.get_all_patients() if p.status == PatientStatus.WAITING]

    def get_active_patients(self) -> List[Patient]:
        return [p for p in self.get_all_patients() if p.status == PatientStatus.IN_ATTENTION]

    def get_discharged_patients(self) -> List[Patient]:
        return [p for p in self.get_all_patients() if p.status in (
            PatientStatus.DISCHARGED, PatientStatus.TRANSFERRED
        )]

    # ─────────────────────────────────────────────────────
    # ACCIONES DE FLUJO
    # ─────────────────────────────────────────────────────

    def start_attention(self, patient_id: str) -> bool:
        """Marca al paciente como en atención."""
        with self._lock:
            patient = self._patients.get(patient_id)
            if not patient or patient.status != PatientStatus.WAITING:
                return False
            patient.status = PatientStatus.IN_ATTENTION
            patient.attention_start = datetime.now()
        return True

    def discharge_patient(self, patient_id: str, notes: str = "", transfer: bool = False) -> bool:
        """Da de alta o transfiere al paciente."""
        with self._lock:
            patient = self._patients.get(patient_id)
            if not patient:
                return False
            patient.status = PatientStatus.TRANSFERRED if transfer else PatientStatus.DISCHARGED
            patient.discharge_time = datetime.now()
            if notes:
                patient.notes = notes
        return True

    def update_triage(self, patient_id: str, new_level: TriageLevel, notes: str = "") -> bool:
        """Permite a un médico reclasificar manualmente el triage."""
        with self._lock:
            patient = self._patients.get(patient_id)
            if not patient:
                return False
            patient.triage_level = new_level
            if notes:
                patient.notes = notes
        return True

    def delete_patient(self, patient_id: str) -> bool:
        with self._lock:
            if patient_id in self._patients:
                del self._patients[patient_id]
                return True
        return False

    # ─────────────────────────────────────────────────────
    # ESTADÍSTICAS
    # ─────────────────────────────────────────────────────

    def get_statistics(self) -> dict:
        all_p = list(self._patients.values())
        waiting = [p for p in all_p if p.status == PatientStatus.WAITING]
        active = [p for p in all_p if p.status == PatientStatus.IN_ATTENTION]
        discharged = [p for p in all_p if p.status in (
            PatientStatus.DISCHARGED, PatientStatus.TRANSFERRED
        )]

        # Distribución por nivel de triage
        triage_dist = {}
        for level in TriageLevel:
            cfg = TRIAGE_CONFIG[level]
            count = sum(1 for p in all_p if p.triage_level == level)
            triage_dist[level.value] = {
                "name": cfg["name"],
                "color": cfg["color"],
                "badge": cfg["badge"],
                "count": count
            }

        # Tiempo promedio de espera (pacientes en espera)
        avg_wait = 0
        if waiting:
            total_wait = sum(
                (datetime.now() - p.arrival_time).total_seconds() / 60
                for p in waiting
            )
            avg_wait = round(total_wait / len(waiting), 1)

        # Pacientes con espera excedida
        overdue = []
        for p in waiting:
            if p.triage_level:
                max_wait = TRIAGE_CONFIG[p.triage_level]["max_wait_minutes"]
                wait = (datetime.now() - p.arrival_time).total_seconds() / 60
                if wait > max_wait:
                    overdue.append(p.id)

        return {
            "total": len(all_p),
            "waiting": len(waiting),
            "active": len(active),
            "discharged": len(discharged),
            "avg_wait_minutes": avg_wait,
            "overdue_patients": overdue,
            "triage_distribution": triage_dist,
        }
