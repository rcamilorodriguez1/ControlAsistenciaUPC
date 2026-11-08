import streamlit as st
import numpy as np
import pandas as pd

import time
from datetime import datetime, timezone, timedelta
ZONA_COLOMBIA = timezone(timedelta(hours=-5), "COT")  # Colombia: UTC-5, sin horario de verano

from src.interfaz.diseno_base import (
    estilo_fondo_panel,
    estilo_diseno_base,
    estilo_espaciado_compacto,
)

from src.base_datos.bd import existe_profesor, crear_profesor, iniciar_sesion_profesor, obtener_materias_profesor, obtener_asistencia_profesor, obtener_estudiantes_matriculados, obtener_resumen_profesor

from src.canalizaciones.canalizacion_facial import predecir_asistencia

from src.componentes.encabezado import encabezado_panel
from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.tarjeta_materia import tarjeta_materia
from src.componentes.dialogo_crear_materia import dialogo_crear_materia
from src.componentes.dialogo_compartir_materia import dialogo_compartir_materia
from src.componentes.dialogo_agregar_foto import dialogo_agregar_foto
from src.componentes.dialogo_resultado_asistencia import dialogo_resultado_asistencia
from src.componentes.dialogo_asistencia_voz import dialogo_asistencia_voz


def pantalla_profesor():

    estilo_fondo_panel()
    estilo_diseno_base()
    estilo_espaciado_compacto()

    if "datos_profesor" in st.session_state:
        panel_profesor()
    elif "tipo_ingreso_profesor" not in st.session_state or st.session_state.tipo_ingreso_profesor == "iniciar_sesion":
        pantalla_login_profesor()
    elif st.session_state.tipo_ingreso_profesor == "registrarse":
        pantalla_registro_profesor()


def panel_profesor():
    datos_profesor = st.session_state.datos_profesor

    logo_url= "https://i.ibb.co/YTYGn5qV/logo.png"  

    logo_col, spacer_col, action_col = st.columns([1.2, 2.2, 2.2], vertical_alignment="center")

    with logo_col:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:flex-start;">
                <img src="{logo_url}" style="height:100px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_col:
        if st.button( "Cerrar sesión",  type="primary",  key="loginbackbtn", shortcut="Ctrl+Backspace", width="stretch"):
            st.session_state["sesion_iniciada"] = False
            del st.session_state.datos_profesor
            st.rerun()

    st.markdown(
        """
        <h1 style="text-align:center; color:#1B2E10; margin-bottom:30px;">Control De Asistencia UPC</h1>
        """,
        unsafe_allow_html=True,
    )

    st.header(f"""Bienvenido, {datos_profesor['nombre']} """)

    resumen = obtener_resumen_profesor(datos_profesor["profesor_id"])

    with st.container(border=True):
        k1, k2, k3 = st.columns(3)
        k1.metric("Materias Activas", resumen["total_materias"])
        k2.metric("Estudiantes Matriculados", resumen["total_estudiantes"])
        k3.metric("Asistencia Promedio", f"{resumen['asistencia_promedio']:.0f}%")

    st.space()

    # st.space()

    if "pestana_actual_profesor" not in st.session_state:
        st.session_state.pestana_actual_profesor = "tomar_asistencia"

    tab1, tab2, tab3 = st.columns(3)

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

    st.divider()


    if st.session_state.pestana_actual_profesor == "tomar_asistencia":
        pestana_tomar_asistencia()
    if st.session_state.pestana_actual_profesor == "gestionar_materias":
        pestana_gestionar_materias()
    if st.session_state.pestana_actual_profesor == "registros_asistencia":
        pestana_registros_asistencia()


    pie_pagina_panel()


