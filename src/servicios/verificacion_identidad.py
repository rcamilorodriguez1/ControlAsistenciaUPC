"""Pruebas de acceso de corta vida; el resultado se confirma junto con la sesión en Oracle.

El documento es un identificador: una excepción requiere aprobación y contraseña.
La política facial existente exige un factor; la voz no se cuenta como prueba de acceso.
"""
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
import hmac
import json
import logging
from pathlib import Path
import re
import secrets
import time

import bcrypt
import oracledb

from src.base_datos.configuracion import obtener_conexion
from src.configuracion import obtener_configuracion
from src.servicios.autenticacion import exigir_acceso_disponible
from src.base_datos.consultas import cargar_sql
from src.base_datos.esquema import esquema_propietario
from src.utilidades.claves_identidad import leer_clave

_logger = logging.getLogger(__name__)
TIPOS_DOCUMENTO = ('CC', 'TI', 'CE', 'PA')
CATEGORIAS = ('FISICA', 'MEDICA', 'TECNICA', 'ADMINISTRATIVA')
ESTADOS = {'PENDIENTE': 'Verificación pendiente',
           'BIOMETRICA_COMPLETA': 'Verificación biométrica completa',
           'EXCEPCIONAL': 'Verificación excepcional / biometría incompleta'}
FACTORES_REQUERIDOS = 1  # Política real actual: rostro. No incluye plantillas simplemente almacenadas.
VIGENCIA_PRUEBA = 90


def ruta_clave():
    raiz = Path(__file__).resolve().parents[2]
    ruta = Path(obtener_configuracion('IDENTIDAD_CLAVE_RUTA', str(raiz / '.local/claves/identidad.key')))
    return ruta if ruta.is_absolute() else raiz / ruta


def preparar_clave():
    """Provisionamiento explícito; nunca sustituye una clave perdida con documentos registrados."""
    from src.base_datos.recuperacion import clave_local
    ruta = ruta_clave()
    if not ruta.exists():
        if obtener_configuracion('IDENTIDAD_CLAVE_FORMATO', 'binario') != 'binario':
            raise ValueError('Falta el archivo de la clave de identidad original; restaura su copia privada.')
        with obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute(cargar_sql('servicios/verificacion_identidad/preparar_clave_01'), esquema=esquema_propietario())
            if cur.fetchone()[0]:
                cur.execute(cargar_sql('servicios/verificacion_identidad/preparar_clave_02'))
                if cur.fetchone()[0]:
                    raise ValueError('Falta la clave de identidad original. Restáurala desde su copia privada.')
        try:
            clave_local(ruta, crear=True)
        except FileExistsError:
            pass
    _clave()


def _clave():
    try:
        return leer_clave(ruta_clave(), obtener_configuracion('IDENTIDAD_CLAVE_FORMATO', 'binario'))
    except (OSError, ValueError):
        raise ValueError('No está preparada la clave de identidad. Ejecuta scripts/preparar_identidad.py o restaura la copia original.') from None


def normalizar_documento(tipo, numero):
    if tipo not in TIPOS_DOCUMENTO or not isinstance(numero, str) or len(numero) > 40:
        raise ValueError('Documento no válido.')
    numero = re.sub(r'[ .\-]', '', numero.strip()).upper()
    patron = r'[A-Z0-9]{5,20}' if tipo == 'PA' else r'[0-9]{5,20}'
    if not re.fullmatch(patron, numero, flags=re.ASCII):
        raise ValueError('Revisa el tipo y el número de documento.')
    return numero


def huella_documento(tipo, numero):
    numero = normalizar_documento(tipo, numero)
    return hmac.new(_clave(), ('documento:v1:' + tipo + ':' + numero).encode(), sha256).hexdigest(), numero[-4:]


def _evento(cur, estudiante_id, accion, motivo):
    cur.execute(cargar_sql('servicios/verificacion_identidad/evento_01'), i=estudiante_id or 0, a=accion, m=motivo)


def registrar_fallo_biometrico(causa='NO_COINCIDE', *, metodo='BIOMETRIA', estudiante_id=0):
    # Lista cerrada: nunca almacenar imágenes, nombres, documentos ni mensajes del motor.
    if causa not in ('NO_COINCIDE', 'MUESTRA_INVALIDA', 'ERROR_TECNICO', 'PRUEBA_RECHAZADA', 'DOCUMENTO_INVALIDO'):
        causa = 'MUESTRA_INVALIDA'
    if metodo not in ('BIOMETRIA', 'EXCEPCION'):
        metodo = 'BIOMETRIA'
    try:
        with obtener_conexion() as conn, conn.cursor() as cur:
            _evento(cur, estudiante_id, 'VALIDACION_FALLIDA', 'Método: ' + metodo + '; resultado: ' + causa)
            conn.commit()
    except Exception:
        _logger.error('No se pudo persistir VALIDACION_FALLIDA; causa=%s', causa)


@dataclass(frozen=True)
class PruebaIdentidad:
    estudiante_id: int
    metodo: str
    version: int
    emitida: float
    nonce: str
    credencial: str = ''
    firma: str = ''


def _firma(prueba):
    campos = [prueba.estudiante_id, prueba.metodo, prueba.version, prueba.emitida, prueba.nonce, prueba.credencial]
    contenido = json.dumps(campos, separators=(',', ':'), ensure_ascii=True).encode()
    return hmac.new(_clave(), b'prueba:v1:' + contenido, sha256).hexdigest()


def _emitir(estudiante_id, metodo, version, credencial=''):
    prueba = PruebaIdentidad(int(estudiante_id), metodo, int(version), time.time(), secrets.token_hex(16), credencial)
    return replace(prueba, firma=_firma(prueba))


