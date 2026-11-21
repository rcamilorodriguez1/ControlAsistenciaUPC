"""Mediciones y criterios visuales comunes a Chromium y Firefox."""


def medir_interfaz(js):
    return js("""({ancho:innerWidth,contenido:document.documentElement.scrollWidth,
                    focoCuentaInstalado:window.__upcFocoCuenta instanceof MutationObserver,
                    marcaNombreCompleto:[...document.querySelectorAll('.upc-brand-title,.upc-brand-subtitle')].every(e=>e.getBoundingClientRect().width>70&&e.scrollWidth<=e.clientWidth+2),
                    perfilEstudiante:(()=>{const p=document.querySelector('.st-key-perfil_estudiante');if(!p)return null;const circulo=p.querySelector('.perfil-circulo').getBoundingClientRect(),valor=p.querySelector('.perfil-circulo strong').getBoundingClientRect();return {ruta:location.pathname,porcentajeCentrado:Math.abs(valor.left+valor.width/2-circulo.left-circulo.width/2)<1,porcentajeSinRecorte:valor.left>=circulo.left&&valor.right<=circulo.right,mes:p.querySelector('.perfil-mes-titulo').textContent,dias:p.querySelectorAll('.perfil-dia').length,presentes:p.querySelectorAll('[data-estado=presente]').length,ausentes:p.querySelectorAll('[data-estado=ausente]').length,mixtos:p.querySelectorAll('[data-estado=mixto]').length,sinRegistros:p.querySelectorAll('[data-estado=sin-registros]').length,materias:p.querySelectorAll('.st-key-perfil_materias [data-testid=stExpander]').length,recortes:[...p.querySelectorAll('h1,.perfil-codigo,.perfil-mes-titulo,summary p,.perfil-metricas span')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.tagName)}})(),
                    pieAcademico:(()=>{const pies=[...document.querySelectorAll('.upc-academic-footer')].filter(e=>e.getBoundingClientRect().height>0),e=pies[0];if(!e)return null;const r=e.getBoundingClientRect(),main=document.querySelector('[data-testid=stMain]'),m=main.getBoundingClientRect(),zonas=[...e.querySelectorAll('.academic-footer-zone')].map(z=>{const b=z.getBoundingClientRect();return {x:b.x,y:b.y,ancho:b.width,alto:b.height,fondo:getComputedStyle(z).backgroundImage}}),banda=e.querySelector('.academic-footer-band').getBoundingClientRect();return {cantidad:pies.length,izquierda:r.left,derecha:r.right,ancho:r.width,alto:r.height,inicioDisponible:m.left+main.clientLeft,finDisponible:m.left+main.clientLeft+main.clientWidth,zonas,banda:{x:banda.x,ancho:banda.width},titulos:[...e.querySelectorAll('.academic-footer-title')].map(t=>{const s=getComputedStyle(t);return {texto:t.textContent,fuente:s.fontFamily,estilo:s.fontStyle,peso:s.fontWeight}}),textosRecortados:[...e.querySelectorAll('h2,p,li,dt,dd,span')].filter(t=>t.scrollWidth>t.clientWidth+1).map(t=>t.textContent),posicion:getComputedStyle(e).position,despuesContenido:!e.closest('[role=dialog]')&&Boolean(e.closest('.st-key-pie_academico'))}})(),
                    geometriaControles:(()=>{const a=document.querySelector('.st-key-navegacion_inicio a'),hr=document.querySelector('.st-key-opciones_cuenta hr'),salir=document.querySelector('.st-key-loginbackbtn button');const limites=e=>{const r=e.getBoundingClientRect();return {izquierda:r.left,derecha:r.right,ancho:r.width}};let inicio=null;if(a){const i=a.querySelector('[data-testid=stIconMaterial]'),p=a.querySelector('p'),r=a.getBoundingClientRect(),centro=e=>{const b=e.getBoundingClientRect();return b.top+b.height/2};const barras=[];for(let e=a;e&&!e.classList.contains('st-key-barra_panel');e=e.parentElement)if(['auto','scroll'].includes(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight)barras.push(e.dataset.testid||e.tagName);inicio={barras,iconoCentrado:Math.abs(centro(i)-centro(a))<1,textoCentrado:Math.abs(centro(p)-centro(a))<1,sinRecortes:[i,p].every(e=>{const b=e.getBoundingClientRect();return b.top>=r.top&&b.bottom<=r.bottom})}}return {inicio,separador:hr&&salir?{linea:limites(hr),resaltado:(()=>{const s=getComputedStyle(salir),r=salir.getBoundingClientRect(),reserva=parseFloat(s.outlineWidth)+Math.max(0,parseFloat(s.outlineOffset));return s.outlineStyle!=='none'?{izquierda:r.left-reserva,derecha:r.right+reserva,ancho:r.width+2*reserva}:limites(salir.closest('.st-key-cierre_cuenta'))})(),boton:limites(salir),separacion:salir.getBoundingClientRect().top-hr.getBoundingClientRect().bottom,contorno:parseFloat(getComputedStyle(salir).outlineWidth)+Math.max(0,parseFloat(getComputedStyle(salir).outlineOffset)),contenedorComun:hr.closest('.st-key-cierre_cuenta')===salir.closest('.st-key-cierre_cuenta')&&Boolean(hr.closest('.st-key-cierre_cuenta')),independiente:!salir.contains(hr)}:null}})(),
                    medidasInicio:(()=>{const a=document.querySelector('.st-key-navegacion_inicio a');if(!a)return null;const medir=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {tag:e.tagName,testid:e.dataset.testid,clase:e.className,ancho:r.width,alto:r.height,cliente:e.clientHeight,contenido:e.scrollHeight,overflowY:s.overflowY,display:s.display,height:s.height,maxHeight:s.maxHeight,padding:s.padding,lineHeight:s.lineHeight,alignItems:s.alignItems,boxSizing:s.boxSizing,estilo:e.getAttribute('style')}};const padres=[];for(let e=a;e&&!e.classList.contains('st-key-barra_panel');e=e.parentElement)padres.push(medir(e));return {padres,hijos:[...a.querySelectorAll('*')].map(medir)}})(),
                    errores:[...document.querySelectorAll('[data-testid="stException"]')].map(e=>e.innerText),
                    imagenesRotas:[...document.images].filter(e=>e.complete&&!e.naturalWidth).map(e=>e.alt),
                    iconos:[...document.querySelectorAll('[data-testid="stIconMaterial"]')].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility==='visible').map(e=>{const s=getComputedStyle(e),r=document.createRange();r.selectNodeContents(e);return {nombre:e.textContent,fuente:s.fontFamily,cargada:document.fonts.check(s.fontSize+' '+s.fontFamily.split(',')[0],e.textContent),tamano:parseFloat(s.fontSize),anchoGlifo:r.getBoundingClientRect().width,ligaduras:s.fontFeatureSettings}}),
                    tipografia:[...document.querySelectorAll('h1,h2,h3,.upc-eyebrow,.upc-brand-title,.upc-role p,.stButton button p,[data-testid=stTextInput] input')].filter(e=>e.getClientRects().length).map(e=>({elemento:e.tagName,fuente:getComputedStyle(e).fontFamily,tamano:getComputedStyle(e).fontSize,peso:getComputedStyle(e).fontWeight})),
                    selectores:[...document.querySelectorAll('[role=combobox]')].filter(e=>e.getClientRects().length).map(e=>{let a=e;const r=[];for(let i=0;a&&i<5;i++,a=a.parentElement){const s=getComputedStyle(a);r.push({tag:a.tagName,testid:a.dataset.testid,baseweb:a.dataset.baseweb,alto:a.getBoundingClientRect().height,fondo:s.backgroundColor,fuente:s.fontSize})}return r}),
                    selectoresAcademicos:[...document.querySelectorAll('[class*=st-key-selector_academico_] input[role=combobox]')].filter(e=>e.getClientRects().length).map(e=>({alto:e.parentElement.getBoundingClientRect().height,fuente:getComputedStyle(e).fontSize,placeholder:e.placeholder})),
                    crearMateria:(()=>{const b=document.querySelector('.st-key-crear_nueva_materia button');return b?{fondo:getComputedStyle(b).backgroundColor,texto:getComputedStyle(b).color}:null})(),
                    color:getComputedStyle(document.querySelector('[data-testid="stAppViewContainer"]')).backgroundColor,
                    botonesRecortados:[...document.querySelectorAll('.stButton button p')].filter(e=>{if(!e.getClientRects().length||getComputedStyle(e).clipPath!=='none'||getComputedStyle(e).visibility==='hidden')return false;const b=e.closest('button').getBoundingClientRect(),r=document.createRange();r.selectNodeContents(e);return [...r.getClientRects()].some(t=>t.left<b.left-1||t.right>b.right+1||t.top<b.top-1||t.bottom>b.bottom+1)}).map(e=>e.textContent),
                    accesoInstitucionalCompleto:!document.querySelector('.upc-hero')||[...document.querySelectorAll('.st-key-barra_panel button')].some(b=>b.querySelector('p')?.textContent.trim()==='Gestión académica'),
                    marcaInstitucional:[...document.querySelectorAll('.upc-official-logo,.st-key-logo_inicio img')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().height>0).map(e=>({ancho:e.getBoundingClientRect().width,alto:e.getBoundingClientRect().height,originalAncho:e.naturalWidth,originalAlto:e.naturalHeight,filtro:getComputedStyle(e).filter,reserva:parseFloat(getComputedStyle(e.closest('.st-key-logo_inicio')||e.parentElement).paddingLeft)})),
                    accesoADerecha:(()=>{if(!document.querySelector('.upc-hero'))return true;const b=document.querySelector('.st-key-acciones_cabecera');return Boolean(b&&Math.abs(b.getBoundingClientRect().right-document.querySelector('.st-key-barra_panel').getBoundingClientRect().right)<24)})(),
                    navegacionCabecera:(()=>{const visible=e=>e.getBoundingClientRect().height>0&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility==='visible';const controles=[...document.querySelectorAll('.st-key-barra_panel a,.st-key-barra_panel button')].filter(visible);const inicios=controles.filter(e=>e.querySelector('p')?.textContent.trim()==='Inicio');const cuenta=document.querySelector('.st-key-menu_cuenta [data-testid=stPopoverButton]');const rect=inicios[0]?.getBoundingClientRect(),otro=cuenta?.getBoundingClientRect();return {inicioPublico:Boolean(document.querySelector('.upc-hero')),inicios:inicios.length,etiquetaAntigua:controles.some(e=>e.querySelector('p')?.textContent.trim()==='Ir al inicio'),alineados:!rect||!otro||Math.abs(rect.top+rect.height/2-otro.top-otro.height/2)<2,logoEnlace:Boolean(document.querySelector('.st-key-logo_inicio a'))}})(),
                    menuCuenta:(()=>{const e=document.querySelector('[data-testid=stPopoverBody]:has(.st-key-opciones_cuenta)');if(!e)return null;const r=e.getBoundingClientRect();return {ancho:r.width,dentro:r.left>=0&&r.right<=innerWidth,separador:Boolean(e.querySelector('hr')),opciones:[...e.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height>0&&getComputedStyle(b).visibility==='visible').map(b=>({texto:b.querySelector('p')?.textContent,icono:b.querySelector('[data-testid=stIconMaterial]')?.textContent,alto:b.getBoundingClientRect().height,borde:getComputedStyle(b).borderWidth,opacidad:getComputedStyle(b).opacity,color:getComputedStyle(b).color,alineacion:getComputedStyle(b).justifyContent}))}})(),
                    anchoPrincipal:document.querySelector('[data-testid=stMain]').clientWidth,
                    contenidoPrincipal:document.querySelector('[data-testid=stMain]').scrollWidth})""")


