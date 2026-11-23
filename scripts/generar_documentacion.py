"""Genera la memoria académica; dependencias opcionales en docs/requirements-documentacion.txt."""
from __future__ import annotations

import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.request
import uuid
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
import markdown
import pymupdf
from websockets.sync.client import connect

DOCS = ROOT / 'docs'
OUT = DOCS / 'UPC_Aula_Documentacion_Integral.pdf'
HTML = DOCS / 'UPC_Aula_Documentacion_Integral.html'
WORK = ROOT / '.local/memoria_pdf'
WORK.mkdir(parents=True, exist_ok=True)
REPO = 'https://github.com/rcamilorodriguez1/ControlAsistenciaUPC/blob/main/'
EDICION = '1.2'
FECHA_EDICION = '22 de noviembre de 2026'


def slug(value: str, sep: str = '-') -> str:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', sep, value).strip(sep)


def data_asset(path: str, mime: str) -> str:
    return f'data:{mime};base64,' + base64.b64encode((ROOT / path).read_bytes()).decode()


def box(x, y, w, h, title, subtitle='', dark=False):
    fill, ink = ('#007337', '#ffffff') if dark else ('#f2f6f3', '#123e2b')
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#b8ccc0"/>'
            f'<text x="{x+w/2}" y="{y+h/2-3 if subtitle else y+h/2+6}" text-anchor="middle" '
            f'font-size="18" font-weight="bold" fill="{ink}">{html.escape(title)}</text>'
            + (f'<text x="{x+w/2}" y="{y+h/2+20}" text-anchor="middle" font-size="13" fill="{ink}">{html.escape(subtitle)}</text>' if subtitle else ''))


def svg_start(w, h, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}" style="font-family:Arial,sans-serif">
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#49765e"/></marker></defs>'''


def path(d):
    return f'<path d="{d}" fill="none" stroke="#49765e" stroke-width="2" marker-end="url(#arrow)"/>'


def figure(svg, caption, css=''):
    return f'<figure class="diagram {css}">{svg}<figcaption>{caption}</figcaption></figure>'


def architecture():
    svg = svg_start(720, 308, 'Capas de la arquitectura UPC Aula')
    for y, title, sub in [
        (10, 'Portales · docente / estudiante / administración', 'Navegador HTTPS · interfaz y navegación compartidas'),
        (86, 'Servicios y control de identidad', 'Sesión · permisos · revisión · validación de muestras'),
        (162, 'Persistencia y transacciones', 'Repositorios Python · pool python-oracledb · contexto de auditoría'),
        (238, 'Oracle · esquema 001–009', '14 tablas · 140 columnas · 11 FK · 8 paquetes · 10 triggers')]:
        svg += box(10, y, 700, 60, title, sub, y == 238)
        if y < 238:
            svg += path(f'M360,{y+60} L360,{y+76}')
    svg += '</svg>'
    return figure(svg, 'Figura 1. Capas y responsabilidades. El servidor valida identidad y permisos antes de operar en Oracle.', 'architecture')


def flow():
    svg = svg_start(720, 334, 'Flujo de revisión y confirmación de una clase')
    nodes = [(10, 10, '1 · Abrir clase', 'Materia y fecha/hora'),
             (390, 10, '2 · Analizar muestras', 'Propuesta de detección'),
             (390, 116, '3 · Revisar decisiones', 'Motivo ante cambio o falta de muestra'),
             (10, 116, '4 · Validar en servidor', 'Propiedad, matrícula y estados'),
             (10, 222, '5 · Confirmar en Oracle', 'Una transacción; reintento idempotente'),
             (390, 222, '6 · Consultar / corregir', 'Resultado e historial auditable')]
    for x, y, title, sub in nodes:
        svg += box(x, y, 320, 78, title, sub, title.startswith('5'))
    for d in ['M330,49 L390,49', 'M550,88 L550,116', 'M390,155 L330,155', 'M170,194 L170,222', 'M330,261 L390,261']:
        svg += path(d)
    return figure(svg + '</svg>', 'Figura 2. La biometría propone; la confirmación persiste la decisión revisada. Un análisis fallido no genera ausencias.')


