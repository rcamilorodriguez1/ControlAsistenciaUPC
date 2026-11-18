"""Revisión visual local sin iniciar sesión, usar biometría ni modificar Oracle."""
import argparse
import base64
import json
import math
import os
import re
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import urlopen
from uuid import uuid4

from _comun import RAIZ, usar_entorno


def revisar_excepciones(cdp, js, esperar, captura, url):
    for ancho, alto in [(1440,1080),(768,1024),(390,844),(320,740)]:
        cdp('Emulation.setDeviceMetricsOverride', {'width': ancho, 'height': alto, 'deviceScaleFactor': 1, 'mobile': ancho<700})
        cdp('Page.navigate', {'url': url+'/estudiante'})
        esperar("Boolean(document.querySelector('.st-key-acceso_estudiante details'))")
        js("document.querySelector('.st-key-acceso_estudiante details').open=true")
        esperar("Boolean(document.querySelector('input[type=password]')?.getClientRects().length)")
        captura('excepcion_acceso_'+str(ancho))
        cdp('Page.navigate', {'url': url+'/estudiante?fixture=estudiante&excepcion=1'})
        esperar("document.querySelector('[data-testid=stMain]')?.textContent.includes('Verificación excepcional / biometría incompleta')")
        captura('excepcion_panel_'+str(ancho))
        cdp('Page.navigate', {'url': url+'/administracion?fixture=administrador'})
        esperar("Boolean(document.querySelector('[role=radiogroup]'))")
        js("[...document.querySelectorAll('[role=radiogroup] label')].find(e=>e.textContent.includes('Verificación')).click()")
        esperar("[...document.querySelectorAll('button')].some(e=>e.textContent.includes('Autorizar excepción'))")
        captura('excepcion_administracion_'+str(ancho))