def pestana_tomar_asistencia():
    id_profesor = st.session_state.datos_profesor["profesor_id"]
    st.header("Asistencia con Inteligencia Artificial")

    if "imagenes_asistencia" not in st.session_state:
        st.session_state.imagenes_asistencia = [] 

    materias = obtener_materias_profesor(id_profesor)

    if not materias:
        st.warning("¡Aún no has creado ninguna materia! ¡Crea una para comenzar!")
        return 

    opciones_materia = { f"{m['nombre']} - {m['codigo_materia']}" : m["materia_id"] for m in materias }

    col1, col2 = st.columns([3,1], vertical_alignment="bottom")

    with col1:
        etiqueta_materia_seleccionada = st.selectbox("Selecciona una Materia", options=list(opciones_materia.keys()))

    with col2:
        if st.button("Agregar Fotos", type="primary", icon=":material/photo_prints:", width="stretch"):
            dialogo_agregar_foto()

    id_materia_seleccionada = opciones_materia[etiqueta_materia_seleccionada]

    st.divider()

    if st.session_state.imagenes_asistencia:
        st.header("Fotos Agregadas")
        columnas_galeria = st.columns(4)

        for idx, img in enumerate(st.session_state.imagenes_asistencia):
            with columnas_galeria[idx % 4]:
                st.image(img, width="stretch", caption=f"Foto {idx+1}")

    hay_fotos = bool(st.session_state.imagenes_asistencia)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Borrar Todas las Fotos", width="stretch", type="tertiary", icon=":material/delete:", disabled=not hay_fotos):
            st.session_state.imagenes_asistencia = []
            st.session_state.claves_subidas_procesadas = set()
            st.session_state.clave_camara_procesada = None
            st.success("Todas las imágenes fueron eliminadas")
            time.sleep(1)
            st.rerun()

    with c2:
        if st.button("Ejecutar Análisis Facial", width="stretch", type="primary", icon=":material/analytics:", disabled=not hay_fotos):
            with st.spinner("Escaneando fotos del salón de clases..."):
                ids_detectados = {}

                for idx, img in enumerate(st.session_state.imagenes_asistencia):
                    img_np = np.array(img.convert("RGB"))
                    detectado, _, _ = predecir_asistencia(img_np)

                    if detectado:
                        for sid in detectado.keys():
                            id_estudiante = int(sid)

                            ids_detectados.setdefault(id_estudiante, []).append(f"Foto {idx+1}")

                estudiantes_matriculados = obtener_estudiantes_matriculados(id_materia_seleccionada)

                if not estudiantes_matriculados:
                    st.warning(f"No hay estudiantes matriculados en {etiqueta_materia_seleccionada}")

                else:
                    resultados, asistencia_a_registrar = [], []

                    marca_tiempo_actual = datetime.now(ZONA_COLOMBIA).isoformat()
                    for estudiante in estudiantes_matriculados:
                        fuentes = ids_detectados.get(int(estudiante["estudiante_id"]), [])
                        esta_presente = len(fuentes) > 0

                        resultados.append(
                            {
                                "Nombre": estudiante["nombre"],
                                "ID": estudiante["estudiante_id"],
                                "Fuente": ( ", ".join(fuentes) if esta_presente else "--" ),
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

                    dialogo_resultado_asistencia(pd.DataFrame(resultados), asistencia_a_registrar)

    with c3:
        if st.button("Usar Asistencia por Voz", type="secondary", width="stretch", icon=":material/mic:"):
            dialogo_asistencia_voz(id_materia_seleccionada)    

                


def pestana_gestionar_materias():
    id_profesor = st.session_state.datos_profesor["profesor_id"]
    col1, col2 = st.columns(2)
    with col1:
        st.header("Gestión de Materias")
    with col2:
        if st.button("Crear nueva Materia", width="stretch"):
            dialogo_crear_materia(id_profesor)

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
    st.header("Registros de Asistencia")

    id_profesor = st.session_state.datos_profesor["profesor_id"]

    registros = obtener_asistencia_profesor(id_profesor)

    if not registros:
        st.warning("No se encontró ninguna asistencia")
        time.sleep(1)
        return

    datos = [] 

    for r in registros:
        fh = r.get("fecha_hora")
        
        if fh:
            dt = datetime.fromisoformat(fh)
            if dt.tzinfo:
                dt = dt.astimezone(ZONA_COLOMBIA)
            else:
                dt = dt.replace(tzinfo=timezone.utc).astimezone(ZONA_COLOMBIA)
            hora_formateada = dt.strftime("%Y-%m-%d %I:%M %p")
            grupo_fh = dt.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            hora_formateada = "N/D"
            grupo_fh = None

        datos.append(
            {
                "grupo_fh": grupo_fh,
                "Hora": hora_formateada,
                "Materia": r["materia"]["nombre"],
                "Código de Materia": r["materia"]["codigo_materia"],
                "presente": bool(r.get("presente", False))
            }
        )

    df = pd.DataFrame(datos)

    resumen = (
        df.groupby(["grupo_fh", "Hora", "Materia", "Código de Materia"])
        .agg(
            Cantidad_Presentes = ("presente", "sum"),
            Cantidad_Total =  ("presente", "count")
        ).reset_index()   # regresa el dataframe al formato original previo a la agrupación
    )

    resumen["Estadísticas de Asistencia"] = (
        "☑️ " + resumen["Cantidad_Presentes"].astype(str) + "/" + resumen["Cantidad_Total"].astype(str) + " Estudiantes"
    )

    df_mostrar = ( resumen.sort_values(by="grupo_fh", ascending=False)
                    [["Hora", "Materia", "Código de Materia", "Estadísticas de Asistencia"]]
                   )

    st.dataframe(df_mostrar, width="stretch", hide_index=True)




def procesar_login_profesor(usuario, contrasena):
    if not usuario or not contrasena:
        st.error("¡Todos los campos son obligatorios!")
        return False

    profesor = iniciar_sesion_profesor(usuario, contrasena)

    if profesor:
        st.session_state.rol_usuario = "profesor"
        st.session_state.datos_profesor = profesor
        st.session_state.sesion_iniciada = True
        return True

    else:
        return False


def pantalla_login_profesor():
    encabezado_panel()

    st.header("Inicia sesión con tu contraseña", text_alignment="center")
    st.space(size="small")

    usuario_profesor = st.text_input("Ingresa tu Usuario", placeholder="Ej. MihirGupta665 " )
    contrasena_profesor = st.text_input("Ingresa tu Contraseña", type="password", placeholder="********")
    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button("Iniciar Sesión", type="tertiary", icon=":material/passkey:", shortcut="control+enter", width="stretch"):
            if procesar_login_profesor(usuario_profesor, contrasena_profesor):
                st.toast(f"Bienvenido de nuevo {usuario_profesor}", icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciales inválidas")


    with btnc2:
        if st.button("Registrarme en su lugar", type="secondary", icon=":material/passkey:", width="stretch"):
            st.session_state.tipo_ingreso_profesor = "registrarse" 

    pie_pagina_panel()


def procesar_registro_profesor(usuario_profesor, contrasena_profesor, nombre_profesor, confirmar_contrasena):
    if not usuario_profesor or not nombre_profesor or not contrasena_profesor or not confirmar_contrasena:
        return False, "¡Todos los campos son obligatorios!"

    if confirmar_contrasena!=contrasena_profesor:
        return False, "¡La confirmación de contraseña no coincide!"

    if existe_profesor(usuario_profesor):
        return False, "Este nombre de usuario ya está en uso"

    try:
        crear_profesor(usuario_profesor, contrasena_profesor, nombre_profesor)
        return True, "Registro de profesor exitoso"

    except Exception as e:
        return False, "Ocurrió un error al registrar al profesor"


def pantalla_registro_profesor():
    encabezado_panel()

    st.header("Registra tu perfil de profesor", text_alignment="center")
    st.space(size="small")

    usuario_profesor = st.text_input("Ingresa tu Usuario", placeholder="Ej. MihirGupta665 " )
    nombre_profesor = st.text_input("Ingresa tu Nombre", placeholder="Ej. Mihir Gupta" )

    contrasena_profesor = st.text_input("Ingresa tu Contraseña", type="password", placeholder="********")
    confirmar_contrasena = st.text_input("Confirma tu Contraseña", type="password", placeholder="********")
    st.space("xxsmall")

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button("Registrarme Ahora", type=    "tertiary", icon=":material/passkey:", shortcut="control+enter", width="stretch"):
            exito, mensaje = procesar_registro_profesor(usuario_profesor, contrasena_profesor, nombre_profesor, confirmar_contrasena)
            if exito:
                st.success(mensaje)
                import time
                time.sleep(2)
                st.session_state.tipo_ingreso_profesor = "iniciar_sesion"
                st.rerun()
            else:
                st.error(mensaje)


    with btnc2:
        if st.button("Iniciar Sesión en su lugar", type="secondary", icon=":material/passkey:", width="stretch"):
            st.session_state.tipo_ingreso_profesor = "iniciar_sesion"
                 

    pie_pagina_panel()
