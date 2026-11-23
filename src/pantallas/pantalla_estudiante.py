from src.componentes.gestion_cuenta import gestion_cuenta
import streamlit as st

from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.encabezado import encabezado_panel, introduccion
from src.componentes.dialogo_inscripcion import dialogo_inscripcion
from src.componentes.tarjeta_materia import tarjeta_materia

import logging

from src.base_datos.bd import obtener_todos_estudiantes, obtener_materias_estudiante, obtener_asistencia_estudiante, desmatricular_estudiante_de_materia, obtener_resumen_estudiante

from src.servicios.biometria_diferida import predecir_asistencia
from src.servicios.registro_estudiante import registrar_estudiante
from src.utilidades.muestra_facial import leer_foto_registro
from src.utilidades.biometria import MuestraInvalida
from src.utilidades.sesiones import sesion_activa, iniciar_sesion, salir_al_portal
from src.utilidades.sesiones import sesion_incompatible
from src.componentes.conflicto_sesion import mostrar_conflicto_sesion
from src.componentes.acceso_excepcional import acceso_excepcional
from src.componentes.estado_verificacion import mostrar_estado_verificacion
from src.servicios.verificacion_identidad import acreditar_biometria, registrar_fallo_biometrico, TIPOS_DOCUMENTO

_logger = logging.getLogger(__name__)

def panel_estudiante(inscripcion_pendiente=False):
    datos_estudiante = st.session_state.datos_estudiante
    id_estudiante = datos_estudiante["estudiante_id"]

    encabezado_panel('estudiante', autenticado=True)
    introduccion('Portal del estudiante', f"Bienvenido, {datos_estudiante['nombre']}",
                 'Inscríbete con el código de tu docente o administra tus matrículas actuales.')
    mostrar_estado_verificacion(datos_estudiante.get('estado_verificacion'))

    from src.interfaz.navegacion import abrir_perfil
    st.button('Ver mi asistencia y calendario', key='abrir_historial_estudiante', type='tertiary',
        icon=':material/calendar_month:', on_click=abrir_perfil)

    c1, c2 = st.columns(2)
    with c1:
        st.header("Tus Materias Inscritas")
    with c2:
        st.space()
        if st.button("Inscribirse en una Materia", type="primary", width="stretch", disabled=inscripcion_pendiente):
            dialogo_inscripcion(st.session_state.sesion_token)

    st.divider()

    with st.spinner("Cargando tus materias inscritas..."):
        materias = obtener_materias_estudiante(id_estudiante)
        registros = obtener_asistencia_estudiante(id_estudiante)
        if not materias:
            st.info('Todavía no tienes materias inscritas. Usa el código o el enlace que te comparta tu profesor.')

        mapa_estadisticas = {}

        for registro in registros:
            id_materia = registro["materia_id"]
            if id_materia not in mapa_estadisticas:
                mapa_estadisticas[id_materia] = {"total":0, "asistio":0}

            mapa_estadisticas[id_materia]["total"] += 1

            if registro.get("presente"):
                mapa_estadisticas[id_materia]["asistio"] += 1

        columnas = st.columns(2)    
        for i, nodo_materia in enumerate(materias):
            materia = nodo_materia["materia"]
            id_materia = materia["materia_id"]

            estadisticas = mapa_estadisticas.get(id_materia, {"total": 0, "asistio": 0})

            def boton_retirar():
                if st.button("Retirarse de esta materia", type="tertiary", width="stretch", icon=":material/delete_forever:", key=f"unenroll_{st.session_state.sesion_token}_{id_materia}"):
                    desmatricular_estudiante_de_materia(id_estudiante, id_materia)
                    st.toast(f"Te has retirado de {materia['nombre']} exitosamente")
                    st.rerun()

            with columnas[i%2]:
                tarjeta_materia(
                    nombre=materia["nombre"],
                    codigo=materia["codigo_materia"],
                    seccion=materia["seccion"],
                    estadisticas=[
                        ("🗓️", "Total", estadisticas["total"]),
                        ("☑️", "Asistió", estadisticas["asistio"]),
                    ],
                    al_pie=boton_retirar  
                )

    gestion_cuenta()
    pie_pagina_panel()