def revisar_paneles(cdp, js, esperar, pulsar, captura, url):
    def estados_separador(etiqueta):
        raiz = cdp('DOM.getDocument')['root']['nodeId']
        nodo = cdp('DOM.querySelector', {'nodeId': raiz, 'selector': '.st-key-loginbackbtn button'})['nodeId']
        medir = """(()=>{const e=document.querySelector('.st-key-cierre_cuenta hr'),r=e.getBoundingClientRect(),origen=e.closest('.st-key-cierre_cuenta').getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x-origen.x,y:r.y-origen.y,ancho:r.width,alto:r.height,color:s.borderBottomColor}})()"""
        referencia = js(medir)
        for estado, pseudo in [('hover', ['hover']), ('focus', ['focus', 'focus-visible'])]:
            cdp('CSS.forcePseudoState', {'nodeId': nodo, 'forcedPseudoClasses': pseudo})
            captura(etiqueta + '_separador_' + estado)
            assert js(medir) == referencia, 'El separador cambia de posición o color con el botón.'
        cdp('CSS.forcePseudoState', {'nodeId': nodo, 'forcedPseudoClasses': []})
    def resaltar_inicio(etiqueta):
        raiz = cdp('DOM.getDocument')['root']['nodeId']
        nodo = cdp('DOM.querySelector', {'nodeId': raiz, 'selector': '.st-key-navegacion_inicio a'})['nodeId']
        for estado, pseudo in [('hover', ['hover']), ('focus', ['focus', 'focus-visible']), ('active', ['hover', 'active'])]:
            if estado == 'focus':
                js("document.querySelector('.st-key-navegacion_inicio a').focus()")
            cdp('CSS.forcePseudoState', {'nodeId': nodo, 'forcedPseudoClasses': pseudo})
            centro = js("(()=>{const r=document.querySelector('.st-key-navegacion_inicio a').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()")
            cdp('Input.dispatchMouseEvent', {'type': 'mouseMoved', **centro})
            captura(etiqueta + '_' + estado)
        cdp('CSS.forcePseudoState', {'nodeId': nodo, 'forcedPseudoClasses': []})
        js("document.querySelector('.st-key-navegacion_inicio a').blur()")
    def pulsar_logo():
        esperar("(()=>{const a=[...document.querySelectorAll('.st-key-logo_inicio a')].find(a=>a.getClientRects().length);if(!a)return false;a.click();return true})()")
    def cerrar_dialogo():
        js("document.querySelector('[role=dialog] button[aria-label=Close]')?.click()")
        esperar("!document.querySelector('[role=dialog]') || !document.querySelector('[role=dialog]').getClientRects().length")
    def cuenta_y_conflicto(rol, otro):
        # La vista aislada usa el router y componentes reales, con Oracle bloqueado.
        activador = "document.querySelector('.st-key-menu_cuenta button')"
        abierto = "Boolean(document.querySelector('[data-testid=stPopoverBody]')?.getClientRects().length)"
        esperar("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
        esperar(f'Boolean({activador})')
        cdp('Page.bringToFront')
        cdp('Emulation.setFocusEmulationEnabled', {'enabled': True})
        js(f'{activador}.focus()')
        assert js(f'document.activeElement==={activador}'), 'El activador no recibe foco.'
        cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'text': '\r', 'windowsVirtualKeyCode': 13})
        cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13})
        esperar(abierto)
        opciones = js("[...document.querySelectorAll('[data-testid=stPopoverBody] button')].filter(b=>b.getClientRects().length && getComputedStyle(b).visibility==='visible').map(b=>({texto:b.querySelector('p')?.textContent.trim(),deshabilitado:b.disabled}))")
        assert [o['texto'] for o in opciones] == ['Mi perfil', 'Configuración', 'Cerrar sesión'], opciones
        assert [o['deshabilitado'] for o in opciones] == [rol == 'docente', True, False], opciones
        for _ in range(6):
            if js("document.activeElement?.querySelector('p')?.textContent.trim()==='Cerrar sesión'"):
                break
            cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Tab', 'code': 'Tab', 'windowsVirtualKeyCode': 9})
            cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Tab', 'code': 'Tab', 'windowsVirtualKeyCode': 9})
        assert js("document.activeElement?.querySelector('p')?.textContent.trim()==='Cerrar sesión'"), 'No se alcanza el cierre de sesión con Tab.'
        captura(rol + '_menu_cuenta_movil')
        estados_separador(rol + '_movil')
        cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Escape', 'code': 'Escape', 'windowsVirtualKeyCode': 27})
        cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Escape', 'code': 'Escape', 'windowsVirtualKeyCode': 27})
        esperar('!'+abierto)
        js(f'{activador}.click()'); esperar(abierto)
        time.sleep(.1)  # El popover nativo ignora clics exteriores en los primeros 50 ms.
        cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': 5, 'y': 200, 'button': 'left', 'clickCount': 1})
        cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': 5, 'y': 200, 'button': 'left', 'clickCount': 1})
        esperar('!'+abierto)
        if not js("Boolean(document.querySelector('.upc-hero'))"):
            assert js("document.querySelector('.st-key-logo_inicio a').getAttribute('href')===document.querySelector('.st-key-navegacion_inicio a').getAttribute('href')"), 'Inicio y logo tienen rutas diferentes.'
        if not js("Boolean(document.querySelector('.upc-hero'))"):
            pulsar('Inicio'); esperar("Boolean(document.querySelector('.upc-hero'))")
        pulsar('Portal del ' + otro)
        esperar("Boolean(document.querySelector('.st-key-aviso_conflicto_sesion'))")
        formulario = 'estudiante' if otro == 'Estudiante' else 'docente'
        assert js(f"document.querySelector('.st-key-aviso_conflicto_sesion').getBoundingClientRect().top >= document.querySelector('.st-key-acceso_{formulario}').getBoundingClientRect().bottom"), 'El aviso debe estar debajo del login.'
        assert not js("Boolean(document.querySelector('[role=dialog]'))"), 'El conflicto no debe abrir un diálogo.'
        if formulario == 'docente':
            assert js("[...document.querySelectorAll('.st-key-acceso_docente button')].find(b=>b.innerText.includes('Iniciar Sesión')).disabled"), 'Login incompatible habilitado.'
        captura(rol + '_conflicto_login_movil')
        pulsar('Volver a mi portal')
        try:
            esperar("!document.querySelector('.st-key-aviso_conflicto_sesion') && Boolean(document.querySelector('.st-key-resumen_panel'))")
        except Exception:
            captura(rol + '_diagnostico_volver')
            print('Diagnóstico de vista sintética:', js("({ruta:location.pathname,texto:document.body.innerText.slice(-2000)})"))
            raise
        pulsar('Inicio'); esperar("Boolean(document.querySelector('.upc-hero'))")
        pulsar('Portal del ' + otro); esperar("Boolean(document.querySelector('.st-key-aviso_conflicto_sesion'))")
        pulsar('Cerrar sesión actual')
        esperar("!document.querySelector('.st-key-aviso_conflicto_sesion') && !document.querySelector('.st-key-menu_cuenta')")
        captura(rol + '_cierre_habilita_otro_portal')
        resaltar_inicio('inicio_' + rol + '_sin_sesion')
    esperar("Boolean(document.querySelector('[class*=st-key-selector_academico_clase] input[role=combobox]'))")
    captura('docente_asistencia_escritorio')
    cdp('DOM.enable'); cdp('CSS.enable')
    resaltar_inicio('inicio_docente_escritorio')
    js("document.querySelector('.st-key-menu_cuenta [data-testid=stPopoverButton]').click()")
    esperar("Boolean(document.querySelector('[data-testid=stPopoverBody]'))")
    captura('docente_menu_cuenta_escritorio')
    estados_separador('docente_escritorio')
    cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Escape', 'code': 'Escape', 'windowsVirtualKeyCode': 27})
    cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Escape', 'code': 'Escape', 'windowsVirtualKeyCode': 27})
    esperar("!document.querySelector('[data-testid=stPopoverBody]')")
    pulsar('Revisar resultado pendiente')
    esperar("Boolean(document.querySelector('[data-testid=stDataFrame]'))")
    captura('revision_asistencia_escritorio')
    cerrar_dialogo()
    pulsar('Gestionar Materias')
    esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Crear nueva materia'))")
    captura('docente_materias_escritorio')
    pulsar('Crear nueva materia')
    esperar("Boolean(document.querySelector('[role=dialog] input'))")
    captura('crear_materia_escritorio')
    cerrar_dialogo()
    pulsar('Compartir Código: Bases de Datos')
    esperar("Boolean(document.querySelector('[role=dialog] img'))")
    captura('compartir_materia_escritorio')
    cerrar_dialogo()
    pulsar('Registros de Asistencia')
    esperar("Boolean(document.querySelector('[data-testid=stDataFrame]'))")
    captura('docente_reportes_escritorio')
    pulsar('Inicio')
    esperar("Boolean(document.querySelector('.upc-hero'))")
    captura('docente_inicio_conserva_sesion')
    pulsar('Portal del Profesor')
    esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Gestionar Materias'))")
    pulsar('Gestionar Materias')
    pulsar_logo()
    esperar("Boolean(document.querySelector('.upc-hero'))")
    captura('docente_logo_conserva_sesion')
    cdp('Emulation.setDeviceMetricsOverride', {'width': 320, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
    captura('docente_inicio_autenticado_320')
    cdp('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
    pulsar('Portal del Profesor')
    cdp('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
    pulsar('Tomar Asistencia')
    captura('docente_asistencia_movil')
    resaltar_inicio('inicio_docente_movil')
    pulsar('Gestionar Materias')
    captura('docente_materias_movil')
    cuenta_y_conflicto('docente', 'Estudiante')
    cdp('Page.navigate', {'url': url + '/estudiante?fixture=estudiante'})
    esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Inscribirse en una Materia'))")
    captura('estudiante_panel_movil')
    resaltar_inicio('inicio_estudiante_movil')
    cdp('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
    captura('estudiante_panel_escritorio')
    resaltar_inicio('inicio_estudiante_escritorio')
    js("document.querySelector('.st-key-menu_cuenta [data-testid=stPopoverButton]').click()")
    esperar("Boolean(document.querySelector('[data-testid=stPopoverBody]'))")
    pulsar('Mi perfil')
    esperar("Boolean(document.querySelector('.perfil-portada')) && location.pathname.endsWith('/mi-perfil')")
    captura('perfil_estudiante_escritorio')
    assert js("document.querySelectorAll('.perfil-dia[data-estado=mixto]').length>0 && document.querySelectorAll('.perfil-dia[data-estado=ausente]').length>0 && document.querySelectorAll('.perfil-dia[data-estado=presente]').length>0"), 'Faltan estados en el calendario sintético.'
    esperar("(()=>{const e=document.querySelector('.st-key-perfil_materias summary');if(!e)return false;e.click();return true})()")
    esperar("Boolean(document.querySelector('.perfil-materia-estado'))")
    captura('perfil_estudiante_materia_desplegada')
    pulsar('Mes anterior')
    esperar("document.querySelector('.perfil-mes-titulo')?.textContent.includes('Octubre')")
    captura('perfil_estudiante_calendario_anterior')
    pulsar('Mes siguiente')
    esperar("document.querySelector('.perfil-mes-titulo')?.textContent.includes('Noviembre')")
    for ancho, alto in [(768,1024), (390,844), (320,844)]:
        cdp('Emulation.setDeviceMetricsOverride', {'width':ancho,'height':alto,'deviceScaleFactor':1,'mobile':ancho<700})
        captura('perfil_estudiante_' + str(ancho))
    pulsar('Volver a mi portal')
    esperar("Boolean(document.querySelector('.st-key-resumen_panel')) && !document.querySelector('.perfil-portada')")
    cdp('Emulation.setDeviceMetricsOverride', {'width':1440,'height':1080,'deviceScaleFactor':1,'mobile':False})
    pulsar('Inicio')
    esperar("Boolean(document.querySelector('.upc-hero'))")
    pulsar('Portal del Estudiante')
    esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Inscribirse en una Materia'))")
    pulsar_logo()
    esperar("Boolean(document.querySelector('.upc-hero'))")
    captura('estudiante_logo_conserva_sesion')
    cdp('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
    cuenta_y_conflicto('estudiante', 'Profesor')
    cdp('Page.navigate', {'url': url + '/mi-perfil?fixture=estudiante&perfil-vacio=1'})
    esperar("Boolean(document.querySelector('.perfil-portada'))")
    captura('perfil_estudiante_sin_registros')
    assert js("Boolean(document.querySelector('.perfil-estado--sin-registros')) && !document.querySelector('.perfil-estado--riesgo') && !document.querySelector('.st-key-perfil_materias [data-testid=stExpander]')"), 'El perfil sin datos no debe mostrar un estado de riesgo.'


def revisar_claves(js, esperar, captura, informe):
    # Exclusivamente datos de prueba; no se envía el formulario ni se guardan valores en el informe.
    def escribir(campo, valor):
        selector = '[class*="st-key-auth_profesor_' + campo + '_alta_"] input'
        js('(()=>{const e=document.querySelector(' + json.dumps(selector) + ');e.focus();'
           'Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(e,' + json.dumps(valor) + ');'
           'e.dispatchEvent(new Event("input",{bubbles:true}));})()')
    escribir('clave', '12345678')
    esperar("document.querySelector('[data-testid=clave-fortaleza]')?.textContent.includes('Muy débil')")
    fuerte = 'Faro!Nube7Bosque*Reloj26'
    escribir('clave', fuerte)
    esperar("document.querySelector('[data-testid=clave-fortaleza]')?.textContent.includes('Muy fuerte')")
    selector_clave = '[class*="st-key-auth_profesor_clave_alta_"] input'
    sin_barra = js('getComputedStyle(document.querySelector(' + json.dumps(selector_clave) + ')).outlineStyle==="none"')
    informe['clave_sin_contorno_marron'] = sin_barra
    if not sin_barra: informe['fallos'].append('El campo de contraseña conserva el contorno interno.')
    captura('clave_fortaleza_escritorio')
    escribir('confirmar', 'OtraClaveDePrueba!')
    esperar("document.querySelector('[data-testid=clave-confirmacion]')?.textContent.includes('no coinciden')")
    selector_confirmar = '[class*="st-key-auth_profesor_confirmar_alta_"] input'
    sin_barra = js('getComputedStyle(document.querySelector(' + json.dumps(selector_confirmar) + ')).outlineStyle==="none"')
    informe['confirmacion_sin_contorno_marron'] = sin_barra
    if not sin_barra: informe['fallos'].append('La confirmación conserva el contorno interno.')
    captura('clave_confirmacion_distinta')
    escribir('confirmar', fuerte)
    esperar("document.querySelector('[data-testid=clave-confirmacion]')?.textContent.includes('Las contraseñas coinciden.')")
    informe['fortaleza_y_coincidencia_en_vivo'] = True
    captura('clave_confirmacion_correcta')


def revisar_foco_texto(js, informe, etiqueta, esperar):
    # Streamlit puede mantener temporalmente controles de la pantalla anterior durante el rerun.
    esperar("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
    js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))', True)
    controles = js("""[...document.querySelectorAll('[data-testid=stTextInput] input')].map((e,i)=>{
        e.focus();const raiz=e.closest('[data-testid=stTextInputRootElement]');
        return {campo:i+1,contorno:getComputedStyle(e).outlineStyle,
            focoCompleto:raiz?getComputedStyle(raiz).boxShadow:'sin contenedor'};
    })""")
    informe.setdefault('foco_texto', {})[etiqueta] = controles
    for control in controles:
        if control['contorno'] != 'none' or control['focoCompleto'] in ('none', 'sin contenedor'):
            informe['fallos'].append(etiqueta + ': foco interno o falta de foco visible en el campo ' + str(control['campo']))


def revisar_recuperacion_docente(cdp,js,esperar,pulsar,captura,informe):
    """Solo datos sinteticos y cambios de vista: nunca se envia un restablecimiento."""
    pulsar('Olvidé mi contraseña')
    esperar("Boolean(document.querySelector('[class*=st-key-auth_profesor_recuperacion_clave_] input'))")
    captura('recuperacion_docente_escritorio')
    def escribir(campo,valor):
        selector='[class*=st-key-auth_profesor_recuperacion_'+campo+'_] input'
        js('(()=>{const e=document.querySelector('+json.dumps(selector)+');e.focus();'
           'Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(e,'+json.dumps(valor)+');'
           'e.dispatchEvent(new Event("input",{bubbles:true}));})()')
    fuerte='Faro!Bosque7Luna*Reloj26'
    escribir('clave',fuerte)
    esperar("document.querySelector('[data-testid=clave-fortaleza]')?.textContent.includes('Muy fuerte')")
    escribir('confirmar','OtraClaveDePrueba!')
    esperar("document.querySelector('[data-testid=clave-confirmacion]')?.textContent.includes('no coinciden')")
    captura('recuperacion_docente_confirmacion_distinta')
    escribir('confirmar',fuerte)
    esperar("document.querySelector('[data-testid=clave-confirmacion]')?.textContent.includes('Las contraseñas coinciden.')")
    revisar_foco_texto(js,informe,'recuperacion_docente',esperar)
    captura('recuperacion_docente_coincidencia')
    cdp('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    captura('recuperacion_docente_movil')
    pulsar('Volver al acceso')
    esperar("document.querySelectorAll('input[type=password]').length===1")
    informe['recuperacion_docente_sin_enviar']=True
    informe['recuperacion_limpia_campos']=js("[...document.querySelectorAll('[data-testid=stTextInput] input')].every(e=>!e.value)")
    if not informe['recuperacion_limpia_campos']:informe['fallos'].append('Volver del restablecimiento conserva campos.')
    cdp('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1080,'deviceScaleFactor':1,'mobile':False})


def revisar_administracion_real(cdp, js, esperar, pulsar, captura, informe):
    """Acceso real privado; solo consultas y preparación de CSV, sin editar cuentas/materias."""
    privado = (RAIZ / '.local/ADMINISTRADOR.md').read_text(encoding='utf-8')
    def credencial(etiqueta):
        encontrado = re.search(r'(?im)^\s*(?:-\s*)?' + etiqueta + r'\s*:\s*`([^`]+)`', privado)
        if not encontrado: raise RuntimeError('No se encontró la credencial local administrativa.')
        return encontrado.group(1)
    pulsar('Gestión académica')
    esperar("Boolean(document.querySelector('input[type=password]'))")
    captura('administracion_acceso')
    # Insertar desde CDP evita interpolar secretos en expresiones o mensajes de error JavaScript.
    for selector, valor in [('input:not([type=password])', credencial('Usuario')), ('input[type=password]', credencial('Contraseña'))]:
        js('document.querySelector(' + json.dumps(selector) + ').focus()')
        cdp('Input.insertText', {'text': valor})
        js('document.activeElement.blur()')
        time.sleep(.4)
    pulsar('Ingresar a Administración')
    esperar("Boolean(document.querySelector('[class*=st-key-admin_modulo]'))")
    informe['acceso_administrativo_real'] = True
    pulsar('Consultar auditoría')
    esperar("Boolean(document.querySelector('[data-testid=stDataFrame]'))")
    captura('administracion_auditoria')
    pulsar('Generar CSV de estos resultados')
    esperar("[...document.querySelectorAll('button,a')].some(b=>b.innerText.includes('Descargar CSV'))")
    informe['csv_administrativo_disponible'] = True
    for modulo in ('Cuentas', 'Materias'):
        js("[...document.querySelectorAll('[class*=st-key-admin_modulo] label')].find(e=>e.textContent.includes(" + json.dumps(modulo) + ")).click()")
        esperado = 'Guardar cambios de cuenta' if modulo == 'Cuentas' else 'Guardar cambios de materia'
        esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes(" + json.dumps(esperado) + "))")
        if not js("[...document.querySelectorAll('button')].find(b=>b.innerText.includes(" + json.dumps(esperado) + ")).disabled"):
            informe['fallos'].append(modulo + ': guardar habilitado sin revisión del cambio.')
        captura('administracion_' + modulo.lower())
        cdp('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
        captura('administracion_' + modulo.lower() + '_movil')
        cdp('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
    pulsar('Cerrar sesión')
    esperar("Boolean(document.querySelector('input[type=password]'))")
    informe['cierre_administrativo_real'] = True


def main():
    usar_entorno()
    from websockets.sync.client import connect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--navegador', type=Path)
    parser.add_argument('--paneles', action='store_true', help='Datos sintéticos, proveedor Oracle bloqueado; no usa la app activa.')
    parser.add_argument('--excepciones', action='store_true', help='Acceso alternativo, estado excepcional y consola administrativa con datos sintéticos; Oracle bloqueado.')
    parser.add_argument('--lento', action='store_true', help='Emular CPU x4 y latencia de red de 120 ms.')
    parser.add_argument('--claves', action='store_true', help='Probar fortaleza y confirmación con contraseñas sintéticas, sin registrar usuarios.')
    parser.add_argument('--url', help='Revisar la instancia local ya activa; no iniciar ni detener su servidor.')
    parser.add_argument('--registro-estudiante', action='store_true', help='Revisar los campos reales del registro estudiantil con captura sintética y Oracle bloqueado.')
    parser.add_argument('--administracion-real', action='store_true', help='Comprobar acceso y consultas con la cuenta privada local, sin editar datos académicos.')
    parser.add_argument('--identidad', action='store_true', help='Añadir revisión de identidad y presentación en anchos de 320, 390 y 768 px.')
    parser.add_argument('--zoom', type=int, choices=[25, 30, 33, 50, 100, 200], help='Zoom nativo del navegador en un perfil aislado, con escala del dispositivo fijada en 1.')
    parser.add_argument('--recuperacion-docente',action='store_true',help='Revisar recuperacion con datos sinteticos; no enviar ni cambiar contrasenas.')
    args = parser.parse_args()
    if args.zoom is not None and (args.identidad or args.claves or args.paneles or args.registro_estudiante or args.administracion_real or args.recuperacion_docente or args.excepciones):
        parser.error('--zoom es un escenario independiente; no combinar con otras vistas.')
    candidatos = [args.navegador] if args.navegador else [
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe',
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'BraveSoftware/Brave-Browser/Application/brave.exe']
    navegador = next((p for p in candidatos if p and p.is_file()), None)
    if navegador is None: parser.error('Indica una instalación de Chrome/Brave con --navegador.')
    carpeta = RAIZ / '.local' / 'frontend' / uuid4().hex[:12]
    perfil = carpeta / 'perfil'
    perfil.mkdir(parents=True)
    if args.zoom is not None:
        # Preferencia de Chromium: nivel=log(factor)/log(1.2), partición predeterminada «x».
        # Solo se escribe en el perfil nuevo de esta prueba; no se aplica zoom CSS ni pinch.
        predeterminado = perfil / 'Default'
        predeterminado.mkdir()
        preferencias = {'partition': {'default_zoom_level': {'x': math.log(args.zoom/100)/math.log(1.2)}}}
        (predeterminado / 'Preferences').write_text(json.dumps(preferencias), encoding='utf-8')
    with socket.socket() as reserva:
        reserva.bind(('127.0.0.1', 0)); puerto = reserva.getsockname()[1]
    url = args.url.rstrip('/') if args.url else f'http://127.0.0.1:{puerto}'
    destino = urlsplit(url)
    if destino.scheme not in ('http', 'https') or destino.hostname not in ('localhost', '127.0.0.1') or destino.username or destino.password or destino.query or destino.fragment or destino.path not in ('', '/'):
        parser.error('La comprobación admite únicamente la raíz de una aplicación local, sin credenciales ni parámetros.')
    if args.url and (args.paneles or args.registro_estudiante or args.excepciones): parser.error('Las vistas sintéticas requieren su servidor separado.')
    if args.administracion_real and (not args.url or args.paneles or args.registro_estudiante or args.claves):
        parser.error('La revisión administrativa requiere --url y no se combina con otros escenarios.')
    oculto = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    log = (carpeta / 'servidor.log').open('w', encoding='utf-8')
    entrada = RAIZ / ('tests/preview_frontend.py' if args.paneles or args.registro_estudiante or args.excepciones else 'principal.py')
    servidor = None if args.url else subprocess.Popen([sys.executable, '-B', '-m', 'streamlit', 'run', str(entrada),
        '--server.address', '127.0.0.1', '--server.port', str(puerto), '--browser.serverAddress', '127.0.0.1',
        '--browser.serverPort', str(puerto), '--browser.gatherUsageStats', 'false'], cwd=RAIZ,
        env={**os.environ, 'APP_BASE_URL': url}, stdout=log, stderr=subprocess.STDOUT, creationflags=oculto)
    chrome = None
    informe = {'modo': 'vista_sintetica_oracle_bloqueado' if args.paneles or args.registro_estudiante or args.excepciones else 'navegacion_anonima_sin_red_externa',
               'servidor_existente': bool(args.url), 'url_local': url,
               'estado': 'INICIADO', 'pantallas': {}, 'externos': [], 'fallos': []}
    try:
        for _ in range(160):
            if servidor is not None and servidor.poll() is not None: raise RuntimeError('El servidor terminó; revisar servidor.log.')
            try:
                contexto = ssl.create_default_context(cafile=RAIZ / '.certs/ca.pem') if destino.scheme == 'https' else None
                with urlopen(url + '/_stcore/health', timeout=1, context=contexto) as r:
                    if r.status == 200: break
            except OSError: time.sleep(.15)
        else: raise RuntimeError('Tiempo de arranque agotado.')
        chrome = subprocess.Popen([str(navegador), '--headless=new', '--no-first-run', '--no-default-browser-check',
            '--disable-background-networking', '--disable-extensions', '--remote-debugging-port=0',
            *(['--force-device-scale-factor=1'] if args.zoom is not None else []),
            '--window-size=1440,1080', '--user-data-dir=' + str(perfil), 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=oculto)
        for _ in range(160):
            try:
                lineas = (perfil / 'DevToolsActivePort').read_text().splitlines()
                if lineas and lineas[0].isdigit():
                    debug = lineas[0]
                    break
            except OSError:
                # En Windows puede existir mientras Chromium aún lo escribe con bloqueo.
                pass
            if chrome.poll() is not None: raise RuntimeError('El navegador terminó antes de iniciar CDP.')
            time.sleep(.1)
        else: raise RuntimeError('Tiempo de inicio del navegador agotado.')
        for _ in range(100):
            with urlopen(f'http://127.0.0.1:{debug}/json/list') as r: paginas = json.load(r)
            pagina = next((p for p in paginas if p['type'] == 'page'), None)
            if pagina: break
            time.sleep(.1)
        else: raise RuntimeError('El navegador no creó una pestaña de prueba.')
        with connect(pagina['webSocketDebuggerUrl'], proxy=None, max_size=20_000_000) as ws:
            secuencia = 0
            def cdp(metodo, parametros=None):
                nonlocal secuencia
                secuencia += 1; mensaje = secuencia
                ws.send(json.dumps({'id': mensaje, 'method': metodo, 'params': parametros or {}}))
                while True:
                    respuesta = json.loads(ws.recv(timeout=45))
                    if respuesta.get('method') == 'Fetch.requestPaused':
                        solicitud = respuesta['params']
                        recurso = solicitud['request']['url']
                        partes = urlsplit(recurso)
                        bloquear = partes.scheme in ('http', 'https') and partes.hostname not in ('localhost', '127.0.0.1')
                        if bloquear and recurso not in informe['externos']: informe['externos'].append(recurso)
                        secuencia += 1
                        ws.send(json.dumps({'id': secuencia, 'method': 'Fetch.failRequest' if bloquear else 'Fetch.continueRequest',
                            'params': {'requestId': solicitud['requestId'], **({'errorReason': 'BlockedByClient'} if bloquear else {})}}))
                        continue
                    if respuesta.get('method') == 'Network.requestWillBeSent':
                        recurso = respuesta['params']['request']['url']
                        partes = urlsplit(recurso)
                        if partes.scheme in ('http', 'https') and partes.hostname not in ('localhost', '127.0.0.1'):
                            if recurso not in informe['externos']: informe['externos'].append(recurso)
                    if respuesta.get('id') == mensaje:
                        if 'error' in respuesta: raise RuntimeError(str(respuesta['error']))
                        return respuesta.get('result', {})
            def js(expresion, esperar=False):
                r = cdp('Runtime.evaluate', {'expression': expresion, 'returnByValue': True, 'awaitPromise': esperar})
                if 'exceptionDetails' in r: raise RuntimeError(str(r['exceptionDetails']))
                return r.get('result', {}).get('value')
            def esperar(expresion):
                for _ in range(200):
                    if js(expresion): return
                    time.sleep(.1)
                raise RuntimeError('No apareció el elemento esperado: ' + expresion)
            def pulsar(texto):
                expresion = f"[...document.querySelectorAll('button,a')].find(b=>b.getClientRects().length&&b.innerText.includes({json.dumps(texto)}))"
                esperar('Boolean(' + expresion + ')')
                js(expresion + '.click()')
            def captura(etiqueta):
                esperar("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
                js('document.fonts.ready.then(()=>true)', True)
                js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))', True)
                anterior_pie = None
                estable_pie = 0
                for _ in range(40):
                    medida_pie = js("(()=>{const m=document.querySelector('[data-testid=stMain]'),p=m.querySelector('.upc-academic-footer');if(!p)return null;const ancho=m.clientWidth,r=p.getBoundingClientRect(),izquierda=m.getBoundingClientRect().left+m.clientLeft;return {ancho,izquierda:r.left,derecha:r.right,correcto:Math.abs(r.left-izquierda)<1&&Math.abs(r.right-izquierda-ancho)<1&&m.scrollWidth<=ancho+2}})()")
                    if medida_pie is None:
                        break
                    estable_pie = estable_pie + 1 if medida_pie == anterior_pie and medida_pie['correcto'] else 0
                    if estable_pie >= 3:
                        break
                    anterior_pie = medida_pie
                    time.sleep(.1)
                else:
                    raise RuntimeError('No se estabilizó el ancho útil del pie académico: ' + str(medida_pie))
                dimensiones = js("""({ancho:innerWidth,contenido:document.documentElement.scrollWidth,
                    focoCuentaInstalado:window.__upcFocoCuenta instanceof MutationObserver,
                    marcaNombreCompleto:[...document.querySelectorAll('.upc-brand-title,.upc-brand-subtitle')].every(e=>e.getBoundingClientRect().width>70&&e.scrollWidth<=e.clientWidth+2),
                    perfilEstudiante:(()=>{const p=document.querySelector('.st-key-perfil_estudiante');if(!p)return null;const circulo=p.querySelector('.perfil-circulo').getBoundingClientRect(),valor=p.querySelector('.perfil-circulo strong').getBoundingClientRect();return {ruta:location.pathname,porcentajeCentrado:Math.abs(valor.left+valor.width/2-circulo.left-circulo.width/2)<1,porcentajeSinRecorte:valor.left>=circulo.left&&valor.right<=circulo.right,mes:p.querySelector('.perfil-mes-titulo').textContent,dias:p.querySelectorAll('.perfil-dia').length,presentes:p.querySelectorAll('[data-estado=presente]').length,ausentes:p.querySelectorAll('[data-estado=ausente]').length,mixtos:p.querySelectorAll('[data-estado=mixto]').length,sinRegistros:p.querySelectorAll('[data-estado=sin-registros]').length,materias:p.querySelectorAll('.st-key-perfil_materias [data-testid=stExpander]').length,recortes:[...p.querySelectorAll('h1,.perfil-codigo,.perfil-mes-titulo,summary p,.perfil-metricas span')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.tagName)}})(),
                    pieAcademico:(()=>{const pies=[...document.querySelectorAll('.upc-academic-footer')].filter(e=>e.getBoundingClientRect().height>0),e=pies[0];if(!e)return null;const r=e.getBoundingClientRect(),main=document.querySelector('[data-testid=stMain]'),m=main.getBoundingClientRect(),zonas=[...e.querySelectorAll('.academic-footer-zone')].map(z=>{const b=z.getBoundingClientRect();return {x:b.x,y:b.y,ancho:b.width,alto:b.height,fondo:getComputedStyle(z).backgroundImage}}),banda=e.querySelector('.academic-footer-band').getBoundingClientRect();return {cantidad:pies.length,izquierda:r.left,derecha:r.right,ancho:r.width,alto:r.height,inicioDisponible:m.left+main.clientLeft,finDisponible:m.left+main.clientLeft+main.clientWidth,zonas,banda:{x:banda.x,ancho:banda.width},titulos:[...e.querySelectorAll('.academic-footer-title')].map(t=>{const s=getComputedStyle(t);return {texto:t.textContent,fuente:s.fontFamily,estilo:s.fontStyle,peso:s.fontWeight}}),textosRecortados:[...e.querySelectorAll('h2,p,li,dt,dd,span')].filter(t=>t.scrollWidth>t.clientWidth+1).map(t=>t.textContent),posicion:getComputedStyle(e).position,despuesContenido:!e.closest('[role=dialog]')&&Boolean(e.closest('.st-key-pie_academico'))}})(),
                    geometriaControles:(()=>{const a=document.querySelector('.st-key-navegacion_inicio a'),hr=document.querySelector('.st-key-opciones_cuenta hr'),salir=document.querySelector('.st-key-loginbackbtn button');const limites=e=>{const r=e.getBoundingClientRect();return {izquierda:r.left,derecha:r.right,ancho:r.width}};let inicio=null;if(a){const i=a.querySelector('[data-testid=stIconMaterial]'),p=a.querySelector('p'),r=a.getBoundingClientRect(),centro=e=>{const b=e.getBoundingClientRect();return b.top+b.height/2};const barras=[];for(let e=a;e&&!e.classList.contains('st-key-barra_panel');e=e.parentElement)if(['auto','scroll'].includes(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight)barras.push(e.dataset.testid||e.tagName);inicio={barras,iconoCentrado:Math.abs(centro(i)-centro(a))<1,textoCentrado:Math.abs(centro(p)-centro(a))<1,sinRecortes:[i,p].every(e=>{const b=e.getBoundingClientRect();return b.top>=r.top&&b.bottom<=r.bottom})}}return {inicio,separador:hr&&salir?{linea:limites(hr),resaltado:(()=>{const s=getComputedStyle(salir),r=salir.getBoundingClientRect(),reserva=parseFloat(s.outlineWidth)+Math.max(0,parseFloat(s.outlineOffset));return s.outlineStyle!=='none'?{izquierda:r.left-reserva,derecha:r.right+reserva,ancho:r.width+2*reserva}:limites(salir.closest('.st-key-cierre_cuenta'))})(),boton:limites(salir),separacion:salir.getBoundingClientRect().top-hr.getBoundingClientRect().bottom,contorno:parseFloat(getComputedStyle(salir).outlineWidth)+Math.max(0,parseFloat(getComputedStyle(salir).outlineOffset)),contenedorComun:hr.closest('.st-key-cierre_cuenta')===salir.closest('.st-key-cierre_cuenta')&&Boolean(hr.closest('.st-key-cierre_cuenta')),independiente:!salir.contains(hr)}:null}})(),
                    medidasInicio:(()=>{const a=document.querySelector('.st-key-navegacion_inicio a');if(!a)return null;const medir=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {tag:e.tagName,testid:e.dataset.testid,clase:e.className,ancho:r.width,alto:r.height,cliente:e.clientHeight,contenido:e.scrollHeight,overflowY:s.overflowY,display:s.display,height:s.height,maxHeight:s.maxHeight,padding:s.padding,lineHeight:s.lineHeight,alignItems:s.alignItems,boxSizing:s.boxSizing,estilo:e.getAttribute('style')}};const padres=[];for(let e=a;e&&!e.classList.contains('st-key-barra_panel');e=e.parentElement)padres.push(medir(e));return {padres,hijos:[...a.querySelectorAll('*')].map(medir)}})(),
                    errores:[...document.querySelectorAll('[data-testid="stException"]')].map(e=>e.innerText),
                    imagenesRotas:[...document.images].filter(e=>e.complete&&!e.naturalWidth).map(e=>e.alt),
                    iconos:[...document.querySelectorAll('[data-testid="stIconMaterial"]')].map(e=>({nombre:e.textContent,fuente:getComputedStyle(e).fontFamily})),
                    tipografia:[...document.querySelectorAll('h1,h2,h3,.upc-eyebrow,.upc-brand-title,.upc-role p,.stButton button p,[data-testid=stTextInput] input')].filter(e=>e.getClientRects().length).map(e=>({elemento:e.tagName,fuente:getComputedStyle(e).fontFamily,tamano:getComputedStyle(e).fontSize,peso:getComputedStyle(e).fontWeight})),
                    selectores:[...document.querySelectorAll('[role=combobox]')].filter(e=>e.getClientRects().length).map(e=>{let a=e;const r=[];for(let i=0;a&&i<5;i++,a=a.parentElement){const s=getComputedStyle(a);r.push({tag:a.tagName,testid:a.dataset.testid,baseweb:a.dataset.baseweb,alto:a.getBoundingClientRect().height,fondo:s.backgroundColor,fuente:s.fontSize})}return r}),
                    selectoresAcademicos:[...document.querySelectorAll('[class*=st-key-selector_academico_] input[role=combobox]')].filter(e=>e.getClientRects().length).map(e=>({alto:e.parentElement.getBoundingClientRect().height,fuente:getComputedStyle(e).fontSize,placeholder:e.placeholder})),
                    crearMateria:(()=>{const b=document.querySelector('.st-key-crear_nueva_materia button');return b?{fondo:getComputedStyle(b).backgroundColor,texto:getComputedStyle(b).color}:null})(),
                    color:getComputedStyle(document.querySelector('[data-testid="stAppViewContainer"]')).backgroundColor,
                    botonesRecortados:[...document.querySelectorAll('.stButton button p')].filter(e=>getComputedStyle(e).clipPath==='none'&&e.scrollWidth>e.clientWidth+2).map(e=>e.textContent),
                    accesoInstitucionalCompleto:!document.querySelector('.upc-hero')||[...document.querySelectorAll('.st-key-barra_panel button')].some(b=>b.querySelector('p')?.textContent.trim()==='Gestión académica'),
                    marcaInstitucional:[...document.querySelectorAll('.upc-official-logo,.st-key-logo_inicio img')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().height>0).map(e=>({ancho:e.getBoundingClientRect().width,alto:e.getBoundingClientRect().height,originalAncho:e.naturalWidth,originalAlto:e.naturalHeight,filtro:getComputedStyle(e).filter,reserva:parseFloat(getComputedStyle(e.closest('.st-key-logo_inicio')||e.parentElement).paddingLeft)})),
                    accesoADerecha:(()=>{if(!document.querySelector('.upc-hero'))return true;const b=document.querySelector('.st-key-acciones_cabecera');return Boolean(b&&Math.abs(b.getBoundingClientRect().right-document.querySelector('.st-key-barra_panel').getBoundingClientRect().right)<24)})(),
                    navegacionCabecera:(()=>{const visible=e=>e.getBoundingClientRect().height>0&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility==='visible';const controles=[...document.querySelectorAll('.st-key-barra_panel a,.st-key-barra_panel button')].filter(visible);const inicios=controles.filter(e=>e.querySelector('p')?.textContent.trim()==='Inicio');const cuenta=document.querySelector('.st-key-menu_cuenta [data-testid=stPopoverButton]');const rect=inicios[0]?.getBoundingClientRect(),otro=cuenta?.getBoundingClientRect();return {inicioPublico:Boolean(document.querySelector('.upc-hero')),inicios:inicios.length,etiquetaAntigua:controles.some(e=>e.querySelector('p')?.textContent.trim()==='Ir al inicio'),alineados:!rect||!otro||Math.abs(rect.top+rect.height/2-otro.top-otro.height/2)<2,logoEnlace:Boolean(document.querySelector('.st-key-logo_inicio a'))}})(),
                    menuCuenta:(()=>{const e=document.querySelector('[data-testid=stPopoverBody]:has(.st-key-opciones_cuenta)');if(!e)return null;const r=e.getBoundingClientRect();return {ancho:r.width,dentro:r.left>=0&&r.right<=innerWidth,separador:Boolean(e.querySelector('hr')),opciones:[...e.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height>0&&getComputedStyle(b).visibility==='visible').map(b=>({texto:b.querySelector('p')?.textContent,icono:b.querySelector('[data-testid=stIconMaterial]')?.textContent,alto:b.getBoundingClientRect().height,borde:getComputedStyle(b).borderWidth,opacidad:getComputedStyle(b).opacity,color:getComputedStyle(b).color,alineacion:getComputedStyle(b).justifyContent}))}})(),
                    anchoPrincipal:document.querySelector('[data-testid=stMain]').clientWidth,
                    contenidoPrincipal:document.querySelector('[data-testid=stMain]').scrollWidth})""")
                if dimensiones['contenidoPrincipal'] > dimensiones['anchoPrincipal'] + 2:
                    dimensiones['elementosDesbordados'] = js("(()=>{const m=document.querySelector('[data-testid=stMain]'),limite=m.getBoundingClientRect().left+m.clientLeft+m.clientWidth;return [...m.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>limite+1).slice(0,12).map(e=>({tag:e.tagName,testid:e.dataset.testid,derecha:e.getBoundingClientRect().right,ancho:e.getBoundingClientRect().width}))})()")
                informe['pantallas'][etiqueta] = dimensiones
                if dimensiones['contenido'] > dimensiones['ancho'] + 2: informe['fallos'].append(etiqueta + ': desbordamiento horizontal')
                if dimensiones['contenidoPrincipal'] > dimensiones['anchoPrincipal'] + 2: informe['fallos'].append(etiqueta + ': desbordamiento del panel')
                if dimensiones['botonesRecortados']: informe['fallos'].append(etiqueta + ': texto de botón recortado')
                if not dimensiones['accesoInstitucionalCompleto']: informe['fallos'].append(etiqueta + ': acceso Gestión académica recortado')
                if args.identidad and not dimensiones['accesoADerecha']: informe['fallos'].append(etiqueta + ': acceso institucional desalineado')
                for logo in dimensiones['marcaInstitucional']:
                    if not logo['originalAlto'] or abs(logo['ancho']/logo['alto']-logo['originalAncho']/logo['originalAlto'])>.01:
                        informe['fallos'].append(etiqueta + ': proporciones del logosímbolo alteradas')
                    if logo['filtro']!='none' or logo['reserva']<logo['ancho']/12:
                        informe['fallos'].append(etiqueta + ': filtro o reserva insuficiente en el logosímbolo')
                if dimensiones['errores'] or dimensiones['imagenesRotas']: informe['fallos'].append(etiqueta + ': error de pantalla o recurso')
                for control in dimensiones['selectoresAcademicos']:
                    if abs(control['alto']-44)>1 or control['fuente']!='16px' or 'Choose' in control['placeholder']:
                        informe['fallos'].append(etiqueta + ': selector académico inconsistente')
                if not dimensiones['focoCuentaInstalado']:
                    informe['fallos'].append(etiqueta + ': falta el complemento vigente de foco de cuenta')
                if not dimensiones['marcaNombreCompleto']:
                    informe['fallos'].append(etiqueta + ': texto institucional recortado')
                perfil = dimensiones['perfilEstudiante']
                if perfil and (not perfil['ruta'].endswith('/mi-perfil') or not perfil['porcentajeCentrado'] or not perfil['porcentajeSinRecorte'] or perfil['recortes']):
                    informe['fallos'].append(etiqueta + ': perfil sin centrar o con textos recortados')
                pie = dimensiones['pieAcademico']
                if not pie or pie['cantidad']!=1:
                    informe['fallos'].append(etiqueta + ': falta un único pie académico compartido')
                elif (abs(pie['izquierda']-pie['inicioDisponible'])>1 or abs(pie['derecha']-pie['finDisponible'])>1 or abs(pie['banda']['ancho']-pie['ancho'])>1 or pie['textosRecortados'] or pie['posicion']=='fixed' or not pie['despuesContenido'] or any('Georgia' not in t['fuente'] or t['estilo']!='italic' or t['peso']!='400' for t in pie['titulos'])):
                    informe['fallos'].append(etiqueta + ': composición o legibilidad del pie académico incorrecta')
                elif dimensiones['ancho']>1000 and abs(pie['zonas'][0]['ancho']/pie['ancho']-.53)>.01:
                    informe['fallos'].append(etiqueta + ': proporción del pie diferente de 53/47')
                elif dimensiones['ancho']<=600 and pie['zonas'][1]['y']<=pie['zonas'][0]['y']:
                    informe['fallos'].append(etiqueta + ': las zonas del pie deben apilarse en móvil')
                geometria = dimensiones['geometriaControles']
                if geometria['inicio'] and (geometria['inicio']['barras'] or not all(geometria['inicio'][k] for k in ('iconoCentrado','textoCentrado','sinRecortes'))):
                    informe['fallos'].append(etiqueta + ': scroll o desajuste vertical en Inicio')
                separador = geometria['separador']
                if separador and any(abs(separador['linea'][k]-separador['resaltado'][k])>.1 for k in ('izquierda','derecha','ancho')):
                    informe['fallos'].append(etiqueta + ': separador desalineado con Cerrar sesión')
                if separador and (not separador['contenedorComun'] or not separador['independiente'] or separador['separacion']<=separador['contorno']):
                    informe['fallos'].append(etiqueta + ': el separador debe estar separado del contorno y compartir contenedor')
                nav = dimensiones['navegacionCabecera']
                if nav['inicios'] != (0 if nav['inicioPublico'] else 1) or nav['etiquetaAntigua'] or not nav['alineados'] or not nav['logoEnlace']:
                    informe['fallos'].append(etiqueta + ': composición inconsistente del encabezado')
                menu = dimensiones['menuCuenta']
                if menu and (not 200 <= menu['ancho'] <= 240 or not menu['dentro'] or not menu['separador'] or any(not o['icono'] or o['borde']!='0px' or float(o['opacidad'])<1 or o['alineacion']!='flex-start' for o in menu['opciones'])):
                    informe['fallos'].append(etiqueta + ': menú de cuenta inconsistente')
                if dimensiones['crearMateria'] and dimensiones['crearMateria']!={'fondo':'rgb(0, 115, 55)','texto':'rgb(255, 255, 255)'}:
                    informe['fallos'].append(etiqueta + ': crear materia no tiene contraste primario')
                for icono in dimensiones['iconos']:
                    if 'Material' not in icono['fuente']: informe['fallos'].append(etiqueta + ': fuente de icono incorrecta')
                if args.zoom is not None:
                    # El viewport físico se mantiene fijo; un clip con el ancho CSS a 25 %
                    # produciría un lienzo cuatro veces mayor que la ventana real.
                    datos = cdp('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
                else:
                    contenido = cdp('Page.getLayoutMetrics')['cssContentSize']
                    datos = cdp('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True,
                        'clip': {'x': 0, 'y': 0, 'width': contenido['width'], 'height': contenido['height'], 'scale': 1}})
                (carpeta / (etiqueta + '.png')).write_bytes(base64.b64decode(datos['data']))
                if js("document.querySelector('[data-testid=stMain]').scrollHeight>innerHeight+20"):
                    js("document.querySelector('[data-testid=stMain]').scrollTop=100000")
                    js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))', True)
                    abajo = cdp('Page.captureScreenshot', {'format': 'png'})
                    (carpeta / (etiqueta + '_inferior.png')).write_bytes(base64.b64decode(abajo['data']))
                    js("document.querySelector('[data-testid=stMain]').scrollTop=0")
            cdp('Page.enable'); cdp('Runtime.enable'); cdp('Network.enable')
            # Bloquear recursos remotos prueba que el frontend funciona sin Google Fonts/ibb.
            cdp('Fetch.enable', {'patterns': [{'urlPattern': '*', 'requestStage': 'Request'}]})
            if args.lento:
                cdp('Emulation.setCPUThrottlingRate', {'rate': 4})
                cdp('Network.emulateNetworkConditions', {'offline': False, 'latency': 120,
                    'downloadThroughput': 512 * 1024, 'uploadThroughput': 128 * 1024})
                informe['cpu_x4_latencia_120ms'] = True
            cdp('Page.addScriptToEvaluateOnNewDocument', {'source': """
                window.__barraVisible=[];
                const registrar=()=>{
                    const selectores=['stAppDeployButton','stStatusWidget','stMainMenu'];
                    for(const nombre of selectores) for(const e of document.querySelectorAll('[data-testid="'+nombre+'"]')) {
                        if(e.getClientRects().length && getComputedStyle(e).visibility==='visible' && getComputedStyle(e).display!=='none' && !window.__barraVisible.includes(nombre)) window.__barraVisible.push(nombre);
                    }
                };
                new MutationObserver(registrar).observe(document,{subtree:true,childList:true,attributes:true});
                """})
            inicio = time.monotonic()
            cdp('Page.navigate', {'url': url + '/estudiante?registro=1' if args.registro_estudiante else url + '/docente?fixture=profesor' if args.paneles else url})
            esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Crear Cuenta'))" if args.registro_estudiante else
                    "[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Tomar Asistencia'))" if args.paneles else
                    "[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Portal del Profesor'))")
            informe['segundos_inicio_frio'] = round(time.monotonic() - inicio, 3)
            if args.zoom is not None:
                informe['modo'] = 'zoom_nativo_perfil_aislado'
                informe['zoom'] = js("""({factor:devicePixelRatio,escalaPinch:visualViewport.scale,ventana:outerWidth,
                    viewportCSS:innerWidth,altoCSS:innerHeight,
                    anchoContenidoCSS:document.querySelector('.stMainBlockContainer').getBoundingClientRect().width,
                    tituloCSS:parseFloat(getComputedStyle(document.querySelector('.upc-hero h1')).fontSize),
                    textoCSS:parseFloat(getComputedStyle(document.querySelector('.upc-hero-description')).fontSize)})""")
                informe['zoom']['solicitado'] = args.zoom
                if abs(informe['zoom']['factor']-args.zoom/100)>.01 or abs(informe['zoom']['escalaPinch']-1)>.01:
                    informe['fallos'].append('El navegador no aplicó el zoom nativo solicitado.')
                captura('inicio_zoom_' + str(args.zoom))
                pulsar('Portal del Profesor')
                esperar("Boolean(document.querySelector('input[type=password]'))")
                captura('docente_zoom_' + str(args.zoom))
                pulsar('Inicio')
                esperar("Boolean(document.querySelector('.upc-hero'))")
                pulsar('Portal del Estudiante')
                esperar("Boolean(document.querySelector('[data-testid=stCameraInput]'))")
                captura('estudiante_zoom_' + str(args.zoom))
            elif args.excepciones:
                revisar_excepciones(cdp, js, esperar, captura, url)
            elif args.registro_estudiante:
                revisar_foco_texto(js, informe, 'registro_estudiante', esperar)
                captura('registro_estudiante_escritorio')
                cdp('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
                revisar_foco_texto(js, informe, 'registro_estudiante_movil', esperar)
                captura('registro_estudiante_movil')
            elif args.paneles:
                revisar_paneles(cdp, js, esperar, pulsar, captura, url)
            elif args.administracion_real:
                informe['modo'] = 'administracion_real_solo_consultas_y_preparacion_csv'
                revisar_administracion_real(cdp, js, esperar, pulsar, captura, informe)
            else:
                captura('inicio_escritorio')
                if args.identidad:
                    for ancho, alto in [(768, 1024), (390, 844), (320, 740)]:
                        cdp('Emulation.setDeviceMetricsOverride', {'width': ancho, 'height': alto, 'deviceScaleFactor': 1, 'mobile': ancho<700})
                        captura('identidad_' + str(ancho))
                    cdp('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
                informe['barra_visible_durante_arranque'] = js('window.__barraVisible')
                if informe['barra_visible_durante_arranque']: informe['fallos'].append('Se vio la barra de desarrollo en el arranque.')
                pulsar('Gestión académica')
                esperar("Boolean(document.querySelector('.st-key-acceso_administrativo'))")
                captura('administracion_acceso_escritorio')
                pulsar('Inicio')
                esperar("Boolean(document.querySelector('.upc-hero'))")
                cdp('Page.navigate', {'url': url + '/mi-perfil?estudiante_id=999999'})
                esperar("Boolean(document.querySelector('.st-key-acceso_estudiante'))")
                assert not js("Boolean(document.querySelector('.perfil-portada'))"), 'El perfil no debe mostrarse sin sesión.'
                captura('perfil_acceso_sin_sesion')
                pulsar('Inicio')
                esperar("Boolean(document.querySelector('.upc-hero'))")
                pulsar('Portal del Profesor')
                esperar("Boolean(document.querySelector('input[type=password]'))")
                js("document.querySelector('input:not([type=password])').focus()")
                cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Tab', 'code': 'Tab', 'windowsVirtualKeyCode': 9})
                cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Tab', 'code': 'Tab', 'windowsVirtualKeyCode': 9})
                informe['teclado_usuario_contrasena'] = js("document.activeElement?.type==='password'")
                if not informe['teclado_usuario_contrasena']: informe['fallos'].append('El foco no avanza del usuario a la contraseña con Tab.')
                revisar_foco_texto(js, informe, 'acceso_docente', esperar)
                captura('docente_acceso_escritorio')
                pulsar('Registrarme en su lugar')
                esperar("document.querySelectorAll('input[type=password]').length===3")
                revisar_foco_texto(js, informe, 'registro_docente', esperar)
                captura('docente_registro_escritorio')
                if args.claves: revisar_claves(js, esperar, captura, informe)
                pulsar('Iniciar Sesión en su lugar')
                esperar("document.querySelectorAll('input[type=password]').length===1")
                js("document.querySelector('button[aria-label=\"Show password\"]').click()")
                esperar("Boolean(document.querySelector('button[aria-label=\"Hide password\"]'))")
                informe['mostrar_password'] = True
                js("document.querySelector('button[aria-label=\"Hide password\"]').click()")
                esperar("Boolean(document.querySelector('input[type=password]'))")
                informe['ocultar_password'] = True
                if args.recuperacion_docente:
                    revisar_recuperacion_docente(cdp,js,esperar,pulsar,captura,informe)
                cdp('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
                captura('docente_acceso_movil')
                pulsar('Registrarme en su lugar')
                esperar("document.querySelectorAll('input[type=password]').length===3")
                captura('docente_registro_movil')
                pulsar('Inicio')
                esperar("[...document.querySelectorAll('button')].some(b=>b.innerText.includes('Portal del Estudiante'))")
                captura('inicio_movil')
                pulsar('Portal del Estudiante')
                esperar("Boolean(document.querySelector('[data-testid=stCameraInput]'))")
                captura('estudiante_acceso_movil')
            if informe['externos']: informe['fallos'].append('Se solicitaron recursos externos.')
            informe['estado'] = 'CORRECTO' if not informe['fallos'] else 'FALLIDO'
    except Exception as exc:
        informe['estado'] = 'FALLIDO'
        informe['fallos'].append('Comprobación interrumpida: ' + type(exc).__name__)
        raise
    finally:
        if chrome:
            chrome.terminate()
            try: chrome.wait(timeout=8)
            except subprocess.TimeoutExpired: chrome.kill(); chrome.wait()
        if servidor is not None:
            servidor.terminate()
            try: servidor.wait(timeout=8)
            except subprocess.TimeoutExpired: servidor.kill(); servidor.wait()
        log.close()
        (carpeta / 'resultado.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Evidencia:', carpeta.relative_to(RAIZ))
    print('Inicio frío:', informe['segundos_inicio_frio'], 's | Pantallas:', len(informe['pantallas']))
    print('Resultado:', 'CORRECTO' if not informe['fallos'] else informe['fallos'])
    if informe['fallos']: raise SystemExit(1)


if __name__ == '__main__': main()
