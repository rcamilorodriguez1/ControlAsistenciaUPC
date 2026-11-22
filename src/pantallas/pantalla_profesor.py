import streamlit as st


from src.base_datos.bd import existe_profesor, crear_profesor, iniciar_sesion_profesor, obtener_materias_profesor, obtener_asistencia_profesor, obtener_estudiantes_matriculados, obtener_resumen_profesor

from src.servicios.biometria_diferida import predecir_asistencia

from src.componentes.encabezado import encabezado_panel, introduccion
from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.tarjeta_materia import tarjeta_materia
from src.componentes.dialogo_crear_materia import dialogo_crear_materia
from src.componentes.dialogo_compartir_materia import dialogo_compartir_materia
from src.componentes.dialogo_agregar_foto import dialogo_agregar_foto
from src.componentes.dialogo_resultado_asistencia import dialogo_resultado_asistencia
from src.componentes.dialogo_asistencia_voz import dialogo_asistencia_voz
from src.componentes.selector_clase import selector_clase
from src.utilidades.imagenes import abrir_foto, vista_previa_foto
from src.componentes.seguridad_claves import mostrar_fortaleza, mostrar_coincidencia
from src.componentes.conflicto_sesion import mostrar_conflicto_sesion
from src.utilidades.sesiones import sesion_incompatible
from src.utilidades.fecha_hora import convertir_a_hora_colombia, hora_actual_colombia
from src.servicios.estados_asistencia import PRESENTE, AUSENTE, SIN_MUESTRA, ETIQUETAS
from src.servicios.cuentas import autorizar_alta_docente
from src.utilidades.sesiones import (
    sesion_activa, iniciar_sesion, salir_al_portal, cambiar_formulario_profesor,
    preparar_toma, reiniciar_toma, limpiar_asistencia, guardar_resultado,
    obtener_resultado, invalidar_resultado,
)


def pantalla_profesor():

    if sesion_activa("profesor"):
        panel_profesor()
    elif sesion_incompatible('profesor') or "tipo_ingreso_profesor" not in st.session_state or st.session_state.tipo_ingreso_profesor == "iniciar_sesion":
        pantalla_login_profesor()
    elif st.session_state.tipo_ingreso_profesor == "registrarse":
        pantalla_registro_profesor()
    elif st.session_state.tipo_ingreso_profesor == 'recuperar':
        from src.componentes.recuperar_clave import recuperar_clave_profesor
        recuperar_clave_profesor()


def panel_profesor():
    datos_profesor = st.session_state.datos_profesor

    encabezado_panel('profesor', autenticado=True)
    introduccion('Portal del profesor', f"Bienvenido, {datos_profesor['nombre']}",
                 'Toma asistencia, gestiona tus materias y revisa los registros de cada clase.')

    from src.interfaz.navegacion import abrir_perfil
    st.button('Consultar mi agenda', key='abrir_agenda_docente', type='tertiary',
              icon=':material/calendar_month:', on_click=abrir_perfil)

    if "pestana_actual_profesor" not in st.session_state:
        st.session_state.pestana_actual_profesor = "tomar_asistencia"

    with st.container(key='navegacion_docente'):
        tab1, tab2, tab3, tab4 = st.columns(4)

        with tab1:
            tipo1 = "primary" if st.session_state.pestana_actual_profesor == "tomar_asistencia" else "tertiary"
            if st.button("Tomar Asistencia", type=tipo1, width="stretch", icon=":material/ar_on_you:"):
                st.session_state.pestana_actual_profesor = "tomar_asistencia"
                st.rerun()        

        with tab2:
            tipo2 = "primary" if st.session_state.pestana_actual_profesor == "gestionar_materias" else "tertiary"
            if st.button("Gestionar Materias", type=tipo2, width="stretch", icon=":material/book_ribbon:"):
                st.session_state.pestana_actual_profesor = "gestionar_materias"
                st.rerun()        

        with tab3:
            tipo3 = "primary" if st.session_state.pestana_actual_profesor == "registros_asistencia" else "tertiary"
            if st.button("Registros de Asistencia", type=tipo3, width="stretch", icon=":material/library_books:"):
                st.session_state.pestana_actual_profesor = "registros_asistencia"
                st.rerun()
        with tab4:
            tipo4 = 'primary' if st.session_state.pestana_actual_profesor == 'excepciones' else 'tertiary'
            if st.button('Excepciones de acceso', type=tipo4, width='stretch', icon=':material/key:'):
                st.session_state.pestana_actual_profesor = 'excepciones'
                st.rerun()

    st.divider()


    if st.session_state.pestana_actual_profesor == "tomar_asistencia":
        pestana_tomar_asistencia()
    if st.session_state.pestana_actual_profesor == "gestionar_materias":
        pestana_gestionar_materias()
    if st.session_state.pestana_actual_profesor == "registros_asistencia":
        pestana_registros_asistencia()
    if st.session_state.pestana_actual_profesor == 'excepciones':
        from src.componentes.excepciones_docentes import gestionar_excepciones_docentes
        gestionar_excepciones_docentes()


    pie_pagina_panel()


