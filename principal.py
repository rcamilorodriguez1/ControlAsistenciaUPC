import streamlit as st
from src.interfaz.diseno_base import estilo_diseno_base, RAIZ
from src.utilidades.sesiones import inicializar_sesion, seleccionar_portal, sesion_activa
from src.utilidades.sesiones import obtener_actor, rechazar_sesion
from src.interfaz.navegacion import navegar, vigilar_sesion
from src.servicios.sesiones_servidor import SesionInvalida
from src.servicios.autenticacion import ConflictoSesion
import oracledb

def principal():

    st.set_page_config(
        page_title="UPC | Aula",
        page_icon=str(RAIZ / 'static' / 'img' / 'upc' / 'logo-vertical-manual.jpg'),
        layout="wide",
    )
    estilo_diseno_base()
    try: inicializar_sesion()
    except oracledb.Error:
        st.error('No se pudo validar el acceso con el servidor. Intenta de nuevo.'); st.stop()
    try: navegar(mostrar_portal)
    except ConflictoSesion:
        st.rerun()  # La identidad vigente se conserva; el login mostrará el aviso compartido.
    except SesionInvalida as exc:
        rechazar_sesion(str(exc)); st.rerun()
    except oracledb.Error:
        st.error('No se pudo verificar la operación con el servidor. Revisa el estado antes de repetir un cambio.')


def mostrar_portal():
    actor = obtener_actor()
    if actor is not None: vigilar_sesion()
    if 'aviso_sesion' in st.session_state:
        st.warning(st.session_state.pop('aviso_sesion'))
    codigo_union = st.query_params.get("join-code", "").strip()

    match st.session_state["tipo_sesion"]:
        case "profesor":
            with st.spinner('Abriendo el portal del profesor...'):
                from src.pantallas.pantalla_profesor import pantalla_profesor
            pantalla_profesor()

        case "estudiante":
            if st.session_state.get('_vista_estudiante') == 'perfil' and sesion_activa('estudiante'):
                from src.pantallas.perfil_estudiante import pantalla_perfil_estudiante
                pantalla_perfil_estudiante()
            else:
                with st.spinner('Abriendo el portal del estudiante...'):
                    from src.pantallas.pantalla_estudiante import pantalla_estudiante
                pantalla_estudiante(inscripcion_pendiente=bool(codigo_union))

        case "administrador":
            with st.spinner('Abriendo Administración...'):
                from src.pantallas.pantalla_administrador import pantalla_administrador
            pantalla_administrador()

        case None:
            from src.pantallas.pantalla_inicio import pantalla_inicio
            pantalla_inicio()
            if codigo_union:
                st.info('Tienes un enlace de inscripción. Continúa en el portal del estudiante para utilizarlo.')
                st.button('Continuar con la inscripción', on_click=seleccionar_portal, args=('estudiante',))

    if codigo_union and st.session_state['tipo_sesion'] == 'estudiante' and sesion_activa("estudiante"):
        from src.componentes.dialogo_inscripcion_automatica import dialogo_inscripcion_automatica
        dialogo_inscripcion_automatica(codigo_union, st.session_state.sesion_token)


principal()