def cloud():
    svg = svg_start(720, 312, 'Arquitectura elegida: Render y Oracle Autonomous')
    for y, title, sub in [
        (8, 'Navegador · otros equipos y dispositivos', 'Dominio público · HTTPS / WebSocket'),
        (86, 'Render · Docker / Streamlit', 'Aplicación completa · HTTPS / WebSocket · secretos separados'),
        (164, 'Aplicación Python', 'Servicios · modelos CPU · pool Oracle / TCPS'),
        (242, 'Autonomous UPCAula · esquema 001–009', 'TLS / ACL · propietario, runtime y cuenta técnica restringida')]:
        svg += box(10, y, 700, 62, title, sub, y == 242)
        if y < 242:
            svg += path(f'M360,{y+62} L360,{y+78}')
    return figure(svg + '</svg>', 'Figura 5. Render aloja la aplicación y Autonomous conserva los datos. La comprobación del último despliegue y de la página corresponde al usuario.', 'architecture')


def er():
    svg = svg_start(930, 610, 'Once claves foráneas físicas del esquema Oracle 009')
    # Todas las flechas parten del padre hacia la tabla que contiene la FK.
    for d in ['M130,98 L130,195', 'M240,224 L355,224',
              'M800,98 L800,133 L465,133 L465,195',
              'M130,267 L130,390', 'M240,246 L285,246 L285,410 L355,410',
              'M690,62 L640,62 L640,443 L575,443',
              'M240,439 L355,439', 'M800,98 L800,195', 'M800,390 L800,267',
              'M240,62 L315,62 L315,167 L725,167 L725,195',
              'M240,247 C570,320 600,245 690,245']:
        svg += path(d)
    nodes = [(20, 26, 'Profesores', 'PROFESORES'), (20, 195, 'Materias', 'MATERIAS'),
             (20, 390, 'Clases', 'CLASES'), (690, 26, 'Estudiantes', 'ESTUDIANTES'),
             (355, 195, 'Matrículas', 'MATERIA_ESTUDIANTES'),
             (355, 390, 'Resultados', 'REGISTROS_ASISTENCIA'),
             (690, 195, 'Verificación', 'VERIFICACION_ESTUDIANTES'),
             (690, 390, 'Administradores', 'ADMINISTRADORES')]
    for x, y, title, sub in nodes:
        svg += box(x, y, 220, 72, title, sub, title == 'Resultados')
    svg += '''<text x="20" y="510" font-size="17" fill="#123e2b">Flecha: tabla padre → tabla con FK. Cada flecha representa una restricción física.</text>
    <text x="20" y="537" font-size="15" fill="#4c6055">Verificación: aprobador administrativo o docente con materia, con exclusión mutua.</text>
    <text x="20" y="562" font-size="15" fill="#4c6055">Clases → Resultados utiliza la FK compuesta (clase_id, materia_id).</text>
    <text x="20" y="587" font-size="15" fill="#4c6055">Historias, eventos, límites, sesiones y versiones conservan referencias sin FK según el caso.</text></svg>'''
    return figure(svg, 'Figura 3. Once FK entre ocho tablas. 009 añade profesor y materia de autorización; las seis tablas restantes no añaden FK. El anexo B contiene las columnas y restricciones vigentes.')


def screenshot():
    svg = svg_start(720, 240, 'Diferencia entre portal, perfil y configuración')
    for x, titulo, lineas in [
        (5, 'Portal', ['Operaciones del rol', 'Materias y matrícula', 'Asistencia y excepciones']),
        (245, 'Perfil', ['Identidad y actividad', 'Historial del estudiante', 'Agenda del docente']),
        (485, 'Configuración', ['Cuenta del docente', 'Archivo con motivo', 'Conservación del historial'])]:
        svg += box(x, 12, 230, 58, titulo, '', titulo == 'Perfil')
        for n, texto in enumerate(lineas):
            svg += f'<text x="{x+12}" y="{108+n*38}" font-size="14" fill="#304f3b">{html.escape(texto)}</text>'
    return figure(svg+'</svg>', 'Figura 4. Organización funcional actual. Diagrama explicativo, sin capturas de personas ni ensayo de la página.')


def render_md(value, prefix):
    converter = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'sane_lists'],
                                 extension_configs={'toc': {'slugify': lambda text, sep: prefix + slug(text)}})
    result = converter.convert(value)
    return result, converter.toc_tokens