def pestana_tomar_asistencia():
    import numpy as np
    id_profesor = st.session_state.datos_profesor["profesor_id"]
    st.header("Asistencia con Inteligencia Artificial")

    materias = obtener_materias_profesor(id_profesor)

    if not materias:
        limpiar_asistencia()
        st.info('Tu panel está listo. Crea una materia y comparte su código para recibir estudiantes.')
        if st.button('Crear mi primera materia', type='primary'):
            dialogo_crear_materia(id_profesor, st.session_state.sesion_token)
        return 

    opciones_materia = {m["materia_id"]: f"{m['nombre']} - {m['codigo_materia']}" for m in materias}

    col1, = st.columns(1)

    with col1, st.container(key='selector_academico_materia'):
        if 'materia_asistencia' not in st.session_state:
            anterior = st.session_state.get('materia_asistencia_id')
            st.session_state['materia_asistencia'] = anterior if anterior in opciones_materia else next(iter(opciones_materia))
        id_materia_seleccionada = st.selectbox(
            "Selecciona una Materia", options=list(opciones_materia),
            format_func=opciones_materia.get, key="materia_asistencia",
            placeholder='Selecciona una materia',
        )
        etiqueta_materia_seleccionada = opciones_materia[id_materia_seleccionada]
        materia_seleccionada = next(
            m
            for m in materias
            if m["materia_id"] == id_materia_seleccionada
        )
        materia_sin_estudiantes = materia_seleccionada["total_estudiantes"] == 0
        if materia_sin_estudiantes:
            st.info("Esta materia aún no tiene estudiantes matriculados. Comparte el enlace de inscripción antes de tomar asistencia.")

    clase = selector_clase(id_materia_seleccionada, id_profesor)
    contexto = preparar_toma(id_materia_seleccionada, clase_id=clase['clase_id'] if clase else None)
    if clase is None:
        st.info('Selecciona una clase o crea su horario antes de tomar asistencia.')
        return
    if clase['estado'] == 'CONFIRMADA':
        if obtener_resultado() or st.session_state.imagenes_asistencia:
            reiniciar_toma()
        st.info('Esta clase ya tiene asistencia confirmada. Consulta Registros de Asistencia; no se añadirá una segunda toma.')
        return
    if st.button("Agregar Fotos", type="primary", icon=":material/photo_prints:", width="stretch", disabled=materia_sin_estudiantes):
        dialogo_agregar_foto(contexto)

    st.divider()

    if st.session_state.imagenes_asistencia:
        st.header("Fotos Agregadas")
        columnas_galeria = st.columns(4)

        for idx, img in enumerate(st.session_state.imagenes_asistencia):
            with columnas_galeria[idx % 4]:
                st.image(vista_previa_foto(img), width="stretch", caption=f"Foto {idx+1}")

    hay_fotos = bool(st.session_state.imagenes_asistencia)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Borrar Todas las Fotos", width="stretch", type="tertiary", icon=":material/delete:", disabled=not hay_fotos):
            reiniciar_toma()
            st.success("Todas las imágenes fueron eliminadas")
            st.rerun()

    with c2:
        if st.button("Ejecutar Análisis Facial", width="stretch", type="primary", icon=":material/analytics:", disabled=not hay_fotos or materia_sin_estudiantes):
            invalidar_resultado()
            with st.spinner("Escaneando fotos del salón de clases..."):
                estudiantes_matriculados = obtener_estudiantes_matriculados(id_materia_seleccionada)
                if not estudiantes_matriculados:
                    st.warning(f"No hay estudiantes matriculados en {etiqueta_materia_seleccionada}")
                    return

                ids_detectados = {}

                try:
                    for idx, img in enumerate(st.session_state.imagenes_asistencia):
                        with abrir_foto(img) as imagen:
                            img_np = np.asarray(imagen)
                            detectado, ids_modelo, _ = predecir_asistencia(img_np,
                                permitidos={e['estudiante_id'] for e in estudiantes_matriculados})
                            del img_np
                        if not ids_modelo and any(e.get('embedding_facial') for e in estudiantes_matriculados):
                            raise RuntimeError('Modelo facial no disponible para perfiles con muestra.')
                        if detectado:
                            for sid in detectado.keys():
                                id_estudiante = int(sid)
                                ids_detectados.setdefault(id_estudiante, []).append(f"Foto {idx+1}")
                except Exception:
                    st.error('Análisis facial fallido. No se generó asistencia. Vuelve a intentar o usa otro método.')
                    return

                resultados, asistencia_a_registrar = [], []

                marca_tiempo_actual = hora_actual_colombia().isoformat()
                for estudiante in estudiantes_matriculados:
                    fuentes = ids_detectados.get(int(estudiante["estudiante_id"]), [])
                    muestra = estudiante.get('embedding_facial')
                    tiene_muestra = muestra is not None and len(muestra) > 0
                    esta_presente = bool(fuentes) if tiene_muestra else None
                    estado = (SIN_MUESTRA if not tiene_muestra else PRESENTE if esta_presente else AUSENTE)

                    resultados.append(
                        {
                            "Nombre": estudiante["nombre"],
                            "ID": estudiante["estudiante_id"],
                            "Fuente": ( ", ".join(fuentes) if esta_presente else "--" ),
                            "Estado": ETIQUETAS[estado],
                        }
                    )

                    asistencia_a_registrar.append(
                        {
                            "fecha_hora" : marca_tiempo_actual,
                            "materia_id" : id_materia_seleccionada,
                            "estudiante_id" : estudiante["estudiante_id"],
                            "presente": esta_presente, "estado_deteccion": estado,
                        }
                    )

                resultado_id = guardar_resultado(contexto, resultados, asistencia_a_registrar, "facial")
                dialogo_resultado_asistencia(resultado_id)

    with c3:
        if st.button("Usar Asistencia por Voz", type="secondary", width="stretch", icon=":material/mic:", disabled=materia_sin_estudiantes):
            dialogo_asistencia_voz(contexto)

    pendiente = obtener_resultado()
    if pendiente and pendiente["origen"] == "facial":
        if st.button("Revisar resultado pendiente", key="revisar_resultado_facial"):
            dialogo_resultado_asistencia(pendiente["id"])

                


