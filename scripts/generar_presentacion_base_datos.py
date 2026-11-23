"""Presentación para la asignatura Base de Datos, reutilizando la identidad UPC."""
from pathlib import Path
import argparse
import json
import os
from generar_presentacion import Presentacion, DOCS, ROOT, VERDE, BOSQUE, BLANCO, MENTA, PAPEL, TINTA, GRIS, LINEA


def generar(fuentes, salida=DOCS):
    d=Presentacion(fuentes,salida=salida,nombre='UPC_Aula_Presentacion_Base_de_Datos',
        titulo='UPC | Aula — Proyecto de Base de Datos',trabajo=ROOT/'.local/paquete_presentacion/slides')
    d.ppt.core_properties.subject='Exposición de Base de Datos e Ingeniería de Sistemas; esquema Oracle 009.'
    d.pdf.setSubject(d.ppt.core_properties.subject)
    d.new('', 'Proyecto de Base de Datos · Ingeniería de Sistemas','Estado documentado · Oracle 009',True,
        'Presentar el producto con un caso sencillo: una clase tiene materia, horario, alumnos y decisiones que deben poder explicarse. El centro de esta exposición es el modelo y sus reglas, con la IA como apoyo y la revisión del docente.')
    d.text(50,183,850,145,'Los datos detrás\nde cada clase.',51,BLANCO,bold=True,interlineado=59)
    d.text(53,348,820,73,'Modelo relacional, integridad y trazabilidad para el seguimiento académico.',24,MENTA)
    d.pill(53,443,365,'UPC | AULA · EDUCACIÓN Y FUTURO',True)

    d.new('Una marca de presencia\nnecesita contexto.','01 · Problemática','INFORME_PROYECTO · planteamiento',notas=
        'Explicar tres preguntas del problema: a qué clase pertenece el dato, cómo se decidió y quién lo cambió. No se presenta como una encuesta oficial o un ahorro de tiempo ya medido. El error de reconocimiento debe distinguirse de una ausencia.')
    for i,(t,c) in enumerate([('Contexto','Materia, matrícula y horario de la clase.'),('Decisión','Detección propuesta y revisión docente.'),('Historia','Responsable, motivo y valores del cambio.')]):
        d.card(50+i*293,272,274,205,t,c,f'0{i+1}')

    d.new('Un objetivo de software.\nUn fundamento de datos.','02 · Objetivos','GUIA_EXPOSICION_BASE_DATOS',notas=
        'Objetivo general: integrar la gestión académica y asistencia con control de acceso y trazabilidad en Oracle. Destacar modelado, restricciones, confirmación transaccional e historial como objetivos de la asignatura; no solo la apariencia de la web.')
    d.text(50,267,860,68,'Integrar materias, matrículas y clases con decisiones de asistencia revisadas y trazables.',25,VERDE,bold=True)
    for i,(t,c) in enumerate([('Modelar','Entidades y relaciones.'),('Proteger','Claves y restricciones.'),('Confirmar','Transacciones completas.'),('Explicar','Consultas e historial.')]):
        x=50+i*219;d.rect(x,369,203,109,PAPEL,radio=4);d.text(x+14,385,175,28,t,20,bold=True);d.text(x+14,425,175,47,c,15,GRIS)

    d.new('Una aplicación completa\ncon Oracle en el centro.','03 · Alcance y arquitectura','CONEXION_BASE_DATOS',notas=
        'El navegador accede a Render por HTTPS. Streamlit y los servicios Python validan identidad y coordinan el flujo. python-oracledb se conecta a Autonomous por TCPS. SQL Developer y SQLPlus son clientes de la misma base, no almacenes adicionales.')
    for y,t,c,oscuro in [(273,'Navegador','Docente · estudiante · administración',False),(338,'Render / Python','Interfaz · servicios · driver y pool',True),(403,'Oracle Autonomous','Tablas · reglas · transacciones · historia',False)]:
        d.rect(50,y,860,54,BOSQUE if oscuro else PAPEL,radio=4);d.text(67,y+14,330,29,t,21,BLANCO if oscuro else TINTA,bold=True);d.text(415,y+18,473,27,c,15,MENTA if oscuro else GRIS)

    d.new('Catorce tablas en total:\nocho conectadas y seis de soporte.','04 · Inventario completo','DICCIONARIO_DATOS · catálogo 009',notas=
        'Las ocho tablas del bloque principal están conectadas mediante once FK físicas. Las otras seis también son tablas reales del modelo: conservan auditoría, eventos, matrículas históricas, límites, sesiones y versiones. No tener FK no significa carecer de PK ni de referencias lógicas; estas últimas se validan en los flujos y no se dibujan como relaciones físicas. El modelo A3 incluye los dos grupos.')
    catalogo=json.loads((DOCS/'base_datos/catalogo.json').read_text(encoding='utf-8'))
    conectadas=set()
    for tabla in catalogo['tablas']:
        for restriccion in tabla['restricciones']:
            if restriccion['tipo']=='R':
                conectadas.update((tabla['nombre'],restriccion['referencia']))
    grupos=[('8 tablas conectadas por FK',[t['nombre'] for t in catalogo['tablas'] if t['nombre'] in conectadas]),
            ('6 tablas sin FK físicas',[t['nombre'] for t in catalogo['tablas'] if t['nombre'] not in conectadas])]
    for i,(titulo,nombres) in enumerate(grupos):
        x=50+i*440;d.rect(x,269,420,205,PAPEL,radio=4)
        d.text(x+16,282,386,29,titulo,20,VERDE,bold=True)
        d.text(x+16,321,386,148,'\n'.join(nombres),14,GRIS,interlineado=18)
    d.text(50,480,860,18,'Las 14 pertenecen al modelo. Una referencia lógica no equivale a una FK declarada.',12,GRIS)

    d.new('Seis tablas resumen\nel núcleo académico.','05 · Vista parcial del modelo','Modelo 009 · núcleo académico',notas=
        'Esta diapositiva es una vista parcial de seis tablas académicas, no el modelo completo. Administradores y verificación completan el bloque de ocho conectado por FK. Las otras seis tablas de soporte aparecen en el inventario anterior y en la franja inferior del modelo A3. El esquema completo tiene catorce tablas y once FK físicas.')
    nodos=[(50,274,'PROFESORES'),(50,385,'MATERIAS'),(347,274,'MATRÍCULA'),(644,274,'ESTUDIANTES'),(347,385,'CLASES'),(644,385,'RESULTADOS')]
    for x,y,t in nodos:
        d.rect(x,y,265,69,BOSQUE if t=='RESULTADOS' else PAPEL,radio=4);d.text(x+12,y+24,241,26,t,17,BLANCO if t=='RESULTADOS' else TINTA,bold=True)
    for x1,y1,x2,y2 in [(182,343,182,385),(315,419,347,419),(330,419,330,309),(330,309,347,309),(612,309,644,309),(612,419,644,419),(776,343,776,385)]:d.line(x1,y1,x2,y2,VERDE,2)
    d.text(50,468,860,19,'Vista parcial: 6 de 14 tablas. El modelo físico A3 incluye las 14 tablas y las 11 FK.',13,GRIS)

    d.new('Una relación N:M\nse convierte en una tabla.','06 · Cardinalidad y claves','MATERIA_ESTUDIANTES',notas=
        'Un alumno puede matricularse en varias materias; una materia puede tener varios alumnos. La tabla intermedia contiene materia_id y estudiante_id como PK compuesta y ambas columnas como FK. No repite nombre de estudiante ni descripción de materia.')
    d.rect(50,276,860,112,BOSQUE,radio=5);d.text(70,291,820,31,'MATERIA_ESTUDIANTES',25,BLANCO,bold=True)
    d.text(70,340,820,30,'PK (materia_id, estudiante_id) · dos FK · fecha de matrícula',19,MENTA)
    d.text(50,417,860,61,'La misma combinación no puede matricularse dos veces. Los datos de cada entidad permanecen en su tabla.',21,GRIS)

    d.new('El diccionario convierte\nel esquema en una referencia.','07 · Diccionario de datos','140 columnas · tipos y restricciones',notas=
        'Mostrar el PDF del diccionario y el catálogo HTML. Cada columna tiene tipo, nulabilidad, identidad y significado; las restricciones aparecen junto a su tabla. Los 140 campos son metadatos; no se han copiado filas de personas al paquete de exposición.')
    for i,(n,t) in enumerate([('14','tablas'),('140','columnas'),('11','claves foráneas')]):
        x=50+i*293;d.rect(x,277,274,126,PAPEL,radio=5);d.text(x+18,291,238,61,n,45,VERDE,bold=True);d.text(x+18,363,238,27,t,19,bold=True)
    d.text(50,438,860,39,'Tipo · NULL · identidad · PK/FK · valor predeterminado · significado',18,GRIS)

    d.new('La integridad protege\nla coherencia de la clase.','08 · Restricciones','PK · FK · UNIQUE · CHECK',notas=
        'Dar ejemplos concretos: identidad de cada fila, PK compuesta de matrícula, resultado único alumno/clase y FK compuesta que impide cruzar materias. CHECK delimita estados y exige un aprobador excepcional coherente. Son reglas del esquema, no solo de los botones.')
    for i,(t,c) in enumerate([('PK','Identifica cada fila.'),('FK','Relaciona entidades válidas.'),('UNIQUE','Evita resultados duplicados.'),('CHECK','Restringe estados y aprobación.')]):
        x=50+i*219;d.rect(x,278,203,180,PAPEL,radio=5);d.text(x+16,298,171,36,t,27,VERDE,bold=True);d.text(x+16,359,171,76,c,17,GRIS)

    d.new('Separar entidades\nevita repetir su información.','09 · Normalización','Modelo y decisiones de trazabilidad',notas=
        'Ejemplo para defender: el nombre depende del estudiante y no de la matrícula; la fecha de matrícula pertenece a la combinación materia/alumno. La auditoría conserva instantáneas deliberadamente. No afirmar una demostración global de 3FN sin presentar dependencias funcionales.')
    d.card(50,276,420,196,'Datos maestros','Persona y materia se guardan una vez. Las relaciones usan sus identificadores.')
    d.card(490,276,420,196,'Instantáneas históricas','La historia conserva el estado del momento para poder explicar un cambio.',dark=True)

    d.new('Una vista almacena\nuna consulta, no otra base.','10 · Vistas y SQL','11 vistas · consultas de exposición',notas=
        'Las vistas simplifican los JOIN y reportes. Una vista no equivale a una copia de la información ni a un diagrama del modelo. En la demostración, mostrar USER_VIEWS y el agregado por materia con LEFT JOIN, GROUP BY y COUNT para incluir materias vacías.')
    d.text(50,274,860,68,'JOIN relaciona. GROUP BY resume. LEFT JOIN conserva los casos sin matrícula.',27,VERDE,bold=True)
    for i,(t,c) in enumerate([('Materias','Inscritos y clases.'),('Resultados','Presencias por clase.'),('Historia','Cambios y responsables.')]):
        x=50+i*293;d.rect(x,372,274,106,PAPEL,radio=4);d.text(x+16,388,242,29,t,20,bold=True);d.text(x+16,428,242,36,c,15,GRIS)

    d.new('Ocho paquetes\norganizan las operaciones.','11 · Programación PL/SQL','Paquetes vigentes del esquema 009',notas=
        'Explicar la responsabilidad de los ocho paquetes. Las especificaciones son contratos públicos y los cuerpos implementan las reglas. El paquete no confirma por sí solo todos los aspectos de identidad: los servicios Python validan pruebas y sesión. Python decide el COMMIT del flujo.')
    nombres=['PKG_AUDITORIA','PKG_ASISTENCIA','PKG_GESTION','PKG_CLASES','PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES','PKG_EXCEPCIONES_DOCENTES']
    for i,n in enumerate(nombres):
        x=50+(i%2)*440;y=270+(i//2)*49;d.rect(x,y,420,40,PAPEL,radio=3);d.text(x+13,y+12,394,24,n,15,VERDE,bold=True)

    d.new('Los triggers reaccionan\na eventos concretos.','12 · Disparadores','10 triggers habilitados',notas=
        'Los triggers actualizan fechas/versiones, comprueban actividad, protegen la identidad de clases/resultados y conservan historia cuando se modifica una asistencia o matrícula. No son cron jobs ni generan todos los eventos: también hay eventos explícitos en servicios y paquetes.')
    for i,(t,c) in enumerate([('Actualizar','Fechas y versiones.'),('Comprobar','Cuentas y materias activas.'),('Conservar','Historia de cambios.')]):d.card(50+i*293,276,274,198,t,c,f'0{i+1}')

    d.new('Confirmar una clase\nes una transacción.','13 · Atomicidad e idempotencia','PKG_CLASES · confirmación',notas=
        'La propuesta se valida completa, se bloquean las filas necesarias y se guardan resultados y clase como una unidad. Ante error se revierte. Repetir la misma solicitud válida no duplica: devuelve el resultado existente. Una nueva propuesta distinta para una clase confirmada se rechaza.')
    for i,t in enumerate(['Validar','Bloquear','Guardar','Confirmar']):
        x=50+i*219;d.rect(x,284,203,77,BOSQUE if i==3 else PAPEL,radio=4);d.text(x+15,310,173,31,t,22,BLANCO if i==3 else TINTA,bold=True)
    d.text(50,398,860,75,'Una operación completa. Un reintento reconocido. Una clase sin duplicar.',26,VERDE,bold=True)

    d.new('El historial explica\nla decisión y su cambio.','14 · Auditoría','Detección original · revisión · corrección',notas=
        'Distinguir la detección inicial, la revisión original y una corrección posterior. La auditoría conserva valores y responsable con motivo. Archivar una materia o cuenta conserva su historia. Un DBA o el propietario tienen facultades superiores; no afirmar inmutabilidad absoluta.')
    for i,(t,c) in enumerate([('Origen','Qué detectó el análisis.'),('Revisión','Qué confirmó el docente.'),('Corrección','Quién cambió el dato y por qué.')]):d.card(50+i*293,276,274,198,t,c)

    d.new('Los roles web\nno son usuarios Oracle.','15 · Conexión y permisos','Driver Thin · pools · TLS',notas=
        'El propietario mantiene el esquema. UPC_AULA_APP opera con 53 permisos. UPC_ADMIN_APP ejecuta cinco paquetes y lee tres vistas de historia, sin DML directo de aprobación. Un docente sigue siendo PROFESOR al usar el paquete restringido; la conexión no lo convierte en administrador web.')
    for y,t,c in [(272,'UPC_ASISTENCIA','Propietario y mantenimiento.'),(335,'UPC_AULA_APP','Runtime ordinario: 53 permisos.'),(398,'UPC_ADMIN_APP','Operaciones restringidas: cinco EXECUTE.')]:
        d.rect(50,y,860,52,PAPEL,radio=4);d.text(65,y+15,335,27,t,20,VERDE,bold=True);d.text(405,y+18,481,26,c,16,GRIS)
    d.text(50,466,860,20,'El servidor valida la sesión y limpia el contexto de la conexión al devolverla.',14,GRIS)

    d.new('El acceso alternativo\ntambién deja evidencia.','16 · Seguridad e identidad','Excepciones autorizadas · 009',notas=
        'La clave alternativa se autoriza por estudiante con documento y vigencia. El docente solo gestiona sus propias aprobaciones de alumnos matriculados. Se guarda bcrypt y documento HMAC, no la clave ni el documento completo. Entrar por excepción no registra presencia de una clase.')
    for i,(t,c) in enumerate([('Autorizar','Identidad y matrícula comprobadas.'),('Limitar','Vigencia y revocación.'),('Registrar','Método excepcional y eventos.')]):d.card(50+i*293,276,274,198,t,c,f'0{i+1}')

    d.new('La demostración SQL\nempieza por el diccionario.','17 · Qué mostrar en Oracle','05_SQL · guiones de solo lectura',notas=
        'Abrir primero el guion 01 de consultas. Mostrar versiones, columnas y claves; continuar con un agregado JOIN/GROUP BY y terminar con vistas, paquetes y triggers. Las consultas se ejecutan manualmente como propietario. La carpeta incluye respaldo offline, no filas de personas ni credenciales.')
    for i,(t,c) in enumerate([('Estructura','USER_TABLES y columnas.'),('Relaciones','PK y FK por posición.'),('Consultas','JOIN y agregación.'),('Reglas','Vistas, paquetes y triggers.')]):
        x=50+i*219;d.rect(x,279,203,181,PAPEL,radio=5);d.text(x+15,300,173,35,t,20,VERDE,bold=True);d.text(x+15,357,173,73,c,16,GRIS)

    d.new('Una base verificable\npara defender el proyecto.','18 · Evidencia','CAMBIOS · 22/11/2026',oscuro=True,notas=
        'La última batería registró 293 pruebas: 288 aprobadas y cinco omitidas por falta del perfil temporal limitado. El esquema local y Autonomous 009 se verificaron. Es evidencia de software e integridad; no es exactitud biométrica ni aceptación de la página, que corresponden al usuario.')
    d.text(50,270,430,128,'288',102,MENTA,bold=True);d.text(55,403,430,42,'pruebas aprobadas',26,BLANCO,bold=True)
    d.text(558,283,350,70,'293 ejecutadas\n5 omitidas',27,BLANCO,bold=True)
    d.text(558,386,350,74,'Oracle local y Autonomous 009 verificados.',22,MENTA)

    d.new('Ingeniería de Sistemas:\nintegrar, operar y explicar.','19 · Aporte al programa','Relación formativa del proyecto',notas=
        'Relacionar el trabajo con bases de datos, ingeniería de software, programación, infraestructura, seguridad e IA. El aporte de la asignatura se ve en el modelo, sus consultas y reglas. No se está declarando una equivalencia oficial con el currículo, sino el aporte del proyecto al aprendizaje.')
    for i,(t,c) in enumerate([('Datos','Modelo, SQL y PL/SQL.'),('Software','Capas, pruebas y versiones.'),('Operación','Red, permisos y recuperación.')]):d.card(50+i*293,276,274,198,t,c)

    d.new('El valor del software\nse sostiene en sus datos.','20 · Valor y cierre','GOODWILL · beneficios por medir',notas=
        'Cerrar vendiendo utilidad: seguimiento por clase, revisión humana, consulta e historia. El ahorro, precio y costos se medirán en un piloto; no se prometen ingresos ni exactitud. Nombrar al equipo y al docente y abrir el modelo o las consultas para las preguntas de Base de Datos.')
    d.text(50,274,860,70,'Seguimiento académico, decisiones revisadas e historia que puede explicarse.',28,VERDE,bold=True)
    d.text(50,378,860,70,'Rafael Camilo Rodriguez Ayala · Harold Steven Torres Diaz\nOscar William Rivero Ordoñez',18,GRIS)
    d.text(50,455,860,28,'Amilkat Sierra Romano · Docente de referencia',18,VERDE,bold=True)
    d.finish()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fuentes',type=Path,default=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts')
    p.add_argument('--salida',type=Path,default=DOCS)
    args=p.parse_args();generar(args.fuentes,args.salida)


if __name__=='__main__':main()