def rewrite_links(value, db_ids):
    def replace(match):
        url = html.unescape(match.group(1))
        if url.startswith('#'):
            key = slug(url[1:])
            return f'href="#{db_ids.get(key, "db-"+key)}"'
        if re.match(r'https?://|mailto:', url):
            return match.group(0)
        if 'BASE_DE_DATOS.md' in url:
            return 'href="#anexo-a"'
        if 'DICCIONARIO_DATOS.md' in url:
            return 'href="#anexo-b"'
        if url.startswith('../'):
            target = url[3:]
        else:
            target = 'docs/' + url
        if '.local/' in target or 'exports/' in target:
            return 'data-local-reference="true"'
        return f'href="{html.escape(REPO+target, quote=True)}"'
    return re.sub(r'href="([^"]+)"', replace, value)


def split_sections(value):
    # Las secciones se paginan por tema; títulos y sus tablas se mantienen relacionados.
    pieces = re.split(r'(?=<h2\b)', value)
    return pieces[0], pieces[1:]


def make_html():
    main = (DOCS / 'INFORME_PROYECTO.md').read_text(encoding='utf-8')
    main = re.sub(r'^# .*\n.*?\n(?=## 1\.)', '', main, count=1, flags=re.S)
    for marker, content in [('ARQUITECTURA', architecture()), ('FLUJO', flow()), ('MODELO', er()), ('PORTADA', screenshot()), ('CLOUD', cloud())]:
        main = main.replace(f'<!-- FIGURA_{marker} -->', content)
    main_html, main_toc = render_md(main, 'cap-')
    db = (DOCS / 'BASE_DE_DATOS.md').read_text(encoding='utf-8')
    db = db.split('## 13. Diccionario vigente')[0]
    db = db.replace('## Fuentes y alcance de la revisión', '### Fuentes y alcance de la revisión')
    db = re.sub(r'^# .*\n', '', db, count=1)
    db = re.sub(r'^## Índice\s*\n.*?(?=^## 1\.)', '', db, count=1, flags=re.S | re.M)
    db = re.sub(r'```mermaid\n.*?```', er().replace('Figura 3.', 'Figura A.1.'), db, flags=re.S)
    # Los nombres y números originales se conservan dentro de su anexo.
    db_html, db_toc = render_md(db, 'db-')
    diccionario = (DOCS / 'DICCIONARIO_DATOS.md').read_text(encoding='utf-8')
    diccionario = re.sub(r'^# .*\n', '', diccionario, count=1)
    dic_html, dic_toc = render_md(diccionario, 'dic-')
    db_ids = {slug(item['name']): item['id'] for item in db_toc}
    main_html, db_html, dic_html = [rewrite_links(value, db_ids) for value in [main_html, db_html, dic_html]]
    _, main_sections = split_sections(main_html)
    intro, db_sections = split_sections(db_html)
    content = ''
    for part in main_sections:
        compact = ' compact' if re.match(r'<h2[^>]*>(1|2|5|9|12)\.', part) else ''
        if re.match(r'<h2[^>]*>12\.', part):
            compact += ' roadmap'
        if re.match(r'<h2[^>]*>5\.', part):
            part = re.sub(r'(<h3[^>]*>5\.2 .*?</ul>)', r'<div class="keep">\1</div>', part, flags=re.S)
        content += f'<section class="chapter{compact}">{part}</section>'
    content += '<section class="appendix-cover" id="anexo-a"><p class="eyebrow">ANEXO A · REFERENCIA TÉCNICA</p><h1>Base de datos<br>y programación PL/SQL.</h1><p class="lead">Funcionamiento, relaciones, reglas y consultas del esquema Oracle 009.</p><div class="rule"></div>' + intro + '<div class="key-facts"><div><b>14</b><span>tablas</span></div><div><b>11</b><span>claves foráneas</span></div><div><b>10</b><span>disparadores</span></div><div><b>8</b><span>paquetes PL/SQL</span></div></div><p class="small">Fuente funcional: docs/BASE_DE_DATOS.md. Metadatos vigentes: catálogo de Autonomous del 22/11/2026. El diccionario completo aparece en el anexo B.</p></section>'
    for part in db_sections:
        wide = bool(re.match(r'<h2[^>]*>1[34]\.', part))
        # Las tablas extensas de seis columnas se presentan en páginas A4 apaisadas.
        part = re.sub(r'(<h3[^>]*>(?:Inventario verificado|Identidades)</h3>.*?</table>)', r'<div class="keep">\1</div>', part, flags=re.S)
        compact = ' compact' if re.match(r'<h2[^>]*>5\.', part) else ''
        if re.match(r'<h2[^>]*>4\.', part):
            part = re.sub(r'(<h3[^>]*>4\.13 .*?$)', r'<div class="keep">\1</div>', part, flags=re.S)
        content += f'<section class="chapter appendix {"landscape" if wide else ""}{compact}">{part}</section>'
    dic_intro, dic_sections = split_sections(dic_html)
    content += '<section class="appendix-cover" id="anexo-b"><p class="eyebrow">ANEXO B · DICCIONARIO VIGENTE</p><h1>140 columnas.<br>Una referencia verificable.</h1><p class="lead">Tipos, nulabilidad, identidades, valores predeterminados, claves y restricciones de las 14 tablas.</p><div class="rule"></div>' + dic_intro + '<p class="small">La procedencia de los tipos y restricciones es Oracle Autonomous 009. Las descripciones funcionales se mantienen en la plantilla del proyecto.</p></section>'
    for part in dic_sections:
        def distribuir_tabla(match):
            tabla = match.group(0)
            columnas = len(re.findall(r'<th(?:\s[^>]*)?>', tabla.split('</thead>')[0]))
            anchos = [22, 17, 9, 8, 7, 13, 24] if columnas == 7 else [23, 62, 15]
            grupo = '<colgroup>' + ''.join(f'<col style="width:{ancho}%">' for ancho in anchos) + '</colgroup>'
            return tabla.replace('<table>', '<table>'+grupo, 1)
        part = re.sub(r'<table>.*?</table>', distribuir_tabla, part, flags=re.S)
        content += f'<section class="chapter appendix landscape dictionary">{part}</section>'
    toc_main = ''.join(f'<li><a href="#{item["id"]}"><span>{html.escape(item["name"])}</span><span class="toc-page" data-target="{item["id"]}"></span></a></li>' for item in main_toc)
    toc_db = ''.join(f'<li><a href="#{item["id"]}"><span>{html.escape(item["name"])}</span><span class="toc-page" data-target="{item["id"]}"></span></a></li>' for item in db_toc)
    toc_dic = ''.join(f'<li><a href="#{item["id"]}"><span>{html.escape(item["name"])}</span><span class="toc-page" data-target="{item["id"]}"></span></a></li>' for item in dic_toc)
    logo = data_asset('static/img/upc/logo-horizontal-manual.jpg', 'image/jpeg')
    return '''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>UPC | Aula — Documentación integral del proyecto</title><meta name="description" content="Memoria académica y técnica de UPC Aula. Edición 1.2, 22 de noviembre de 2026."><style>
    @page {size:A4; margin:20mm 18mm 20mm 20mm;}
    @page landscape {size:A4 landscape; margin:20mm 18mm 20mm 20mm;}
    *{box-sizing:border-box;} html{font-size:10.3pt;} body{margin:0;color:#263b30;background:white;font-family:Arial,Helvetica,sans-serif;line-height:1.43;}
    p{margin:0 0 2.8mm;orphans:3;widows:3;} strong{color:#143e29;} em{font-style:italic;}
    a{color:#006631;text-decoration:none;overflow-wrap:anywhere;} a:hover{text-decoration:underline;}
    h1,h2,h3,h4{color:#16432e;line-height:1.19;break-after:avoid-page;}
    h1{font-size:32pt;margin:0 0 7mm;letter-spacing:-.6pt;}
    h2{font-size:22pt;font-weight:700;margin:0 0 7mm;padding:0 0 4mm;border-bottom:1.2pt solid #007337;letter-spacing:-.4pt;}
    h3{font-size:12.5pt;margin:5mm 0 2.8mm;} h4{font-size:11pt;margin:5mm 0 2.5mm;}
    ul,ol{margin:2mm 0 4mm;padding-left:6mm;} li{margin:0 0 1.8mm;orphans:2;widows:2;}
    table{width:100%;border-collapse:collapse;margin:4mm 0 6mm;table-layout:auto;font-size:8.7pt;line-height:1.4;}
    thead{display:table-header-group;} th{text-align:left;background:#e9f0eb;color:#16432e;font-weight:700;border-top:1px solid #a5bfaf;border-bottom:1px solid #a5bfaf;}
    th,td{padding:2.1mm 2.3mm;vertical-align:top;overflow-wrap:anywhere;}
    td{border-bottom:1px solid #dbe4de;} tr{break-inside:avoid-page;} tbody tr:nth-child(even){background:#f7f9f7;}
    code{font-family:Consolas,'Courier New',monospace;font-size:.89em;overflow-wrap:anywhere;}
    pre{margin:3mm 0 5mm;padding:3.8mm;background:#f2f5f2;border-left:2pt solid #88aa95;white-space:pre-wrap;overflow-wrap:anywhere;word-break:normal;break-inside:avoid-page;font-size:8.1pt;line-height:1.4;color:#233d2e;}
    pre code{font-size:1em;} blockquote{border-left:2pt solid #007337;margin:4mm 0;padding:1mm 0 1mm 4mm;color:#476052;}
    figure{margin:5mm 0 7mm;break-inside:avoid-page;} figure svg,figure img{display:block;width:100%;height:auto;}
    figcaption{font-size:8.2pt;line-height:1.4;margin-top:3mm;color:#52675a;}
    .diagram{padding:3mm 0;} .architecture{padding:0;margin:4mm 0;} .architecture svg{max-height:60mm;} .screenshot img{border:1px solid #dbe4de;max-height:80mm;object-fit:contain;}
    .chapter{break-before:page;} .compact{font-size:10pt;line-height:1.35;} .compact p{margin-bottom:2.4mm;} .compact h3{margin-top:4mm;margin-bottom:2.2mm;} .compact table{font-size:8.6pt;} .compact th,.compact td{padding:1.8mm 2.3mm;}
    .roadmap{font-size:9.8pt;line-height:1.32;} .roadmap table{font-size:8.4pt;line-height:1.32;} .roadmap th,.roadmap td{padding:1.4mm 2.3mm;} .keep{break-inside:avoid-page;}
    .landscape{page:landscape;} .landscape table{font-size:8.7pt;}
    .landscape th,.landscape td{padding:2.2mm 2.5mm;}
    .landscape table th:first-child{min-width:37mm;}
    .landscape table th:nth-child(2){min-width:30mm;}
    .dictionary table{font-size:8.3pt;line-height:1.35;table-layout:fixed;}
    .dictionary th,.dictionary td{padding:1.8mm 2mm;}
    .dictionary table:first-of-type th:last-child{min-width:58mm;}
    .dictionary h2{font-size:20pt;}
    .cover{break-after:page;min-height:250mm;position:relative;display:flex;flex-direction:column;}
    .cover-logo{width:78mm;height:auto;margin:0 0 12mm;}
    .eyebrow{font-size:9pt;letter-spacing:1.25pt;font-weight:700;color:#007337;margin:0 0 6mm;}
    .cover h1{font-size:42pt;font-weight:700;line-height:1.06;letter-spacing:-1.2pt;margin-bottom:5mm;}
    .cover .subtitle{font-size:23pt;line-height:1.2;color:#16432e;margin:0 0 7mm;max-width:145mm;}
    .cover .lead,.appendix-cover .lead{font-size:12pt;line-height:1.6;color:#53685a;max-width:150mm;}
    .rule{width:25mm;height:1.4mm;background:#007337;margin:8mm 0;}
    .cover-bottom{margin-top:auto;padding-top:12mm;}
    .meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm 9mm;border-top:1px solid #baccc0;padding-top:6mm;font-size:9.5pt;}
    .meta-grid span{display:block;color:#637768;font-size:8pt;letter-spacing:.7pt;text-transform:uppercase;margin-bottom:1.5mm;}
    .motto{font-family:Arial,Helvetica,sans-serif;font-style:italic;font-size:13pt;color:#3f6b4b;margin:7mm 0 0;}
    .small{font-size:8.5pt;color:#5b6e60;line-height:1.5;}
    .toc{break-before:page;break-after:page;} .toc h2{margin-bottom:4mm;}
    .toc h3{font-size:10.5pt;margin-top:5mm;}
    .toc ol{list-style:none;padding:0;margin:0;} .toc li{margin:0;border-bottom:1px solid #e2e9e3;font-size:9.3pt;break-inside:avoid;}
    .toc a{display:flex;justify-content:space-between;gap:5mm;padding:1.8mm 0;color:#244b34;} .toc-page{min-width:9mm;text-align:right;color:#5d7565;font-variant-numeric:tabular-nums;}
    .appendix-cover{break-before:page;min-height:230mm;} .appendix-cover h1{margin-top:13mm;}
    .key-facts{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #b8ccc0;border-bottom:1px solid #b8ccc0;padding:6mm 0;margin:12mm 0 7mm;}
    .key-facts b{display:block;font-size:25pt;color:#007337;} .key-facts span{font-size:8.5pt;color:#5a6e60;}
    @media screen{body{max-width:1000px;margin:36px auto;padding:30px;box-shadow:0 0 0 1px #dbe4de;} .chapter{margin-top:70px;} .toc{margin-top:55px;} .landscape{max-width:none;}}
    @media print{.cover{height:250mm;}.toc{min-height:210mm;} a{color:#1a5935;}}
    </style></head><body>''' + f'''
    <section class="cover"><img class="cover-logo" src="{logo}" alt="Logotipo oficial Universidad Popular del Cesar">
    <p class="eyebrow">PROYECTO ACADÉMICO · DOCUMENTACIÓN INTEGRAL</p><h1>UPC | Aula</h1>
    <p class="subtitle">Gestión y seguimiento<br>académico.</p><div class="rule"></div>
    <p class="lead">Planteamiento, objetivos, arquitectura, flujos funcionales y referencia de la base de datos.</p>
    <div class="cover-bottom"><div class="meta-grid"><div><span>Universidad</span>Universidad Popular del Cesar</div><div><span>Contexto académico</span>Ingeniería de Sistemas · Base de Datos</div><div><span>Edición documental</span>1.2 · 22 de noviembre de 2026</div><div><span>Estado técnico de referencia</span>Oracle · versiones 001–009</div><div><span>Equipo</span>Rafael Camilo Rodriguez Ayala<br>Harold Steven Torres Diaz<br>Oscar William Rivero Ordoñez</div><div><span>Docente</span>Amilkat Sierra Romano</div></div>
    <p class="motto">Educación y Futuro</p><p class="small" style="margin-top:5mm">Memoria del proyecto en desarrollo. Los estados implementado, verificado y aceptado se documentan por separado. Sin credenciales ni registros personales.</p></div></section>
    <section class="toc"><p class="eyebrow">GUÍA DE LECTURA</p><h2>Contenido</h2><p>Memoria principal</p><ol>{toc_main}<li><a href="#anexo-a"><span>Anexo A · Base de datos y PL/SQL</span><span class="toc-page" data-target="anexo-a"></span></a></li><li><a href="#anexo-b"><span>Anexo B · Diccionario vigente</span><span class="toc-page" data-target="anexo-b"></span></a></li></ol><p class="small">La evidencia técnica y la aceptación del usuario se distinguen en toda la memoria.</p></section>
    <section class="toc"><p class="eyebrow">REFERENCIA DEL ESQUEMA</p><h2>Contenido del anexo A</h2><ol>{toc_db}</ol><p class="small" style="margin-top:6mm">Reglas, relaciones físicas, ocho paquetes y consultas de estudio.</p></section>
    <section class="toc"><p class="eyebrow">DICCIONARIO VIGENTE</p><h2>Contenido del anexo B</h2><ol>{toc_dic}</ol><p class="small" style="margin-top:6mm">Tablas A4 apaisadas. Metadatos de Autonomous 009; no contiene registros de personas.</p></section>
    {content}</body></html>'''


