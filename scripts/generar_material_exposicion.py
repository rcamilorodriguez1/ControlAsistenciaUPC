"""Guía PDF, diccionario independiente y modelo relacional offline de UPC Aula."""
from pathlib import Path
from html import escape
import json
import os
import re
import xml.etree.ElementTree as ET

import markdown
import pymupdf
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Preformatted,KeepTogether

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
FUENTES=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'


def fuentes():
    for nombre,archivo in [('AulaArial','arial.ttf'),('AulaArial-Bold','arialbd.ttf'),('AulaArial-Italic','ariali.ttf')]:
        pdfmetrics.registerFont(TTFont(nombre,str(FUENTES/archivo)))
    pdfmetrics.registerFontFamily('AulaArial',normal='AulaArial',bold='AulaArial-Bold',italic='AulaArial-Italic',boldItalic='AulaArial-Bold')


def interior(elemento):
    valor=ET.tostring(elemento,encoding='unicode')
    valor=re.sub(r'^<[^>]+>|</[^>]+>$','',valor)
    return valor.replace('<code>','<font name="Courier">').replace('</code>','</font>')


def guia_pdf():
    fuentes()
    estilos=getSampleStyleSheet()
    estilos.add(ParagraphStyle(name='AulaCuerpo',fontName='AulaArial',fontSize=10,leading=14,textColor=colors.HexColor('#173D2D'),spaceAfter=8))
    estilos.add(ParagraphStyle(name='AulaTitulo',parent=estilos['AulaCuerpo'],fontName='AulaArial-Bold',fontSize=25,leading=29,spaceAfter=17,keepWithNext=True))
    estilos.add(ParagraphStyle(name='AulaSeccion',parent=estilos['AulaCuerpo'],fontName='AulaArial-Bold',fontSize=16,leading=20,textColor=colors.HexColor('#007337'),spaceBefore=15,spaceAfter=10,keepWithNext=True))
    estilos.add(ParagraphStyle(name='AulaCelda',parent=estilos['AulaCuerpo'],fontSize=8.7,leading=11.7,spaceAfter=0))
    estilos.add(ParagraphStyle(name='AulaCabecera',parent=estilos['AulaCelda'],fontName='AulaArial-Bold'))
    html=markdown.markdown((DOCS/'GUIA_EXPOSICION_BASE_DATOS.md').read_text(encoding='utf-8'),extensions=['tables','fenced_code'])
    raiz=ET.fromstring('<root>'+html+'</root>');flujo=[]
    ancho=A4[0]-100
    for elem in raiz:
        if elem.tag in ('h1','h2','h3'):
            flujo.append(Paragraph(interior(elem),estilos['AulaTitulo' if elem.tag=='h1' else 'AulaSeccion']))
        elif elem.tag=='p':flujo.append(Paragraph(interior(elem),estilos['AulaCuerpo']))
        elif elem.tag in ('ul','ol'):
            for n,li in enumerate(elem.findall('li'),1):
                prefijo=f'{n}. ' if elem.tag=='ol' else '• '
                flujo.append(Paragraph(prefijo+interior(li),estilos['AulaCuerpo']))
        elif elem.tag=='table':
            filas=[]
            for tr in elem.findall('.//tr'):
                filas.append([Paragraph(interior(c),estilos['AulaCabecera' if c.tag=='th' else 'AulaCelda']) for c in tr])
            anchos=[.30,.70] if len(filas[0])==2 else [.24,.38,.38]
            tabla=Table(filas,colWidths=[ancho*v for v in anchos],repeatRows=1,hAlign='LEFT')
            tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8F1E5')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#D6E2D6')),
                ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            flujo.extend([tabla,Spacer(1,10)])
    def pagina(c,doc):
        c.saveState();c.drawImage(str(ROOT/'static/img/upc/logo-horizontal-manual.jpg'),50,A4[1]-80,width=145,height=145*474/1369)
        c.setFont('AulaArial',7);c.setFillColor(colors.HexColor('#53504F'))
        c.drawRightString(A4[0]-50,A4[1]-47,'UPC | Aula · Exposición de Base de Datos')
        c.setStrokeColor(colors.HexColor('#D6E2D6'));c.line(50,39,A4[0]-50,39)
        c.drawString(50,25,'Ingeniería de Sistemas · Proyecto académico')
        c.drawRightString(A4[0]-50,25,f'Página {doc.page}');c.restoreState()
    destino=DOCS/'UPC_Aula_Guia_Exposicion_Base_de_Datos.pdf'
    doc=SimpleDocTemplate(str(destino),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=105,bottomMargin=54,
        title='UPC | Aula — Guía de exposición de Base de Datos',author='Equipo UPC | Aula')
    doc.build(flujo,onFirstPage=pagina,onLaterPages=pagina)
    return destino


