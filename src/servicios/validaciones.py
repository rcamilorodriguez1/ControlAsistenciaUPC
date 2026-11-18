import re
import unicodedata


def texto(valor, campo, limite, *, opcional=False):
    if valor is None and opcional:
        return None
    if not isinstance(valor, str):
        raise ValueError(f'{campo}: se requiere texto.')
    valor = unicodedata.normalize('NFC', valor).strip()
    if not valor and opcional:
        return None
    if not 1 <= len(valor) <= limite or any(unicodedata.category(c).startswith('C') for c in valor):
        raise ValueError(f'{campo}: usa entre 1 y {limite} caracteres sin controles.')
    return valor


def codigo(valor, campo='Código', limite=50):
    valor = texto(valor, campo, limite).upper()
    if len(valor) > limite or not re.fullmatch(r'[A-Z0-9][A-Z0-9_.-]*', valor):
        raise ValueError(f'{campo}: usa letras, números, punto, guion o guion bajo.')
    return valor


def usuario(valor):
    return codigo(valor, 'Usuario', 100).lower()


def clave(valor):
    if not isinstance(valor, str) or not 8 <= len(valor.encode('utf-8')) <= 72 or '\x00' in valor:
        raise ValueError('La contraseña debe tener entre 8 y 72 bytes UTF-8, sin caracteres nulos.')
    return valor