class CDP:
    def __init__(self, ws):
        self.ws, self.seq = ws, 0
    def call(self, method, params=None):
        self.seq += 1
        self.ws.send(json.dumps({'id': self.seq, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv(timeout=60))
            if msg.get('id') == self.seq:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})


def inspect_pdf(path):
    doc = pymupdf.open(path)
    pages = []
    failures = []
    toc_targets = {}
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({'pagina': i+1, 'ancho': round(page.rect.width), 'alto': round(page.rect.height), 'caracteres': len(text), 'imagenes': len(page.get_images())})
        if len(text.strip()) < 60:
            failures.append(f'Pagina casi vacia: {i+1}')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < 15 or y0 < 4 or x1 > page.rect.width-12 or y1 > page.rect.height-4:
                        failures.append(f'Texto fuera de margenes: {i+1}: {span["text"][:65]}')
        # El índice usa enlaces reales del PDF para resolver el destino de página.
        if i in (1, 2):
            for link in page.get_links():
                if link.get('page', -1) >= 0:
                    toc_targets[(i, round(link['from'].y0, 1))] = link['page'] + 1
    all_text = '\n'.join(p.get_text() for p in doc)
    for token in ['Planteamiento del programa', 'Objetivos', 'Q42.', 'TRG_ASISTENCIA_AUD', 'VERIFICACION_ESTUDIANTES', 'AUTORIZADO_DOCENTE_POR']:
        if token not in all_text:
            failures.append('Contenido no encontrado: ' + token)
    for token in ['C:\\Users\\', 'file:///', 'BEGIN PRIVATE KEY', 'BEGIN RSA PRIVATE KEY', 'BEGIN CERTIFICATE']:
        if token in all_text:
            failures.append('Contenido privado o ruta local: ' + token)
    return doc, {'paginas': len(doc), 'bytes': path.stat().st_size, 'paginas_detalle': pages, 'errores': failures, 'enlaces': sum(len(p.get_links()) for p in doc), 'marcadores': len(doc.get_toc())}


