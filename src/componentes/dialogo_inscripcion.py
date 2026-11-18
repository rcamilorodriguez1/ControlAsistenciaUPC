import streamlit as st
from src.base_datos.bd import matricular_estudiante_en_materia, obtener_materia_por_codigo, esta_estudiante_matriculado
import oracledb
from src.utilidades.sesiones import misma_sesion

@st.dialog("Inscribirse en una Materia")
def dialogo_inscripcion(token):
    if not misma_sesion("estudiante", token):
        st.warning("La sesión cambió. Vuelve a iniciar sesión para inscribirte.")
        return
    st.write("Ingresa el código de materia proporcionado por tu profesor para inscribirte")
    codigo_ingresado = st.text_input("Código de Materia", placeholder="Ej. CSE101", key=f"codigo_inscripcion_{token}").strip()

    if st.button("Inscribirme Ahora", type="primary", width="stretch"):
        if codigo_ingresado:
            try:
                materia = obtener_materia_por_codigo(codigo_ingresado)
            except ValueError as exc:
                st.warning(str(exc))
                return
            if materia:
                id_estudiante = st.session_state.datos_estudiante["estudiante_id"]
                nombre_estudiante = st.session_state.datos_estudiante["nombre"]

                if esta_estudiante_matriculado(materia["materia_id"], id_estudiante):
                    st.warning(f"{nombre_estudiante} ya está inscrito en la materia {materia['nombre']}")
                else:
                    try:
                        matricular_estudiante_en_materia(id_estudiante, materia["materia_id"])
                    except oracledb.IntegrityError as exc:
                        if exc.args[0].code != 1:
                            raise
                        st.info("Ya estás inscrito en esta materia.")
                        return
                    except (ValueError, PermissionError) as exc:
                        st.warning(str(exc))
                        return
                    st.success(f"{nombre_estudiante} se inscribió exitosamente en la materia {materia['nombre']}")
                    st.rerun()
            else:
                st.warning("No existe una materia con ese código.")

        else:
            st.warning("Por favor ingresa un código de materia") 