def pestana_gestionar_materias():
    id_profesor = st.session_state.datos_profesor["profesor_id"]
    col1, col2 = st.columns(2)
    with col1:
        st.header("Gestión de Materias")
    with col2:
        if st.button("Crear nueva materia", type='primary', width="content", key='crear_nueva_materia'):
            dialogo_crear_materia(id_profesor, st.session_state.sesion_token)

    # Listar todas las materias
    materias = obtener_materias_profesor(id_profesor)
    if materias:
        for materia in materias:
            estadisticas = [
                ("🧑‍🎓👩‍🎓", "Estudiantes", materia["total_estudiantes"]),
                ("🕰️", "Clases", materia["total_clases"]),
            ]
            def boton_compartir():
                if st.button(f"Compartir Código: {materia['nombre']}", key=f"share_{materia['codigo_materia']}", type="primary", icon=":material/share:"):
                    dialogo_compartir_materia(materia["nombre"], materia["codigo_materia"])
                st.space(size="xxsmall")

            tarjeta_materia(
                nombre = materia["nombre"],
                codigo = materia["codigo_materia"],
                seccion = materia["seccion"],
                estadisticas = estadisticas,
                al_pie=boton_compartir
            )
    else:
        st.info("No se encontró ninguna materia. Crea tu primera materia")


