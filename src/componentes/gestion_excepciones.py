"""Consola administrativa; no solicita diagnósticos ni conserva documentos completos."""
import streamlit as st
from src.base_datos import administracion
from src.servicios import excepciones_biometricas as servicio
from src.servicios.verificacion_identidad import CATEGORIAS, TIPOS_DOCUMENTO, ESTADOS


def gestion_excepciones():
    st.subheader('Verificación de identidad')
    st.caption('La aprobación habilita el método alternativo. El estado refleja la última verificación realizada, no la presencia de plantillas almacenadas.')
    busqueda = st.text_input('Buscar estudiante por nombre o código', max_chars=100, key='admin_verificacion_busqueda')
    filas = servicio.listar(busqueda)
    filtro = st.selectbox('Mostrar verificaciones', ['Todas', 'Excepción vigente', 'Último acceso excepcional', 'Verificación pendiente'])
    visibles = [f for f in filas if filtro == 'Todas' or
                (filtro == 'Excepción vigente' and f['excepcion_vigente']) or
                (filtro == 'Último acceso excepcional' and f['estado_verificacion'] == 'EXCEPCIONAL') or
                (filtro == 'Verificación pendiente' and f['estado_verificacion'] == 'PENDIENTE')]
    st.caption(f"{sum(f['estado_verificacion']=='EXCEPCIONAL' for f in filas)} estudiantes con última verificación excepcional · "
               f"{sum(bool(f['excepcion_vigente']) for f in filas)} autorizaciones vigentes")
    tabla = [{'Estudiante': f['nombre'], 'Código': f['codigo_institucional'],
              'Verificación': ESTADOS.get(f['estado_verificacion'], ESTADOS['PENDIENTE']),
              'Excepción vigente': 'Sí' if f['excepcion_vigente'] else 'No',
              'Documento': f.get('documento'), 'Categoría': f.get('categoria'),
              'Vencimiento': f.get('expira_en'), 'Última verificación': f.get('verificado_en')}
             for f in visibles]
    st.dataframe(tabla, hide_index=True, width='stretch')
    if st.button('Preparar exportación de verificaciones', disabled=not visibles):
        csv = administracion.exportar_csv('GESTION', visibles)
        st.download_button('Descargar verificaciones CSV', csv, 'verificaciones.csv', 'text/csv')
    opciones = {int(f['estudiante_id']): f for f in filas}
    elegido = st.selectbox('Cuenta para gestionar', [None, *opciones],
        format_func=lambda i: 'Crear estudiante sin biometría' if i is None else f"{opciones[i]['nombre']} · {opciones[i]['codigo_institucional'] or i}")
    fila = opciones.get(elegido)
    version = int(fila['version_credencial']) if fila else 0
    if fila:
        st.info(ESTADOS.get(fila['estado_verificacion'], ESTADOS['PENDIENTE']))
    # Incluye versión/cuenta en la clave para no reutilizar formularios con datos obsoletos.
    with st.form(f'admin_autorizar_excepcion_{elegido}_{version}', clear_on_submit=True):
        st.markdown('**Autorizar o renovar acceso alternativo**')
        nombre = st.text_input('Nombre del estudiante', max_chars=200) if fila is None else ''
        codigo = st.text_input('Código institucional', max_chars=50) if fila is None else ''
        tipo = st.selectbox('Tipo de documento oficial', TIPOS_DOCUMENTO)
        documento = st.text_input('Número del documento comprobado', max_chars=40)
        categoria = st.selectbox('Motivo de excepción', CATEGORIAS)
        referencia = st.text_input('Referencia del expediente administrativo', max_chars=100,
            help='Solo un código de expediente. No escribas diagnósticos ni números de documento.')
        dias = st.number_input('Vigencia en días', min_value=1, max_value=365, value=90, step=1)
        clave = st.text_input('Contraseña alternativa (mínimo 12 caracteres)', type='password')
        confirmacion = st.text_input('Confirmar contraseña alternativa', type='password')
        comprobado = st.checkbox('Comprobé el documento oficial y la correspondencia con la cuenta mediante el procedimiento institucional.')
        st.caption('La autorización o renovación cierra las sesiones actuales del estudiante. Entrega la contraseña por un canal institucional privado; no se mostrará de nuevo.')
        guardar = st.form_submit_button('Autorizar excepción', type='primary', disabled=bool(fila and not fila['activo']))
    if guardar:
        if clave != confirmacion:
            st.warning('Las contraseñas no coinciden.')
        else:
            servicio.autorizar(elegido, tipo, documento, clave, categoria, referencia, int(dias),
                version=version, documento_comprobado=comprobado, nombre=nombre, codigo_institucional=codigo)
            st.success('Excepción autorizada. El primer acceso alternativo registrará el estado excepcional.')
            st.rerun()
    if fila and fila['excepcion_activa']:
        with st.form(f'admin_revocar_excepcion_{elegido}_{version}', clear_on_submit=True):
            motivo = st.text_input('Motivo administrativo de revocación', max_chars=450,
                help='Sin diagnósticos ni números de documento.')
            revocar = st.form_submit_button('Revocar excepción y cerrar sesión')
        if revocar:
            servicio.revocar(elegido, motivo, version=version)
            st.success('Excepción revocada; las sesiones anteriores ya no tienen acceso.')
            st.rerun()