def pantalla_estudiante(inscripcion_pendiente=False):

    if sesion_activa("estudiante"):
        panel_estudiante(inscripcion_pendiente)
        return

    conflicto = bool(sesion_incompatible('estudiante'))
    if "mostrar_registro_estudiante" not in st.session_state:
        st.session_state.mostrar_registro_estudiante = False

    encabezado_panel()

    with st.container(key='acceso_estudiante'):
        st.caption('PORTAL DEL ESTUDIANTE')
        acceso_excepcional(deshabilitado=conflicto)
        st.header("Inicia sesión con tu Rostro")
        st.caption('Mira a la cámara con el rostro completo y buena iluminación. Si aún no tienes perfil, podrás registrarte después de la captura.')

        token = st.session_state.sesion_token
        fuente_foto = st.camera_input("Ubica tu rostro en el centro", disabled=conflicto, key=f"auth_estudiante_camara_{token}")
        if not fuente_foto:
            st.session_state.mostrar_registro_estudiante = False

        if fuente_foto and not conflicto and not st.session_state.mostrar_registro_estudiante:
            with st.spinner("La IA está escaneando..."):
                try:
                    imagen = leer_foto_registro(fuente_foto)
                    detectado, todos_ids, num_rostros = predecir_asistencia(imagen, rostro_unico=True)
                except MuestraInvalida as exc:
                    registrar_fallo_biometrico('MUESTRA_INVALIDA')
                    st.warning(str(exc))
                    return
                except Exception as exc:
                    registrar_fallo_biometrico('ERROR_TECNICO')
                    _logger.error('Fallo en acceso facial: tipo=%s', type(exc).__name__)
                    st.error('No se pudo analizar el rostro. Intenta nuevamente; no se creó ningún perfil.')
                    return

                if num_rostros == 0:
                    registrar_fallo_biometrico('MUESTRA_INVALIDA')
                    st.warning("¡No se encontró ningún rostro en la imagen!")
                elif num_rostros>1:
                    registrar_fallo_biometrico('MUESTRA_INVALIDA')
                    st.warning("Se encontraron múltiples rostros en la imagen")
                else:

                    if detectado:
                        id_estudiante = list(detectado.keys())[0]
                        todos_estudiantes = obtener_todos_estudiantes()
                        estudiante = next((e for e in todos_estudiantes if e["estudiante_id"]==id_estudiante), None)

                        if estudiante:
                            try:
                                iniciar_sesion("estudiante", acreditar_biometria(estudiante))
                            except (ValueError, PermissionError):
                                st.warning('No se pudo acreditar el acceso. Repite la captura o consulta con Gestión académica.')
                                return
                            st.toast(f"{estudiante['nombre']} - ¡Bienvenido de nuevo!")
                            st.rerun()
                        else:
                            registrar_fallo_biometrico('PRUEBA_RECHAZADA')
                            st.warning('La cuenta detectada ya no está disponible. Consulta con Gestión académica.')


                    else:    
                        registrar_fallo_biometrico('NO_COINCIDE')
                        st.info("¡Rostro no reconocido! Puede que seas un nuevo estudiante")
                        st.session_state.mostrar_registro_estudiante = True

        if not conflicto and st.session_state.mostrar_registro_estudiante and fuente_foto:
            with st.container(border=True):
                st.header("Registrar nuevo perfil")
                nuevo_nombre = st.text_input("Ingresa tu nombre", placeholder=" Ej. Mihir Gupta", key=f"auth_estudiante_nombre_{token}")
                tipo_documento = st.selectbox('Tipo de documento', TIPOS_DOCUMENTO, key=f'auth_estudiante_tipo_registro_{token}')
                documento = st.text_input('Número de documento', key=f'auth_estudiante_documento_registro_{token}', max_chars=40)

                st.subheader("(Opcional): Inscripción de voz")
                st.info('La voz es opcional. Si la grabas, habla de 3 a 30 segundos, con al menos 1,6 segundos de voz clara. Una grabación inválida debe repetirse o eliminarse antes de continuar.')

                audio_grabado = None

                try:
                    audio_grabado = st.audio_input(
                        f"Graba una frase corta para capturar tu voz. Ejemplo: 'Estoy presente profesor, mi nombre es {nuevo_nombre}'",
                        key=f"auth_estudiante_voz_{token}",
                    )
                except Exception:
                    st.error("Ocurrió un error al capturar la voz para la grabación")

                if st.button("Crear Cuenta", type="primary"):
                    if nuevo_nombre:
                        with st.spinner("Creando perfil..."):
                            try:
                                datos_respuesta = registrar_estudiante(nuevo_nombre, fuente_foto,
                                    audio_grabado.getvalue() if audio_grabado is not None else None,
                                    tipo_documento=tipo_documento, documento=documento)
                            except (ValueError, PermissionError) as exc:
                                st.warning(str(exc))
                            except Exception as exc:
                                _logger.error('Fallo de registro: tipo=%s', type(exc).__name__)
                                st.error('No se pudo confirmar el registro. Intenta acceder con tu rostro antes de repetirlo.')
                            else:
                                if datos_respuesta:
                                    try:
                                        iniciar_sesion("estudiante", acreditar_biometria(datos_respuesta[0]))
                                    except Exception as exc:
                                        _logger.error('Fallo al acreditar el alta: tipo=%s', type(exc).__name__)
                                        st.warning('El perfil se creó, pero no se pudo confirmar el acceso. Intenta iniciar sesión con tu rostro.')
                                        return
                                    st.toast(f"Bienvenido {nuevo_nombre} \n Perfil creado exitosamente")
                                    st.rerun()
                    else:
                        st.warning("¡Por favor ingresa tu nombre!")

    mostrar_conflicto_sesion('estudiante')
    pie_pagina_panel()