def pestana_registros_asistencia():
    import pandas as pd
    st.header("Registros de Asistencia")

    id_profesor = st.session_state.datos_profesor["profesor_id"]

    registros = obtener_asistencia_profesor(id_profesor)

    if not registros:
        st.warning("No se encontró ninguna asistencia")
        return

    datos = [] 

    for r in registros:
        fh = r.get("fecha_clase") or r.get("fecha_hora")
        
        if fh:
            dt = convertir_a_hora_colombia(fh)
            hora_formateada = dt.strftime("%Y-%m-%d %I:%M %p")
        else:
            hora_formateada = "N/D"

        datos.append(
            {
                "Clase": r['clase_id'],
                "Hora": hora_formateada,
                "Materia": r["materia"]["nombre"],
                "Código de Materia": r["materia"]["codigo_materia"],
                "presente": bool(r.get("presente", False)),
                "corregido": bool(r.get('corregido_manual', False)),
                "Origen": r.get('origen', 'LEGADO'),
            }
        )

    df = pd.DataFrame(datos)

    resumen = (
        df.groupby(["Clase", "Hora", "Materia", "Código de Materia", "Origen"])
        .agg(
            Cantidad_Presentes = ("presente", "sum"),
            Cantidad_Total = ("presente", "count"),
            Correcciones = ('corregido', 'sum')
        ).reset_index()   # regresa el dataframe al formato original previo a la agrupación
    )

    resumen["Estadísticas de Asistencia"] = (
        "☑️ " + resumen["Cantidad_Presentes"].astype(str) + "/" + resumen["Cantidad_Total"].astype(str) + " Estudiantes"
    )

    df_mostrar = ( resumen.sort_values(by="Clase", ascending=False)
                    [["Clase", "Hora", "Materia", "Código de Materia", "Origen", "Estadísticas de Asistencia", "Correcciones"]]
                   )

    st.dataframe(df_mostrar, width="stretch", hide_index=True)




def procesar_login_profesor(usuario, contrasena):
    if not usuario or not contrasena:
        st.error("¡Todos los campos son obligatorios!")
        return False

    try:
        profesor = iniciar_sesion_profesor(usuario, contrasena)
    except ValueError:
        return False

    if profesor:
        iniciar_sesion("profesor", profesor)
        return True

    else:
        return False


