"""Copia la entrega de Base de Datos al Escritorio y genera un ZIP portable."""
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from pathlib import Path
from urllib.parse import quote, unquote
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def preparar(destino):
    destino=Path(destino).resolve()
    if destino.exists():
        raise FileExistsError('La carpeta de destino ya existe. Indica otra para conservar sus archivos.')
    destino.mkdir(parents=True)
    mapeo={}
    def copiar(origen,relativo):
        original=(ROOT/origen).resolve();final=destino/relativo
        final.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,final)
        mapeo[original]=final
        return final
    pares=[
        ('docs/UPC_Aula_Presentacion_Base_de_Datos.pptx','01_Presentacion/UPC_Aula_Base_de_Datos.pptx'),
        ('docs/UPC_Aula_Presentacion_Base_de_Datos.pdf','01_Presentacion/UPC_Aula_Base_de_Datos.pdf'),
        ('docs/UPC_Aula_Guia_Exposicion_Base_de_Datos.pdf','02_Documentacion/Guia_para_defender_el_proyecto.pdf'),
        ('docs/UPC_Aula_Documentacion_Integral.pdf','02_Documentacion/Documentacion_integral_1_2.pdf'),
        ('docs/GUIA_EXPOSICION_BASE_DATOS.md','02_Documentacion/GUIA_EXPOSICION_BASE_DATOS.md'),
        ('docs/INFORME_PROYECTO.md','02_Documentacion/INFORME_PROYECTO.md'),
        ('docs/BASE_DE_DATOS.md','02_Documentacion/BASE_DE_DATOS.md'),
        ('docs/UPC_Aula_Diccionario_de_Datos_009.pdf','03_Diccionario/Diccionario_de_datos_009.pdf'),
        ('docs/DICCIONARIO_DATOS.md','03_Diccionario/DICCIONARIO_DATOS.md'),
        ('docs/base_datos/index.html','03_Diccionario/Catalogo_interactivo/index.html'),
        ('docs/base_datos/catalogo.json','03_Diccionario/Catalogo_interactivo/catalogo.json'),
        ('docs/base_datos/modelo_relacional_009.pdf','04_Modelo_relacional/Modelo_relacional_009.pdf'),
        ('docs/base_datos/modelo_relacional_009.png','04_Modelo_relacional/Modelo_relacional_009.png'),
        ('docs/base_datos/modelo_relacional_009.svg','04_Modelo_relacional/Modelo_relacional_009.svg'),
        ('docs/base_datos/modelo_relacional_009.mmd','04_Modelo_relacional/Modelo_relacional_009.mmd'),
        ('exports/modelo_009.sql','04_Modelo_relacional/Modelo_009_para_Data_Modeler.sql'),
        ('sql/presentacion/01_consultas_para_exponer.sql','05_SQL/01_consultas_para_exponer.sql'),
        ('sql/presentacion/02_consultas_con_parametros.sql','05_SQL/02_consultas_con_parametros.sql'),
        ('sql/presentacion/LEER_PRIMERO.md','05_SQL/LEER_PRIMERO.md'),
        ('docs/CONEXION_BASE_DATOS.md','06_Conexion_y_valor/CONEXION_BASE_DATOS.md'),
        ('docs/GOODWILL.md','06_Conexion_y_valor/GOODWILL.md'),
        ('docs/UPC_Aula_Presentacion_Comercial.pptx','08_Comercial_opcional/Presentacion_comercial.pptx'),
        ('docs/UPC_Aula_Presentacion_Comercial.pdf','08_Comercial_opcional/Presentacion_comercial.pdf'),
        ('docs/PRESENTACION_COMERCIAL.md','08_Comercial_opcional/GUIA_COMERCIAL.md'),
        ('Proyecto_recursos/MANUAL DE IDENTIDAD VISUAL-UPC-2010.pdf','09_Identidad_UPC/Manual_identidad_UPC_2010.pdf')]
    for origen,relativo in pares:copiar(origen,relativo)

    # Snapshot de lo publicado: Git excluye secretos y el entorno local.
    fuente=destino/'07_Codigo_fuente';fuente.mkdir()
    archivo=fuente/'Proyecto_UPC_Aula.zip'
    subprocess.run(['git','archive','--format=zip','--output',str(archivo),'HEAD'],cwd=ROOT,check=True)
    expandido=fuente/'Proyecto';expandido.mkdir()
    with zipfile.ZipFile(archivo) as z:
        for entrada in z.infolist():
            if entrada.is_dir():continue
            final=(expandido/entrada.filename).resolve()
            if not final.is_relative_to(expandido.resolve()):raise ValueError('Ruta de archivo no admitida.')
            if '.local' in final.relative_to(expandido).parts or entrada.filename.endswith('secrets.toml'):
                raise ValueError('El snapshot contiene una ruta privada.')
            final.parent.mkdir(parents=True,exist_ok=True);final.write_bytes(z.read(entrada))
    # Instalador separado, con sus inclusiones relativas intactas.
    instalacion=destino/'05_SQL/03_Instalacion_y_migraciones'
    shutil.copytree(expandido/'sql',instalacion/'sql')
    shutil.copy2(expandido/'oracle_scripts.sql',instalacion/'oracle_scripts.sql')
    (instalacion/'LEER_PRIMERO.txt').write_text(
        'Esta carpeta conserva el SQL original versionado y sus rutas relativas.\n'
        'El guion para exponer esta en 05_SQL/01_consultas_para_exponer.sql.\n'
        'El instalador inicial se usa en un esquema nuevo; la base existente usa migraciones.\n'
        'Para dibujar el modelo se importa el DDL con Data Modeler.\n',encoding='utf-8')

    # Las fuentes copiadas apuntan a la copia del código, no al PC original.
    def nueva_ruta(original,actual):
        if original in mapeo:objetivo=mapeo[original]
        elif original.is_relative_to(ROOT):objetivo=expandido/original.relative_to(ROOT)
        else:return None
        return quote(os.path.relpath(objetivo,actual.parent).replace('\\','/'),safe='/_.-')
    for original,actual in mapeo.items():
        if actual.suffix=='.md':
            texto=actual.read_text(encoding='utf-8')
            def enlace(m):
                valor=m.group(1);dest=valor.strip('<>')
                if not dest or dest.startswith('#') or '://' in dest:return m.group(0)
                ruta,marca,seccion=dest.partition('#')
                resuelta=(original.parent/unquote(ruta)).resolve()
                nueva=nueva_ruta(resuelta,actual)
                return ']('+nueva+('#'+seccion if marca else '')+')' if nueva else m.group(0)
            texto=re.sub(r'\]\(([^)]+)\)',enlace,texto)
            actual.write_text(texto,encoding='utf-8')
    catalogo=mapeo[(ROOT/'docs/base_datos/index.html').resolve()]
    html=catalogo.read_text(encoding='utf-8')
    for viejo,original in [('../DICCIONARIO_DATOS.md','docs/DICCIONARIO_DATOS.md'),
        ('../CONEXION_BASE_DATOS.md','docs/CONEXION_BASE_DATOS.md'),('../GOODWILL.md','docs/GOODWILL.md'),('../ROADMAP.md','docs/ROADMAP.md')]:
        html=html.replace('href="'+viejo+'"','href="'+nueva_ruta((ROOT/original).resolve(),catalogo)+'"')
    catalogo.write_text(html,encoding='utf-8')

    # Piezas breves para tener problemática, objetivos y programa a mano.
    guia=(ROOT/'docs/GUIA_EXPOSICION_BASE_DATOS.md').read_text(encoding='utf-8')
    for titulo,inicio,fin in [('PROBLEMATICA_Y_OBJETIVOS.md','## 2. Problemática','## 4. Relación'),
                              ('APORTE_A_INGENIERIA_DE_SISTEMAS.md','## 4. Relación','## 5. Modelo')]:
        texto=guia[guia.index(inicio):guia.index(fin)]
        (destino/'02_Documentacion'/titulo).write_text('# UPC | Aula · Material de exposición\n\n'+texto,encoding='utf-8')
    conexion=destino/'06_Conexion_y_valor'
    (conexion/'Abrir_UPC_Aula_en_Render.url').write_text('[InternetShortcut]\nURL=https://controlasistenciaupc.onrender.com\n',encoding='utf-8')
    (conexion/'CONEXION_PARA_MANANA.txt').write_text(
        'Web: https://controlasistenciaupc.onrender.com\n'
        'Oracle: usar la conexion autorizada del proyecto o la configuracion privada del equipo.\n'
        'SQL Developer y SQLPlus son clientes de Oracle; no necesitan copiar los datos entre ellos.\n'
        'La carpeta compartible no contiene contrasenas, DSN privados ni claves de identidad.\n'
        'Sin internet: mostrar modelo PDF, diccionario PDF y catalogo HTML.\n',encoding='utf-8')
    enlaces=[('Presentación principal · PowerPoint','01_Presentacion/UPC_Aula_Base_de_Datos.pptx','21 diapositivas centradas en el modelo y sus reglas.'),
        ('Presentación principal · PDF','01_Presentacion/UPC_Aula_Base_de_Datos.pdf','Respaldo para proyectar sin PowerPoint.'),
        ('Guía para defender el proyecto','02_Documentacion/Guia_para_defender_el_proyecto.pdf','8 páginas: problemática, objetivos, programa, SQL y preguntas.'),
        ('Documentación integral 1.2','02_Documentacion/Documentacion_integral_1_2.pdf','87 páginas de referencia académica y técnica.'),
        ('Diccionario de datos','03_Diccionario/Diccionario_de_datos_009.pdf','30 páginas · 14 tablas · 140 columnas.'),
        ('Catálogo de tablas interactivo','03_Diccionario/Catalogo_interactivo/index.html','Funciona sin internet; búsqueda, columnas y relaciones.'),
        ('Modelo relacional 009','04_Modelo_relacional/Modelo_relacional_009.pdf','Diagrama completo en A3; también PNG, SVG, Mermaid y DDL.'),
        ('Consultas para mostrar en clase','05_SQL/01_consultas_para_exponer.sql','Solo lectura: diccionario, JOIN, agregados, vistas y PL/SQL.'),
        ('Conexión y valor del proyecto','06_Conexion_y_valor/CONEXION_BASE_DATOS.md','Render → Python → Oracle; roles y cuentas técnicas.'),
        ('Código fuente publicado','07_Codigo_fuente/Proyecto/README.md','Copia completa y ZIP del repositorio, sin secretos.'),
        ('Presentación comercial opcional','08_Comercial_opcional/Presentacion_comercial.pdf','20 diapositivas como apoyo al valor del software.'),
        ('Libro de identidad UPC','09_Identidad_UPC/Manual_identidad_UPC_2010.pdf','Referencia institucional del diseño.')]
    logo=base64.b64encode((ROOT/'static/img/upc/logo-horizontal-manual.jpg').read_bytes()).decode()
    tarjetas=''.join(f'<a class="tarjeta" href="{escape(ruta,quote=True)}"><strong>{escape(titulo)}</strong><span>{escape(desc)}</span></a>' for titulo,ruta,desc in enlaces)
    indice='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UPC Aula · Exposición de Base de Datos</title>
