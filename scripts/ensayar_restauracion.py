"""Ensayo local de recuperación: dos esquemas temporales, nunca el esquema activo."""
import json
import re
import secrets
import shutil
import time
from hashlib import sha256
from uuid import uuid4

from _comun import RAIZ, usar_entorno
from preparar_oracle import ejecutar_sqlplus


def main():
    usar_entorno()
    import oracledb
    from src.configuracion import obtener_configuracion
    from src.base_datos.recuperacion import respaldar, restaurar, verificar, clave_local
    dsn = obtener_configuracion('ORACLE_DSN', 'localhost:1521/XEPDB1')
    if not re.fullmatch(r'(localhost|127\.0\.0\.1):\d+/XEPDB1', dsn, re.I):
        raise ValueError('Este ensayo automático solo admite Oracle local/XEPDB1.')
    sqlplus = shutil.which('sqlplus')
    if not sqlplus: raise ValueError('SQLPlus no está disponible.')
    nonce = uuid4().hex[:12].upper()
    usuarios = ['UPC_RT_' + nonce + sufijo for sufijo in ('_S', '_D')]
    claves = ['Rt_' + secrets.token_hex(12) for _ in usuarios]
    creados = []
    destino = RAIZ / '.local' / 'ensayos' / nonce
    destino.mkdir(parents=True, exist_ok=False)
    informe = {'ensayo': nonce, 'esquemas_temporales': usuarios, 'estado': 'INICIADO'}
    cabecera = ('SET ECHO OFF\nSET VERIFY OFF\nSET DEFINE OFF\nWHENEVER OSERROR EXIT FAILURE\n'
                'WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK\n')
    def admin(sql):
        ejecutar_sqlplus(sqlplus, cabecera + 'CONNECT / AS SYSDBA\nALTER SESSION SET CONTAINER=XEPDB1;\n' + sql + '\nEXIT SUCCESS\n', claves)
    try:
        for usuario, clave in zip(usuarios, claves):
            # Nombre aleatorio exclusivo y preflight. DROP solo para cuentas creadas aquí.
            admin(f"DECLARE n NUMBER; BEGIN SELECT COUNT(*) INTO n FROM dba_users WHERE username='{usuario}'; IF n<>0 THEN RAISE_APPLICATION_ERROR(-20991,'La cuenta temporal ya existe.'); END IF; END;\n/\nCREATE USER {usuario} IDENTIFIED BY \"{clave}\" QUOTA 100M ON USERS;")
            creados.append(usuario)
            admin(f'GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, CREATE SEQUENCE, CREATE TRIGGER TO {usuario};')
        instalacion = (RAIZ / 'sql' / 'instalar.sql').read_text(encoding='utf-8')
        instalacion = instalacion.replace('@sql/migraciones/005_gestion.sql', '')
        instalacion = instalacion.replace('@sql/migraciones/006_administracion.sql', '')
        instalacion = instalacion.replace('@sql/migraciones/007_sesiones.sql', '')
        instalacion = instalacion.replace('@sql/migraciones/008_excepciones.sql', '')
        conectar = cabecera + f'CONNECT {usuarios[0]}@"//{dsn}"\n{claves[0]}\n'
        ejecutar_sqlplus(sqlplus, conectar + instalacion + '\nEXIT SUCCESS\n', claves)
        # Una actualización real 004 -> 005 con historia previa, sin recrear tablas.
        with oracledb.connect(user=usuarios[0], password=claves[0], dsn=dsn) as legado:
            with legado.cursor() as cur:
                cur.execute('''DECLARE p NUMBER; e NUMBER; m NUMBER; BEGIN
                    INSERT INTO profesores(usuario,contrasena,nombre) VALUES('legado','FIXTURE','Docente anterior') RETURNING profesor_id INTO p;
                    INSERT INTO estudiantes(nombre) VALUES('Estudiante anterior sin código') RETURNING estudiante_id INTO e;
                    INSERT INTO materias(codigo_materia,nombre,profesor_id) VALUES('LEGADO','Historia anterior',p) RETURNING materia_id INTO m;
                    pkg_auditoria.establecer_contexto('PROFESOR',p,'Ensayo previo a 005');
                    pkg_asistencia.matricular_estudiante(e,m);
                    pkg_asistencia.registrar_asistencia(m,e,SYSTIMESTAMP,1);
                    END;''')
                historicas = ['PROFESORES', 'ESTUDIANTES', 'MATERIAS', 'CLASES', 'REGISTROS_ASISTENCIA', 'HISTORIAL_MATRICULAS']
                def conteos():
                    resultado = {}
                    for tabla in historicas:
                        cur.execute('SELECT COUNT(*) FROM ' + tabla); resultado[tabla] = cur.fetchone()[0]
                    return resultado
                anteriores = conteos()
                legado.commit()
        ejecutar_sqlplus(sqlplus, conectar + '@sql/migraciones/005_gestion.sql\nEXIT SUCCESS\n', claves)
        with oracledb.connect(user=usuarios[0], password=claves[0], dsn=dsn) as legado, legado.cursor() as cur:
            assert conteos() == anteriores
            cur.execute("SELECT codigo_institucional FROM estudiantes WHERE nombre='Estudiante anterior sin código'")
            assert cur.fetchone()[0] is None
            informe['migracion_004_005_con_historial'] = anteriores
        ejecutar_sqlplus(sqlplus, conectar + '@sql/migraciones/006_administracion.sql\nEXIT SUCCESS\n', claves)
        informe['migracion_006'] = True
        ejecutar_sqlplus(sqlplus, conectar + '@sql/migraciones/007_sesiones.sql\nEXIT SUCCESS\n', claves)
        informe['migracion_007'] = True
        ejecutar_sqlplus(sqlplus, conectar + '@sql/migraciones/008_excepciones.sql\nEXIT SUCCESS\n', claves)
        informe['migracion_008'] = True
        with oracledb.connect(user=usuarios[0], password=claves[0], dsn=dsn) as origen:
            with origen.cursor() as cur:
                def insertar(sql, **kw):
                    salida = cur.var(oracledb.NUMBER)
                    cur.execute(sql + ' RETURNING ' + kw.pop('columna') + ' INTO :salida', salida=salida, **kw)
                    return int(salida.getvalue()[0])
                profesor = insertar("INSERT INTO profesores(usuario,contrasena,nombre) VALUES('ensayo','NO_ES_UNA_CLAVE_REAL','Docente Ñandú')", columna='profesor_id')
                cur.callproc('pkg_sesiones.abrir',['PROFESOR',profesor,sha256(secrets.token_bytes(32)).hexdigest()])
                cur.callproc('pkg_auditoria.establecer_contexto', ['PROFESOR', profesor, 'Ensayo sintético'])
                alumnos = []
                for i in range(2):
                    cur.setinputsizes(f=oracledb.DB_TYPE_CLOB, v=oracledb.DB_TYPE_CLOB)
                    alumnos.append(insertar('INSERT INTO estudiantes(nombre,codigo_institucional,embedding_facial,embedding_voz) VALUES(:n,:c,:f,:v)',
                        columna='estudiante_id', n='Alumno sintético ' + str(i), c='ENSAYO-' + str(i),
                        f=json.dumps([0.1] * 128) if i == 0 else None, v=json.dumps([0.0625] * 256) if i == 0 else None))
                materia = insertar("INSERT INTO materias(codigo_materia,nombre,seccion,profesor_id) VALUES('ENSAYO','Recuperación áéíóú','Ñ',:p)", columna='materia_id', p=profesor)
                for alumno in alumnos: cur.callproc('pkg_gestion.matricular', [alumno, materia])
                salida = cur.var(oracledb.NUMBER)
                cur.execute('''BEGIN pkg_clases.abrir_clase(:m,TO_TIMESTAMP_TZ('2026-11-11T08:00:00.123456-05:00','YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),:c); END;''', m=materia, c=salida)
                clase = int(salida.getvalue())
                carga = json.dumps([{'estudiante_id': a, 'detectado': 1 if i == 0 else None,
                    'estado_deteccion': 'PRESENTE' if i == 0 else 'SIN_MUESTRA', 'presente': 1 if i == 0 else 0,
                    'motivo': None if i == 0 else 'Resolución manual de ensayo', 'fecha_hora': '2026-11-11T08:05:00.123456-05:00'} for i, a in enumerate(alumnos)], ensure_ascii=False)
                cur.setinputsizes(carga=oracledb.DB_TYPE_CLOB)
                cur.execute('BEGIN pkg_clases.confirmar_clase(:c,:k,:o,:carga,:n); END;', c=clase, k=uuid4().hex, o='FACIAL', carga=carga, n=cur.var(oracledb.NUMBER))
                cur.execute('SELECT asistencia_id FROM registros_asistencia WHERE estudiante_id=:e', e=alumnos[0])
                cur.callproc('pkg_asistencia.corregir_asistencia', [cur.fetchone()[0], 0, 'Corrección sintética de recuperación'])
                cur.callproc('pkg_gestion.retirar', [alumnos[1], materia, 'Retiro de ensayo; conservar historia'])
                cur.callproc('pkg_gestion.archivar_materia', [materia, 'Archivo de ensayo'])
                # Verificacion 008 con datos sinteticos: documento HMAC ficticio, hash bcrypt y estado.
                import bcrypt
                aprobador = insertar("INSERT INTO administradores(usuario,nombre,contrasena) VALUES('ensayo008','Administrador sintetico','FIXTURE')", columna='administrador_id')
                cur.callproc('pkg_auditoria.establecer_contexto', ['ADMINISTRADOR', aprobador, 'Ensayo sintetico 008'])
                credencial = bcrypt.hashpw(b'PruebaTemporalDeRestauracion!', bcrypt.gensalt(rounds=4)).decode()
                for i, alumno in enumerate(alumnos):
                    identidad = cur.var(oracledb.NUMBER); identidad.setvalue(0, alumno)
                    cur.callproc('pkg_excepciones.autorizar', [identidad,None,None,sha256(('documento-sintetico-'+str(i)).encode()).hexdigest(),
                        'CC','0000',credencial,'TECNICA','ENSAYO-008',30,0])
                cur.execute("UPDATE verificacion_estudiantes SET estado_verificacion='EXCEPCIONAL',verificado_en=SYSTIMESTAMP WHERE estudiante_id=:e", e=alumnos[1])
                informe['excepciones_sinteticas_origen'] = 2
                borrado = insertar("INSERT INTO estudiantes(nombre) VALUES('Identidad eliminada de ensayo')", columna='estudiante_id')
                cur.execute('DELETE FROM estudiantes WHERE estudiante_id=:e', e=borrado)
                origen.commit()
            clave = clave_local(RAIZ / '.local' / 'clave_respaldos.bin', crear=True)
            # XE puede rechazar una lectura consistente iniciada en el mismo segundo que el ultimo DDL.
            time.sleep(1.1)
            copia = respaldar(origen, destino / 'respaldo', clave)
        manifiesto, _ = verificar(copia, clave)
        with oracledb.connect(user=usuarios[1], password=claves[1], dsn=dsn) as receptor:
            try:
                restaurar(copia, bytes(32), receptor, usuario_esperado=usuarios[1])
            except ValueError: informe['clave_incorrecta_rechazada'] = True
            else: raise AssertionError('Se aceptó una clave incorrecta.')
            ruta_manifiesto = copia / 'manifiesto.json'
            original_manifiesto = ruta_manifiesto.read_bytes()
            try:
                alterado = dict(manifiesto)
                alterado['versiones'] = ['INVENTADA']
                ruta_manifiesto.write_text(json.dumps(alterado), encoding='utf-8')
                try: restaurar(copia, clave, receptor, usuario_esperado=usuarios[1])
                except ValueError: informe['manifiesto_alterado_rechazado'] = True
                else: raise AssertionError('Se aceptó un manifiesto alterado.')
            finally: ruta_manifiesto.write_bytes(original_manifiesto)
            with receptor.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM user_objects'); assert cur.fetchone()[0] == 0
            archivo = copia / next(iter(manifiesto['archivos']))
            original = archivo.read_bytes()
            try:
                archivo.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
                try: restaurar(copia, clave, receptor, usuario_esperado=usuarios[1])
                except ValueError: informe['alteracion_rechazada'] = True
                else: raise AssertionError('Se aceptó una copia alterada.')
            finally: archivo.write_bytes(original)
            informe['restauracion'] = restaurar(copia, clave, receptor, usuario_esperado=usuarios[1])
            assert informe['restauracion']['sesiones_revocadas']==1
            informe['sesiones_restauradas_revocadas']=True
            with receptor.cursor() as cur:
                cur.execute('SELECT estado_verificacion,excepcion_activa,documento_final FROM verificacion_estudiantes ORDER BY estudiante_id')
                assert cur.fetchall()==[('PENDIENTE',1,'0000'),('EXCEPCIONAL',1,'0000')]
                informe['estados_excepcionales_restaurados']=True
                siguiente = cur.var(oracledb.NUMBER)
                cur.execute("INSERT INTO estudiantes(nombre) VALUES('Prueba de secuencia') RETURNING estudiante_id INTO :id", id=siguiente)
                metadata = next(t for t in manifiesto['tablas'] if t['nombre'] == 'ESTUDIANTES')
                minimo = int(next(c for c in metadata['columnas'] if c['identidad'])['siguiente_seguro'])
                assert int(siguiente.getvalue()[0]) >= minimo and int(siguiente.getvalue()[0]) > borrado
                receptor.rollback()
                informe['identidad_no_reutilizada'] = True
            try: restaurar(copia, clave, receptor, usuario_esperado=usuarios[1])
            except ValueError: informe['destino_ocupado_rechazado'] = True
            else: raise AssertionError('Se aceptó un destino ocupado.')
        informe['filas_por_tabla'] = {t['nombre']: t['filas'] for t in manifiesto['tablas']}
        informe['estado'] = 'CORRECTO'
    finally:
        eliminados = []
        for usuario in reversed(creados):
            if not re.fullmatch('UPC_RT_' + nonce + r'_[SD]', usuario): raise ValueError('Limpieza fuera del ensayo rechazada.')
            admin(f'DROP USER {usuario} CASCADE;')
            eliminados.append(usuario)
        informe['temporales_eliminados'] = eliminados
        (destino / 'resultado.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Ensayo verificado:', (destino / 'resultado.json').relative_to(RAIZ))


if __name__ == '__main__': main()
