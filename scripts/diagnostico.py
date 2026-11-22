"""Comprueba el entorno y Oracle sin modificar datos ni mostrar credenciales."""

import argparse
import importlib
import importlib.metadata as metadata
import platform
import ssl
import subprocess
import sys
from urllib.request import urlopen

from _comun import RAIZ, usar_entorno


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-bd', action='store_true')
    parser.add_argument('--url', help='Comprobar HTTPS del servidor local ya iniciado.')
    args = parser.parse_args()
    fallos = []
    print('Python:', platform.python_version(), '| sistema:', platform.system(), platform.machine())
    print('Interprete:', sys.executable)
    for modulo, paquete in [('streamlit', 'streamlit'), ('numpy', 'numpy'), ('pandas', 'pandas'),
                            ('sklearn', 'scikit-learn'), ('dlib', 'dlib-bin'),
                            ('face_recognition_models', 'face_recognition_models'), ('oracledb', 'oracledb'),
                            ('bcrypt', 'bcrypt'), ('zxcvbn', 'zxcvbn'), ('segno', 'segno'), ('PIL', 'pillow'),
                            ('librosa', 'librosa'), ('soundfile', 'soundfile'), ('resemblyzer', 'resemblyzer'),
                            ('webrtcvad', 'webrtcvad'), ('cryptography', 'cryptography')]:
        try:
            importlib.import_module(modulo)
            print('OK', paquete, metadata.version(paquete))
        except Exception as exc:
            fallos.append(paquete)
            print('ERROR', paquete, type(exc).__name__)
    if subprocess.call([sys.executable, '-m', 'pip', 'check'], cwd=RAIZ):
        fallos.append('pip check')
    if not args.sin_bd:
        try:
            from src.base_datos.configuracion import obtener_pool, obtener_conexion
            with obtener_conexion() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT USER, SYS_CONTEXT('USERENV','CON_NAME') FROM dual")
                    print('Oracle:', cur.fetchone())
                    cur.execute('SELECT version FROM versiones_esquema ORDER BY version')
                    versiones = [f[0] for f in cur]
                    print('Versiones del esquema:', versiones)
                    if not {'001', '002', '003', '004', '005', '006', '007', '008', '009'}.issubset(versiones):
                        raise ValueError('Falta alguna version 001–009. Ejecutar scripts/oracle.py migrar.')
                    cur.execute("SELECT COUNT(*) FROM user_objects WHERE object_name='PKG_EXCEPCIONES' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID'")
                    if cur.fetchone()[0] != 2: raise ValueError('Falta PKG_EXCEPCIONES válido.')
                    cur.execute("SELECT COUNT(*) FROM user_objects WHERE status <> 'VALID'")
                    if cur.fetchone()[0]:
                        raise ValueError('Hay objetos invalidos.')
                    cur.execute('SELECT COUNT(*) FROM user_errors')
                    if cur.fetchone()[0]:
                        raise ValueError('Hay errores de compilacion PL/SQL.')
                    cur.execute("SELECT COUNT(*) FROM user_triggers WHERE trigger_name IN ('TRG_ASISTENCIA_AUD','TRG_MATRICULAS_HIST','TRG_PROFESORES_ACTUALIZADO','TRG_ESTUDIANTES_ACTUALIZADO','TRG_MATERIAS_ACTUALIZADO') AND status='ENABLED'")
                    if cur.fetchone()[0] != 5:
                        raise ValueError('Faltan disparadores activos de la version 002.')
                    cur.execute("SELECT COUNT(*) FROM user_triggers WHERE trigger_name IN ('TRG_ASISTENCIA_CLASE','TRG_CLASES_IDENTIDAD') AND status='ENABLED'")
                    if cur.fetchone()[0] != 2:
                        raise ValueError('Faltan disparadores activos de la version 003.')
                    cur.execute("SELECT COUNT(*) FROM user_constraints WHERE constraint_name IN ('UQ_RA_CLASE_ESTUDIANTE','UQ_CLASES_INSTANTE','FK_RA_CLASE_MATERIA') AND status='ENABLED' AND validated='VALIDATED'")
                    if cur.fetchone()[0] != 3:
                        raise ValueError('Faltan restricciones principales de clases 003.')
                    cur.execute("SELECT COUNT(*) FROM user_constraints WHERE constraint_name IN ('CK_RA_ESTADO_DETECCION','CK_RA_DETECCION_COHERENTE') AND status='ENABLED' AND validated='VALIDATED'")
                    if cur.fetchone()[0] != 2:
                        raise ValueError('Faltan restricciones de deteccion 004.')
                    cur.execute("SELECT COUNT(*) FROM user_triggers WHERE trigger_name IN ('TRG_MATRICULA_ACTIVA','TRG_ASISTENCIA_ACTIVA') AND status='ENABLED'")
                    if cur.fetchone()[0] != 2:
                        raise ValueError('Faltan disparadores activos de gestion 005.')
                    cur.execute("SELECT COUNT(*) FROM user_objects WHERE object_name='PKG_GESTION' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID'")
                    if cur.fetchone()[0] != 2:
                        raise ValueError('Falta PKG_GESTION valido.')
                    cur.execute("SELECT COUNT(*) FROM user_objects WHERE object_name='PKG_ADMINISTRACION' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID'")
                    if cur.fetchone()[0] != 2: raise ValueError('Falta PKG_ADMINISTRACION válido.')
                    cur.execute("SELECT COUNT(*) FROM user_objects WHERE object_name='PKG_SESIONES' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID'")
                    if cur.fetchone()[0] != 2: raise ValueError('Falta PKG_SESIONES válido.')
                    cur.execute('SELECT COUNT(*) FROM sesiones_usuario')
                    print('Filas sesiones_usuario:',cur.fetchone()[0])
                    for tabla in ['profesores', 'estudiantes', 'materias', 'materia_estudiantes', 'clases', 'registros_asistencia', 'auditoria_asistencia', 'historial_matriculas', 'eventos_gestion', 'limites_acceso', 'administradores', 'verificacion_estudiantes']:
                        cur.execute('SELECT COUNT(*) FROM ' + tabla)
                        print('Filas', tabla, cur.fetchone()[0])
                    cur.execute('SELECT pkg_asistencia.porcentaje_asistencia(-1) FROM dual')
                    print('Funcion PL/SQL sin registros:', cur.fetchone()[0])
            obtener_pool().close()
            from src.servicios.verificacion_identidad import _clave
            _clave()
            print('Clave privada de identidad: OK (contenido oculto)')
        except Exception as exc:
            fallos.append('Oracle')
            # Los errores de conectividad del driver no incluyen la contrasena.
            print('ERROR Oracle:', exc)
    if args.url:
        try:
            contexto = ssl.create_default_context(cafile=str(RAIZ / '.certs/ca.pem'))
            with urlopen(args.url.rstrip('/') + '/_stcore/health', context=contexto, timeout=10) as respuesta:
                print('HTTPS health:', respuesta.status, respuesta.read().decode())
        except Exception as exc:
            fallos.append('HTTPS')
            print('ERROR HTTPS:', exc)
    raise SystemExit(1 if fallos else 0)


if __name__ == '__main__':
    main()