<style>body{margin:0;background:#f1f5ee;color:#173d2d;font:16px/1.5 Arial,sans-serif}header{padding:34px 6%;background:white;border-bottom:1px solid #cddfcc}header img{width:235px;height:auto}main{max-width:1180px;margin:auto;padding:35px 22px}h1{font-size:clamp(30px,4vw,48px);line-height:1.1;margin:12px 0}p{max-width:85ch;color:#53504f}.etiqueta{font-size:12px;letter-spacing:.14em;color:#007337;font-weight:bold}.rejilla{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:26px 0}.tarjeta{display:block;text-decoration:none;color:#173d2d;background:white;border:1px solid #d6e2d6;border-radius:9px;padding:22px}.tarjeta:hover,.tarjeta:focus{outline:2px solid #007337}.tarjeta strong{display:block;color:#007337;font-size:19px}.tarjeta span{display:block;color:#53504f;margin-top:8px}.nota{background:#e2eedc;padding:22px;border-radius:8px}li{margin:8px 0}footer{font-size:13px;padding:25px 0;color:#53504f}</style>
<header><img alt="Universidad Popular del Cesar" src="data:image/jpeg;base64,'''+logo+'''"></header><main><span class="etiqueta">UPC | AULA · MATERIAL PARA EXPONER</span><h1>La base de datos detrás<br>de cada clase.</h1><p>Todo reunido para la exposición de Base de Datos: presentación, problemática, objetivos, modelo relacional, consultas y conexión con el programa de Ingeniería de Sistemas.</p><div class="nota"><strong>Orden sugerido</strong><ol><li>Abrir la presentación principal y ensayar con la guía.</li><li>Tener a mano el modelo y el diccionario para preguntas.</li><li>Mostrar las consultas seleccionadas en la conexión Oracle autorizada.</li><li>Cerrar con integración, evidencia y valor del software.</li></ol></div><div class="rejilla">'''+tarjetas+'''</div><p>Los PDF y el catálogo funcionan sin conexión. La web en Render y la demostración contra Oracle necesitan conectividad y la configuración privada del equipo.</p><footer>Rafael Camilo Rodriguez Ayala · Harold Steven Torres Diaz · Oscar William Rivero Ordoñez<br>Docente: Amilkat Sierra Romano · Ingeniería de Sistemas</footer></main></html>'''
    (destino/'00_EMPEZAR_AQUI.html').write_text(indice,encoding='utf-8')
    (destino/'00_LEER_PRIMERO.txt').write_text(
        'UPC | AULA - EXPOSICION DE BASE DE DATOS\n\n'
        '1. Abrir 00_EMPEZAR_AQUI.html con doble clic.\n'
        '2. Presentacion principal: 01_Presentacion (Base de Datos, 21 diapositivas).\n'
        '3. Guia de defensa: 02_Documentacion (problematica, objetivos y preguntas).\n'
        '4. Diccionario y modelo: 03_Diccionario y 04_Modelo_relacional.\n'
        '5. SQL para exponer: 05_SQL/01_consultas_para_exponer.sql.\n'
        '6. La presentacion comercial anterior esta en 08_Comercial_opcional.\n\n'
        'Se copiaron los originales; el proyecto sigue en su carpeta.\n'
        'No se incluyen credenciales ni filas de personas.\n',encoding='utf-8')
    hash_git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archivos=[]
    for archivo in sorted(destino.rglob('*')):
        if archivo.is_file():archivos.append(dict(ruta=archivo.relative_to(destino).as_posix(),bytes=archivo.stat().st_size,sha256=sha256(archivo.read_bytes()).hexdigest()))
    manifiesto=dict(proyecto='UPC | Aula',uso='Exposición de Base de Datos',esquema='009',commit_fuente=hash_git,
        fecha_utc=datetime.now(timezone.utc).isoformat(),archivos=archivos,secretos_incluidos=False)
    (destino/'MANIFIESTO.json').write_text(json.dumps(manifiesto,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paquete=Path(str(destino)+'.zip')
    if paquete.exists():raise FileExistsError('El ZIP ya existe; no se reemplazó.')
    with zipfile.ZipFile(paquete,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for archivo in destino.rglob('*'):
            if archivo.is_file():z.write(archivo,archivo.relative_to(destino.parent))
    print(json.dumps(dict(carpeta=str(destino),zip=str(paquete),archivos=len(archivos)+1,commit=hash_git),ensure_ascii=False))
    return destino


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destino',type=Path,default=Path.home()/'Desktop/UPC_Aula_Presentacion_Base_de_Datos')
    args=p.parse_args();preparar(args.destino)


if __name__=='__main__':main()