def pantalla_login_profesor():
    conflicto = bool(sesion_incompatible('profesor'))
    encabezado_panel()

    with st.container(key='acceso_docente'):
        st.caption('PORTAL DOCENTE')
        if 'aviso_recuperacion_profesor' in st.session_state:
            st.success(st.session_state.pop('aviso_recuperacion_profesor'))
        st.header("Inicia sesión con tu contraseña", text_alignment="left")
        st.space(size="small")

        token = st.session_state.sesion_token
        usuario_profesor = st.text_input("Ingresa tu Usuario", placeholder="Ej. docente.upc", max_chars=100, key=f"auth_profesor_usuario_login_{token}")
        contrasena_profesor = st.text_input("Ingresa tu Contraseña", type="password", placeholder="********", key=f"auth_profesor_clave_login_{token}")
        st.divider()

        btnc1, btnc2 = st.columns(2)

        with btnc1:
            if st.button("Iniciar Sesión", disabled=conflicto, type="primary", icon=":material/login:", shortcut="control+enter", width="stretch"):
                if procesar_login_profesor(usuario_profesor, contrasena_profesor):
                    st.toast(f"Bienvenido de nuevo {usuario_profesor}", icon="👋")
                    st.rerun()
                else:
                    st.error("Credenciales inválidas")


        with btnc2:
            st.button("Registrarme en su lugar", disabled=conflicto, type="secondary", icon=":material/passkey:", width="stretch",
                      on_click=cambiar_formulario_profesor, args=("registrarse",))
        st.button('Olvidé mi contraseña',disabled=conflicto,type='tertiary',key='olvide_clave_docente',
                  on_click=cambiar_formulario_profesor,args=('recuperar',))

    mostrar_conflicto_sesion('profesor')
    pie_pagina_panel()


def procesar_registro_profesor(usuario_profesor, contrasena_profesor, nombre_profesor, confirmar_contrasena, codigo_alta=''):
    if not usuario_profesor or not nombre_profesor or not contrasena_profesor or not confirmar_contrasena:
        return False, "¡Todos los campos son obligatorios!"

    if confirmar_contrasena!=contrasena_profesor:
        return False, "¡La confirmación de contraseña no coincide!"

    try:
        autorizar_alta_docente(codigo_alta)
        if existe_profesor(usuario_profesor):
            return False, 'Este nombre de usuario ya está en uso'
        crear_profesor(usuario_profesor, contrasena_profesor, nombre_profesor)
        return True, "Registro de profesor exitoso"

    except ValueError as exc:
        return False, str(exc)
    except Exception:
        return False, "Ocurrió un error al registrar al profesor"


def pantalla_registro_profesor():
    encabezado_panel()

    with st.container(key='registro_docente'):
        st.header("Registra tu perfil de profesor", text_alignment="left")
        st.space(size="small")

        token = st.session_state.sesion_token
        usuario_profesor = st.text_input("Ingresa tu Usuario", placeholder="Ej. docente.upc", max_chars=100, key=f"auth_profesor_usuario_alta_{token}")
        nombre_profesor = st.text_input("Ingresa tu Nombre", placeholder="Tu nombre completo", max_chars=200, key=f"auth_profesor_nombre_alta_{token}")

        contrasena_profesor = st.text_input("Ingresa tu Contraseña", type="password", placeholder="********", key=f"auth_profesor_clave_alta_{token}", live='300ms', autocomplete='new-password')
        mostrar_fortaleza(contrasena_profesor, usuario=usuario_profesor, nombre=nombre_profesor)
        confirmar_contrasena = st.text_input("Confirma tu Contraseña", type="password", placeholder="********", key=f"auth_profesor_confirmar_alta_{token}", live='300ms', autocomplete='new-password')
        mostrar_coincidencia(contrasena_profesor, confirmar_contrasena)
        codigo_alta = st.text_input('Autorización docente', type='password', key=f'auth_profesor_autorizacion_{token}')
        st.space("xxsmall")

        btnc1, btnc2 = st.columns(2)

        with btnc1:
            if st.button("Registrarme Ahora", type="primary", icon=":material/person_add:", shortcut="control+enter", width="stretch"):
                exito, mensaje = procesar_registro_profesor(usuario_profesor, contrasena_profesor, nombre_profesor, confirmar_contrasena, codigo_alta)
                if exito:
                    st.success(mensaje)
                    st.session_state.tipo_ingreso_profesor = "iniciar_sesion"
                    st.rerun()
                else:
                    st.error(mensaje)


        with btnc2:
            st.button("Iniciar Sesión en su lugar", type="secondary", icon=":material/passkey:", width="stretch",
                      on_click=cambiar_formulario_profesor, args=("iniciar_sesion",))
                     

    pie_pagina_panel()
