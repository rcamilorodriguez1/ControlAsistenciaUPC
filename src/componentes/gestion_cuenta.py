"""Acciones de cuenta con motivo; el historial académico se conserva."""
import streamlit as st
from src.base_datos import gestion
from src.base_datos.bd import obtener_materias_profesor
from src.utilidades.sesiones import obtener_actor, cerrar_sesion, limpiar_asistencia


def gestion_cuenta():
    actor = obtener_actor()
    if actor is None: return
    rol, identificador, token = actor
    with st.expander('Administrar cuenta e historial'):
        st.caption('El archivo conserva clases, asistencias e historial. Retirar biometría elimina los vectores activos y cierra la sesión; las copias anteriores siguen su retención.')
        opciones = ['Archivar mi cuenta']
        if rol == 'estudiante': opciones.insert(0, 'Retirar mi biometría')
        materias = obtener_materias_profesor(identificador) if rol == 'profesor' else []
        if materias: opciones.insert(0, 'Archivar una materia')
        accion = st.selectbox('Acción', opciones, key=f'gestion_accion_{token}')
        materia = None
        if accion == 'Archivar una materia':
            mapa = {m['materia_id']: m for m in materias}
            materia = st.selectbox('Materia para archivar', list(mapa),
                format_func=lambda m: mapa[m]['codigo_materia'] + ' — ' + mapa[m]['nombre'], key=f'gestion_materia_{token}')
        motivo = st.text_input('Motivo del cambio', max_chars=500, key=f'gestion_motivo_{token}')
        confirmar = st.checkbox('He revisado la acción y deseo aplicarla', key=f'gestion_confirmar_{token}')
        if st.button('Aplicar cambio', disabled=not confirmar, key=f'gestion_aplicar_{token}'):
            try:
                if accion == 'Archivar una materia': gestion.archivar_materia(materia, motivo)
                elif accion == 'Retirar mi biometría': gestion.retirar_biometria(identificador, motivo)
                elif rol == 'estudiante': gestion.archivar_estudiante(identificador, motivo)
                else: gestion.archivar_profesor(identificador, motivo)
            except (ValueError, PermissionError) as exc: st.warning(str(exc))
            except Exception: st.error('No se pudo confirmar el cambio. Revisa el estado antes de repetirlo.')
            else:
                if materia is None: cerrar_sesion(rol)
                else: limpiar_asistencia()
                st.rerun()