def validar_mediciones(dimensiones, etiqueta, *, identidad=False):
    fallos = []
    if dimensiones['contenido'] > dimensiones['ancho'] + 2: fallos.append(etiqueta + ': desbordamiento horizontal')
    if dimensiones['contenidoPrincipal'] > dimensiones['anchoPrincipal'] + 2: fallos.append(etiqueta + ': desbordamiento del panel')
    if dimensiones['botonesRecortados']: fallos.append(etiqueta + ': texto de botón recortado')
    if not dimensiones['accesoInstitucionalCompleto']: fallos.append(etiqueta + ': acceso Gestión académica recortado')
    if identidad and not dimensiones['accesoADerecha']: fallos.append(etiqueta + ': acceso institucional desalineado')
    for logo in dimensiones['marcaInstitucional']:
        if not logo['originalAlto'] or abs(logo['ancho']/logo['alto']-logo['originalAncho']/logo['originalAlto'])>.01:
            fallos.append(etiqueta + ': proporciones del logosímbolo alteradas')
        if logo['filtro']!='none' or logo['reserva']<logo['ancho']/12:
            fallos.append(etiqueta + ': filtro o reserva insuficiente en el logosímbolo')
    if dimensiones['errores'] or dimensiones['imagenesRotas']: fallos.append(etiqueta + ': error de pantalla o recurso')
    for control in dimensiones['selectoresAcademicos']:
        if abs(control['alto']-44)>1 or control['fuente']!='16px' or 'Choose' in control['placeholder']:
            fallos.append(etiqueta + ': selector académico inconsistente')
    if not dimensiones['focoCuentaInstalado']:
        fallos.append(etiqueta + ': falta el complemento vigente de foco de cuenta')
    if not dimensiones['marcaNombreCompleto']:
        fallos.append(etiqueta + ': texto institucional recortado')
    perfil = dimensiones['perfilEstudiante']
    if perfil and (not perfil['ruta'].endswith('/mi-perfil') or not perfil['porcentajeCentrado'] or not perfil['porcentajeSinRecorte'] or perfil['recortes']):
        fallos.append(etiqueta + ': perfil sin centrar o con textos recortados')
    pie = dimensiones['pieAcademico']
    if not pie or pie['cantidad']!=1:
        fallos.append(etiqueta + ': falta un único pie académico compartido')
    elif (abs(pie['izquierda']-pie['inicioDisponible'])>1 or abs(pie['derecha']-pie['finDisponible'])>1 or abs(pie['banda']['ancho']-pie['ancho'])>1 or pie['textosRecortados'] or pie['posicion']=='fixed' or not pie['despuesContenido'] or any('Georgia' not in t['fuente'] or t['estilo']!='italic' or t['peso']!='400' for t in pie['titulos'])):
        fallos.append(etiqueta + ': composición o legibilidad del pie académico incorrecta')
    elif dimensiones['ancho']>1000 and abs(pie['zonas'][0]['ancho']/pie['ancho']-.53)>.01:
        fallos.append(etiqueta + ': proporción del pie diferente de 53/47')
    elif dimensiones['ancho']<=600 and pie['zonas'][1]['y']<=pie['zonas'][0]['y']:
        fallos.append(etiqueta + ': las zonas del pie deben apilarse en móvil')
    geometria = dimensiones['geometriaControles']
    if geometria['inicio'] and (geometria['inicio']['barras'] or not all(geometria['inicio'][k] for k in ('iconoCentrado','textoCentrado','sinRecortes'))):
        fallos.append(etiqueta + ': scroll o desajuste vertical en Inicio')
    separador = geometria['separador']
    if separador and any(abs(separador['linea'][k]-separador['resaltado'][k])>.1 for k in ('izquierda','derecha','ancho')):
        fallos.append(etiqueta + ': separador desalineado con Cerrar sesión')
    if separador and (not separador['contenedorComun'] or not separador['independiente'] or separador['separacion']<=separador['contorno']):
        fallos.append(etiqueta + ': el separador debe estar separado del contorno y compartir contenedor')
    nav = dimensiones['navegacionCabecera']
    if nav['inicios'] != (0 if nav['inicioPublico'] else 1) or nav['etiquetaAntigua'] or not nav['alineados'] or not nav['logoEnlace']:
        fallos.append(etiqueta + ': composición inconsistente del encabezado')
    menu = dimensiones['menuCuenta']
    # Algunos motores serializan flex-start como flow-start; ambos indican el
    # inicio de la fila de este menú. Mantener los demás controles geométricos.
    if menu and (not 200 <= menu['ancho'] <= 240 or not menu['dentro'] or not menu['separador'] or any(not o['icono'] or o['borde']!='0px' or float(o['opacidad'])<1 or o['alineacion'] not in ('flex-start','flow-start') for o in menu['opciones'])):
        fallos.append(etiqueta + ': menú de cuenta inconsistente')
    if dimensiones['crearMateria'] and dimensiones['crearMateria']!={'fondo':'rgb(0, 115, 55)','texto':'rgb(255, 255, 255)'}:
        fallos.append(etiqueta + ': crear materia no tiene contraste primario')
    for icono in dimensiones['iconos']:
        if 'Material' not in icono['fuente']: fallos.append(etiqueta + ': fuente de icono incorrecta')
        if not icono['cargada'] or icono['anchoGlifo'] > icono['tamano']*1.25:
            fallos.append(etiqueta + ': nombre visible en lugar del icono ' + icono['nombre'])
    return fallos
