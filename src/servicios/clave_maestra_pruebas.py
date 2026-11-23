"""Clave temporal del ensayo académico; deshabilitada sin secreto y fecha válidos."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import re
import secrets

from src.configuracion import obtener_configuracion


@dataclass(frozen=True, repr=False)
class ConfiguracionPruebas:
    huella: bytes
    hasta: datetime

    @property
    def marca(self):
        return hmac.new(self.huella, self.hasta.isoformat().encode(), sha256).hexdigest()

    def coincide(self, clave):
        return (isinstance(clave, str) and 12 <= len(clave.encode('utf-8')) <= 72 and
                '\x00' not in clave and hmac.compare_digest(self.huella, sha256(clave.encode()).digest()))

    def firma(self, actor_id, vence, nonce):
        contenido = f'PRUEBA_ACADEMICA:{actor_id}:{vence}:{nonce}:{self.marca}'
        return hmac.new(self.huella, contenido.encode(), sha256).hexdigest()


def configuracion_pruebas():
    clave = obtener_configuracion('ESTUDIANTE_CLAVE_MAESTRA')
    fecha = obtener_configuracion('ESTUDIANTE_CLAVE_MAESTRA_HASTA')
    if not isinstance(clave, str) or not 12 <= len(clave.encode('utf-8')) <= 72 or '\x00' in clave:
        return None
    try:
        hasta = datetime.fromisoformat(fecha)
        if hasta.tzinfo is None or datetime.now(timezone.utc) >= hasta:
            return None
    except (TypeError, ValueError):
        return None
    return ConfiguracionPruebas(sha256(clave.encode()).digest(), hasta.astimezone(timezone.utc))


def emitir_token_pruebas(actor_id):
    config = configuracion_pruebas()
    if config is None:
        raise PermissionError('El modo académico de prueba ya no está disponible.')
    vence = str(int(config.hasta.timestamp()))
    nonce = secrets.token_urlsafe(16)
    return '.'.join(('prueba', vence, nonce, config.firma(actor_id, vence, nonce)))


def validar_token_pruebas(rol, actor_id, token):
    config = configuracion_pruebas()
    if rol != 'estudiante' or config is None:
        return False
    partes = token.split('.')
    if len(partes) != 4:
        return False
    prefijo, vence, nonce, firma = partes
    if (prefijo != 'prueba' or not re.fullmatch(r'[0-9]{1,11}', vence) or
            not re.fullmatch(r'[A-Za-z0-9_-]{22}', nonce) or not re.fullmatch(r'[a-f0-9]{64}', firma)):
        return False
    if datetime.now(timezone.utc).timestamp() >= int(vence) or int(vence) > config.hasta.timestamp():
        return False
    return hmac.compare_digest(firma, config.firma(actor_id, vence, nonce))
