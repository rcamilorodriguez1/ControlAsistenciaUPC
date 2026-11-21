"""Revisión de Firefox instalado mediante WebDriver BiDi, con un perfil temporal."""
import argparse
import base64
import json
import os
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
from _frontend_mediciones import medir_interfaz, validar_mediciones
from verificar_frontend import revisar_claves, revisar_foco_texto, revisar_recuperacion_docente


class FirefoxBiDi:
    def __init__(self, ws, informe, fallo_fuente):
        self.ws, self.informe, self.fallo_fuente = ws, informe, fallo_fuente
        self.secuencia = 0
        self.contexto = None

    def enviar(self, metodo, parametros):
        self.secuencia += 1
        self.ws.send(json.dumps({'id': self.secuencia, 'method': metodo, 'params': parametros}))
        return self.secuencia

    def llamar(self, metodo, parametros=None):
        mensaje = self.enviar(metodo, parametros or {})
        while True:
            respuesta = json.loads(self.ws.recv(timeout=45))
            if respuesta.get('method') == 'network.beforeRequestSent':
                solicitud = respuesta['params']
                recurso = solicitud['request']['url']
                partes = urlsplit(recurso)
                externo = partes.scheme in ('http', 'https', 'ws', 'wss') and partes.hostname not in ('localhost', '127.0.0.1')
                bloquear = externo
                if externo and recurso not in self.informe['externos']:
                    self.informe['externos'].append(recurso)
                if self.fallo_fuente and 'MaterialSymbols-Rounded.' in partes.path and not partes.query.startswith('upc_iconos='):
                    bloquear = True
                    if recurso not in self.informe['fuentes_iconos_bloqueadas']:
                        self.informe['fuentes_iconos_bloqueadas'].append(recurso)
                if solicitud.get('isBlocked'):
                    self.enviar('network.failRequest' if bloquear else 'network.continueRequest', {'request': solicitud['request']['request']})
                continue
            if respuesta.get('id') == mensaje:
                if respuesta.get('type') == 'error':
                    raise RuntimeError(f'{metodo}: {respuesta.get("error")}: {respuesta.get("message")}')
                return respuesta.get('result', {})

    def js(self, expresion, esperar=False):
        # JSON evita depender de la serialización de objetos remotos propia del motor.
        expresion = '(async()=>JSON.stringify(await (' + expresion + ')))()'
        resultado = self.llamar('script.evaluate', {'expression': expresion,
            'target': {'context': self.contexto}, 'awaitPromise': True})
        if resultado.get('type') == 'exception':
            raise RuntimeError(resultado['exceptionDetails'].get('text', 'Error JavaScript'))
        valor = resultado['result']
        return json.loads(valor['value']) if valor['type'] == 'string' else None

    def navegar(self, url):
        self.llamar('browsingContext.navigate', {'context': self.contexto, 'url': url, 'wait': 'complete'})

    def viewport(self, ancho, alto):
        self.llamar('browsingContext.setViewport', {'context': self.contexto,
            'viewport': {'width': ancho, 'height': alto}, 'devicePixelRatio': 1})

    def tecla(self, nombre):
        valor = {'Enter': '\ue007', 'Escape': '\ue00c', 'Tab': '\ue004'}[nombre]
        self.llamar('input.performActions', {'context': self.contexto,
            'actions': [{'type': 'key', 'id': 'teclado', 'actions': [
                {'type': 'keyDown', 'value': valor}, {'type': 'keyUp', 'value': valor}]}]})

    def activar(self):
        self.llamar('browsingContext.activate', {'context': self.contexto})

    def adaptar_viewport(self, metodo, parametros):
        # Permite reutilizar el recorrido de recuperación sin simular APIs de Chrome.
        if metodo != 'Emulation.setDeviceMetricsOverride':
            raise ValueError('El recorrido compartido solicitó una acción no soportada.')
        self.viewport(parametros['width'], parametros['height'])

    def captura(self, ruta):
        datos = self.llamar('browsingContext.captureScreenshot', {'context': self.contexto,
            'origin': 'viewport', 'format': {'type': 'image/png'}})
        ruta.write_bytes(base64.b64decode(datos['data']))


