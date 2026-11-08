import streamlit as st


def ir_a_inicio():
    st.session_state["tipo_sesion"] = None

def encabezado_inicio():

    logo_url= "https://i.ibb.co/YTYGn5qV/logo.png"  

    st.markdown(
        f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:30px; margin-top:10px" >
        <img src="{logo_url}" style="height:100px;"  />
        <h1 style="text-align:center; color:#1B2E10" >Control De Asistencia UPC</h1>
    </div>


        """,
        unsafe_allow_html=True,
    )


def encabezado_panel():

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
        st.button(
            "Volver al inicio",
            type="primary",
            key="go_home_button",
            on_click=ir_a_inicio,
            shortcut="Ctrl+Backspace",
            width="stretch",
        )

    st.markdown(
        """
        <h1 style="text-align:center; color:#1B2E10; margin-bottom:30px;">Control De Asistencia UPC</h1>
        """,
        unsafe_allow_html=True,
    )