def diccionario_pdf():
    original=pymupdf.open(DOCS/'UPC_Aula_Documentacion_Integral.pdf')
    inicio=next(p for nivel,t,p in original.get_toc() if t.startswith('Anexo B'))-1
    destino=pymupdf.open();destino.insert_pdf(original,from_page=inicio)
    indice=[]
    for nivel,t,p in original.get_toc():
        if p>=inicio+1:
            indice.append([max(1,nivel-1),t if nivel>1 else 'Diccionario vigente · Oracle 009',p-inicio])
    destino.set_toc(indice)
    for n,p in enumerate(destino,1):
        r=pymupdf.Rect(p.rect.width-190,p.rect.height-25,p.rect.width-14,p.rect.height-6)
        p.add_redact_annot(r,fill=(1,1,1));p.apply_redactions(images=0)
        p.insert_font(fontname='AulaArial',fontfile=str(FUENTES/'arial.ttf'))
        p.insert_textbox(r,f'Diccionario · página {n} de {len(destino)}',fontsize=7,fontname='AulaArial',align=2,color=(.32,.35,.32))
    destino.set_metadata(dict(title='UPC | Aula — Diccionario de datos 009',author='Equipo UPC | Aula',
        subject='Extracto del anexo B de la memoria 1.2; 14 tablas y 140 columnas de Autonomous 009.'))
    ruta=DOCS/'UPC_Aula_Diccionario_de_Datos_009.pdf';destino.save(ruta,garbage=4,deflate=True)
    destino.close();original.close();return ruta