def main():
    usar_entorno()
    from websockets.sync.client import connect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--navegador', type=Path)
    parser.add_argument('--url', help='Instancia HTTPS/HTTP local ya activa; no se inicia ni detiene.')
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument('--paneles', action='store_true', help='Portales y diálogos con datos sintéticos y Oracle bloqueado.')
    grupo.add_argument('--excepciones', action='store_true', help='Verificación excepcional y panel administrativo sintéticos.')
    parser.add_argument('--fallo-fuente-iconos', action='store_true')
    args = parser.parse_args()
    candidatos = [args.navegador] if args.navegador else [
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Mozilla Firefox/firefox.exe',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'))/'Mozilla Firefox/firefox.exe']
    navegador = next((p for p in candidatos if p and p.is_file()), None)
    if navegador is None:
        parser.error('No se encontró Firefox; indicar --navegador.')
    if args.url and (args.paneles or args.excepciones):
        parser.error('Las vistas sintéticas requieren su proceso separado.')
    with socket.socket() as reserva:
        reserva.bind(('127.0.0.1', 0)); puerto = reserva.getsockname()[1]
    with socket.socket() as reserva:
        reserva.bind(('127.0.0.1', 0)); puerto_bidi = reserva.getsockname()[1]
    url = args.url.rstrip('/') if args.url else f'http://127.0.0.1:{puerto}'
    destino = urlsplit(url)
    if destino.scheme not in ('http', 'https') or destino.hostname not in ('localhost', '127.0.0.1') or destino.username or destino.password or destino.path not in ('', '/') or destino.query or destino.fragment:
        parser.error('Solo se admite la raíz de una instancia local, sin credenciales.')
    carpeta = RAIZ/'.local/frontend'/uuid4().hex[:12]
    perfil = carpeta/'perfil'
    perfil.mkdir(parents=True)
    # Confía en las raíces ya instaladas en Windows; no instala certificados ni omite TLS.
    (perfil/'user.js').write_text(
        'user_pref("security.enterprise_roots.enabled", true);\n'
        # Preferencia del harness de Mozilla para acciones de foco automatizadas;
        # document.hasFocus se comprueba antes de evaluar su indicador visual.
        'user_pref("focusmanager.testmode", true);\n', encoding='utf-8')
    oculto = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    log = (carpeta/'servidor.log').open('w', encoding='utf-8')
    log_firefox = (carpeta/'firefox.log').open('w', encoding='utf-8')
    sintetico = args.paneles or args.excepciones
    entrada = RAIZ/('tests/preview_frontend.py' if sintetico else 'principal.py')
    servidor = None if args.url else subprocess.Popen([sys.executable, '-B', '-m', 'streamlit', 'run', str(entrada),
        '--server.address', '127.0.0.1', '--server.port', str(puerto), '--browser.serverAddress', '127.0.0.1',
        '--browser.serverPort', str(puerto), '--browser.gatherUsageStats', 'false'], cwd=RAIZ,
        env={**os.environ, 'APP_BASE_URL': url}, stdout=log, stderr=subprocess.STDOUT, creationflags=oculto)
    firefox = None
    informe = {'estado': 'INICIADO', 'motor': 'Firefox / WebDriver BiDi',
        'modo': 'vista_sintetica_oracle_bloqueado' if sintetico else 'navegacion_anonima',
        'servidor_existente': bool(args.url), 'url_local': url, 'pantallas': {}, 'externos': [],
        'fuentes_iconos_bloqueadas': [], 'fallos': []}
    try:
        for _ in range(160):
            try:
                contexto = ssl.create_default_context(cafile=RAIZ/'.certs/ca.pem') if destino.scheme == 'https' else None
                with urlopen(url+'/_stcore/health', timeout=1, context=contexto) as respuesta:
                    if respuesta.status == 200:
                        break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('La instancia local no respondió.')
        firefox = subprocess.Popen([str(navegador), '--headless', '--no-remote', '--profile', str(perfil),
            '--remote-debugging-port', str(puerto_bidi), 'about:blank'], stdout=log_firefox,
            stderr=subprocess.STDOUT, creationflags=oculto)
        for _ in range(150):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1', puerto_bidi)) == 0:
                    break
            if firefox.poll() is not None:
                raise RuntimeError('Firefox terminó antes de iniciar BiDi.')
            time.sleep(.1)
        else:
            raise RuntimeError('Firefox no abrió su canal local de automatización.')
        with connect(f'ws://127.0.0.1:{puerto_bidi}/session', proxy=None, max_size=25_000_000) as ws:
            bidi = FirefoxBiDi(ws, informe, args.fallo_fuente_iconos)
            capacidades = bidi.llamar('session.new', {'capabilities': {'alwaysMatch': {'acceptInsecureCerts': False}}})['capabilities']
            informe['navegador'] = capacidades['browserName']+'/'+capacidades['browserVersion']
            informe['acceptInsecureCerts'] = capacidades['acceptInsecureCerts']
            bidi.contexto = bidi.llamar('browsingContext.getTree', {'maxDepth': 0})['contexts'][0]['context']
            bidi.activar()
            bidi.llamar('session.subscribe', {'events': ['network.beforeRequestSent']})
            bidi.llamar('network.addIntercept', {'phases': ['beforeRequestSent'], 'contexts': [bidi.contexto]})
            js = bidi.js
            def esperar(expresion):
                for _ in range(200):
                    if js(expresion):
                        return
                    time.sleep(.1)
                raise RuntimeError('No apareció el elemento esperado: '+expresion)
            def pulsar(texto):
                expresion = f'[...document.querySelectorAll("button,a")].find(b=>b.getClientRects().length&&b.innerText.includes({json.dumps(texto)}))'
                esperar('Boolean('+expresion+')')
                js(expresion+'.click()')
            def captura(etiqueta):
                esperar("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state')==='notRunning'")
                # Los widgets lazy de navegación pueden terminar de hidratar después
                # del script Python, especialmente con la caché vacía de Firefox.
                esperar("Boolean(document.querySelector('.st-key-logo_inicio a')) && (document.querySelector('.upc-hero') ? [...document.querySelectorAll('.st-key-barra_panel button')].some(b=>b.querySelector('p')?.textContent.trim()==='Gestión académica') : Boolean(document.querySelector('.st-key-navegacion_inicio a')))")
                js('document.fonts.ready.then(()=>true)', True)
                js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))', True)
                # El scrollbar puede cambiar el ancho disponible durante el rerun.
                for _ in range(40):
                    if js("(()=>{const m=document.querySelector('[data-testid=stMain]'),p=m.querySelector('.upc-academic-footer');if(!p)return true;const r=p.getBoundingClientRect(),b=m.getBoundingClientRect();return Math.abs(r.left-b.left-m.clientLeft)<1&&Math.abs(r.width-m.clientWidth)<1})()"):
                        break
                    time.sleep(.1)
                medidas = medir_interfaz(js)
                informe['pantallas'][etiqueta] = medidas
                informe['fallos'].extend(validar_mediciones(medidas, etiqueta, identidad=True))
                bidi.captura(carpeta/(etiqueta+'.png'))
                if js("document.querySelector('[data-testid=stMain]').scrollHeight>innerHeight+20"):
                    js("document.querySelector('[data-testid=stMain]').scrollTop=100000")
                    js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))', True)
                    bidi.captura(carpeta/(etiqueta+'_inferior.png'))
                    js("document.querySelector('[data-testid=stMain]').scrollTop=0")
            def revisar_foco_firefox(js,informe,etiqueta,esperar):
                # Una ventana inactiva de este entorno Windows no aplica :focus.
                # No presentarlo como fallo de la app ni como una prueba superada.
                if not js('document.hasFocus()'):
                    informe.setdefault('comprobaciones_omitidas',[]).append(
                        etiqueta+': indicador visual de foco; ventana de automatización inactiva')
                    return
                revisar_foco_texto(js,informe,etiqueta,esperar)
            def menu(rol):
                js("document.querySelector('.st-key-menu_cuenta button').click()")
                esperar("Boolean(document.querySelector('[data-testid=stPopoverBody]')?.getClientRects().length)")
                captura(rol+'_menu_'+str(js('innerWidth')))
                bidi.tecla('Escape')
                esperar("!document.querySelector('[data-testid=stPopoverBody]')?.getClientRects().length")
            bidi.viewport(1440, 1080)
            bidi.navegar(url+'/docente?fixture=profesor' if args.paneles else url)
            esperar("Boolean(document.querySelector('.st-key-resumen_panel'))" if args.paneles else "Boolean(document.querySelector('.upc-hero'))")
            if args.fallo_fuente_iconos:
                informe['fuente_nativa_disponible'] = js('document.fonts.load(\'24px "Material Symbols Rounded"\',"visibility").then(()=>true,()=>false)', True)
            if args.excepciones:
                for ancho, alto in [(1440,1080),(768,1024),(390,844),(320,740)]:
                    bidi.viewport(ancho, alto)
                    bidi.navegar(url+'/estudiante')
                    esperar("Boolean(document.querySelector('.st-key-acceso_estudiante details'))")
                    js("document.querySelector('.st-key-acceso_estudiante details').open=true")
                    esperar("Boolean(document.querySelector('input[type=password]')?.getClientRects().length)")
                    captura('excepcion_acceso_'+str(ancho))
                    bidi.navegar(url+'/estudiante?fixture=estudiante&excepcion=1')
                    esperar("document.body.innerText.includes('Verificación excepcional / biometría incompleta')")
                    captura('excepcion_panel_'+str(ancho))
                    bidi.navegar(url+'/administracion?fixture=administrador')
                    esperar("Boolean(document.querySelector('[role=radiogroup]'))")
                    js("[...document.querySelectorAll('[role=radiogroup] label')].find(e=>e.textContent.includes('Verificación')).click()")
                    esperar("[...document.querySelectorAll('button')].some(e=>e.textContent.includes('Autorizar excepción'))")
                    captura('excepcion_administracion_'+str(ancho))
                    menu('administracion')
            elif args.paneles:
                for ancho, alto in [(1440,1080),(390,844),(320,740)]:
                    bidi.viewport(ancho, alto)
                    captura('docente_asistencia_'+str(ancho))
                    menu('docente')
                    pulsar('Gestionar Materias')
                    esperar("[...document.querySelectorAll('button')].some(e=>e.textContent.includes('Crear nueva materia'))")
                    captura('docente_materias_'+str(ancho))
                    if ancho==1440:
                        for accion,etiqueta,selector in [('Crear nueva materia','crear_materia','[role=dialog] input'),
                            ('Compartir Código: Bases de Datos','compartir_materia','[role=dialog] img')]:
                            pulsar(accion);esperar('Boolean(document.querySelector('+json.dumps(selector)+'))')
                            captura(etiqueta)
                            js("document.querySelector('[role=dialog] button[aria-label=Close]').click()")
                            esperar("!document.querySelector('[role=dialog]')?.getClientRects().length")
                    pulsar('Registros de Asistencia')
                    esperar("Boolean(document.querySelector('[data-testid=stDataFrame]'))")
                    captura('docente_registros_'+str(ancho))
                    pulsar('Tomar Asistencia')
                bidi.viewport(1440,1080)
                pulsar('Revisar resultado pendiente')
                esperar("Boolean(document.querySelector('[role=dialog] [data-testid=stDataFrame]'))")
                captura('revision_asistencia')
                js("document.querySelector('[role=dialog] button[aria-label=Close]').click()")
                esperar("!document.querySelector('[role=dialog]')?.getClientRects().length")
                pulsar('Inicio');esperar("Boolean(document.querySelector('.upc-hero'))")
                captura('docente_inicio_con_sesion')
                pulsar('Portal del Profesor');esperar("Boolean(document.querySelector('.st-key-resumen_panel'))")
                js("document.querySelector('.st-key-menu_cuenta button').click()")
                esperar("Boolean(document.querySelector('.st-key-loginbackbtn button')?.getClientRects().length)")
                pulsar('Cerrar sesión');esperar("Boolean(document.querySelector('.st-key-acceso_docente'))")
                captura('docente_salida')
                bidi.navegar(url+'/estudiante?fixture=estudiante')
                esperar("Boolean(document.querySelector('.st-key-resumen_panel'))")
                for ancho,alto in [(1440,1080),(768,1024),(390,844),(320,740)]:
                    bidi.viewport(ancho,alto);captura('estudiante_panel_'+str(ancho));menu('estudiante')
                    js("document.querySelector('.st-key-menu_cuenta button').click()")
                    esperar("Boolean(document.querySelector('[data-testid=stPopoverBody]')?.getClientRects().length)")
                    pulsar('Mi perfil');esperar("Boolean(document.querySelector('.perfil-portada'))")
                    captura('perfil_estudiante_'+str(ancho))
                    if ancho==1440:
                        js("document.querySelector('.st-key-perfil_materias summary').click()")
                        esperar("Boolean(document.querySelector('.perfil-materia-estado'))")
                        captura('perfil_materia_desplegada')
                        pulsar('Mes anterior');esperar("document.querySelector('.perfil-mes-titulo')?.textContent.includes('Octubre')")
                        captura('perfil_mes_anterior');pulsar('Mes siguiente')
                    pulsar('Volver a mi portal');esperar("Boolean(document.querySelector('.st-key-resumen_panel'))")
            else:
                captura('inicio_escritorio')
                for ancho,alto in [(768,1024),(390,844),(320,740)]:
                    bidi.viewport(ancho,alto);captura('inicio_'+str(ancho))
                bidi.viewport(1440,1080)
                pulsar('Gestión académica');esperar("Boolean(document.querySelector('.st-key-acceso_administrativo'))")
                captura('administracion_acceso');pulsar('Inicio')
                esperar("Boolean(document.querySelector('.upc-hero'))")
                pulsar('Portal del Profesor');esperar("Boolean(document.querySelector('input[type=password]'))")
                bidi.activar()
                js("document.querySelector('input:not([type=password])').focus()")
                bidi.tecla('Tab')
                assert js("document.activeElement.type==='password'"), 'Tab no alcanza la contraseña.'
                captura('docente_acceso')
                pulsar('Registrarme en su lugar');esperar("document.querySelectorAll('input[type=password]').length===3")
                captura('docente_registro');revisar_claves(js,esperar,captura,informe)
                pulsar('Iniciar Sesión en su lugar');esperar("document.querySelectorAll('input[type=password]').length===1")
                js("document.querySelector('button[aria-label=\"Show password\"]').click()")
                esperar("Boolean(document.querySelector('button[aria-label=\"Hide password\"]'))")
                captura('docente_password_visible')
                js("document.querySelector('button[aria-label=\"Hide password\"]').click()")
                esperar("Boolean(document.querySelector('input[type=password]'))")
                captura('docente_password_oculto')
                bidi.activar()
                revisar_recuperacion_docente(bidi.adaptar_viewport,js,esperar,pulsar,captura,informe,revisar_foco=revisar_foco_firefox)
                bidi.viewport(390,844);captura('docente_acceso_movil')
                pulsar('Registrarme en su lugar');esperar("document.querySelectorAll('input[type=password]').length===3")
                captura('docente_registro_movil');pulsar('Inicio');esperar("Boolean(document.querySelector('.upc-hero'))")
                pulsar('Portal del Estudiante');esperar("Boolean(document.querySelector('[data-testid=stCameraInput]'))")
                captura('estudiante_acceso_movil')
                js("document.querySelector('.st-key-acceso_estudiante details').open=true")
                esperar("Boolean(document.querySelector('input[type=password]')?.getClientRects().length)")
                bidi.activar()
                revisar_foco_firefox(js,informe,'acceso_estudiante',esperar)
                captura('estudiante_acceso_alternativo_movil')
            if informe['externos']:
                informe['fallos'].append('Se solicitaron recursos externos.')
            if args.fallo_fuente_iconos and (informe.get('fuente_nativa_disponible') or not informe['fuentes_iconos_bloqueadas']):
                informe['fallos'].append('No se reprodujo el fallo de la fuente nativa.')
            informe['estado'] = 'CORRECTO' if not informe['fallos'] else 'FALLIDO'
            try:
                bidi.llamar('browser.close')
            except Exception:
                pass
    except Exception as exc:
        informe['estado'] = 'FALLIDO'
        informe['fallos'].append('Comprobación interrumpida: '+str(exc))
        raise
    finally:
        for proceso in (firefox,servidor):
            if proceso is not None and proceso.poll() is None:
                proceso.terminate()
                try:
                    proceso.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proceso.kill();proceso.wait()
        log.close();log_firefox.close()
        (carpeta/'resultado.json').write_text(json.dumps(informe,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Evidencia:',carpeta.relative_to(RAIZ))
    print('Navegador:',informe['navegador'],'| Pantallas:',len(informe['pantallas']))
    print('Resultado:',informe['estado'],informe['fallos'])
    if informe['fallos']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
