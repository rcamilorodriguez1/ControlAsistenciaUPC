import streamlit as st

def tarjeta_materia(nombre, codigo, seccion, estadisticas=None, al_pie=None):
    partes = []

    partes.append(
        '<div style="background-color:#FFFFFF; padding:26px 28px; border-radius:22px; '
        'border:1px solid #D7E6C2; box-shadow:0 6px 18px rgba(27, 46, 16, 0.06); '
        'margin-bottom:20px; transition:box-shadow 0.25s ease, transform 0.25s ease;">'
    )
    partes.append(
        '<div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">'
        f'<h3 style="margin:0px; color:#1B2E10; font-size:1.4rem; font-weight:800;">{nombre}</h3>'
        '<span style="background:#6FA82E22; color:#1B2E10; border:1px solid #6FA82E; '
        'padding:4px 12px; border-radius:999px; font-size:0.8rem; font-weight:700; '
        f'white-space:nowrap;">{codigo}</span>'
        '</div>'
    )
    partes.append(
        f'<p style="color:#5E6E52; margin:10px 0 0; font-size:0.95rem;">'
        f'Sección: <b style="color:#1B2E10;">{seccion}</b></p>'
    )

    if estadisticas:
        partes.append('<div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:18px;">')
        for icono, etiqueta, valor in estadisticas:
            partes.append(
                '<div style="background:#F3F8EC; border:1px solid #D7E6C2; padding:8px 14px; '
                'border-radius:14px; font-size:0.88rem; color:#1B2E10; display:flex; '
                'align-items:center; gap:6px;">'
                f'<span>{icono}</span><b>{valor}</b>'
                f'<span style="color:#5E6E52;">{etiqueta}</span>'
                '</div>'
            )
        partes.append('</div>')

    partes.append('</div>')

    html = "".join(partes)

    st.markdown(html, unsafe_allow_html=True)

    if al_pie:
        al_pie()
