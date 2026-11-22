"""Copias autenticadas/cifradas y restauracion exclusivamente en un esquema vacio."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from hashlib import sha256
import base64
import hmac
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import oracledb
from src.base_datos.consultas import cargar_sql

IDENTIFICADOR = re.compile(r'^[A-Z][A-Z0-9_$#]{0,127}$')


def nombre(valor):
    if not isinstance(valor, str) or not IDENTIFICADOR.fullmatch(valor):
        raise ValueError('Identificador SQL no valido en el respaldo.')
    return '"' + valor + '"'


def canonico(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def clave_local(ruta, *, crear=False):
    ruta = Path(ruta)
    if not ruta.exists() and crear:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open('xb') as f: f.write(os.urandom(32))
        ruta.chmod(0o600)
    clave = ruta.read_bytes()
    if len(clave) != 32: raise ValueError('La clave de respaldo no tiene el formato esperado.')
    return clave


def _claves(clave, backup_id):
    material = HKDF(algorithm=hashes.SHA256(), length=64, salt=backup_id.encode(), info=b'UPC-respaldo-v2').derive(clave)
    return material[:32], material[32:]


def _columnas(cur, tabla):
    cur.execute(cargar_sql('base_datos/recuperacion/columnas_01'), t=tabla)
    columnas = [{'nombre': n, 'tipo': t, 'virtual': v == 'YES', 'identidad': i == 'YES'} for n,t,v,i in cur]
    cur.execute(cargar_sql('base_datos/recuperacion/columnas_02'), t=tabla)
    identidades = {n: {'generacion': g, 'siguiente_seguro': str(s), 'incremento': str(i)} for n,g,s,i in cur}
    for c in columnas:
        if c['nombre'] in identidades: c.update(identidades[c['nombre']])
    return columnas


def _consulta(tabla, columnas):
    campos = []
    for c in columnas:
        if c['virtual']: continue
        n,t = nombre(c['nombre']),c['tipo']
        if 'TIMESTAMP' in t:
            formato = 'YYYY-MM-DD"T"HH24:MI:SS.FF9' + ('TZH:TZM' if 'TIME ZONE' in t else '')
            campos.append(f"TO_CHAR({n},'{formato}')")
        elif t == 'DATE': campos.append(f'''TO_CHAR({n},'YYYY-MM-DD"T"HH24:MI:SS')''')
        elif t == 'NUMBER': campos.append(f"TO_CHAR({n},'TM9','NLS_NUMERIC_CHARACTERS=''.,''')")
        elif t in ('CLOB','NCLOB'): campos.append(f'TO_CLOB({n})')
        elif t in ('VARCHAR2','NVARCHAR2','CHAR','NCHAR','BLOB','RAW'): campos.append(n)
        else: raise ValueError('Tipo de columna no soportado por la restauracion: '+t)
    return 'SELECT '+','.join(campos)+' FROM '+nombre(tabla)


def _transportar(valor):
    if isinstance(valor, bytes): return {'__bytes__': base64.b64encode(valor).decode('ascii')}
    if hasattr(valor, 'read'): return _transportar(valor.read())
    return valor


def _huella_fila(fila, columnas):
    resultado = []
    with localcontext() as ctx:
        ctx.prec = 80
        for valor,c in zip(fila, (c for c in columnas if not c['virtual'])):
            valor = _transportar(valor)
            if valor is not None and c['tipo'] == 'NUMBER': valor = str(Decimal(valor).normalize())
            if valor is not None and c['tipo'] in ('CLOB','NCLOB'):
                # V1 podia recibir JSON nativo del driver; se compara su contenido semantico.
                if isinstance(valor,(dict,list)): valor = canonico(valor).decode()
                else:
                    try: valor = canonico(json.loads(valor)).decode()
                    except (ValueError,TypeError): pass
            resultado.append(_transportar(valor))
    return sha256(canonico(resultado)).hexdigest()


def _exigir_propietario(conexion):
    with conexion.cursor() as cur:
        cur.execute(cargar_sql('base_datos/recuperacion/identidad_propietario'))
        usuario, esquema = cur.fetchone()
    if usuario != esquema:
        raise PermissionError('El respaldo/restauración requiere la cuenta propietaria; la cuenta de ejecución no sirve para mantenimiento.')


def respaldar(conexion, destino, clave):
    _exigir_propietario(conexion)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=False)
    destino.chmod(0o700)
    backup_id = uuid4().hex
    cifrado, firma = _claves(clave, backup_id)
    manifiesto = {'formato': 2, 'backup_id': backup_id, 'completo': False,
                  'creado_en': datetime.now(timezone.utc).isoformat(), 'tablas': [], 'archivos': {}}

    def guardar(archivo, datos):
        nonce = os.urandom(12)
        contenido = nonce + AESGCM(cifrado).encrypt(nonce, canonico(datos), (backup_id+'/'+archivo).encode())
        ruta = destino/archivo
        with ruta.open('xb') as f: f.write(contenido)
        ruta.chmod(0o600)
        manifiesto['archivos'][archivo] = sha256(contenido).hexdigest()

    with conexion.cursor() as cur:
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_01'))
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_02'))
        manifiesto['origen'] = list(cur.fetchone())
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_03'))
        manifiesto['versiones'] = [r[0] for r in cur]
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_04'))
        tablas = [r[0] for r in cur]
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_05'))
        manifiesto['objetos_invalidos_origen'] = cur.fetchone()[0]
        cur.execute(cargar_sql('compartidas/inventario_objetos'))
        manifiesto['inventario_objetos'] = dict(cur.fetchall())
        cur.execute(cargar_sql('compartidas/estados_disparadores'))
        manifiesto['estados_disparadores'] = dict(cur.fetchall())
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_08'))
        ddl = {k: [] for k in ('tablas','indices','foraneas','vistas','specs','cuerpos','triggers','comentarios')}
        for tabla in tablas:
            nombre(tabla)
            columnas = _columnas(cur, tabla)
            cur.execute(_consulta(tabla,columnas))
            partes, huellas, total, indice = [], [], 0, 0
            while True:
                filas = cur.fetchmany(250)
                if not filas: break
                filas = [[_transportar(v) for v in f] for f in filas]
                archivo = f'{tabla}.{indice:06}.aes'
                guardar(archivo,filas)
                partes.append(archivo)
                huellas.extend(_huella_fila(f,columnas) for f in filas)
                total += len(filas); indice += 1
            manifiesto['tablas'].append({'nombre':tabla,'columnas':columnas,'filas':total,'partes':partes,
                                        'huella_datos':sha256(canonico(sorted(huellas))).hexdigest()})
            cur.execute(cargar_sql('base_datos/recuperacion/respaldar_11'),n=tabla)
            ddl['tablas'].append(_transportar(cur.fetchone()[0]))
        consultas = [
            ('indices','INDEX',cargar_sql('base_datos/recuperacion/respaldar_12')),
            ('foraneas','REF_CONSTRAINT',cargar_sql('base_datos/recuperacion/respaldar_13')),
            ('vistas','VIEW',cargar_sql('base_datos/recuperacion/respaldar_14')),
            ('specs','PACKAGE_SPEC',cargar_sql('base_datos/recuperacion/respaldar_15')),
            ('cuerpos','PACKAGE_BODY',cargar_sql('base_datos/recuperacion/respaldar_16')),
            ('triggers','TRIGGER',cargar_sql('base_datos/recuperacion/respaldar_17'))]
        for grupo,tipo,consulta in consultas:
            cur.execute(consulta)
            for n in [r[0] for r in cur]:
                cur.execute(cargar_sql('base_datos/recuperacion/respaldar_18'),t=tipo,n=n)
                ddl[grupo].append(_transportar(cur.fetchone()[0]))
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_09'))
        for t,comentario in cur.fetchall():
            ddl['comentarios'].append('COMMENT ON TABLE '+nombre(t)+" IS '"+comentario.replace("'","''")+"'")
        cur.execute(cargar_sql('base_datos/recuperacion/respaldar_10'))
        for t,c,comentario in cur.fetchall():
            ddl['comentarios'].append('COMMENT ON COLUMN '+nombre(t)+'.'+nombre(c)+" IS '"+comentario.replace("'","''")+"'")
        guardar('estructura.aes',ddl)
    conexion.rollback()
    manifiesto['completo'] = True
    manifiesto['firma'] = hmac.new(firma,canonico(manifiesto),sha256).hexdigest()
    ruta = destino/'manifiesto.json'
    with ruta.open('x',encoding='utf-8') as f: json.dump(manifiesto,f,ensure_ascii=False,indent=2)
    ruta.chmod(0o600)
    verificar(destino,clave)
    return destino


def _ruta_segura(destino, archivo):
    if not isinstance(archivo,str) or Path(archivo).name != archivo or '/' in archivo or '\\' in archivo:
        raise ValueError('Ruta no valida dentro del respaldo.')
    ruta = destino/archivo
    if ruta.is_symlink() or ruta.resolve().parent != destino.resolve():
        raise ValueError('El respaldo contiene enlaces o rutas externas.')
    return ruta


def verificar(destino, clave=None):
    destino = Path(destino).resolve()
    manifiesto = json.loads((destino/'manifiesto.json').read_text(encoding='utf-8'))
    if manifiesto.get('completo') is not True or manifiesto.get('formato') not in (1,2):
        raise ValueError('Respaldo incompleto o formato no soportado.')
    if manifiesto['formato'] == 2:
        if clave is None: raise ValueError('Se necesita la clave privada del respaldo.')
        cifrado,firma = _claves(clave,manifiesto['backup_id'])
        firmado = dict(manifiesto);esperada=firmado.pop('firma',None)
        if not isinstance(esperada,str) or not hmac.compare_digest(esperada,hmac.new(firma,canonico(firmado),sha256).hexdigest()):
            raise ValueError('La firma del manifiesto no es valida.')
    datos = {}
    for archivo,esperado in manifiesto['archivos'].items():
        contenido = _ruta_segura(destino,archivo).read_bytes()
        if sha256(contenido).hexdigest() != esperado: raise ValueError('Checksum incorrecto: '+archivo)
        if manifiesto['formato'] == 2:
            contenido = AESGCM(cifrado).decrypt(contenido[:12],contenido[12:],(manifiesto['backup_id']+'/'+archivo).encode())
            datos[archivo] = json.loads(contenido)
        else:
            datos[archivo] = contenido.decode('utf-8')
    return manifiesto,datos


def _sql_limpio(sql, *, plsql=False):
    sql=sql.strip()
    if sql.endswith('/'): sql=sql[:-1].rstrip()
    return sql if plsql else sql.rstrip(';').rstrip()


def _valor(valor, columna):
    if valor is None: return None
    t=columna['tipo']
    if t=='NUMBER': return Decimal(str(valor))
    if t in ('CLOB','NCLOB') and isinstance(valor,(dict,list)): return canonico(valor).decode()
    if t in ('BLOB','RAW') and isinstance(valor,dict) and set(valor)=={'__bytes__'}: return base64.b64decode(valor['__bytes__'],validate=True)
    return valor


def restaurar(destino, clave, conexion, *, usuario_esperado):
    _exigir_propietario(conexion)
    manifiesto,datos = verificar(destino,clave)
    if manifiesto['formato'] != 2:
        raise ValueError('V1 no contiene el plan de restauracion autenticado. Convierta/verifique su estructura con el administrador; no se ejecuto DDL.')
    if manifiesto.get('objetos_invalidos_origen'):
        raise ValueError('La copia procede de un esquema invalido; use un respaldo completo anterior.')
    with conexion.cursor() as cur:
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_01'))
        usuario,pdb = cur.fetchone()
        if usuario != usuario_esperado.upper() or usuario in ('SYS','SYSTEM') or pdb=='CDB$ROOT':
            raise ValueError('Destino incorrecto o administrativo; restauracion rechazada.')
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_02'))
        if cur.fetchone()[0] != 0: raise ValueError('El destino debe estar vacio; no se borraron ni reemplazaron objetos.')
        ddl=datos['estructura.aes']
        for tabla in manifiesto['tablas']:
            nombre(tabla['nombre'])
            filas=[f for parte in tabla['partes'] for f in datos[parte]]
            if len(filas)!=tabla['filas'] or sha256(canonico(sorted(_huella_fila(f,tabla['columnas']) for f in filas))).hexdigest()!=tabla['huella_datos']:
                raise ValueError('Los datos no coinciden con el manifiesto.')
        # Toda comprobacion criptografica y de datos precede al primer DDL.
        for sql in ddl['tablas']: cur.execute(_sql_limpio(sql))
        for tabla in manifiesto['tablas']:
            for c in tabla['columnas']:
                if c['identidad']:
                    cur.execute('ALTER TABLE '+nombre(tabla['nombre'])+' MODIFY '+nombre(c['nombre'])+' GENERATED BY DEFAULT AS IDENTITY')
        for tabla in manifiesto['tablas']:
            columnas=[c for c in tabla['columnas'] if not c['virtual']]
            valores=[];tipos={}
            for i,c in enumerate(columnas):
                b=f'p{i}';t=c['tipo']
                if 'TIMESTAMP' in t:
                    fmt='YYYY-MM-DD"T"HH24:MI:SS.FF9'+('TZH:TZM' if 'TIME ZONE' in t else '')
                    valores.append(('TO_TIMESTAMP_TZ' if 'TIME ZONE' in t else 'TO_TIMESTAMP')+f"(:{b},'{fmt}')")
                elif t=='DATE': valores.append(f'''TO_DATE(:{b},'YYYY-MM-DD"T"HH24:MI:SS')''')
                else:
                    valores.append(':'+b)
                    if t in ('CLOB','NCLOB'): tipos[b]=oracledb.DB_TYPE_CLOB
                    elif t=='BLOB': tipos[b]=oracledb.DB_TYPE_BLOB
                    elif t=='NUMBER': tipos[b]=oracledb.DB_TYPE_NUMBER
            sql='INSERT INTO '+nombre(tabla['nombre'])+'('+','.join(nombre(c['nombre']) for c in columnas)+') VALUES('+','.join(valores)+')'
            # Un cursor por tabla evita arrastrar binds tipados de una tabla vacia hacia otra
            # con menos columnas (DPY-4008). No cambiar el formato autenticado del respaldo.
            with conexion.cursor() as cargador:
                cargador.setinputsizes(**tipos)
                for parte in tabla['partes']:
                    if datos[parte]:
                        cargador.executemany(sql,[{f'p{i}':_valor(v,c) for i,(v,c) in enumerate(zip(fila,columnas))} for fila in datos[parte]])
        conexion.commit()
        for tabla in manifiesto['tablas']:
            for c in tabla['columnas']:
                if c['identidad']:
                    incremento=int(c['incremento'])
                    if incremento<=0: raise ValueError('Identidad descendente no soportada.')
                    cur.execute('SELECT NVL(MAX('+nombre(c['nombre'])+'),0) FROM '+nombre(tabla['nombre']))
                    proximo=max(int(c['siguiente_seguro']),int(cur.fetchone()[0])+incremento)
                    generacion=c['generacion']
                    if generacion not in ('ALWAYS','BY DEFAULT'): raise ValueError('Generacion de identidad no soportada.')
                    cur.execute('ALTER TABLE '+nombre(tabla['nombre'])+' MODIFY '+nombre(c['nombre'])+
                                f' GENERATED {generacion} AS IDENTITY (START WITH {proximo} INCREMENT BY {incremento})')
        for grupo in ('indices','foraneas','comentarios','specs','cuerpos','vistas','triggers'):
            for sql in ddl[grupo]:
                # GET_DDL(TRIGGER) incluye un ALTER adicional aun con SQLTERMINATOR=FALSE.
                adicional = None
                if grupo == 'triggers':
                    coincidencia = re.search(r'\n(ALTER TRIGGER "[A-Z][A-Z0-9_$#]*" (?:ENABLE|DISABLE))\s*;?\s*$', sql)
                    if coincidencia:
                        adicional = coincidencia.group(1)
                        sql = sql[:coincidencia.start()]
                cur.execute(_sql_limpio(sql,plsql=grupo in ('specs','cuerpos','triggers')))
                if adicional: cur.execute(adicional)
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_03'))
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_04'))
        invalidos = cur.fetchall()
        if invalidos:
            cur.execute(cargar_sql('base_datos/recuperacion/restaurar_08'))
            raise ValueError('El destino conserva objetos invalidos; no utilizarlo como base activa. ' + repr(invalidos) + ' ' + repr(cur.fetchall()))
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_05'))
        if cur.fetchone()[0]: raise ValueError('Hay errores de compilacion en el destino.')
        if 'inventario_objetos' in manifiesto:
            cur.execute(cargar_sql('compartidas/inventario_objetos'))
            if dict(cur.fetchall()) != manifiesto['inventario_objetos']:
                raise ValueError('El inventario de objetos restaurados difiere del origen.')
        if 'estados_disparadores' in manifiesto:
            cur.execute(cargar_sql('compartidas/estados_disparadores'))
            if dict(cur.fetchall()) != manifiesto['estados_disparadores']:
                raise ValueError('El estado de los disparadores difiere del origen.')
        for tabla in manifiesto['tablas']:
            cur.execute(_consulta(tabla['nombre'],tabla['columnas']))
            huellas=[]
            while True:
                filas=cur.fetchmany(250)
                if not filas: break
                huellas.extend(_huella_fila(f,tabla['columnas']) for f in filas)
            if len(huellas)!=tabla['filas'] or sha256(canonico(sorted(huellas))).hexdigest()!=tabla['huella_datos']:
                raise ValueError('La verificacion posterior de datos fallo: '+tabla['nombre'])
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_06'))
        if cur.fetchone()[0]: raise ValueError('Hay restricciones sin validar en el destino.')
        # La copia de datos no debe resucitar credenciales de sesion ya revocadas despues del respaldo.
        sesiones_revocadas=0
        cur.execute(cargar_sql('base_datos/recuperacion/restaurar_07'))
        if cur.fetchone()[0]:
            cur.execute(cargar_sql('base_datos/recuperacion/restaurar_11'))
            sesiones_revocadas=cur.rowcount
    conexion.commit()
    return {'usuario':usuario,'tablas':len(manifiesto['tablas']),'versiones':manifiesto['versiones'],'verificado':True,'sesiones_revocadas':sesiones_revocadas}