def modelo_relacional():
    c=json.loads((DOCS/'base_datos/catalogo.json').read_text(encoding='utf-8'))
    tablas={t['nombre']:t for t in c['tablas']}
    w,h=1800,1110
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
       '<rect width="1800" height="1110" fill="white"/>',
       '<style>text{font-family:Arial,sans-serif;fill:#173d2d}.nombre{font-size:21px;font-weight:bold}.campo{font-size:18px}.flecha{fill:none;stroke:#688c75;stroke-width:3}.nueva{stroke:#007337;stroke-width:4}</style>',
       '<text x="40" y="42" font-size="29" font-weight="bold">UPC | Aula · Modelo relacional físico 009</text>',
       '<text x="40" y="77" font-size="18">14 tablas = 8 conectadas por 11 FK + 6 sin FK físicas · el diccionario contiene las 140 columnas</text>',
       '<text x="40" y="100" font-size="18" font-weight="bold">BLOQUE PRINCIPAL · 8 TABLAS CONECTADAS POR FK</text>',
       '<defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#49765e"/></marker></defs>']
    relaciones=[('M175 285 L175 370',False),('M175 520 L175 620',False),
        ('M310 430 C405 430 415 230 500 230',False),
        ('M1440 235 L1390 235 L1390 115 L945 115 L945 230 L920 230',False),
        ('M310 475 C420 475 410 657 500 657',False),
        ('M1450 300 L1380 340 L1020 340 L1020 665 L970 665',False),
        ('M310 706 L500 706',False),('M1600 315 L1600 450',False),
        ('M1180 285 L1180 400 L1350 400 L1350 450',False),
        ('M175 155 L175 108 L1775 108 L1775 570 L1760 570',True),
        ('M310 500 L367 500 L367 820 L1500 820 L1500 715',True)]
    extremos=[(175,370,'abajo'),(175,620,'abajo'),(500,230,'derecha'),(920,230,'izquierda'),
        (500,657,'derecha'),(970,665,'izquierda'),(500,706,'derecha'),(1600,450,'abajo'),
        (1350,450,'abajo'),(1760,570,'izquierda'),(1500,715,'arriba')]
    for (ruta,nueva),(x,y,direccion) in zip(relaciones,extremos):
        s.append(f'<path d="{ruta}" fill="none" stroke="{"#007337" if nueva else "#688c75"}" stroke-width="{4 if nueva else 3}"/>')
        if direccion=='abajo':puntos=f'{x-7},{y-14} {x+7},{y-14} {x},{y}'
        elif direccion=='arriba':puntos=f'{x-7},{y+14} {x+7},{y+14} {x},{y}'
        elif direccion=='derecha':puntos=f'{x-14},{y-7} {x-14},{y+7} {x},{y}'
        else:puntos=f'{x+14},{y-7} {x+14},{y+7} {x},{y}'
        s.append(f'<polygon points="{puntos}" fill="#49765e"/>')
    nodos=[('PROFESORES',40,155,270,130,['profesor_id · PK','usuario · UQ','nombre']),
        ('MATERIAS',40,370,270,150,['materia_id · PK','profesor_id · FK','codigo_materia · UQ','seccion']),
        ('CLASES',40,620,270,180,['clase_id · PK','materia_id · FK','fecha_hora','estado','UNIQUE materia/instante']),
        ('MATERIA_ESTUDIANTES',500,170,420,130,['PK (materia_id, estudiante_id)','materia_id · FK','estudiante_id · FK']),
        ('REGISTROS_ASISTENCIA',500,570,470,215,['asistencia_id · PK','estudiante_id · FK','materia_id · FK','FK (clase_id, materia_id)','UNIQUE (clase_id, estudiante_id)','deteccion · decision · motivo']),
        ('ESTUDIANTES',1440,155,320,160,['estudiante_id · PK','codigo_institucional · UQ','nombre','plantillas biométricas opcionales']),
        ('ADMINISTRADORES',1030,155,300,130,['administrador_id · PK','usuario','nombre']),
        ('VERIFICACION_ESTUDIANTES',1200,450,560,265,['estudiante_id · PK / FK','autorizado_por · FK (administrador)','autorizado_docente_por · FK (009)','materia_autorizacion_id · FK (009)','clave_hash · documento_huella','vigencia · versión · estado','Administrador O docente+materia'])]
    for nombre,x,y,ancho,alto,campos in nodos:
        s += [f'<rect x="{x}" y="{y}" width="{ancho}" height="{alto}" rx="6" fill="#eef5eb" stroke="#70917b" stroke-width="2"/>',
            f'<rect x="{x}" y="{y}" width="{ancho}" height="39" rx="6" fill="#d4e7d1"/>',
            f'<text class="nombre" x="{x+12}" y="{y+27}">{escape(nombre)}</text>']
        for n,campo in enumerate(campos):s.append(f'<text class="campo" x="{x+13}" y="{y+67+n*25}">{escape(campo)}</text>')
    s.append('<text x="40" y="866" font-size="20" font-weight="bold">SOPORTE · 6 TABLAS DEL MISMO MODELO SIN FK FÍSICAS</text>')
    independientes=[n for n in tablas if n not in {t[0] for t in nodos}]
    for i,nombre in enumerate(independientes):
        x=40+i*293
        s.append(f'<rect x="{x}" y="895" width="277" height="94" rx="5" fill="#f3f6ef" stroke="#d4e1d3"/>')
        s.append(f'<text x="{x+10}" y="923" font-size="17" font-weight="bold">{escape(nombre)}</text>')
        campos=tablas[nombre]['columnas'][:2]
        for j,columna in enumerate(campos):s.append(f'<text x="{x+10}" y="{948+j*23}" font-size="15">{escape(columna["nombre"].lower())}</text>')
    s.extend(['<text x="40" y="1019" font-size="17">Estas seis también forman parte de las 14 tablas. Sin FK no significa sin clave primaria ni sin referencias lógicas.</text>',
        '<text x="40" y="1045" font-size="18">Flecha: padre → tabla que contiene la FK. Verificación: como máximo una fila por alumno.</text>',
        '<text x="40" y="1064" font-size="18">Verde intenso: relaciones añadidas en 009. La aprobación activa exige administrador o docente con materia, con exclusión mutua.</text>',
        '<text x="40" y="1093" font-size="16">Fuente: catálogo de metadatos de Autonomous 009 · sin filas de personas ni credenciales.</text></svg>'])
    contenido='\n'.join(s).replace('class="nombre"','font-size="21" font-weight="bold"').replace('class="campo"','font-size="18"')
    contenido=contenido.replace('<text ','<text font-family="Arial" fill="#173d2d" ')
    ruta=DOCS/'base_datos/modelo_relacional_009.svg';ruta.write_text(contenido,encoding='utf-8')
    svg=pymupdf.open(stream=ruta.read_bytes(),filetype='svg');original=pymupdf.open('pdf',svg.convert_to_pdf())
    pdf=pymupdf.open();pagina=pdf.new_page(width=1190.55,height=841.89)
    pagina.show_pdf_page(pagina.rect,original,0)
    pdf.set_metadata(dict(title='UPC | Aula — Modelo relacional 009',author='Equipo UPC | Aula',subject='14 tablas y 11 FK físicas; campos guía.'))
    pdf.save(DOCS/'base_datos/modelo_relacional_009.pdf',garbage=4,deflate=True)
    pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(DOCS/'base_datos/modelo_relacional_009.png')
    lineas=['erDiagram']
    for t in c['tablas']:
        for r in t['restricciones']:
            if r['tipo']=='R':
                relacion='||--o|' if r['nombre']=='FK_VERIFICACION_EST' else '|o--o{' if t['nombre']=='VERIFICACION_ESTUDIANTES' else '||--o{'
                lineas.append(f'    {r["referencia"]} {relacion} {t["nombre"]} : {r["nombre"]}')
    for t in c['tablas']:
        lineas += [f'    {t["nombre"]} {{']
        for col in t['columnas']:
            claves=[{'P':'PK','R':'FK','U':'UK'}[r['tipo']] for r in t['restricciones'] if r['tipo'] in 'PRU' and col['nombre'] in r['columnas']]
            lineas.append('        '+re.sub(r'[^A-Z0-9_]','_',col['tipo'])+' '+col['nombre']+(' '+','.join(dict.fromkeys(claves)) if claves else ''))
        lineas += ['    }']
    (DOCS/'base_datos/modelo_relacional_009.mmd').write_text('\n'.join(lineas)+'\n',encoding='utf-8')


def main():
    destinos=[guia_pdf(),diccionario_pdf()];modelo_relacional()
    print('Generados: guía PDF, diccionario PDF y modelo relacional SVG/PDF/PNG/Mermaid.')
    for p in destinos:
        with pymupdf.open(p) as d:print(p.name,len(d),'páginas')


if __name__=='__main__':main()
