"""Libro ilustrado de Oracle 011: lectura sencilla, diccionario completo y ejemplos ficticios."""
from datetime import datetime
from html import escape
from pathlib import Path
import argparse
import json
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,
    PageBreak,Table,TableStyle,Flowable,KeepTogether,CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
ANCHO,ALTO=A4
W=ANCHO-96
VERDE='#007337';BOSQUE='#073D2B';TINTA='#183C2D';GRIS='#526057';MENTA='#E8F2E5';LINEA='#D5E1D2'


def registrar_fuentes():
    fuentes=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    for nombre,archivo in [('Aula','arial.ttf'),('AulaB','arialbd.ttf'),('AulaI','ariali.ttf')]:
        pdfmetrics.registerFont(TTFont(nombre,str(fuentes/archivo)))
    pdfmetrics.registerFontFamily('Aula',normal='Aula',bold='AulaB',italic='AulaI',boldItalic='AulaB')


def estilo(nombre,tamano=10.5,leading=15,**kwargs):
    atributos=dict(fontName='Aula',fontSize=tamano,leading=leading,textColor=colors.HexColor(TINTA),
                   spaceAfter=8,splitLongWords=True)
    atributos.update(kwargs)
    return ParagraphStyle(nombre,**atributos)


EST={}


def texto(valor):
    s=escape(str(valor))
    s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`([^`]+)`',r'<font name="AulaB">\1</font>',s)
    return s.replace('\n','<br/>')


def p(valor,tipo='cuerpo'):
    return Paragraph(texto(valor),EST[tipo])


def tabla(cabecera,filas,anchos=None):
    anchos=anchos or [1/len(cabecera)]*len(cabecera)
    datos=[[p(x,'cabecera') for x in cabecera]]+[[p(x,'celda') for x in f] for f in filas]
    t=Table(datos,colWidths=[W*x for x in anchos],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(MENTA)),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor(LINEA)),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t


def caja(titulo,contenido):
    t=Table([[p(titulo,'caja_titulo')],[p(contenido,'caja')]],colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(MENTA)),
        ('BOX',(0,0),(-1,-1),.6,colors.HexColor(LINEA)),('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,0),10),
        ('BOTTOMPADDING',(0,-1),(-1,-1),9)]))
    return KeepTogether([Spacer(1,7),t,Spacer(1,10)])


def codigo(valor):
    t=Table([[Paragraph(escape(valor).replace(' ','&#160;').replace('\n','<br/>'),EST['codigo'])]],colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F3F5F0')),
        ('BOX',(0,0),(-1,-1),.5,colors.HexColor(LINEA)),('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    return KeepTogether([t,Spacer(1,9)])


class Grafico(Flowable):
    def __init__(self,tipo):
        Flowable.__init__(self);self.tipo=tipo;self.width=W
        self.height={'tabla':155,'conexion':230,'matricula':160,'nucleo':215,'inventario':250,
                     'clase':150,'transaccion':175,'documento':175,'historial':155,'capas':120}[tipo]

    def draw(self):
        c=self.canv
        def box(x,y,w,h,t,sub='',oscuro=False):
            c.setFillColor(colors.HexColor(BOSQUE if oscuro else MENTA));c.setStrokeColor(colors.HexColor(LINEA))
            c.roundRect(x,y,w,h,6,fill=1,stroke=1)
            titulo=Paragraph(texto(t),EST['grafico_blanco' if oscuro else 'grafico'])
            tw,th=titulo.wrap(w-16,h-12);titulo.drawOn(c,x+8,y+h-th-8)
            if sub:
                subt=Paragraph(texto(sub),EST['grafico_sub_blanco' if oscuro else 'grafico_sub'])
                _,sh=subt.wrap(w-16,h-26);subt.drawOn(c,x+8,y+7)
        def flecha(x1,y1,x2,y2):
            import math
            c.setStrokeColor(colors.HexColor(VERDE));c.setLineWidth(1.5);c.line(x1,y1,x2,y2)
            a=math.atan2(y2-y1,x2-x1);l=6
            ruta=c.beginPath();ruta.moveTo(x2,y2)
            ruta.lineTo(x2-l*math.cos(a-.45),y2-l*math.sin(a-.45))
            ruta.lineTo(x2-l*math.cos(a+.45),y2-l*math.sin(a+.45));ruta.close()
            c.setFillColor(colors.HexColor(VERDE));c.drawPath(ruta,fill=1,stroke=0)
        def nota(x,y,t):
            c.setFont('Aula',8.7);c.setFillColor(colors.HexColor(GRIS));c.drawString(x,y,t)
        tipo=self.tipo
        if tipo=='tabla':
            x=0;y=40;cw=[65,130,90]
            for i,(titulo,ancho) in enumerate(zip(['ID','NOMBRE','ACTIVO'],cw)):
                px=sum(cw[:i]);box(px,y+60,ancho-2,32,titulo)
                box(px,y+30,ancho-2,28,['101','Ana','1'][i]);box(px,y,ancho-2,28,['102','Luis','1'][i])
            box(320,76,175,52,'Cada fila','Un estudiante completo.')
            box(320,12,175,52,'Cada columna','Un dato de ese estudiante.')
            flecha(285,84,317,96);nota(0,15,'Ejemplo inventado: no se ha insertado en Oracle.')
        elif tipo=='conexion':
            box(0,135,140,62,'Tu PC','Aplicación local')
            box(310,135,185,62,'Oracle local','XEPDB1',True);flecha(145,166,305,166);nota(170,175,'conexión configurada')
            box(0,35,140,62,'Navegador','Docente o alumno')
            box(177,35,140,62,'Render','Python / Streamlit')
            box(355,35,140,62,'Autonomous','UPCAula',True)
            flecha(145,66,172,66);flecha(322,66,350,66)
            nota(8,8,'SQL Developer puede conectarse a cualquiera. Las filas no se sincronizan solas.')
        elif tipo=='matricula':
            box(0,65,140,62,'ESTUDIANTES','Ana · ID 101')
            box(177,65,140,62,'MATRÍCULA','(materia 10, alumno 101)',True)
            box(355,65,140,62,'MATERIAS','Base de Datos · ID 10')
            flecha(145,96,172,96);flecha(350,96,322,96)
            nota(8,35,'Un alumno puede aparecer en varias parejas. Una materia también.')
            nota(8,15,'La pareja completa no se repite: esa es la PK compuesta.')
        elif tipo=='nucleo':
            for x,y,t,sub in [(0,130,'PROFESORES','quién enseña'),(0,35,'MATERIAS','qué asignatura'),
                (177,130,'MATRÍCULAS','quién está inscrito'),(355,130,'ESTUDIANTES','quién aprende'),
                (177,35,'CLASES','qué sesión'),(355,35,'ASISTENCIAS','qué resultado')]:box(x,y,140,58,t,sub,t=='ASISTENCIAS')
            for a in [(70,125,70,98),(145,64,172,64),(145,64,160,64),(160,64,160,159),(160,159,172,159),
                      (350,159,322,159),(322,64,350,64),(425,125,425,98)]:flecha(*a)
            nota(0,7,'Vista simplificada: 6 de 14 tablas. Las relaciones físicas completas se listan después.')
        elif tipo=='inventario':
            grupos=[('CUENTAS · 3','PROFESORES\nESTUDIANTES\nADMINISTRADORES'),
                ('ACADEMIA · 4','MATERIAS\nMATERIA_ESTUDIANTES\nCLASES\nREGISTROS_ASISTENCIA'),
                ('HISTORIA · 3','AUDITORIA_ASISTENCIA\nHISTORIAL_MATRICULAS\nEVENTOS_GESTION'),
                ('SEGURIDAD · 3','LIMITES_ACCESO\nSESIONES_USUARIO\nVERIFICACION_ESTUDIANTES')]
            for i,(t,s) in enumerate(grupos):box((i%2)*253,145-(i//2)*100,242,90,t,s)
            box(0,0,495,35,'VERSIONES_ESQUEMA · 1. Total: 3 + 4 + 3 + 3 + 1 = 14.','',True)
        elif tipo=='clase':
            etapas=[('BORRADOR','Horario guardado'),('PROPUESTA','Análisis temporal'),('REVISIÓN','Decisión docente'),('CONFIRMADA','Resultados guardados')]
            for i,(t,s) in enumerate(etapas):
                box(i*126,48,116,65,t,s,i==3)
                if i<3:flecha(i*126+118,80,i*126+124,80)
            nota(0,20,'El reloj y la matrícula no confirman la clase automáticamente.')
        elif tipo=='transaccion':
            for i,t in enumerate(['Validar lista','Bloquear','Guardar resultados','Confirmar clase']):
                box(i*126,92,116,57,t,'',i==3)
                if i<3:flecha(i*126+118,120,i*126+124,120)
            box(0,15,240,52,'COMMIT','Se confirma la operación completa.',True)
            box(255,15,240,52,'ROLLBACK','Se deshace lo que quedó pendiente.')
        elif tipo=='documento':
            box(0,92,150,58,'Documento escrito','Tipo + número')
            box(175,92,145,58,'HMAC','Con clave privada')
            box(345,92,150,58,'Oracle','Huella + últimos 4',True)
            flecha(154,120,171,120);flecha(324,120,341,120)
            box(0,10,495,57,'ESTUDIANTE_ID permanece estable','La relación con matrículas y asistencias utiliza el ID interno, aunque se corrija el documento.')
        elif tipo=='historial':
            box(0,75,140,58,'Antes','presente = 0')
            box(177,75,140,58,'Corrección','Docente + motivo')
            box(355,75,140,58,'Después','presente = 1',True)
            flecha(145,104,172,104);flecha(322,104,350,104)
            box(0,4,495,52,'AUDITORIA_ASISTENCIA','Conserva 0 → 1, responsable, motivo y fecha. La detección original se mantiene.')
        elif tipo=='capas':
            for i,(t,s) in enumerate([('Python','valida y coordina'),('SQL / paquete','consulta y aplica reglas'),('Tablas / triggers','guardan y reaccionan')]):
                box(i*169,40,157,66,t,s,i==2)
                if i<2:flecha(i*169+159,73,i*169+166,73)
            nota(0,12,'El cliente decide COMMIT o ROLLBACK. El pool devuelve la conexión limpia.')


class Libro(BaseDocTemplate):
    def __init__(self,destino):
        BaseDocTemplate.__init__(self,str(destino),pagesize=A4,leftMargin=48,rightMargin=48,
            topMargin=104,bottomMargin=50,title='UPC Aula — La base de datos desde cero',
            author='Equipo UPC Aula',subject='Guía didáctica completa del esquema Oracle 011; ejemplos ficticios.')
        self.addPageTemplates(PageTemplate(id='lectura',frames=[Frame(48,50,W,ALTO-154,id='texto',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.pagina))

    def beforeDocument(self):self.indice=0

    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name in ('TituloLeccion','SubtituloIndice'):
            self.indice+=1;clave='tema-'+str(self.indice);nivel=0 if f.style.name=='TituloLeccion' else 1
            self.canv.bookmarkPage(clave);self.canv.addOutlineEntry(f.getPlainText(),clave,level=nivel)
            self.notify('TOCEntry',(nivel,f.getPlainText(),self.page,clave))

    def pagina(self,c,doc):
        c.saveState()
        if doc.page==1:
            c.setFillColor(colors.HexColor(BOSQUE));c.rect(0,0,ANCHO,ALTO,fill=1,stroke=0)
            c.setFillColor(colors.white);c.roundRect(36,ALTO-107,236,96,5,fill=1,stroke=0)
            c.drawImage(str(ROOT/'static/img/upc/logo-horizontal-manual.jpg'),49,ALTO-95,width=207,height=207*474/1369)
            c.setFillColor(colors.HexColor('#CDE6CB'));c.setFont('AulaB',11)
            c.drawString(49,102,'BASE DE DATOS · INGENIERÍA DE SISTEMAS')
            c.setFont('Aula',9);c.drawString(49,80,'Edición de estudio · esquema 011 · 23 de noviembre de 2026')
            c.drawString(49,59,'Sin datos personales ni contraseñas. Ejemplos inventados.')
        else:
            c.drawImage(str(ROOT/'static/img/upc/logo-horizontal-manual.jpg'),48,ALTO-84,width=146,height=146*474/1369)
            c.setFillColor(colors.HexColor(GRIS));c.setFont('Aula',8)
            c.drawRightString(ANCHO-48,ALTO-47,'UPC Aula · Aprender Oracle desde cero')
            c.setStrokeColor(colors.HexColor(LINEA));c.line(48,42,ANCHO-48,42)
            c.setFont('Aula',7.6);c.drawString(48,28,'Esquema 011 · Guía de estudio · Todos los ejemplos son ficticios')
            c.drawRightString(ANCHO-48,28,str(doc.page))
        c.restoreState()


TABLAS_INFO={
 'PROFESORES':('El carnet del docente','Una fila representa una cuenta docente. Laura puede administrar varias materias.',
     ['ID interno automático; usuario de acceso; nombre; hash de contraseña.','ACTIVO permite archivar. La versión detecta formularios antiguos.'],
     ['PROFESOR_ID','USUARIO','NOMBRE'],[['7','laura.demo','Laura']],
     'Un docente puede tener muchas materias. La contraseña de alta docente es configuración privada, no una columna de esta tabla.'),
 'ESTUDIANTES':('El carnet del alumno','Una fila representa a un alumno. Ana conserva el mismo ID aunque cambie su documento.',
     ['El documento se registra en VERIFICACION_ESTUDIANTES.','Las plantillas de rostro y voz son vectores JSON; pueden faltar.'],
     ['ESTUDIANTE_ID','NOMBRE','ACTIVO'],[['101','Ana','1'],['102','Luis','1']],
     'CODIGO_INSTITUCIONAL es legado: se conserva para datos antiguos y ya no se pide en el registro 011.'),
 'ADMINISTRADORES':('La cuenta que gestiona la web','Una fila es una cuenta administrativa de la aplicación.',
     ['Tiene usuario, nombre, hash bcrypt y actividad.','Puede consultar gestión y autorizar cambios mediante paquetes restringidos.'],
     ['ADMINISTRADOR_ID','USUARIO','ACTIVO'],[['1','admin.demo','1']],
     'Esta cuenta web es distinta de ADMIN de Oracle y de UPC_ADMIN_APP.'),
 'MATERIAS':('La carpeta de una asignatura','Una fila reúne materia, sección y docente responsable.',
     ['El código de materia sirve para localizar la asignatura e inscribirse.','Archivar conserva historia. No hay una tabla separada de períodos o grupos.'],
     ['MATERIA_ID','NOMBRE','PROFESOR_ID'],[['10','Base de Datos','7']],
     'El código de materia sigue existiendo. Es distinto del código institucional antiguo del alumno.'),
 'MATERIA_ESTUDIANTES':('La lista de inscritos','Una fila representa que un alumno está matriculado actualmente en una materia.',
     ['Resuelve muchos a muchos: alumno ↔ materia.','Su PK es la pareja MATERIA_ID + ESTUDIANTE_ID.'],
     ['MATERIA_ID','ESTUDIANTE_ID'],[['10','101'],['10','102']],
     'Retirar esta pareja no borra al alumno ni sus asistencias anteriores. El trigger conserva el retiro.'),
 'CLASES':('Una cita concreta en el calendario','Una fila identifica una sesión de una materia en una fecha y hora.',
     ['Comienza BORRADOR con origen PENDIENTE.','La confirmación guarda clave y propuesta para reconocer reintentos.'],
     ['CLASE_ID','MATERIA_ID','ESTADO'],[['50','10','BORRADOR']],
     'Crear la clase o llegar a su hora no registra asistencia. REGISTROS_CONFIRMADOS conserva la cantidad original al confirmar.'),
 'REGISTROS_ASISTENCIA':('El resultado de cada alumno','Una fila guarda la decisión de un estudiante para una clase concreta.',
     ['Hay como máximo una fila por pareja CLASE_ID + ESTUDIANTE_ID.','Conserva detección inicial, decisión final y revisión inicial cuando procede.'],
     ['CLASE_ID','ESTUDIANTE_ID','PRESENTE'],[['50','101','1'],['50','102','0']],
     'Es la tabla central de resultados. SIN_MUESTRA necesita decisión y motivo; no equivale automáticamente a ausencia.'),
 'AUDITORIA_ASISTENCIA':('La libreta de correcciones','Una fila conserva un cambio relevante o una eliminación de asistencia.',
     ['Guarda valores de antes y después, responsable, motivo y fecha.','No registra cada primera inserción. Una corrección sin efecto no genera historia adicional.'],
     ['OPERACION','PRESENTE_ANTERIOR','PRESENTE_NUEVO'],[['UPDATE','0','1']],
     'Conserva referencias históricas sin FK para que el rastro sobreviva a una eliminación.'),
 'HISTORIAL_MATRICULAS':('Las entradas y salidas del grupo','Una fila registra un ALTA o RETIRO de matrícula.',
     ['La matrícula actual y su historia son cosas diferentes.','Una reinscripción genera otra ALTA, sin borrar el RETIRO anterior.'],
     ['ACCION','MATERIA_ID','ESTUDIANTE_ID'],[['ALTA','10','101'],['RETIRO','10','101']],
     'El trigger escribe el historial dentro de la misma transacción de la matrícula.'),
 'EVENTOS_GESTION':('La bitácora de las operaciones','Una fila describe una acción de gestión o verificación de identidad.',
     ['Por ejemplo: archivo de cuenta, acceso verificado o documento actualizado.','Los paquetes y servicios escriben estos eventos explícitamente.'],
     ['ENTIDAD','ENTIDAD_ID','ACCION'],[['ESTUDIANTE','101','DOCUMENTO_ACTUALIZADO']],
     'No existe un trigger universal que registre cualquier SQL del propietario. Los eventos excluyen claves y documentos completos.'),
 'LIMITES_ACCESO':('El contador de intentos','Una fila permite contar fallos y aplicar un bloqueo temporal a un identificador.',
     ['CLAVE es una huella identificadora, no la contraseña.','La política de los flujos protegidos es cinco fallos y quince minutos de bloqueo.'],
     ['CLAVE','INTENTOS','BLOQUEADO_HASTA'],[['huella ficticia','3','Sin bloqueo']],
     'El contador está en Oracle y no desaparece simplemente por cerrar la pestaña.'),
 'SESIONES_USUARIO':('La entrada vigente de una cuenta','Una fila identifica la sesión registrada de un rol y una cuenta.',
     ['La PK es ROL + ACTOR_ID. El alumno 7 y el profesor 7 son identidades distintas.','Guarda hash del token, actividad, vencimiento y revocación.'],
     ['ROL','ACTOR_ID','TOKEN_HASH'],[['ESTUDIANTE','101','huella del token']],
     'Un nuevo acceso reemplaza el token previo. Se validan 30 minutos de inactividad y ocho horas máximas.'),
 'VERIFICACION_ESTUDIANTES':('Documento, permiso y método de acceso','Hay como máximo una fila por estudiante. Desde 011 también conserva su documento registrado, aunque no tenga excepción.',
     ['El documento se representa con HMAC, tipo y últimos cuatro caracteres.','Permiso excepcional y último método de acceso tienen campos distintos.'],
     ['ESTUDIANTE_ID','TIPO_DOCUMENTO','DOCUMENTO_FINAL'],[['101','CC','3456']],
     'Registrar documento no autoriza una excepción. Entrar por excepción o prueba académica tampoco marca asistencia.'),
 'VERSIONES_ESQUEMA':('La lista de reformas de la base','Cada fila indica que se aplicó una migración de estructura.',
     ['Conserva versión, descripción y fecha.','Las versiones 001–011 permiten comprobar qué reglas espera el programa.'],
     ['VERSION','DESCRIPCION'],[['011','Documento en registro, perfil y acceso']],
     'Después de limpiar los datos, esta tabla conserva once filas. No son alumnos ni clases.'),
}


RUTINAS={
 'PKG_AUDITORIA':{'ESTABLECER_CONTEXTO':'Declara el rol, actor y motivo en la conexión para validar y atribuir acciones.',
 'LIMPIAR_CONTEXTO':'Borra el contexto al devolver la conexión al pool.', 'FIJAR_MOTIVO':'Define la justificación de la operación actual.',
 'ROL_ACTUAL':'Devuelve el rol declarado.', 'ACTOR_ACTUAL':'Devuelve el ID del actor declarado.', 'MOTIVO_ACTUAL':'Devuelve el motivo declarado.'},
 'PKG_ASISTENCIA':{'PORCENTAJE_ASISTENCIA':'Calcula AVG(presente) × 100; devuelve cero si no hay registros. No filtra por sí sola todas las clases confirmadas.',
 'MATRICULAR_ESTUDIANTE':'Inserta la matrícula y reconoce duplicados.', 'REGISTRAR_ASISTENCIA':'Compatibilidad de registro individual: valida presencia, fecha y matrícula.',
 'CORREGIR_ASISTENCIA':'Comprueba profesor propietario y motivo, bloquea y cambia la presencia; el trigger conserva historia.',
 'ELIMINAR_ASISTENCIA':'Aplica controles de propiedad y motivo antes de una baja auditable.',
 'RETIRAR_ESTUDIANTE':'Retira una matrícula con el actor permitido y conserva su historial.'},
 'PKG_GESTION':{'CREAR_MATERIA':'Crea una materia para el docente activo del contexto y devuelve su ID.',
 'MATRICULAR':'Comprueba identidad, actividad y propiedad antes de matricular.', 'RETIRAR':'Retira matrícula con actor y motivo válidos.',
 'ARCHIVAR_MATERIA':'Pone la materia inactiva y registra el cambio.', 'RETIRAR_BIOMETRIA':'Vacía las plantillas del alumno y deja un evento.',
 'ARCHIVAR_ESTUDIANTE':'Retira matrículas, desactiva cuenta y vacía biometría; conserva resultados e historia.',
 'ARCHIVAR_PROFESOR':'Desactiva docente y sus materias, con evento.',
 'REGISTRAR_ESTUDIANTE':'En 011 crea cuenta y documento HMAC como una unidad; un duplicado revierte el alta.',
 'ACTUALIZAR_DOCUMENTO':'Permite completar/corregir documento propio o mediante administración; comprueba versión y unicidad y revoca sesiones/credencial previas.'},
 'PKG_CLASES':{'ABRIR_CLASE':'Crea o reutiliza el borrador de materia y horario; exige docente propietario activo.',
 'CONFIRMAR_CLASE':'Valida la lista completa, coordina bloqueos, inserta resultados y confirma la clase sin duplicar reintentos idénticos.',
 'CLASE_LEGADA':'Compatibilidad antigua: busca o crea una clase LEGADO. Esta función puede insertar filas.'},
 'PKG_ADMINISTRACION':{'CUENTAS':'Consulta docentes o alumnos con campos permitidos; incluye versión para editar.',
 'LISTAR_MATERIAS':'Consulta materias, responsables, actividad y existencia de clases.', 'AUDITORIA':'Consulta historiales con filtros y límite.',
 'EDITAR_PROFESOR':'Actualiza datos/estado o hash de clave con motivo y versión; audita cambios.',
 'EDITAR_ESTUDIANTE':'Edita cuenta; archivar retira matrículas y biometría. Conserva el código anterior como legado.',
 'EDITAR_MATERIA':'Edita materia; protege al docente histórico si ya hay clases.',
 'REGISTRAR_EXPORTACION':'Registra la preparación de una exportación CSV.',
 'ACTUALIZAR_DOCUMENTO':'En 011 exige administrador activo y delega la actualización controlada del documento.'},
 'PKG_SESIONES':{'ABRIR':'Crea o sustituye la sesión de la cuenta y comprueba actividad.',
 'VALIDAR':'Comprueba token, revocación, caducidad, actividad y, si procede, permiso excepcional; puede renovar actividad.',
 'CERRAR':'Revoca solo el token correspondiente. Un token antiguo no cierra el nuevo.'},
 'PKG_EXCEPCIONES':{'LISTAR':'Consulta alumnos, documento enmascarado, último estado y autorización.',
 'AUTORIZAR':'Administración autoriza/renueva y puede crear una cuenta sin biometría. El documento debe corresponder al perfil.',
 'REVOCAR':'Retira permiso y hash alternativo, aumenta versión y revoca la sesión.'},
 'PKG_EXCEPCIONES_DOCENTES':{'LISTAR':'Muestra alumnos activos matriculados en una materia propia.',
 'AUTORIZAR':'Exige docente, propiedad, matrícula, documento coincidente, autoría, versión y vigencia.',
 'REVOCAR':'Permite revocar las autorizaciones emitidas por ese docente e invalida la sesión anterior.'},
}


PAQUETES_INFO={
 'PKG_AUDITORIA':('La etiqueta de quién actúa','No guarda el historial por sí mismo. Ofrece el contexto que usan reglas y triggers. Ese contexto no sustituye la autenticación.' ,'sql/27_contexto_administrativo.sql'),
 'PKG_ASISTENCIA':('Operaciones de asistencia','La confirmación nueva de una clase utiliza PKG_CLASES. Aquí están las operaciones individuales y las correcciones posteriores.','sql/11_paquete_asistencia.sql'),
 'PKG_GESTION':('La oficina de gestión','Agrupa acciones académicas y de cuentas. En 011 también registra y actualiza el documento estudiantil.','sql/41_paquete_gestion_documentos.sql'),
 'PKG_CLASES':('El encargado de cada sesión','Comprueba la lista de matrícula completa antes de guardar la confirmación. Un mismo horario se reutiliza.','sql/25_paquete_clases_gestion.sql'),
 'PKG_ADMINISTRACION':('Las operaciones administrativas','Cada rutina exige el rol administrativo permitido. El docente no se convierte en administrador por usar una conexión técnica.','sql/42_paquete_administracion_documentos.sql'),
 'PKG_SESIONES':('La vigilancia de la sesión','Abrir una conexión Oracle y abrir una sesión web son operaciones distintas. Python también valida las pruebas de identidad y los tokens académicos.','sql/32_paquete_sesiones.sql'),
 'PKG_EXCEPCIONES':('La autorización de Administración','El documento es un identificador. El acceso normal por excepción necesita además una contraseña y un permiso vigente.','sql/43_paquete_excepciones_documentos.sql'),
 'PKG_EXCEPCIONES_DOCENTES':('La autorización del docente','El profesor gestiona las autorizaciones que emitió para alumnos de sus materias; la cuenta técnica restringida solo permite las operaciones previstas.','sql/44_paquete_excepciones_docentes_documentos.sql'),
}


TRIGGERS={
 'TRG_PROFESORES_ACTUALIZADO':'Actualiza fecha y aumenta VERSION_EDICION al hacer UPDATE en un docente.',
 'TRG_ESTUDIANTES_ACTUALIZADO':'Actualiza fecha y aumenta VERSION_EDICION al hacer UPDATE en un alumno.',
 'TRG_MATERIAS_ACTUALIZADO':'Actualiza fecha y aumenta VERSION_EDICION al hacer UPDATE en una materia.',
 'TRG_ADMINISTRADORES_ACTUALIZADO':'Actualiza la fecha de la cuenta administrativa; no tiene contador de edición.',
 'TRG_MATRICULA_ACTIVA':'Comprueba estudiante, materia y docente activos antes de insertar o actualizar matrícula.',
 'TRG_MATRICULAS_HIST':'Después de INSERT/DELETE de matrícula crea ALTA/RETIRO en su historial.',
 'TRG_ASISTENCIA_ACTIVA':'Rechaza una asistencia nueva si alumno, materia o docente están inactivos.',
 'TRG_ASISTENCIA_CLASE':'Protege identidad de clase, detección/revisión inicial y compatibilidad de registros antiguos.',
 'TRG_CLASES_IDENTIDAD':'Impide cambiar la identidad o reabrir una clase confirmada.',
 'TRG_ASISTENCIA_AUD':'Después de una corrección relevante o DELETE conserva la instantánea en auditoría.',
}


VISTAS={
 'V_PROFESORES':'ID, usuario, nombre y creación del docente; omite bcrypt.',
 'V_ESTUDIANTES':'Identidad y disponibilidad de rostro/voz; omite los vectores. No incluye todos los campos nuevos.',
 'V_MATERIAS':'Materia con nombre del docente mediante JOIN.',
 'V_MATERIA_ESTUDIANTES':'Matrículas con nombres de materia y alumno.',
 'V_REGISTROS_ASISTENCIA':'Resultado, clase, detección inicial y revisión. ESTADO es la decisión final.',
 'V_RESUMEN_MATERIAS':'Cantidades y promedio; cuenta clases confirmadas. Cero sin resultados es presentación, no prueba de ausencias.',
 'V_VERSIONES_ESQUEMA':'Versiones instaladas y fechas.',
 'V_AUDITORIA_ASISTENCIA':'Correcciones y bajas con contexto.',
 'V_HISTORIAL_MATRICULAS':'Altas y retiros con contexto.',
 'V_CLASES':'Clases, materia, estado, origen y cantidad de confirmación.',
 'V_EVENTOS_GESTION':'Eventos de gestión e identidad con instantáneas cuando corresponden.',
}


CHECKS={
 'CK_CLASES_CONFIRMADA':'El estado debe coincidir con origen, clave, propuesta y fecha de confirmación. Un borrador aún no tiene confirmación.',
 'CK_CLASES_LOTE':'El lote es entero no negativo. Lotes históricos adicionales pertenecen a LEGADO.',
 'CK_CLASES_CANTIDAD':'La cantidad confirmada es un entero no negativo.',
 'CK_RA_DETECCION_COHERENTE':'PRESENTE requiere detectado=1; AUSENTE, detectado=0; SIN_MUESTRA, detectado nulo.',
 'CK_RA_REVISION':'Una revisión manual requiere motivo, revisor y fecha coherentes; una decisión sin muestra exige revisión.',
 'CK_VERIFICACION_APROBADA':'Una excepción activa requiere credencial, documento, referencia y aprobador: administrador o docente con materia, con exclusión mutua.',
 'CK_VERIFICACION_RESULTADO':'PENDIENTE no tiene fecha de verificación; EXCEPCIONAL y PRUEBA_ACADEMICA registran cero factores; BIOMETRICA_COMPLETA cumple los factores requeridos.',
 'CK_VERIFICACION_FACTORES':'Las cantidades de factores están en los intervalos permitidos; requeridos va de uno a tres.',
 'CK_VERIFICACION_VERSION':'La versión es un entero no negativo.',
 'CK_VERIFICACION_HUELLA':'La huella del documento tiene 64 caracteres hexadecimales.',
 'CK_SESIONES_HASH':'El hash de token tiene 64 caracteres hexadecimales.',
 'CK_SESIONES_FECHAS':'La creación de sesión precede al vencimiento.',
 'CK_SESIONES_ACTOR':'El ID de actor es un entero positivo.',
 'CK_LIMITES_INTENTOS':'El contador de intentos es entero no negativo.',
 'CK_ESTUDIANTES_CODIGO':'Valida el código antiguo cuando existe. Desde 011 se conserva como legado y no se pide en el alta.',
}


def descripcion_columna(tabla,columna):
    n=columna['nombre']
    especiales={
      ('ESTUDIANTES','CODIGO_INSTITUCIONAL'):'Dato legado, único cuando existe. Desde 011 no se solicita; se conserva sin convertirlo en documento.',
      ('VERIFICACION_ESTUDIANTES','DOCUMENTO_HUELLA'):'HMAC del tipo y número de documento registrado. Identifica también al alumno sin excepción; el número completo no se guarda aquí.',
      ('VERIFICACION_ESTUDIANTES','DOCUMENTO_FINAL'):'Últimos cuatro caracteres para mostrar el documento enmascarado.',
      ('VERIFICACION_ESTUDIANTES','ESTADO_VERIFICACION'):'Último método: PENDIENTE, BIOMETRICA_COMPLETA, EXCEPCIONAL o PRUEBA_ACADEMICA.',
      ('ADMINISTRADORES','USUARIO'):'Usuario web normalizado; un índice único protege su unicidad.',
    }
    return especiales.get((tabla,n),columna['comentario'])


def agregar_tabla(flujo,t):
    n=t['nombre'];titulo,resumen,ideas,cab,filas,nota=TABLAS_INFO[n]
    flujo.extend([PageBreak(),Paragraph(texto(n+' · '+titulo),EST['SubtituloIndice']),p(resumen)])
    flujo.extend(p('• '+x) for x in ideas)
    flujo.extend([p('Ejemplo inventado','sub'),tabla(cab,filas),caja('Recuerda',nota),CondPageBreak(100),p('Diccionario completo de esta tabla','sub')])
    rows=[]
    for col in t['columnas']:
        claves=[]
        for r in t['restricciones']:
            if r['tipo'] in ('P','R','U') and col['nombre'] in r['columnas']:
                claves.append({'P':'PK','R':'FK','U':'UQ'}[r['tipo']])
        reglas=('Obligatorio' if not col['admite_nulo'] else 'Admite NULL')
        if col['identidad']:reglas+=' · ID automático'
        if claves:reglas+=' · '+', '.join(dict.fromkeys(claves))
        if col['predeterminado'] and not col['identidad']:reglas+='\nPor defecto: '+col['predeterminado']
        rows.append([col['nombre'],col['tipo']+'\n'+reglas,descripcion_columna(n,col)])
    flujo.extend([tabla(['Campo','Tipo y reglas','Qué significa'],rows,[.29,.26,.45]),Spacer(1,10),CondPageBreak(100),p('Reglas que debes saber leer','sub')])
    reglas=[]
    for r in t['restricciones']:
        cols=' + '.join(r['columnas'])
        if r['tipo']=='P':reglas.append([r['nombre'],'PK: '+cols+'. Identifica la fila.'])
        elif r['tipo']=='U':reglas.append([r['nombre'],'UNIQUE: '+cols+'. La combinación no se repite.'])
        elif r['tipo']=='R':
            regla='FK: '+cols+' → '+r['referencia']+' ('+' + '.join(r['columnas_referencia'])+'). '
            regla+=('Un borrado físico del padre elimina las filas hijas.' if r['al_eliminar']=='CASCADE' else 'Una referencia existente puede impedir el borrado físico del padre.')
            reglas.append([r['nombre'],regla])
        elif r['tipo']=='C' and not r['nombre'].startswith('SYS_'):
            cond=' '.join(r['condicion'].split())
            if ' IS JSON' in cond:exp='El contenido debe ser JSON válido cuando existe; el formato no acredita identidad.'
            elif cond.lower()=='activo in (0,1)':exp='ACTIVO solo admite 0 o 1.'
            else:exp=CHECKS.get(r['nombre'],'Condición permitida: '+cond)
            reglas.append([r['nombre'],exp])
    flujo.append(tabla(['Restricción','Explicación'],reglas,[.38,.62]))
    flujo.append(p('Los NOT NULL aparecen como «Obligatorio» en el diccionario. Las marcas de unicidad por índices funcionales se explican en el capítulo de índices.','pequeno'))


def agregar_paquete(flujo,paquete):
    n=paquete['nombre'];analogia,nota,archivo=PAQUETES_INFO[n]
    flujo.extend([PageBreak(),Paragraph(texto(n+' · '+analogia),EST['SubtituloIndice']),p(nota)])
    filas=[]
    for r in paquete['rutinas']:
        argumentos=r['argumentos'];retorno=next((a['tipo'] for a in argumentos if a['posicion']==0),None)
        firma='Función → '+retorno if retorno else 'Procedimiento'
        detalle=RUTINAS[n][r['nombre']]
        for direccion,etiqueta in [('IN','Recibe'),('OUT','Devuelve'),('IN/OUT','Recibe y devuelve')]:
            nombres=[a['nombre'] for a in argumentos if a['posicion']>0 and a['nombre'] and a['direccion']==direccion]
            if nombres:detalle+='\n'+etiqueta+': '+', '.join(nombres)+'.'
        filas.append([r['nombre']+'\n'+firma,detalle])
    flujo.extend([tabla(['Rutina pública','Qué hace y cómo leerla'],filas,[.33,.67]),Spacer(1,10),caja('Archivo vigente',archivo)])
    flujo.append(p('Los parámetros IN llegan a la rutina; OUT devuelve resultados. La especificación es el contrato público y el cuerpo contiene la implementación.','pequeno'))
    if n=='PKG_AUDITORIA':
        flujo.extend([CondPageBreak(190),p('Leer una llamada, paso a paso','sub'),
            p('Laura ya existe (ID 7) y fue autenticada. Esta llamada no crea su cuenta ni acredita su identidad.'),
            codigo("BEGIN\n  pkg_auditoria.establecer_contexto(\n    p_rol => 'PROFESOR', p_actor_id => 7,\n    p_motivo => 'Revisar resultado de la clase');\nEND;\n/"),
            p('BEGIN y END delimitan el bloque. El punto separa paquete y rutina. La flecha => asigna un valor a un parámetro por su nombre. En SQL*Plus, / envía el bloque al servidor.'),
            p('El contexto vive en esa conexión: no es una fila nueva ni un permiso global. Al devolverla al pool se limpia. Como las cuentas de ejemplo no existen tras el reinicio, el ejemplo no se ejecuta sobre las bases vacías.')])


def mapa_archivos():
    especificos={
      'sql/01_tablas.sql':'Crea la estructura inicial. Después se aplican las migraciones.',
      'sql/instalar.sql':'Ordena la instalación 001–011 mediante inclusiones @.',
      'sql/41_paquete_gestion_documentos.sql':'Gestión vigente y alta/actualización por documento.',
      'sql/42_paquete_administracion_documentos.sql':'Administración vigente con documento y conservación de legado.',
      'sql/43_paquete_excepciones_documentos.sql':'Excepciones administrativas con documento coincidente.',
      'sql/44_paquete_excepciones_docentes_documentos.sql':'Excepciones docentes por matrícula, autoría y documento.',
      'sql/25_paquete_clases_gestion.sql':'Apertura, confirmación completa e idempotencia de clases.',
      'sql/32_paquete_sesiones.sql':'Apertura, validación y cierre de sesiones compartidas.',
      'sql/31_versiones_edicion.sql':'Triggers de fecha y versión de edición.',
    }
    filas=[]
    for archivo in sorted((ROOT/'sql').rglob('*.sql')):
        ruta=archivo.relative_to(ROOT).as_posix();nombre=archivo.stem
        if ruta in especificos:desc=especificos[ruta]
        elif '/migraciones/' in ruta:desc='Aplica la migración '+nombre.split('_')[0]+': '+' '.join(nombre.split('_')[1:])+'.'
        elif ruta.startswith('sql/consultas/'):
            familia=archivo.parent.relative_to(ROOT/'sql/consultas').as_posix().replace('/',' → ').replace('_',' ')
            desc='Consulta o bloque usado por '+familia+'.'
        elif '/cloud/consultas/' in ruta:desc='Consulta de metadatos para comprobar la preparación cloud.'
        elif '/cloud/' in ruta:desc='Preparación/verificación cloud: '+' '.join(nombre.split('_')[1:])+'.'
        elif '/presentacion/' in ruta:desc='Guion de consultas para la exposición; usa SELECT y parámetros.'
        else:desc=' '.join(nombre.split('_')[1:]).capitalize()+'. Revisar su lugar en la instalación para distinguir versión histórica y vigente.'
        filas.append([ruta,desc])
    return filas


def agregar_lecciones(f,c):
    def cap(n,titulo):
        f.extend([PageBreak(),Paragraph(texto(f'{n}. {titulo}'),EST['TituloLeccion'])])
    def par(s):f.append(p(s))
    def sub(s):f.extend([CondPageBreak(90),p(s,'sub')])
    def puntos(*ideas):f.extend(p('• '+x) for x in ideas)
    def cuadro(t,s):f.append(caja(t,s))
    def cuad(cab,rows,w=None):f.extend([tabla(cab,rows,w),Spacer(1,10)])
    def code(s):f.append(codigo(s))
    def dibujo(t):f.extend([Grafico(t),Spacer(1,8)])

    cap(1,'Una base de datos es un cuaderno organizado')
    par('Piensa en un colegio. Necesitamos recordar alumnos, profesores, materias y asistencias. Una base organiza esos datos y aplica reglas para mantenerlos relacionados.')
    dibujo('tabla')
    cuad(['Palabra','En lenguaje sencillo'],[
        ['Base de datos','El lugar organizado donde se conservan datos y reglas.'],
        ['Tabla','Una lista de un mismo tipo de información.'],['Fila o registro','Un caso concreto: por ejemplo, Ana.'],
        ['Columna o campo','Una característica: por ejemplo, NOMBRE.'],['Valor','El contenido de una celda: «Ana».']],[.28,.72])
    cuadro('Comprueba la idea','Si añadimos a Luis, añadimos una fila. Si añadimos un campo nuevo a todos los alumnos, cambiamos la estructura.')

    cap(2,'Oracle, SQL Developer y las dos bases')
    par('Oracle es el gestor que guarda datos y ejecuta instrucciones. SQL Developer y SQL*Plus son clientes que se conectan al gestor. Python también es un cliente.')
    dibujo('conexion')
    puntos('XEPDB1 es la base local de este PC. UPCAula es la Autonomous usada por Render.',
        'Tienen estructura equivalente y sus propios datos. No se copian alumnos automáticamente.',
        'Una ejecución local puede apuntar a una u otra según su configuración.',
        'GitHub conserva código. Hacer push no copia filas entre las bases.')
    cuadro('Ejemplo','Si Ana se registra en la web de Render, su fila se guarda en Autonomous. Eso no crea una fila en la base local.')

    cap(3,'Usuario Oracle, esquema y usuario de la web')
    par('Un esquema es el conjunto de objetos de un propietario: sus tablas, vistas, paquetes e índices. Una cuenta web es una fila de la aplicación.')
    cuad(['Nombre','Qué hace'],[
        ['UPC_ASISTENCIA','Propietario del esquema. Instala, mantiene y respalda.'],
        ['UPC_AULA_APP','Cuenta técnica de ejecución ordinaria: contrato de 53 permisos.'],
        ['UPC_ADMIN_APP','Cuenta técnica restringida: cinco EXECUTE y lectura de tres vistas históricas.'],
        ['Laura / Ana / administrador web','Personas de la aplicación; sus identidades están en las tablas correspondientes.']],[.34,.66])
    dibujo('capas')
    cuadro('Una distinción importante','Laura puede ser docente de la web aunque una operación use la cuenta técnica restringida. El paquete vuelve a comprobar su rol y lo que puede hacer.')
    par('La URL de Render abre la aplicación. El DSN indica a qué servidor y servicio Oracle se conecta Python. Son destinos distintos.')

    cap(4,'Documento e ID: dos trabajos diferentes')
    par('Desde 011, el estudiante escribe tipo y número de documento. El ID interno se genera automáticamente para enlazar sus datos.')
    dibujo('documento')
    cuad(['Dato','Para qué sirve'],[['Tipo + documento','Localizar y comprobar la identidad registrada. CC, TI, CE o PA.'],
        ['ESTUDIANTE_ID','Enlazar matrículas, resultados y verificación dentro de Oracle.'],
        ['CODIGO_INSTITUCIONAL','Dato legado. Ya no se pide en registro o acceso.'],
        ['Código de materia','Sigue existiendo: identifica una asignatura para inscribirse.']],[.34,.66])
    puntos('Se normalizan espacios, puntos y guiones del documento; se conservan ceros iniciales.',
        'Se guarda HMAC y los últimos cuatro caracteres. La clave HMAC se conserva fuera del repositorio.',
        'Corregir el documento conserva el ID, comprueba versión y unicidad y revoca sesiones/credencial anteriores.')
    cuadro('Ejemplo ficticio','El número escrito puede mostrarse como CC · ****3456. Las matrículas siguen apuntando al alumno 101.')

    cap(5,'Tipos de datos, NULL y valores iniciales')
    cuad(['Tipo o regla','Cómo imaginarlo'],[
        ['NUMBER','Una casilla para números: IDs, cantidades o versiones.'],
        ['NUMBER(1,0)','Una cifra. Los CHECK de nuestras banderas la limitan a 0 o 1.'],
        ['VARCHAR2(n CHAR)','Texto con un límite de caracteres.'],
        ['TIMESTAMP WITH TIME ZONE','Fecha y hora con información de zona/desplazamiento.'],
        ['CLOB','Texto largo; aquí puede contener JSON.'],
        ['NULL','No hay un valor informado. No es el número cero.'],
        ['DEFAULT','Valor que Oracle utiliza si la inserción lo omite.'],
        ['Identidad','Oracle genera el número de la fila. No tiene que ser consecutivo.']],[.40,.60])
    cuadro('Ejemplo clave','PRESENTE_DETECTADO = 0 expresa una detección de ausencia. NULL puede expresar falta de muestra. Esa diferencia cambia cómo debe revisar el docente.')
    par('INSTANTE_UTC es una columna virtual: Oracle la calcula a partir de la fecha de la clase. No se rellena como un texto escrito por el usuario.')
    par('JSON organiza datos como listas u objetos. Comprobar «es JSON válido» no prueba que un rostro sea correcto ni que el vector tenga las dimensiones esperadas.')

    cap(6,'Las reglas: PK, FK, UNIQUE y CHECK')
    cuad(['Regla','Qué exige','Ejemplo'],[
        ['PK','Identificar cada fila; no admite duplicados ni NULL.','ESTUDIANTE_ID'],
        ['FK','Que una referencia encuentre su fila padre.','Profesor de una materia.'],
        ['UNIQUE / UQ','Que una combinación no se repita.','Alumno + clase.'],
        ['NOT NULL','Que se informe un dato.','Nombre obligatorio.'],
        ['CHECK','Que el valor o estado sea permitido.','PRESENTE solo 0 o 1.']],[.19,.47,.34])
    par('Estas reglas están en Oracle. Continúan actuando aunque una persona envíe una sentencia desde otro cliente autorizado.')
    cuadro('PK compuesta','La matrícula se identifica con MATERIA_ID + ESTUDIANTE_ID. El alumno puede repetir su ID en otras materias; la misma pareja no puede repetirse.')
    par('Una FK compuesta también usa varias columnas: la asistencia referencia CLASE_ID + MATERIA_ID para impedir que se mezcle una clase con otra materia.')

    cap(7,'Cómo se relacionan los datos')
    par('La cardinalidad explica cuántas filas pueden relacionarse con una fila del otro lado.')
    cuad(['Relación','Ejemplo del proyecto'],[['1:N · uno a muchos','Un profesor administra muchas materias.'],
        ['N:M · muchos a muchos','Un alumno cursa varias materias; cada materia tiene varios alumnos.'],
        ['1:0..1 · opcional uno a uno','Un estudiante tiene como máximo una fila de verificación.']],[.36,.64])
    dibujo('matricula')
    par('Separar entidades reduce repetición. El nombre de Ana se guarda en ESTUDIANTES; las matrículas conservan sus identificadores.')
    cuadro('Normalización','La fecha de matrícula pertenece a la pareja alumno/materia. El nombre pertenece al alumno. La auditoría guarda instantáneas de forma deliberada para conservar historia.')
    par('Para demostrar formalmente una forma normal sobre todo el modelo habría que estudiar sus dependencias funcionales. El diccionario por sí solo no demuestra tercera forma normal.')

    cap(8,'El mapa completo: siguen siendo 14 tablas')
    dibujo('inventario')
    par('Vaciamos 13 tablas de datos. La tabla VERSIONES_ESQUEMA conservó las once migraciones. Vaciar filas no elimina una tabla.')
    par('Ocho tablas forman el bloque conectado por 11 FK físicas. Las otras seis son auditoría, historial de matrícula, eventos, límites, sesiones y versiones.')
    cuadro('Sin FK no significa sin relación','La historia conserva IDs de filas que pueden desaparecer. Las sesiones identifican a la persona con rol + ID. Sus referencias lógicas tienen validaciones específicas.')

    cap(9,'Las 14 tablas y su diccionario completo')
    par('Cada ficha explica qué representa una fila, muestra un ejemplo inventado y después enumera todas sus columnas y reglas.')
    cuad(['Cómo leer la ficha','Significado'],[['Obligatorio','La columna no admite NULL.'],['Admite NULL','Puede no tener un valor informado.'],
        ['ID automático','Oracle genera el número.'],['PK / FK / UQ','Clave primaria, foránea y unicidad.'],
        ['Por defecto','Valor utilizado al omitir el campo.']],[.34,.66])
    par('Los ejemplos explican relaciones. Los números 7, 10, 50, 101 y 102 son inventados; no son los próximos IDs que Oracle promete generar.')
    cuadro('Orden recomendado','Cuentas → materia → matrícula → clase → resultados → historia → seguridad → versiones.')
    orden=list(TABLAS_INFO)
    for nombre in orden:agregar_tabla(f,next(t for t in c['tablas'] if t['nombre']==nombre))

    cap(10,'Las 11 relaciones físicas, una por una')
    par('Una FK sale de la tabla hija y referencia una clave de la tabla padre. En los dibujos una flecha padre → hija explica la dependencia; esta tabla muestra el sentido de la referencia.')
    dibujo('nucleo')
    relaciones=[]
    for t in c['tablas']:
        for r in t['restricciones']:
            if r['tipo']=='R':
                relaciones.append([t['nombre']+'\n'+' + '.join(r['columnas']),r['referencia']+'\n'+' + '.join(r['columnas_referencia']),
                    'Cascada' if r['al_eliminar']=='CASCADE' else 'Sin cascada'])
    cuad(['Hija: columnas que referencian','Padre: clave referenciada','Borrado físico'],relaciones,[.42,.42,.16])
    cuadro('Archivo y borrado físico','El flujo normal archiva cuentas/materias para conservar historia. Las cascadas describen lo que ocurre en un DELETE físico del padre.')
    par('La pertenencia actual a la materia se valida durante la confirmación. Los resultados pueden conservarse cuando el alumno después retira su matrícula.')

    cap(11,'Una clase de principio a fin')
    par('Laura crea Base de Datos. Ana y Luis se matriculan. Después Laura abre la clase del lunes a las 18:00.')
    dibujo('clase')
    cuad(['Momento','Qué existe'],[['Matrícula','Relación en MATERIA_ESTUDIANTES; el historial registra ALTA.'],
        ['Horario preparado','Fila en CLASES como BORRADOR / PENDIENTE.'],
        ['Análisis','Python prepara una propuesta temporal.'],['Revisión','El docente resuelve casos y explica correcciones.'],
        ['Confirmación','Se guardan resultados y clase CONFIRMADA como una operación completa.']],[.28,.72])
    cuadro('Luis no tiene muestra','Estado SIN_MUESTRA, detección NULL. Laura debe decidir y justificar. Un análisis fallido no se convierte en una lista de ausentes.')
    par('La fecha académica pertenece a CLASES. La fecha del análisis pertenece al registro de asistencia. El calendario presenta el día de clase en America/Bogota.')

    cap(12,'Transacciones, reintentos y cambios simultáneos')
    par('Una transacción agrupa cambios que deben quedar completos. Si falla la confirmación, no deben quedar algunos resultados de esa propuesta guardados y otros perdidos.')
    dibujo('transaccion')
    cuad(['Mecanismo','Problema que resuelve'],[['COMMIT','Confirma los cambios pendientes.'],['ROLLBACK','Revierte cambios todavía no confirmados.'],
        ['SAVEPOINT','Marca un punto dentro de la operación para retroceder ante un fallo.'],
        ['Bloqueo','Coordina cambios simultáneos sobre los datos necesarios.'],
        ['Versión de edición','Rechaza guardar un formulario basado en datos que ya cambiaron.'],
        ['Idempotencia','Reconoce la misma confirmación ya guardada y evita repetirla.']],[.32,.68])
    puntos('La misma clase, clave, origen y contenido devuelven la confirmación existente.',
        'Otra propuesta para una clase confirmada se rechaza. Una corrección posterior sigue su flujo auditable.',
        'Los paquetes de negocio no hacen COMMIT interno. Python confirma o revierte el flujo.',
        'El historial de los triggers se confirma o revierte con su operación.')

    cap(13,'Leer SQL: SELECT, WHERE y JOIN')
    par('SQL permite hacer preguntas a las tablas. Para saber quién está matriculado en una materia:')
    code('SELECT e.estudiante_id, e.nombre\nFROM materia_estudiantes me\nJOIN estudiantes e\n  ON e.estudiante_id = me.estudiante_id\nWHERE me.materia_id = :materia_id\nORDER BY e.nombre;')
    cuad(['Parte','Cómo leerla'],[['SELECT','Qué columnas quieres recibir.'],['FROM','De qué tabla partes.'],
        ['JOIN ... ON','Cómo encuentras la fila relacionada.'],['WHERE','Qué filas conservas.'],['ORDER BY','En qué orden se muestran.'],
        [':materia_id','Un valor enlazado, enviado por separado del SQL.'],['me / e','Alias: abreviaturas de las tablas.']],[.29,.71])
    cuadro('Ejemplo','Con materia 10, las parejas (10,101) y (10,102) permiten recuperar los nombres Ana y Luis. Los nombres no se copiaron dentro de la matrícula.')

    cap(14,'Contar y resumir sin inventar ausencias')
    code('SELECT m.materia_id, m.nombre,\n       COUNT(me.estudiante_id) inscritos\nFROM materias m\nLEFT JOIN materia_estudiantes me\n  ON me.materia_id = m.materia_id\nGROUP BY m.materia_id, m.nombre;')
    puntos('LEFT JOIN conserva una materia aunque todavía no tenga inscritos.',
        'COUNT de la columna del alumno devuelve cero cuando no encuentra matrícula.',
        'GROUP BY reúne filas por materia y produce un resumen.')
    cuad(['Materia ficticia','Inscritos'],[['Base de Datos','2'],['Programación','0']],[.70,.30])
    par('El perfil calcula asistidas / registros confirmados. No promedia sin ponderar los porcentajes de las materias.')
    cuadro('Cero y falta de información','Una materia sin resultados no demuestra ausencias. El calendario distingue los días sin registros de los resultados confirmados con presente=0.')
    code('SELECT COUNT(*) total_estudiantes\nFROM estudiantes;')
    par('Esta última consulta cuenta filas. Tras el reinicio documentado, la tabla estaba vacía. El PDF no ejecuta la consulta ni inserta ejemplos.')

    cap(15,'Cambiar datos y cambiar estructura')
    cuad(['Familia','Instrucciones','Qué cambian'],[['Consulta','SELECT','Devuelve información.'],
        ['DML','INSERT, UPDATE, DELETE','Añade, modifica o elimina filas.'],['DDL','CREATE, ALTER, DROP','Crea o cambia objetos de estructura.'],
        ['Transacción','COMMIT, ROLLBACK','Confirma o revierte los cambios pendientes.']],[.24,.34,.42])
    par('Este ejemplo sirve para reconocer un UPDATE:')
    code('UPDATE estudiantes\nSET nombre = :nombre\nWHERE estudiante_id = :id;')
    puntos('SET indica el cambio. WHERE selecciona la fila.',
        'Los flujos reales de edición añaden sesión, permisos, versión, motivo y transacción.',
        'Los DDL de Oracle tienen efectos de confirmación implícita: no se tratan como un DELETE pendiente que siempre pueda deshacerse con ROLLBACK.')
    cuadro('En nuestro reinicio','Se usó DELETE, respetando relaciones y triggers. Se conservaron tablas, permisos, versiones e identidades. Los respaldos permiten recuperar el estado anterior tras confirmar.')

    cap(16,'Las once vistas: ventanas sobre las tablas')
    par('Una vista guarda la definición de una consulta. Puede combinar tablas y presentar columnas útiles sin crear otra copia independiente de las filas.')
    cuad(['Vista','Qué muestra'],[[v['nombre'],VISTAS[v['nombre']]] for v in c['vistas']],[.39,.61])
    code('SELECT * FROM v_materias;')
    cuadro('Una ventana no es una autorización completa','Las vistas generales no filtran automáticamente todo por la identidad web. Los servicios y paquetes aplican los controles de usuario y propiedad.')
    par('V_ESTUDIANTES es una vista histórica con campos concretos; el perfil 011 consulta también verificación para el documento enmascarado. Una vista no adquiere columnas nuevas automáticamente por cambiar la tabla.')

    cap(17,'Los ocho paquetes: oficinas con tareas concretas')
    par('PL/SQL permite expresar reglas y operaciones dentro de Oracle. Un paquete reúne rutinas relacionadas, como una oficina con varios servicios.')
    cuad(['Concepto','Significado'],[['Especificación','El contrato público: nombres y parámetros que se pueden llamar.'],
        ['Cuerpo','La implementación y auxiliares privados.'],['Procedimiento','Realiza una operación y puede entregar parámetros OUT.'],
        ['Función','Devuelve un valor. Eso no garantiza que sea de solo lectura.'],['IN / OUT','Dato que entra / resultado que sale.']],[.31,.69])
    dibujo('capas')
    cuadro('Inventario real','Se verificaron 8 paquetes y 41 rutinas públicas. Tener especificación y cuerpo no significa que sean 16 paquetes diferentes.')
    orden_paquetes=['PKG_AUDITORIA','PKG_ASISTENCIA','PKG_GESTION','PKG_CLASES','PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES','PKG_EXCEPCIONES_DOCENTES']
    for n in orden_paquetes:agregar_paquete(f,next(x for x in c['paquetes'] if x['nombre']==n))

    cap(18,'Los diez disparadores: reglas que reaccionan')
    par('Un trigger se ejecuta por el evento para el que fue definido. BEFORE actúa antes; AFTER, después. Los actuales son por fila.')
    cuad(['Trigger / tabla','Evento y trabajo'],[[t['nombre']+'\n'+t['tabla'],t['momento']+' · '+t['evento']+'\n'+TRIGGERS[t['nombre']]] for t in c['disparadores']],[.40,.60])
    dibujo('historial')
    puntos('Los triggers no son relojes programados: no marcan presencia cuando llega la hora.',
        'Actualizar una cuenta aumenta su versión aunque el valor visible quede igual.',
        'La primera inserción de asistencia no genera una corrección en AUDITORIA_ASISTENCIA.',
        'CREATE OR REPLACE sustituye la definición del objeto; no suma otro trigger con el mismo nombre.')
    sub('Entender :OLD y :NEW con un ejemplo')
    code(':NEW.actualizado_en := SYSTIMESTAMP;\n:NEW.version_edicion := :OLD.version_edicion + 1;')
    par('Son dos instrucciones reales de sql/31_versiones_edicion.sql. :OLD es la fila antes del cambio; :NEW, la que se guardará. Si la versión anterior era 2, la nueva será 3. := asigna un valor; SYSTIMESTAMP aporta el instante actual.')

    cap(19,'Índices e identidades: buscar y numerar')
    par('Un índice se parece al índice de un libro: ayuda a localizar información sin recorrer toda la lista. Su utilidad depende de la consulta y de los datos.')
    puntos('Un índice UNIQUE también impide duplicados.',
        'Los índices funcionales pueden comparar un usuario normalizado con UPPER/TRIM.',
        'Existen índices internos de Oracle para claves y CLOB. El total incluye esos objetos.',
        'Las nueve identidades generan IDs; pueden dejar saltos por caché, reintentos o rollback.')
    cuadro('Después de vaciar','La siguiente fila puede recibir un ID alto. Eso no demuestra que sigan existiendo las filas anteriores.')
    sub('Inventario completo de 37 índices')
    cuad(['Tabla','Índice','Clase'],[[x['tabla'],x['nombre'],('Único' if x['unicidad']=='UNIQUE' else 'No único')+'\n'+x['tipo']] for x in c['indices']],[.30,.45,.25])

    cap(20,'Acceso, hashes y protección de los datos')
    cuad(['Mecanismo','Trabajo concreto'],[['bcrypt','Verificar contraseñas sin guardar el texto recuperable.'],
        ['HMAC del documento','Comparar la identidad registrada usando una clave privada.'],
        ['SHA-256 del token','Guardar la huella del token de sesión.'],['TLS / TCPS','Proteger la conexión hacia Autonomous.'],
        ['ACL','Permitir las redes autorizadas de conexión.'],['Pool','Reutilizar conexiones y devolverlas con el contexto limpio.']],[.34,.66])
    par('Un embedding es una plantilla numérica de comparación: rostro de 128 dimensiones y voz de 256 en el código actual. Sigue siendo información sensible.')
    cuad(['Último estado','Qué significa'],[['PENDIENTE','No hay una verificación registrada con ese estado de credencial.'],
        ['BIOMETRICA_COMPLETA','Se validó el factor facial exigido por la política actual.'],
        ['EXCEPCIONAL','Acceso alternativo autorizado; cero factores biométricos.'],
        ['PRUEBA_ACADEMICA','Ingreso temporal con documento y clave común; no acredita biometría.']],[.39,.61])
    cuadro('Permiso, sesión y asistencia','Autorizar una excepción no abre por sí solo una sesión. Abrir una sesión no marca asistencia. La clase mantiene su confirmación independiente.')
    par('El propietario y un DBA tienen facultades superiores. La auditoría del proyecto no se presenta como inmutable frente a ellos. Algunas reglas de formato y calidad también dependen de Python.')

    cap(21,'Las once migraciones: reformas en orden')
    par('Una migración es un cambio de estructura y reglas. VERSIONES_ESQUEMA registra que se aplicó y verificó. No guarda commits de Git ni versiones de Python.')
    migraciones=[('001','Estructura inicial, consultas y asistencia.'),('002','Auditoría e historial de matrícula.'),
        ('003','Clases, confirmación e identidad del horario.'),('004','Estados de detección y revisión.'),
        ('005','Gestión y archivo de cuentas/materias.'),('006','Administración y edición controlada.'),
        ('007','Sesiones revocables compartidas.'),('008','Documento y excepciones de identidad.'),
        ('009','Autorización docente de excepciones.'),('010','Acceso académico temporal diferenciado.'),
        ('011','Documento como identidad en registro, perfil y acceso.')]
    cuad(['Versión','Qué incorporó'],migraciones,[.17,.83])
    puntos('sql/instalar.sql coordina una instalación nueva.',
        'Las migraciones actualizan una instalación existente en el orden requerido.',
        'No se repite el instalador para obtener un dibujo ni para consultar los datos.',
        'El preflight comprueba estructura, estado de objetos y permisos antes del arranque.')

    cap(22,'Qué hace cada grupo de scripts')
    par('Un script es un archivo de instrucciones. Los Python coordinan tareas; los SQL crean objetos, aplican cambios o ejecutan consultas.')
    cuad(['Archivo de entrada','Qué hace'],[
        ['scripts/oracle.py','Orquesta acciones locales de instalación, migración, respaldo y verificación.'],
        ['scripts/preparar_oracle.py','Prepara una instalación Oracle local.'],
        ['scripts/preparar_oracle_cloud.py','Prepara/continúa cuentas y esquema Autonomous.'],
        ['scripts/probar_oracle_cloud.py','Comprueba parámetros y conectividad cloud.'],
        ['scripts/preparar_ejecucion_cloud.py','Prepara/verifica la cuenta runtime limitada.'],
        ['scripts/preparar_administracion.py','Preparación local de la conexión administrativa y primera cuenta.'],
        ['scripts/crear_administrador.py','Crea explícitamente la primera cuenta web con el propietario; no crea usuarios Oracle.'],
        ['scripts/preparar_identidad.py','Prepara o valida la clave original de identidad.'],
        ['scripts/preparar_prueba_academica.py','Genera clave y variables privadas temporales para la demostración.'],
        ['scripts/respaldo_oracle.py','Crea respaldo privado cifrado.'],['scripts/restaurar_oracle.py','Restaura mediante la herramienta de recuperación.'],
        ['scripts/limpiar_datos_pruebas.py','Cuenta por defecto; con --aplicar respalda y vacía datos.'],
        ['sql/instalar.sql','Incluye la estructura y las migraciones en orden.'],
        ['sql/consultas/','Sentencias utilizadas por repositorios y servicios Python.'],
        ['sql/cloud/','Aprovisionamiento, permisos y verificaciones cloud.']],[.46,.54])
    sub('Cómo estudiar un archivo')
    puntos('Pregunta qué recibe: argumentos, configuración o parámetros SQL.',
        'Identifica si lee datos, escribe filas o cambia estructura.',
        'Busca qué tablas toca y dónde se comprueban rol, propiedad y versión.',
        'Localiza COMMIT/ROLLBACK, manejo de errores y resultado esperado.')
    sub('Mapa de todos los archivos SQL del proyecto')
    par('Este índice sirve para encontrar archivos. Las versiones históricas de paquetes se conservan; las fichas anteriores indican las definiciones vigentes de 011.')
    cuad(['Archivo','Propósito / familia'],mapa_archivos(),[.48,.52])

    cap(23,'Respaldar y reiniciar sin perder la estructura')
    par('El reinicio autorizado vació las dos bases después de verificar sus respaldos cifrados. La estructura 011 y los usuarios técnicos permanecieron.')
    cuad(['Se vació','Se conservó'],[['Cuentas web, alumnos y docentes.','Usuarios técnicos Oracle y permisos.'],
        ['Materias, matrículas, clases y resultados.','Las 14 tablas, sus claves, vistas, paquetes y triggers.'],
        ['Historias, eventos, sesiones y límites.','Las 11 filas de VERSIONES_ESQUEMA.'],
        ['Datos de aplicación.','Claves privadas necesarias para recuperar los respaldos.']],[.50,.50])
    puntos('Primero se identifican y bloquean los destinos.',
        'Se crean y verifican los dos respaldos antes de borrar.',
        'Se eliminan hijas antes que padres; los historiales van al final por los triggers.',
        'Se comprueban cero filas, versiones y objetos; después se confirma cada base.')
    cuadro('Dos transacciones diferentes','Se verifican ambos destinos antes de confirmar. No se promete una transacción distribuida atómica entre las dos bases. Los respaldos permiten recuperar ante un fallo posterior.')
    par('No se añadieron alumnos ficticios automáticamente. Los ejemplos de este libro solo se dibujan en el PDF.')

    cap(24,'Tres historias para conectar todo')
    sub('Historia A · Ana se registra')
    puntos('Escribe nombre y documento y aporta una muestra facial válida.',
        'Python valida formatos y el vector.',
        'PKG_GESTION inserta ESTUDIANTES y VERIFICACION_ESTUDIANTES como una unidad.',
        'Si el documento está repetido se revierte el alta completa.',
        'El acceso se acredita y abre su sesión con estado real y evento.')
    sub('Historia B · Laura confirma una clase')
    puntos('La materia y las dos matrículas ya existen.',
        'Se abre el borrador de la clase.',
        'El análisis propone; Laura resuelve el caso de Luis sin muestra.',
        'La confirmación verifica la lista completa y guarda dos resultados.',
        'Si repite el mismo envío, recibe la confirmación existente.')
    sub('Historia C · Se corrige el resultado')
    puntos('Laura explica el motivo de la corrección.',
        'El paquete verifica que la materia le pertenece y bloquea la fila.',
        'Se cambia PRESENTE; el trigger escribe el historial.',
        'La detección y revisión iniciales permanecen. COMMIT confirma cambio e historia.')
    cuadro('La pregunta útil','Para cualquier acción, pregunta: ¿qué tabla describe la identidad, cuál la relación, cuál el resultado y cuál la historia?')

    cap(25,'Comprueba que lo puedes explicar')
    preguntas=[
      ('¿Hay 13 o 14 tablas?','14. Se vaciaron 13 de datos y se conservó VERSIONES_ESQUEMA.'),
      ('¿Registrar una matrícula marca presencia?','No. La asistencia corresponde a una clase y se guarda en su confirmación.'),
      ('¿Qué representa una fila de REGISTROS_ASISTENCIA?','El resultado de un estudiante en una clase concreta.'),
      ('¿Por qué MATERIA_ESTUDIANTES tiene dos columnas en su PK?','La combinación identifica una matrícula; cada ID puede participar en otras parejas.'),
      ('¿SIN_MUESTRA significa ausente?','No. Exige decisión y motivo del docente.'),
      ('¿Qué hace la FK compuesta de asistencia?','Impide asociar una clase con una materia que no le corresponde.'),
      ('¿La cédula es la PK del estudiante?','No. El documento localiza la identidad; el ID interno mantiene las relaciones.'),
      ('¿Qué sucede ante un fallo de confirmación?','Se revierte la operación incompleta; Python decide la transacción del flujo.'),
      ('¿Una función PL/SQL siempre es de lectura?','No. CLASE_LEGADA puede insertar.'),
      ('¿Qué diferencia hay entre vista y trigger?','La vista define una consulta; el trigger reacciona al evento configurado.'),
      ('¿Por qué un ID puede saltar de 101 a 110?','La identidad no es un número de fila consecutivo; intervienen caché, intentos y rollback.'),
      ('¿Un push copia los alumnos a la otra base?','No. Publica código; las bases tienen datos independientes.'),
      ('¿Una excepción autorizada marca asistencia?','No. Habilita acceso alternativo y la clase conserva su flujo.'),
      ('¿Por qué algunas tablas históricas no tienen FK?','Para conservar referencias aunque desaparezca la fila original; no implica que carezcan de PK.')]
    for i,(q,a) in enumerate(preguntas,1):
        f.append(p(f'{i}. {q}'))
    f.extend([PageBreak(),p('Respuestas razonadas','sub')])
    for i,(q,a) in enumerate(preguntas,1):
        f.append(p(f'**{i}.** {a}'))

    cap(26,'Glosario para volver cuando te pierdas')
    glosario=[('Actor','Persona o sistema al que se atribuye una operación.'),('Archivo','Cambio a inactivo conservando historia.'),
        ('Auditoría','Historia de cambios y su contexto.'),('bcrypt','Algoritmo usado para verificar contraseñas.'),
        ('Cardinalidad','Cuántas filas pueden relacionarse.'),('CHECK','Regla sobre valores/estados permitidos.'),
        ('CLOB','Texto de gran tamaño.'),('COMMIT','Confirmar cambios pendientes.'),('Contexto','Rol, actor y motivo declarados en la conexión.'),
        ('DDL','Instrucciones de definición de estructura.'),('DML','Instrucciones para insertar, actualizar o borrar filas.'),
        ('DSN','Destino técnico de conexión Oracle.'),('Embedding','Vector numérico usado para comparar muestras.'),
        ('Esquema','Objetos pertenecientes a un propietario.'),('FK','Clave que referencia otra clave.'),('HMAC','Huella calculada con una clave privada.'),
        ('Idempotencia','Repetir una solicitud válida ya aplicada no duplica su efecto.'),('Identidad','Generación automática de un ID.'),
        ('Índice','Estructura auxiliar de búsqueda/unicidad.'),('JOIN','Combinar filas relacionadas.'),('JSON','Formato de objetos/listas.'),
        ('Migración','Cambio versionado de estructura o reglas.'),('NULL','Falta de valor informado.'),('Paquete','Grupo de rutinas PL/SQL.'),
        ('PK','Clave primaria de una fila.'),('Pool','Conjunto de conexiones reutilizables.'),('Rollback','Revertir cambios pendientes.'),
        ('Rutina','Procedimiento o función.'),('Sesión','Acceso autenticado de una cuenta.'),('Token','Credencial opaca de esa sesión.'),
        ('Transacción','Unidad de cambios que se confirma o revierte.'),('Trigger','Rutina automática ante eventos definidos.'),
        ('UNIQUE','Unicidad de un valor o combinación.'),('Vista','Consulta almacenada.'),('UTC','Referencia de tiempo para comparar instantes.')]
    cuad(['Término','Significado'],glosario,[.29,.71])

    cap(27,'Fuentes y siguiente paso de estudio')
    par('Esta guía se construyó con metadatos del propietario de Autonomous y el código del proyecto. No usa filas de personas ni credenciales.')
    cuad(['Inventario comprobado','Cantidad'],[['Tablas / columnas','14 / 140'],['FK físicas','11'],['Vistas','11'],
        ['Paquetes / rutinas públicas','8 / 41'],['Triggers habilitados','10'],['Índices, incluidos internos','37'],['Identidades de tablas','9'],['Versiones','001–011']],[.70,.30])
    puntos('Captura de metadatos UTC: '+c['generado_utc'],
        'Fuente de tipos/restricciones: docs/base_datos/catalogo_estudio_011.json.',
        'Fuentes funcionales: BASE_DE_DATOS.md, DOCUMENTO_ESTUDIANTIL.md, CONEXION_BASE_DATOS.md y SQL versionado.',
        'Identidad visual: Manual UPC 2010; logo original y tipografía Arial.')
    cuadro('Cómo seguimos','Estudiamos scripts/crear_administrador.py antes de crear una cuenta. Después añadimos un docente, un alumno por documento, una materia y una matrícula, explicando cada cambio.')
    par('Equipo: Rafael Camilo Rodriguez Ayala, Harold Steven Torres Diaz y Oscar William Rivero Ordoñez. Docente de referencia: Amilkat Sierra Romano. Programa: Ingeniería de Sistemas.')
    par('Documento de estudio del proyecto académico UPC Aula. Los ejemplos ayudan a razonar; no representan datos institucionales reales ni una medición de precisión biométrica.')


def construir(catalogo,destino):
    registrar_fuentes()
    EST.update({
      'cuerpo':estilo('Cuerpo'), 'pequeno':estilo('Pequeno',8.8,12,textColor=colors.HexColor(GRIS)),
      'sub':ParagraphStyle('Sub',fontName='AulaB',fontSize=13,leading=17,textColor=colors.HexColor(VERDE),spaceBefore=10,spaceAfter=8,keepWithNext=False),
      'celda':estilo('Celda',8.8,12,spaceAfter=0), 'cabecera':ParagraphStyle('Cabecera',fontName='AulaB',fontSize=9,leading=12,textColor=colors.HexColor(BOSQUE)),
      'caja_titulo':ParagraphStyle('CajaTitulo',fontName='AulaB',fontSize=11,leading=14,textColor=colors.HexColor(VERDE)),
      'caja':estilo('Caja',10,14), 'codigo':estilo('Codigo',9,13),
      'TituloLeccion':ParagraphStyle('TituloLeccion',fontName='AulaB',fontSize=25,leading=29,textColor=colors.HexColor(BOSQUE),spaceAfter=14,keepWithNext=True),
      'SubtituloIndice':ParagraphStyle('SubtituloIndice',fontName='AulaB',fontSize=21,leading=25,textColor=colors.HexColor(BOSQUE),spaceAfter=13,keepWithNext=True),
      'grafico':ParagraphStyle('Grafico',fontName='AulaB',fontSize=9.5,leading=12,textColor=colors.HexColor(TINTA)),
      'grafico_blanco':ParagraphStyle('GraficoBlanco',fontName='AulaB',fontSize=9.5,leading=12,textColor=colors.white),
      'grafico_sub':estilo('GraficoSub',8.4,11),
      'grafico_sub_blanco':ParagraphStyle('GraficoSubBlanco',fontName='Aula',fontSize=8.4,leading=11,textColor=colors.HexColor('#D9ECD7')),
    })
    flujo=[]
    portada=ParagraphStyle('Portada',fontName='AulaB',fontSize=39,leading=45,textColor=colors.white)
    portada_sub=ParagraphStyle('PortadaSub',fontName='Aula',fontSize=18,leading=25,textColor=colors.HexColor('#D9ECD7'))
    flujo.extend([Spacer(1,110),Paragraph('La base de datos,<br/>paso a paso.',portada),Spacer(1,24),
        Paragraph('Una guía para entender UPC Aula desde el principio, con dibujos, ejemplos y palabras sencillas.',portada_sub),Spacer(1,28),
        Paragraph('14 tablas · 140 columnas<br/>11 vistas · 8 paquetes · 10 triggers',portada_sub),PageBreak()])
    flujo.append(p('Cómo usar este libro','sub'))
    flujo.append(p('Lee primero los conceptos y después sigue la historia de Laura, Ana y Luis. Los números y las filas de ejemplo son inventados: este PDF no añade datos a Oracle.'))
    flujo.append(caja('Tres maneras de estudiar','1. Leer un tema corto.\n2. Seguir el dibujo y explicar el ejemplo con tus palabras.\n3. Buscar un campo o rutina en el índice cuando tengas una duda.'))
    flujo.append(p('El diccionario está integrado en las fichas de las 14 tablas. Cada campo muestra tipo, obligatoriedad, claves y significado. El mapa final permite localizar cada archivo SQL.'))
    flujo.append(p('Índice navegable','sub'))
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('Indice0',fontName='AulaB',fontSize=10,leading=14,leftIndent=0,firstLineIndent=0,spaceBefore=8),
        ParagraphStyle('Indice1',fontName='Aula',fontSize=8.8,leading=12,leftIndent=14,firstLineIndent=0,spaceBefore=4)]
    flujo.append(toc)
    agregar_lecciones(flujo,catalogo)
    destino=Path(destino);destino.parent.mkdir(parents=True,exist_ok=True)
    Libro(destino).multiBuild(flujo)
    return destino


def main():
    p_args=argparse.ArgumentParser(description=__doc__)
    p_args.add_argument('--catalogo',type=Path,default=DOCS/'base_datos/catalogo_estudio_011.json')
    p_args.add_argument('--salida',type=Path,default=DOCS/'UPC_Aula_Base_de_Datos_Desde_Cero.pdf')
    a=p_args.parse_args();catalogo=json.loads(a.catalogo.read_text(encoding='utf-8'))
    destino=construir(catalogo,a.salida)
    print(json.dumps({'pdf':str(destino),'version':'011','datos_de_ejemplo':'ficticios'},ensure_ascii=False))


if __name__=='__main__':main()