def _validar_prueba(prueba, estudiante_id):
    if not isinstance(prueba, PruebaIdentidad) or prueba.estudiante_id != estudiante_id or \
            prueba.metodo not in ('BIOMETRIA', 'EXCEPCION') or not 0 <= time.time() - prueba.emitida <= VIGENCIA_PRUEBA or \
            not hmac.compare_digest(prueba.firma, _firma(prueba)):
        raise PermissionError('Repite la verificación de identidad para iniciar sesión.')


def acreditar_biometria(perfil):
    """Solo llamar después de una coincidencia facial o alta con rostro validado en servidor."""
    exigir_acceso_disponible()
    identificador = perfil['estudiante_id']
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(cargar_sql('servicios/verificacion_identidad/acreditar_biometria_01'), i=identificador)
        fila = cur.fetchone()
        if not fila or fila[:2] != (1, 1):
            registrar_fallo_biometrico('PRUEBA_RECHAZADA', estudiante_id=identificador)
            raise PermissionError('No se pudo acreditar el acceso facial de esta cuenta.')
    return dict(perfil, _prueba_identidad=_emitir(identificador, 'BIOMETRIA', fila[2]))


@lru_cache(maxsize=1)
def _hash_simulado():
    return bcrypt.hashpw(b'identidad-sin-cuenta', bcrypt.gensalt()).decode()


def autenticar_excepcion(tipo, numero, contrasena):
    exigir_acceso_disponible()
    try:
        normalizar_documento(tipo, numero)
    except ValueError:
        registrar_fallo_biometrico('DOCUMENTO_INVALIDO', metodo='EXCEPCION')
        return None
    huella, _ = huella_documento(tipo, numero)
    limite = sha256(('excepcion:' + huella).encode()).hexdigest()
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(cargar_sql('compartidas/limpiar_limites_expirados'))
        try:
            cur.execute(cargar_sql('compartidas/crear_limite'), c=limite)
        except oracledb.IntegrityError as exc:
            if exc.args[0].code != 1:
                raise
        cur.execute(cargar_sql('servicios/verificacion_identidad/autenticar_excepcion_02'), c=limite)
        intentos, bloqueado, expirada = cur.fetchone()
        cur.execute(cargar_sql('servicios/verificacion_identidad/autenticar_excepcion_03'), d=huella)
        fila = cur.fetchone()
        valida = isinstance(contrasena, str) and 1 <= len(contrasena.encode('utf-8')) <= 72 and '\x00' not in contrasena
        # Comparación también para cuentas desconocidas, revocadas o bloqueadas.
        comparacion = bcrypt.checkpw(contrasena.encode() if valida else b'invalida',
            (fila[3] if fila and fila[3] else _hash_simulado()).encode())
        correcto = bool(valida and comparacion and fila and fila[5] and not bloqueado)
        if correcto:
            prueba = _emitir(fila[0], 'EXCEPCION', fila[4], fila[3])
            cur.execute(cargar_sql('compartidas/limpiar_limite'), c=limite)
            _evento(cur, fila[0], 'CREDENCIAL_VALIDADA', 'Método: EXCEPCION; pendiente de apertura de sesión.')
        else:
            if not bloqueado:
                cur.execute(cargar_sql('servicios/verificacion_identidad/autenticar_excepcion_06'),
                    n=(0 if expirada else intentos)+1, e=expirada, c=limite)
            _evento(cur, fila[0] if fila else 0, 'VALIDACION_FALLIDA',
                    'Método: EXCEPCION; resultado: ' + ('LIMITE_INTENTOS' if bloqueado else 'NO_VALIDADA'))
        conn.commit()
    if not correcto:
        return None
    return {'estudiante_id': fila[0], 'nombre': fila[1], 'codigo_institucional': fila[2], '_prueba_identidad': prueba}


def confirmar_en_conexion(conn, estudiante_id, prueba):
    """Después de bloquear SESIONES_USUARIO y antes de commit. No hace commits propios."""
    _validar_prueba(prueba, estudiante_id)
    with conn.cursor() as cur:
        try:
            cur.execute(cargar_sql('servicios/verificacion_identidad/confirmar_en_conexion_04'), i=estudiante_id)
        except oracledb.IntegrityError as exc:
            if exc.args[0].code != 1:
                raise
        cur.execute(cargar_sql('servicios/verificacion_identidad/confirmar_en_conexion_01'), i=estudiante_id)
        version, clave, activa, vigente = cur.fetchone()
        cur.execute(cargar_sql('servicios/verificacion_identidad/confirmar_en_conexion_02'), i=estudiante_id)
        cuenta = cur.fetchone()
        if version != prueba.version or not cuenta or cuenta[0] != 1:
            raise PermissionError('La cuenta o su autorización cambiaron. Repite la validación.')
        if prueba.metodo == 'EXCEPCION':
            if not activa or not vigente or not clave or not hmac.compare_digest(clave, prueba.credencial):
                raise PermissionError('La excepción ya no está vigente. Contacta con Gestión académica.')
            estado, factores = 'EXCEPCIONAL', 0
        else:
            if cuenta[1] != 1:
                raise PermissionError('La cuenta ya no tiene una muestra facial disponible.')
            estado, factores = 'BIOMETRICA_COMPLETA', FACTORES_REQUERIDOS
        # Prueba de un solo uso. La versión también invalida pruebas concurrentes anteriores.
        cur.execute(cargar_sql('servicios/verificacion_identidad/confirmar_en_conexion_03'), e=estado, f=factores, r=FACTORES_REQUERIDOS, i=estudiante_id)
        _evento(cur, estudiante_id, 'ACCESO_VERIFICADO', 'Método: ' + prueba.metodo + '; estado: ' + estado +
                '; factores comprobados: ' + str(factores) + '; requeridos: ' + str(FACTORES_REQUERIDOS))
