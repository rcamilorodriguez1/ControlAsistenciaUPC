import streamlit as st

from src.servicios.biometria_diferida import procesar_audio_masivo
from src.servicios.resultado_audio import ResultadoAudio
from src.servicios.resultados_voz import construir_resultados_voz
from src.base_datos.bd import obtener_estudiantes_matriculados
from src.componentes.dialogo_resultado_asistencia import mostrar_resultado_asistencia
from src.utilidades.fecha_hora import hora_actual_colombia
from src.utilidades.sesiones import contexto_vigente, guardar_resultado, obtener_resultado, invalidar_resultado

MAX_AUDIO_BYTES = 20 * 1024 * 1024


@st.dialog("Asistencia por Voz", width='large')
def dialogo_asistencia_voz(contexto):
    if not contexto_vigente(contexto):
        st.warning("La sesión o materia cambió. Abre nuevamente la asistencia de la materia actual.")
        return
    pendiente = obtener_resultado()
    if pendiente and pendiente["origen"] != "voz":
        invalidar_resultado()
    estudiantes = obtener_estudiantes_matriculados(contexto["materia_id"])
    if not estudiantes:
        invalidar_resultado()
        st.warning("No hay estudiantes matriculados en esta materia.")
        return
    st.write("Graba las intervenciones de los estudiantes para analizar la asistencia por voz.")
    st.caption('Hasta 3 minutos y 20 MB. Cada intervención necesita al menos unos 0,5 segundos de voz clara.')
    audio = st.audio_input("Grabar Audio del Salón de Clases", key=f"audio_asistencia_{contexto['toma_id']}",
                           on_change=invalidar_resultado)
    if st.button("Analizar Audio", width="stretch", type="primary"):
        invalidar_resultado()
        candidatos = {e["estudiante_id"]: e["embedding_voz"] for e in estudiantes
                      if e.get('embedding_voz') is not None and len(e['embedding_voz']) > 0}
        if not audio:
            st.warning("Graba primero el audio del salón de clases.")
            return
        datos = audio.getvalue()
        if len(datos) > MAX_AUDIO_BYTES:
            st.warning("El audio puede ocupar como máximo 20 MB.")
            return
        with st.spinner("Procesando datos de audio"):
            try:
                analisis = procesar_audio_masivo(datos, candidatos)
            except Exception:
                # Defensa del limite UI: nunca reutilizar la propuesta previa tras una excepcion.
                analisis = ResultadoAudio.fallido('ERROR_PROCESAMIENTO')
            if not isinstance(analisis, ResultadoAudio) or analisis.estado not in ('COMPLETADO', 'SIN_MUESTRAS', 'FALLIDO'):
                analisis = ResultadoAudio.fallido('CONTRATO_INVALIDO')
            filas, registros = construir_resultados_voz(estudiantes, contexto['materia_id'], analisis,
                                                       hora_actual_colombia().isoformat())
            if analisis.estado == 'FALLIDO':
                consejos = {
                    'DURACION_AUDIO': 'Usa una grabación de entre 0,5 y 180 segundos.',
                    'SIN_SENAL': 'La grabación está en silencio o tiene un volumen demasiado bajo.',
                    'AUDIO_SATURADO': 'El micrófono está saturado. Aléjalo y vuelve a grabar.',
                    'FORMATO_AUDIO': 'No se pudo leer el audio. Graba nuevamente desde el micrófono.',
                    'SIN_SEGMENTOS_ANALIZABLES': 'No se encontraron intervenciones con suficiente voz identificable.',
                    'VECTOR_INVALIDO': 'No se pudo validar una muestra de voz. Usa otro método mientras se revisa la muestra.',
                }
                if analisis.codigo in consejos:
                    st.warning(consejos[analisis.codigo])
            if analisis.estado == 'SIN_MUESTRAS':
                st.info('No hay muestras de voz registradas. Todas las decisiones quedan pendientes y requieren revisión manual con motivo.')
            guardar_resultado(contexto, filas, registros, "voz")
    st.divider()
    pendiente = obtener_resultado()
    if pendiente and pendiente["origen"] == "voz":
        mostrar_resultado_asistencia(pendiente["id"])