def main():
    parser = argparse.ArgumentParser(description='Genera el HTML y PDF desde las fuentes documentales; no conecta con Oracle.')
    parser.add_argument('--navegador', help='Ruta a un navegador Chromium, Chrome, Brave o Edge para impresión headless.')
    args = parser.parse_args()
    candidates = [args.navegador, os.environ.get('AULA_NAVEGADOR_PDF')]
    candidates += [shutil.which(name) for name in ['chromium', 'chromium-browser', 'google-chrome', 'brave-browser', 'msedge']]
    for variable, relatives in [
        ('PROGRAMFILES', ['BraveSoftware/Brave-Browser/Application/brave.exe', 'Google/Chrome/Application/chrome.exe', 'Microsoft/Edge/Application/msedge.exe']),
        ('PROGRAMFILES(X86)', ['Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe']),
        ('LOCALAPPDATA', ['BraveSoftware/Brave-Browser/Application/brave.exe', 'Google/Chrome/Application/chrome.exe'])]:
        base = os.environ.get(variable)
        if base:
            candidates += [str(Path(base) / relative) for relative in relatives]
    browser = next((Path(candidate) for candidate in candidates if candidate and Path(candidate).is_file()), None)
    if browser is None:
        parser.error('No se encontró Chromium. Usa --navegador con la ruta a su ejecutable.')
    HTML.write_text(make_html(), encoding='utf-8')
    profile = WORK / ('perfil_' + uuid.uuid4().hex[:10])
    process = subprocess.Popen([str(browser), '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--disable-extensions', '--remote-debugging-port=0', f'--user-data-dir={profile}', 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        deadline = time.monotonic()+35
        while not (profile / 'DevToolsActivePort').exists():
            if time.monotonic() > deadline:
                raise RuntimeError('No se pudo abrir navegador para maquetar')
            time.sleep(.2)
        port = (profile / 'DevToolsActivePort').read_text().splitlines()[0]
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list') as response:
            targets = json.load(response)
        target = next(t for t in targets if t['type'] == 'page')
        with connect(target['webSocketDebuggerUrl'], max_size=70_000_000, proxy=None) as ws:
            cdp = CDP(ws)
            cdp.call('Page.enable')
            cdp.call('Page.navigate', {'url': HTML.as_uri()})
            for _ in range(100):
                result = cdp.call('Runtime.evaluate', {'expression': 'document.readyState === "complete" && Array.from(document.images).every(i=>i.complete)', 'returnByValue': True})
                if result.get('result', {}).get('value'):
                    break
                time.sleep(.1)
            cdp.call('Runtime.evaluate', {'expression':'document.fonts.ready.then(()=>true)', 'awaitPromise':True})
            cdp.call('Emulation.setEmulatedMedia', {'media':'print'})
            header = '<div style="font-family:Arial;font-size:8px;width:100%;margin:0 18mm 0 20mm;display:flex;justify-content:space-between;color:#65776b;border-bottom:1px solid #dbe4de;padding-bottom:5px"><span>UPC | AULA · DOCUMENTACIÓN INTEGRAL</span><span>EDICIÓN 1.2 · NOVIEMBRE 2026</span></div>'
            footer = '<div style="font-family:Arial;font-size:8px;width:100%;margin:0 18mm 0 20mm;display:flex;justify-content:space-between;color:#65776b;border-top:1px solid #dbe4de;padding-top:5px"><span>Universidad Popular del Cesar · Proyecto académico</span><span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span></div>'
            settings = {'printBackground':True, 'preferCSSPageSize':True, 'displayHeaderFooter':True, 'headerTemplate':header, 'footerTemplate':footer, 'generateTaggedPDF':True, 'generateDocumentOutline':True}
            result = cdp.call('Page.printToPDF', settings)
            OUT.write_bytes(base64.b64decode(result['data']))
            # Leer destinos de los enlaces para numerar el índice sin estimar alturas.
            doc = pymupdf.open(OUT)
            numbers = []
            comienzo = next(pagina for nivel, titulo, pagina in doc.get_toc()
                            if re.match(r'^1\.\s+Resumen ejecutivo', titulo)) - 1
            for page_index in range(1, comienzo):
                links = [x for x in doc[page_index].get_links() if x.get('page', -1) >= 0]
                links.sort(key=lambda x: (round(x['from'].y0), x['from'].x0))
                for link in links:
                    # La portada del anexo tiene enlace aparte sin columna numérica.
                    numbers.append(link['page']+1)
            doc.close()
            nmain = len(re.findall(r'<span class="toc-page" data-target="cap-', HTML.read_text(encoding='utf-8')))
            ndb = len(re.findall(r'<span class="toc-page" data-target="db-', HTML.read_text(encoding='utf-8')))
            ndic = len(re.findall(r'<span class="toc-page" data-target="dic-', HTML.read_text(encoding='utf-8')))
            if len(numbers) != nmain + ndb + ndic + 2:
                raise RuntimeError('No se pudieron resolver todos los destinos del índice.')
            if numbers:
                js = 'Array.from(document.querySelectorAll(".toc-page")).forEach((el,i)=>{el.textContent='+json.dumps(numbers)+'[i]})'
                cdp.call('Runtime.evaluate', {'expression':js})
                rendered = cdp.call('Runtime.evaluate', {'expression':'document.documentElement.outerHTML','returnByValue':True})['result']['value']
                HTML.write_text('<!doctype html>\n'+rendered, encoding='utf-8')
                OUT.write_bytes(base64.b64decode(cdp.call('Page.printToPDF', settings)['data']))
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
    doc, report = inspect_pdf(OUT)
    outline = [[1, 'Portada · UPC | Aula', 1]]
    appendix = False
    for level, title, page in doc.get_toc():
        if title.strip() == 'UPC | Aula':
            continue
        if title.startswith('Contenido'):
            outline.append([1, title, page])
            continue
        if level == 1:
            appendix = True
            nombre = 'Anexo B · Diccionario vigente' if title.startswith('140 columnas') else 'Anexo A · Base de datos y programación PL/SQL'
            outline.append([1, nombre, page])
        else:
            outline.append([level if appendix else level-1, title, page])
    doc.set_toc(outline)
    report['marcadores'] = len(outline)
    doc.set_metadata({'title':'UPC | Aula — Documentación integral del proyecto', 'author':'Rafael Camilo Rodriguez Ayala; Harold Steven Torres Diaz; Oscar William Rivero Ordoñez', 'subject':'Memoria académica y técnica. Edición 1.2. Oracle 001–009, Render, perfiles y excepciones docentes.', 'keywords':'UPC, Aula, Oracle, PL/SQL, arquitectura, asistencia, documentación, Docker, Autonomous', 'creator':'UPC | Aula — plantilla editorial institucional', 'producer':'Chromium / PyMuPDF'})
    doc.saveIncr()
    report['bytes'] = OUT.stat().st_size
    # Muestras de lectura: portada, índice, arquitectura, consultas y tablas apaisadas.
    samples = {0, 1, 2}
    for i, page in enumerate(doc):
        txt = page.get_text()
        if any(key in txt for key in ['5. Arquitectura y organización', 'Q01. Esquema', '140 columnas.', 'AUTORIZADO_DOCENTE_POR']):
            samples.add(i)
    for i in sorted(samples):
        doc[i].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(WORK/f'pagina_{i+1:03}.png')
    (WORK/'validacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'paginas_detalle'}, ensure_ascii=False))
    doc.close()
    if report['errores']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
