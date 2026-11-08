import streamlit as st
import pandas as pd

import time
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))

from src.canalizaciones.canalizacion_voz import procesar_audio_masivo

from src.base_datos.bd import obtener_estudiantes_matriculados

from src.componentes.dialogo_resultado_asistencia import mostrar_resultado_asistencia

@st.dialog("Asistencia por Voz")
def dialogo_asistencia_voz(id_materia_seleccionada):
    st.write("Graba la voz de 'Estoy presente' de todos los estudiantes. Este audio completo será analizado por la IA para reconocer a cada estudiante y registrar su asistencia.")

    audio_grabado = None

    audio_grabado = st.audio_input("Grabar Audio del Salón de Clases")

    if st.button("Analizar Audio", width="stretch", type="primary"):
        with st.spinner("Procesando datos de audio"):
            estudiantes_matriculados = obtener_estudiantes_matriculados(id_materia_seleccionada)

            if not estudiantes_matriculados:
                st.warning(f"No hay estudiantes matriculados en esta materia")
                time.sleep(1)
                return

            diccionario_candidatos = {
                e["estudiante_id"] : e["embedding_voz"]
                for e in estudiantes_matriculados if e.get("embedding_voz")
            }

            if not diccionario_candidatos:
                st.warning("Ningún estudiante matriculado tiene su voz registrada")
                time.sleep(1)
                return

            if not audio_grabado:
                st.error("Por favor graba primero el audio del salón de clases.")
                return

            audio_bytes = audio_grabado.read()

            puntajes_detectados = procesar_audio_masivo(audio_bytes, diccionario_candidatos) 

            resultados, asistencia_a_registrar = [], []

            marca_tiempo_actual = datetime.now(IST).isoformat()
            for estudiante in estudiantes_matriculados:
                puntaje = puntajes_detectados.get(estudiante["estudiante_id"], 0.0)
                esta_presente = bool(puntaje > 0)

                resultados.append(
                    {
                        "Nombre": estudiante["nombre"],
                        "ID": estudiante["estudiante_id"],
                        "Puntaje": puntaje if esta_presente else "-",
                        "Estado": "☑️ Presente" if esta_presente else "❌ Ausente",
                    }
                )

                asistencia_a_registrar.append(
                    {
                        "fecha_hora" : marca_tiempo_actual,
                        "materia_id" : id_materia_seleccionada,
                        "estudiante_id" : estudiante["estudiante_id"],
                        "presente" : bool(esta_presente)
                    }
                )
            st.session_state.resultados_asistencia_voz = (pd.DataFrame(resultados), asistencia_a_registrar)

    st.divider() 

    if st.session_state.get("resultados_asistencia_voz"):
        df_resultados, registros = st.session_state.resultados_asistencia_voz
        mostrar_resultado_asistencia(df_resultados, registros)
