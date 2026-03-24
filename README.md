# Sistema de Triage y Flujo de Sala de Urgencias

Sistema basado en la **Escala de Manchester (MTS)** para gestión de pacientes en urgencias hospitalarias.

## Instalación y Ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la aplicación
streamlit run app.py
```

## Niveles de Triage (Escala Manchester)

| Nivel | Color | Nombre        | Tiempo máx. | Descripción              |
|-------|-------|---------------|-------------|--------------------------|
| 1     | rojo    | Inmediato     | 0 min       | Riesgo vital inmediato   |
| 2     | naranja | Muy Urgente   | 10 min      | Riesgo vital potencial   |
| 3     | amarillo| Urgente       | 60 min      | Estado grave, estable    |
| 4     | verde   | Poco Urgente  | 120 min     | Situación no urgente     |
| 5     | azul    | No Urgente    | 240 min     | Sin riesgo vital         |

## Algoritmo de Clasificación

El motor de triage evalúa:
1. **Signos vitales**: FC, PA, SpO₂, temperatura, FR, consciencia (AVPU), dolor (EVA)
2. **Síntomas / motivo de consulta**: Más de 60 palabras clave médicas clasificadas
3. **Factores de riesgo**: Edad extrema, antecedentes médicos relevantes

El nivel final es el **más crítico** de los tres factores combinados.

## Funcionalidades

- Registro de pacientes con signos vitales completos
- Clasificación automática por Escala Manchester
- Cola de atención ordenada por prioridad y tiempo de llegada
- Alertas de tiempo de espera excedido
- Flujo: En Espera → En Atención → Alta/Transferido
- Estadísticas en tiempo real
- Reclasificación manual por el médico
- Auto-refresh cada 30 segundos
