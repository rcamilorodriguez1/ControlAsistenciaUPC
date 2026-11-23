"""Presentación comercial editable y PDF, con la identidad UPC y datos del proyecto."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'
WORK = ROOT/'.local/presentacion'
W, H = 960, 540
VERDE, BOSQUE, MENTA = '#007337', '#073D2B', '#CDE6CB'
TINTA, GRIS, PAPEL, LINEA = '#173D2D', '#53504F', '#F4F7F1', '#D6E2D6'
BLANCO = '#FFFFFF'
FONT = 'UPCArial'


def rgb(valor):
    return RGBColor.from_string(valor.lstrip('#'))


class Presentacion:
    """Todos los objetos del PPTX son editables; el PDF usa las mismas coordenadas."""
    def __init__(self, fuentes, *, salida=DOCS, nombre='UPC_Aula_Presentacion_Comercial',
                 titulo='UPC | Aula — Presentación comercial', trabajo=WORK):
        for variante, archivo in [('', 'arial.ttf'), ('Bold', 'arialbd.ttf'), ('Italic', 'ariali.ttf')]:
            pdfmetrics.registerFont(TTFont(FONT+variante, str(fuentes/archivo)))
        self.salida, self.nombre, self.trabajo = Path(salida), nombre, Path(trabajo)
        self.salida.mkdir(parents=True, exist_ok=True)
        self.trabajo.mkdir(parents=True, exist_ok=True)
        self.ppt = Presentation()
        self.ppt.slide_width, self.ppt.slide_height = Pt(W), Pt(H)
        self.ppt.core_properties.title = titulo
        self.ppt.core_properties.subject = 'Propuesta de piloto y desarrollo comercial. Proyecto académico, edición 1.2.'
        self.ppt.core_properties.author = 'Rafael Camilo Rodriguez Ayala; Harold Steven Torres Diaz; Oscar William Rivero Ordoñez'
        self.ppt.core_properties.last_modified_by = 'Equipo UPC | Aula'
        self.ppt.core_properties.language = 'es-CO'
        self.ppt.core_properties.created = datetime.now(timezone.utc)
        self.ppt.core_properties.modified = datetime.now(timezone.utc)
        self.pdf = canvas.Canvas(str(self.salida/(self.nombre+'.pdf')), pagesize=(W,H), pageCompression=1)
        self.pdf.setTitle(self.ppt.core_properties.title)
        self.pdf.setAuthor(self.ppt.core_properties.author)
        self.pdf.setSubject(self.ppt.core_properties.subject)
        self.registro, self.textos, self.notas = [], [], []
        self.num = 0

    def rect(self, x,y,w,h, color, borde=None, radio=0):
        s = self.slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radio else MSO_SHAPE.RECTANGLE,
                                        Pt(x),Pt(y),Pt(w),Pt(h))
        if radio:
            s.adjustments[0] = .06
        s.fill.solid(); s.fill.fore_color.rgb = rgb(color)
        if borde:
            s.line.color.rgb = rgb(borde); s.line.width = Pt(.7)
        else:
            s.line.fill.background()
        self.pdf.setFillColor(HexColor(color))
        self.pdf.setStrokeColor(HexColor(borde or color)); self.pdf.setLineWidth(.7)
        if radio:
            self.pdf.roundRect(x,H-y-h,w,h,radio,stroke=int(bool(borde)),fill=1)
        else:
            self.pdf.rect(x,H-y-h,w,h,stroke=int(bool(borde)),fill=1)
        return s

    def line(self,x1,y1,x2,y2,color=LINEA,grosor=1):
        from pptx.enum.shapes import MSO_CONNECTOR
        s=self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Pt(x1),Pt(y1),Pt(x2),Pt(y2))
        s.line.color.rgb=rgb(color);s.line.width=Pt(grosor)
        self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(grosor)
        self.pdf.line(x1,H-y1,x2,H-y2)

    def circle(self,x,y,d,color,borde=None):
        s=self.slide.shapes.add_shape(MSO_SHAPE.OVAL,Pt(x),Pt(y),Pt(d),Pt(d))
        s.fill.solid();s.fill.fore_color.rgb=rgb(color)
        if borde:s.line.color.rgb=rgb(borde)
        else:s.line.fill.background()
        self.pdf.setFillColor(HexColor(color));self.pdf.setStrokeColor(HexColor(borde or color))
        self.pdf.circle(x+d/2,H-y-d/2,d/2,fill=1,stroke=int(bool(borde)))

    def text(self,x,y,w,h,valor,tamano=18,color=TINTA,bold=False,italic=False,align='left',interlineado=None):
        font=FONT+('Bold' if bold else 'Italic' if italic else '')
        leading=interlineado or tamano*1.22
        lineas=[]
        for parrafo in str(valor).split('\n'):
            fila=''
            for palabra in parrafo.split():
                candidato=(fila+' '+palabra).strip()
                if fila and pdfmetrics.stringWidth(candidato,font,tamano)>w-3:
                    lineas.append(fila);fila=palabra
                else:fila=candidato
            lineas.append(fila)
        if len(lineas)*leading>h+1:
            raise ValueError(f'Diapositiva {self.num}: texto excede caja: {valor[:80]} ({len(lineas)*leading:.1f}>{h})')
        for fila in lineas:
            if pdfmetrics.stringWidth(fila,font,tamano)>w+1:
                raise ValueError(f'Diapositiva {self.num}: palabra excede ancho: {fila}')
        box=self.slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(h))
        tf=box.text_frame;tf.clear();tf.word_wrap=False;tf.vertical_anchor=MSO_ANCHOR.TOP
        tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        for n,fila in enumerate(lineas):
            p=tf.paragraphs[0] if n==0 else tf.add_paragraph()
            p.text=fila;p.line_spacing=Pt(leading);p.space_after=Pt(0);p.space_before=Pt(0)
            p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
            p.font.name='Arial';p.font.size=Pt(tamano);p.font.bold=bold;p.font.italic=italic;p.font.color.rgb=rgb(color)
            self.pdf.setFont(font,tamano);self.pdf.setFillColor(HexColor(color))
            baseline=H-y-n*leading-pdfmetrics.getAscent(font,tamano)
            ancho=pdfmetrics.stringWidth(fila,font,tamano)
            inicio=x+(w-ancho)/2 if align=='center' else x+w-ancho if align=='right' else x
            self.pdf.drawString(inicio,baseline,fila)
        self.textos.append(dict(slide=self.num,texto=str(valor),x=x,y=y,w=w,h=h,tamano=tamano,lineas=len(lineas)))
        return box

    def logo(self, oscuro=False):
        # Manual pp. 23–26 y 94: original, reserva y posición superior izquierda.
        if oscuro:self.rect(35,20,225,81,BLANCO,radio=2)
        imagen=ROOT/'static/img/upc/logo-horizontal-manual.jpg'
        x,y,w,h=50,33,190,190*474/1369
        self.slide.shapes.add_picture(str(imagen),Pt(x),Pt(y),Pt(w),Pt(h))
        self.pdf.drawImage(str(imagen),x,H-y-h,width=w,height=h)

    def new(self,titulo,etiqueta,fuente='',oscuro=False,notas=''):
        if self.num:self.pdf.showPage()
        self.num+=1
        self.pdf.bookmarkPage(f'diapositiva-{self.num}')
        self.pdf.addOutlineEntry((titulo or 'Cada clase cuenta.').replace('\n',' '),f'diapositiva-{self.num}',level=0)
        self.slide=self.ppt.slides.add_slide(self.ppt.slide_layouts[6])
        self.dark=oscuro
        self.rect(0,0,W,H,BOSQUE if oscuro else BLANCO)
        self.logo(oscuro)
        self.text(695,43,215,18,'UPC | Aula',13,MENTA if oscuro else VERDE,bold=True,align='right')
        self.line(50,112,910,112,'#416853' if oscuro else LINEA)
        self.text(50,133,860,18,etiqueta.upper(),10,MENTA if oscuro else VERDE,bold=True)
        if titulo:self.text(50,164,860,92,titulo,32,BLANCO if oscuro else TINTA,bold=True,interlineado=36)
        self.line(50,501,910,501,'#416853' if oscuro else LINEA)
        self.text(50,511,790,14,'Proyecto académico · 22/11/2026'+(' · '+fuente if fuente else ''),9,'#C7DCCF' if oscuro else GRIS)
        self.text(870,509,40,17,f'{self.num:02}',11,MENTA if oscuro else VERDE,align='right')
        self.slide.notes_slide.notes_text_frame.text=notas
        self.notas.append(dict(numero=self.num,titulo=titulo or 'Cada clase cuenta.',notas=notas,fuente=fuente))

    def pill(self,x,y,w,valor,oscuro=False):
        self.rect(x,y,w,26,'#275B43' if oscuro else '#E8F1E5',radio=3)
        self.text(x+10,y+6,w-20,15,valor,10,BLANCO if oscuro else VERDE,bold=True)

    def card(self,x,y,w,h,titulo,cuerpo,numero=None,dark=False):
        self.rect(x,y,w,h,BOSQUE if dark else PAPEL,radio=6)
        if numero:
            self.text(x+18,y+16,w-36,28,str(numero),18,MENTA if dark else VERDE,bold=True)
        top=y+(55 if numero else 20)
        self.text(x+18,top,w-36,62,titulo,21,BLANCO if dark else TINTA,bold=True)
        self.text(x+18,top+70,w-36,h-(top-y)-80,cuerpo,15,'#DCEADD' if dark else GRIS)

    def finish(self):
        self.pdf.save()
        self.ppt.save(self.salida/(self.nombre+'.pptx'))
        errores=[]
        for n,s in enumerate(self.ppt.slides,1):
            for shape in s.shapes:
                if shape.left<0 or shape.top<0 or shape.left+shape.width>self.ppt.slide_width+Pt(1) or shape.top+shape.height>self.ppt.slide_height+Pt(1):
                    errores.append(f'Objeto fuera de la diapositiva {n}')
        reporte=dict(diapositivas=self.num,formato='16:9',fuente='Arial',paleta_principal=VERDE,
            logosimbolo='Imagen original del manual, proporción conservada',objetos_fuera_de_limites=errores,
            datos_financieros_inventados=False,textos=self.textos)
        (self.trabajo/'validacion.json').write_text(json.dumps(reporte,ensure_ascii=False,indent=2),encoding='utf-8')
        (self.trabajo/'notas.json').write_text(json.dumps(self.notas,ensure_ascii=False,indent=2),encoding='utf-8')
        if errores:raise ValueError(errores)
        print(json.dumps({k:v for k,v in reporte.items() if k!='textos'},ensure_ascii=False))


def generar(fuentes):
    d=Presentacion(fuentes)
    d.new('', 'Presentación de producto y propuesta de piloto', 'Manual UPC / estado del proyecto', True,
        'Abrir con la visión: una clase deja información útil cuando se puede relacionar con su materia, su decisión de asistencia y su historia. Presentar UPC Aula como proyecto académico del equipo, listo para conversar sobre un piloto; la identidad UPC no implica aprobación comercial oficial.')
    d.text(50,188,610,148,'Cada clase\ncuenta.',58,BLANCO,bold=True,interlineado=64)
    d.text(53,347,555,72,'Seguimiento académico con IA, revisión humana y trazabilidad.',23,MENTA)
    d.pill(53,443,255,'PRODUCTO · EVIDENCIA · POTENCIAL',True)
    for x,y,t in [(702,206,'Clase'),(766,294,'Revisión'),(674,382,'Historia')]:
        d.line(x+48,y+26,790,324,'#4B7E5B',2)
        d.rect(x,y,140,52,'#1A543B',radio=5);d.text(x+12,y+17,116,22,t,16,BLANCO,bold=True)

    d.new('Una asistencia aislada\nno explica la clase.','01 · El problema','INFORME_PROYECTO · planteamiento',notas=
        'El problema no es solo marcar un nombre. Se necesita saber a qué sesión corresponde, cómo se decidió y qué cambió después. Son necesidades derivadas del proyecto, todavía sin un estudio estadístico institucional. No atribuir cifras de tiempo perdido o de abandono.')
    for x,t,c,n in [(50,'Contexto','¿A qué materia y horario pertenece el registro?','01'),(343,'Decisión','¿Qué propuso la IA y qué confirmó el docente?','02'),(636,'Historia','¿Quién corrigió el dato y por qué?','03')]:
        d.card(x,270,274,204,t,c,n)

    d.new('Una cadena completa,\ndesde el horario hasta la historia.','02 · La solución','CLASES_Y_REVISION / estados',notas=
        'Explicar el recorrido completo. Abrir una clase crea o recupera el horario; no inicia por sí solo una presencia. La propuesta facial o de voz se revisa antes de confirmar. El historial conserva la intervención posterior y su responsable.')
    pasos=[('01','Programar'),('02','Analizar'),('03','Revisar'),('04','Confirmar'),('05','Consultar')]
    for i,(n,t) in enumerate(pasos):
        x=50+i*174;d.rect(x,290,160,105,BOSQUE if i==3 else PAPEL,radio=5)
        d.text(x+15,306,130,27,n,18,MENTA if i==3 else VERDE,bold=True)
        d.text(x+15,347,130,30,t,18,BLANCO if i==3 else TINTA,bold=True)
        if i<4:d.line(x+161,342,x+172,342,VERDE,2)
    d.text(50,432,860,42,'Una confirmación por clase. Una decisión trazable por estudiante.',21,VERDE,bold=True)

    d.new('Tres roles.\nUna experiencia conectada.','03 · Valor por participante','GOODWILL / perfiles',notas=
        'Vincular capacidades con necesidades. El docente opera y revisa; el estudiante consulta e ingresa con una identidad validada; la gestión dispone de trazabilidad. Son capacidades implementadas, mientras su impacto real deberá medirse en el piloto.')
    for x,t,c,n in [(50,'Docente','Materias, agenda, asistencia y excepciones de sus alumnos.','01'),(343,'Estudiante','Matrículas, historial y calendario de asistencia propios.','02'),(636,'Gestión','Cuentas, consultas y auditoría para revisar cambios.','03')]:
        d.card(x,270,274,210,t,c,n,dark=x==50)

    d.new('La IA propone.\nEl docente decide.','04 · Control humano','ESTADOS_DETECCION / CLASES_Y_REVISION',notas=
        'La detección no es una certeza de presencia. Se distinguen coincidencia, ausencia propuesta y falta de muestra. Un fallo técnico no permite confirmar una lista. La corrección de una propuesta requiere motivo y el sistema conserva el valor original.')
    d.rect(50,274,400,153,PAPEL,radio=6);d.text(70,293,360,30,'Propuesta del análisis',21,bold=True)
    for n,t in enumerate(['Coincidencia detectada','Sin muestra utilizable','Análisis fallido']):
        d.circle(72,338+n*24,8,VERDE if n==0 else '#8CA892');d.text(90,334+n*24,320,24,t,16)
    d.line(465,350,490,350,VERDE,2)
    d.rect(510,274,400,153,BOSQUE,radio=6);d.text(530,293,360,30,'Decisión revisada',21,BLANCO,bold=True)
    d.text(530,339,360,78,'Resolver pendientes\nConfirmar con contexto\nConservar el motivo del cambio',16,MENTA,interlineado=25)
    d.text(50,452,860,25,'El resultado original y la decisión final permanecen relacionados.',17,GRIS)

    d.new('Operar y comprender\ntienen espacios propios.','05 · Producto','PERFIL_DOCENTE / PERFIL_ESTUDIANTE',notas=
        'Diferenciar portal y perfil. El portal concentra operaciones; el perfil presenta actividad y agenda. La configuración contiene acciones de archivo. El dibujo del calendario es conceptual y no procede de una prueba de la página ni de datos personales.')
    d.card(50,270,400,207,'Portal de operaciones','Tomar asistencia\nGestionar materias\nRevisar registros\nAutorizar excepciones')
    d.rect(475,270,435,207,PAPEL,radio=5);d.text(495,290,390,28,'Perfil · agenda docente',21,bold=True)
    import calendar
    semanas=calendar.Calendar().monthdayscalendar(2026,11)
    for i,dia in enumerate(['L','M','M','J','V','S','D']):d.text(500+i*54,332,39,16,dia,10,GRIS,align='center')
    for fila,semana in enumerate(semanas[-3:]):
        for col,dia in enumerate(semana):
            x,y=499+col*54,356+fila*31
            if dia:
                d.rect(x,y,39,26,VERDE if dia==25 else '#E2EBDE',radio=2)
                d.text(x,y+5,39,17,str(dia),12,BLANCO if dia==25 else TINTA,align='center')
    d.text(495,457,390,16,'Esquema funcional · calendario ilustrativo',10,GRIS)

    d.new('Una alternativa de acceso\ncon autorización y vencimiento.','06 · Continuidad','EXCEPCIONES_BIOMETRICAS · 009',notas=
        'La excepción permite entrar al portal, no marcar asistencia. El docente elige a un alumno matriculado en su materia, comprueba el documento y autoriza una clave con vigencia. La entrega es manual. Las autorizaciones ajenas no se pueden sustituir desde otra cuenta docente.')
    for i,(t,c) in enumerate([('Matrícula','Alumno de una materia propia.'),('Identidad','Documento comprobado.'),('Autorización','Clave y vigencia acordadas.'),('Control','Renovación o revocación.')]):
        x=50+i*219;d.rect(x,282,203,177,PAPEL,radio=5)
        d.text(x+16,300,171,38,f'0{i+1}',24,VERDE,bold=True)
        d.text(x+16,345,171,31,t,18,bold=True)
        d.text(x+16,387,171,58,c,14,GRIS)

    d.new('Render opera.\nOracle conserva.','07 · Arquitectura','CONEXION_BASE_DATOS / cuenta de ejecución',notas=
        'Explicar que el navegador no recibe credenciales Oracle. Toda la aplicación se aloja en Render y Oracle Autonomous conserva los datos. Vercel está descartado. Los servicios validan la sesión y utilizan la cuenta ordinaria o los paquetes restringidos según la operación.')
    for y,t,c,dark in [(271,'Navegador','Portal docente · estudiante · gestión',False),(333,'Render · Streamlit / Python','Servicios · sesión · modelos CPU · pools',True),(395,'Oracle Autonomous · 009','TCPS / TLS · tablas · paquetes · auditoría',False)]:
        d.rect(50,y,860,52,BOSQUE if dark else PAPEL,radio=4)
        d.text(67,y+14,340,28,t,20,BLANCO if dark else TINTA,bold=True)
        d.text(422,y+18,465,23,c,14,MENTA if dark else GRIS)
    d.text(50,463,860,22,'Runtime: 53 permisos. Conexión técnica restringida: cinco EXECUTE.',15,VERDE,bold=True)

    d.new('Una base diseñada\npara explicar cada decisión.','08 · Fundamento técnico','DICCIONARIO_DATOS · Autonomous 009',notas=
        'Estas cifras describen estructura, no usuarios, ingresos ni precisión. El diccionario corresponde a Autonomous 009, con columnas, claves y restricciones. La cuenta propietaria mantiene privilegios superiores y la auditoría no se declara inmutable frente a un DBA.')
    for i,(n,t) in enumerate([('14','tablas'),('140','columnas'),('11','relaciones físicas'),('11','vistas'),('8','paquetes PL/SQL'),('10','triggers')]):
        x=50+(i%3)*293;y=272+(i//3)*104
        d.rect(x,y,274,91,PAPEL,radio=5);d.text(x+18,y+14,105,57,n,39,VERDE,bold=True)
        d.text(x+126,y+28,134,42,t,16,TINTA)

    d.new('Una base verificable\npara la siguiente conversación.','09 · Evidencia','CAMBIOS · ejecución técnica 22/11/2026',oscuro=True,notas=
        'Se ejecutaron 293 pruebas: 288 aprobadas y cinco omitidas por falta del perfil temporal limitado. Dentro de ellas están las pruebas reales de Oracle y de permisos. No convertir esta cifra en porcentaje de precisión biométrica, tasa de asistencia ni garantía de rendimiento en Render.')
    d.text(50,263,460,128,'288',104,MENTA,bold=True)
    d.text(57,396,420,42,'pruebas aprobadas',27,BLANCO,bold=True)
    for y,n,t in [(282,'293','pruebas ejecutadas'),(369,'5','omitidas por configuración')]:
        d.text(575,y,113,62,n,40,MENTA,bold=True);d.text(702,y+10,205,52,t,18,BLANCO)
    d.text(57,459,800,21,'Verificación de software; evaluación biométrica real pendiente.',15,MENTA)

    d.new('Del prototipo\na un piloto medido.','10 · Estado de madurez','ROADMAP / evidencia de despliegue',notas=
        'La evidencia Live corresponde a 20ed6be y las funciones posteriores se publicaron después. El usuario realiza la comprobación del último despliegue y las pruebas de la página. Se ha comunicado una experiencia informal satisfactoria; no hay un piloto institucional medido ni clientes o ingresos declarados.')
    d.line(93,303,860,303,LINEA,3)
    hitos=[('Estructura','Oracle 009\nverificado'),('Aplicación','Despliegue web\ncon evidencia Live'),('Controles','Perfiles y excepción\nimplementados'),('Piloto','Recorrido real\npor acordar')]
    for i,(t,c) in enumerate(hitos):
        x=50+i*219;d.circle(x+18,284,38,VERDE if i<3 else '#DAE4D5')
        d.text(x+18,295,38,20,str(i+1),14,BLANCO if i<3 else TINTA,align='center',bold=True)
        d.text(x,344,200,35,t,20,bold=True);d.text(x,393,200,67,c,16,GRIS)

    d.new('Empezar donde el proceso\npuede medirse.','11 · Entrada al mercado','Propuesta comercial por validar',notas=
        'Proponer una entrada acotada: grupo, programa y eventualmente institución. No se aportó un estudio de mercado ni un TAM, por lo que no se presentan cifras comerciales como hechos. Primero se deben entrevistar responsables, entender restricciones y comprobar el beneficio en un piloto.')
    for i,(t,c) in enumerate([('Un grupo','Validar operación y aceptación.'),('Un programa','Repetir el proceso con varios docentes.'),('Una institución','Acordar gobierno, soporte y alcance.')]):
        d.card(50+i*293,275,274,198,t,c,f'0{i+1}',dark=i==0)

    d.new('Una hipótesis comercial\nsencilla y comprobable.','12 · Modelo de negocio','Propuesta; sin precios o ingresos validados',notas=
        'La hipótesis es acompañar un piloto, aprender de la implementación y después explorar una licencia institucional con soporte. No hay precios, contratación ni recurrencia comercial confirmados. El comprador, la disposición de pago y los costos se deben validar con la institución.')
    for i,(t,c) in enumerate([('Piloto acotado','Alcance y criterios de aceptación.'),('Implementación','Configuración, formación y acompañamiento.'),('Licencia institucional','Servicio y soporte según el uso acordado.')]):
        d.card(50+i*293,275,274,198,t,c)

    d.new('Medir la unidad económica\nantes de escalar.','13 · Disciplina de inversión','GOODWILL · indicadores propuestos',notas=
        'El costo por clase confirmada es una métrica propuesta, no un valor calculado. Recoger costos reales de cómputo, almacenamiento, soporte y operación y dividirlos por el volumen de clases confirmadas. Complementar con tiempo docente, latencia y consumo de memoria; no prometer un margen sin esos datos.')
    d.rect(50,270,860,108,BOSQUE,radio=6)
    d.text(70,288,820,31,'Costo operativo por clase confirmada',25,BLANCO,bold=True)
    d.text(70,335,820,28,'(cómputo + almacenamiento + soporte) / clases confirmadas',20,MENTA)
    for i,(t,c) in enumerate([('Tiempo','Comparar con el proceso manual.'),('Recursos','Medir RAM, CPU y latencia.'),('Adopción','Observar uso y aceptación real.')]):
        x=50+i*293;d.text(x,405,274,29,t,20,VERDE,bold=True);d.text(x,443,260,42,c,15,GRIS)

    d.new('Cinco capacidades\nque integramos en un proceso.','14 · Diferenciación de producto','Capacidades implementadas del proyecto',notas=
        'Presentar la integración propia, sin afirmar que los competidores carecen de estas capacidades. El valor está en reunir contexto de clase, revisión humana, historia, continuidad y reglas transaccionales. Su ventaja comercial y facilidad de adopción requieren contrastarse en el mercado.')
    items=[('Contexto','Cada resultado pertenece a una clase.'),('Revisión','La detección y la decisión se distinguen.'),('Historia','Actor, motivo y cambios conservados.'),('Continuidad','Excepción de acceso con vigencia.'),('Integridad','Transacciones y reglas en Oracle.')]
    for i,(t,c) in enumerate(items):
        y=267+i*43;d.text(52,y,180,28,t,19,VERDE,bold=True);d.text(245,y+2,655,28,c,17,GRIS)
        d.line(50,y+35,910,y+35,LINEA,.7)

    d.new('Crecer por evidencias.','15 · Roadmap comercial','Propuesta de siguientes hitos',notas=
        'El roadmap de producto está organizado en ramas, pero la adopción comercial necesita puertas de decisión: que el recorrido sea aceptado, que se midan los recursos y que haya un marco de uso y soporte. Los hitos no tienen fechas ni inversiones comprometidas.')
    for i,(t,c) in enumerate([('Validar uso','Pruebas del usuario.\nEscenarios y aceptación.'),('Medir operación','Latencia y recursos.\nCosto por clase.'),('Preparar adopción','Consentimiento y retención.\nSoporte y propuesta comercial.')]):
        d.card(50+i*293,270,274,207,t,c,f'0{i+1}')

    d.new('La siguiente prueba\nes una clase real.','16 · Propuesta de piloto','Alcance propuesto, sujeto a acuerdo',True,notas=
        'Cerrar con una petición concreta y proporcionada: una institución que acuerde un piloto pequeño, acompañamiento académico y recursos de operación. El ejemplo de un docente, un grupo y cuatro sesiones es una propuesta para conversar, no un acuerdo ya cerrado. Definir participantes, consentimiento, criterios y responsables antes de comenzar.')
    d.pill(53,270,180,'1 DOCENTE',True);d.pill(248,270,180,'1 GRUPO',True);d.pill(443,270,180,'4 SESIONES',True)
    d.text(53,327,840,72,'Buscamos una institución piloto y acompañamiento para medir el valor.',26,BLANCO,bold=True)
    for i,t in enumerate(['Uso y aceptación','Rendimiento y costos','Trazabilidad del proceso']):
        d.rect(53+i*285,414,269,54,'#1C543B',radio=4);d.text(66+i*285,431,243,24,t,16,MENTA,bold=True)

    d.new('Un proyecto con origen académico\ny ambición de producto.','17 · Equipo','Ingeniería de Sistemas · Base de Datos',notas=
        'Reconocer a los tres integrantes y al docente de referencia académica. La Universidad es la referencia de identidad y contexto formativo; el equipo no declara por ello propiedad institucional, representación comercial ni aprobación oficial. La asignación de derechos y responsabilidades comerciales se debe acordar en una etapa posterior.')
    for i,nombre in enumerate(['Rafael Camilo\nRodriguez Ayala','Harold Steven\nTorres Diaz','Oscar William\nRivero Ordoñez']):
        x=50+i*293;d.rect(x,274,274,111,PAPEL,radio=5);d.text(x+18,299,238,64,nombre,22,bold=True)
    d.text(50,411,860,31,'Amilkat Sierra Romano · Referencia docente',20,VERDE,bold=True)
    d.text(50,459,860,23,'Educación y Futuro',18,GRIS,italic=True)

    d.new('Hechos, hipótesis\ny validación pendiente.','Anexo · Lectura de la evidencia','Estado al 22/11/2026',notas=
        'Este anexo permite responder preguntas de diligencia. La estructura y las pruebas son hechos documentados. Beneficios, precio y expansión son hipótesis. El reconocimiento físico, la operación final y el marco institucional requieren validación. No confundir una verificación automatizada con un resultado comercial.')
    for i,(t,c) in enumerate([('Documentado','Oracle 009.\nPerfiles y excepciones.\n288 pruebas aprobadas.'),('Por validar','Ahorro de tiempo.\nDisposición de pago.\nModelo de licencia.'),('Con el usuario','Página y biometría.\nRecursos en Render.\nAceptación del piloto.')]):
        d.card(50+i*293,270,274,207,t,c)

    d.new('Una identidad reconocible.\nUna historia que puede comprobarse.','Anexo · Fuentes y contacto del proyecto','Documentación editable del repositorio',notas=
        'Los recursos de marca proceden del Manual de Identidad Visual UPC 2010. La evidencia funcional y técnica está en los documentos indicados. Los enlaces llevan al repositorio y la web; la disponibilidad y versión del último despliegue corresponden a la comprobación del usuario. Esta presentación es de producto y piloto, no una oferta de valores.')
    for i,t in enumerate(['Manual UPC · reserva, tipografía y color: pp. 23–26, 34, 38–39 y 94.',
        'CAMBIOS y ROADMAP · funcionalidades, evidencia y pendientes.',
        'DICCIONARIO_DATOS · metadatos de Autonomous 009.',
        'GOODWILL · valor, beneficios esperados e indicadores.']):
        d.circle(52,272+i*37,7,VERDE);d.text(72,267+i*37,832,29,t,16,GRIS)
    for y,etiqueta,url in [(432,'github.com/rcamilorodriguez1/ControlAsistenciaUPC','https://github.com/rcamilorodriguez1/ControlAsistenciaUPC'),
                            (462,'controlasistenciaupc.onrender.com','https://controlasistenciaupc.onrender.com')]:
        cuadro=d.text(50,y,860,23,etiqueta,16,VERDE,bold=True)
        cuadro.click_action.hyperlink.address=url
        d.pdf.linkURL(url,(50,H-y-23,910,H-y),relative=0,thickness=0)
    d.finish()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fuentes',type=Path,default=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',
        help='Directorio con arial.ttf, arialbd.ttf y ariali.ttf.')
    args=parser.parse_args()
    generar(args.fuentes)


if __name__=='__main__':main()
