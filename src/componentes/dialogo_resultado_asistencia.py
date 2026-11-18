import logging

import streamlit as st

from src.servicios.asistencia import confirmar_resultado
from src.utilidades.sesiones import obtener_resultado, reiniciar_toma
from src.servicios.estados_asistencia import estado_deteccion, ETIQUETAS, ANALISIS_FALLIDO

_logger = logging.getLogger(__name__)


def mostrar_resultado_asistencia(resultado_id):
    import pandas as pd
    resultado = obtener_resultado(resultado_id)
    if resultado is None:
        st.warning("Este resultado ya no está vigente. Cierra el diálogo y vuelve a analizar la materia actual.")
        return
    if any(estado_deteccion(r) == ANALISIS_FALLIDO for r in resultado['registros']):
        st.error('Análisis fallido. No se generaron ausencias y esta propuesta no se puede confirmar. Vuelve a grabar o usa otro método.')
        st.dataframe(pd.DataFrame(resultado['filas']), hide_index=True, width='stretch')
        return
    st.write("Revisa la asistencia. Puedes corregir la presencia indicando un motivo por cada cambio.")
    filas = []
    for fila, registro in zip(resultado['filas'], resultado['registros']):
        filas.append({'ID': registro['estudiante_id'], 'Nombre': fila.get('Nombre', ''),
                      'Detección': ETIQUETAS[estado_deteccion(registro)],
                      **{k: fila[k] for k in ('Fuente', 'Puntaje') if k in fila},
                      'Decisión': ('Pendiente' if registro['presente'] is None else
                                   'Presente' if registro['presente'] else 'Ausente'), 'Motivo': ''})
    tabla = pd.DataFrame(filas)
    revision = st.data_editor(tabla, hide_index=True, width='stretch',
        key=f'revision_{resultado_id}', num_rows='fixed', disabled=[c for c in tabla.columns if c not in ('Decisión', 'Motivo')],
        column_config={'Decisión': st.column_config.SelectboxColumn('Decisión', options=['Pendiente', 'Presente', 'Ausente'], required=True),
                       'Motivo': st.column_config.TextColumn('Motivo del cambio', max_chars=500)})
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Descartar", width="stretch", type="tertiary", key=f"descartar_{resultado_id}"):
            reiniciar_toma()
            st.rerun()
    with col2:
        if st.button("Confirmar y Aprobar", width="stretch", type="primary", key=f"confirmar_{resultado_id}"):
            try:
                confirmar_resultado(resultado_id, revision=revision.to_dict('records'))
            except (PermissionError, ValueError) as exc:
                st.warning(str(exc))
            except Exception:
                _logger.exception("No se pudo confirmar la propuesta de asistencia %s", resultado_id)
                st.error("No se pudo confirmar. Consulta los registros antes de ejecutar nuevamente el análisis.")
            else:
                st.toast("Asistencia aprobada exitosamente")
                st.rerun()


@st.dialog("Revisión de asistencia", width='large')
def dialogo_resultado_asistencia(resultado_id):
    mostrar_resultado_asistencia(resultado_id)
