"""Estimación local de fortaleza: no conserva ni devuelve la contraseña evaluada."""
from dataclasses import dataclass
import re
from threading import Lock

from src.servicios.validaciones import clave as validar_formato

NIVELES = ('Muy débil', 'Débil', 'Moderada', 'Fuerte', 'Muy fuerte')
_candado = Lock()
_ausente = object()
_comunes = ('contraseña', 'contrasena', 'bienvenido', 'administrador', 'usuario',
            'profesor', 'docente', 'asistencia', 'universidad', 'cesar', 'upc')


@dataclass(frozen=True)
class FortalezaClave:
    puntuacion: int | None
    etiqueta: str
    consejos: tuple[str, ...]
    formato_valido: bool


def evaluar_clave(contrasena, *, usuario='', nombre=''):
    if not isinstance(contrasena, str): raise ValueError('Se requiere texto para evaluar la contraseña.')
    if not contrasena:
        return FortalezaClave(None, 'Sin evaluar', ('Prueba una frase larga con palabras poco relacionadas.',), False)
    try:
        validar_formato(contrasena)
        formato_valido = True
    except ValueError:
        formato_valido = False
    # Acotar antes de invocar el estimador y evitar cálculos sobre entradas no admitidas.
    if '\x00' in contrasena or len(contrasena.encode('utf-8', errors='replace')) > 72:
        return FortalezaClave(None, 'No válida', ('La contraseña admite como máximo 72 bytes UTF-8 y no puede contener caracteres nulos.',), False)
    from zxcvbn import zxcvbn, matching
    personales = []
    for valor in (usuario, nombre):
        if not isinstance(valor, str): continue
        partes = re.findall(r'\w+', valor)
        personales.extend(p for p in [valor, ''.join(partes), *partes] if len(p) >= 3)
    # La biblioteca modifica un diccionario global. Aislar cada evaluación y eliminar
    # los términos personales al terminar, incluso si el estimador falla.
    with _candado:
        anterior = matching.RANKED_DICTIONARIES.get('user_inputs', _ausente)
        try:
            resultado = zxcvbn(contrasena, user_inputs=[*_comunes, *personales])
        finally:
            if anterior is _ausente: matching.RANKED_DICTIONARIES.pop('user_inputs', None)
            else: matching.RANKED_DICTIONARIES['user_inputs'] = anterior
    puntuacion = int(resultado['score'])
    consejos = []
    if not formato_valido: consejos.append('Todavía no cumple el mínimo de 8 bytes UTF-8.')
    if puntuacion < 3:
        patrones = {parte['pattern'] for parte in resultado['sequence']}
        if any(p.get('dictionary_name') == 'user_inputs' for p in resultado['sequence']):
            consejos.append('Evita tu nombre, tu usuario y palabras del proyecto.')
        if 'repeat' in patrones: consejos.append('Evita repetir caracteres o palabras.')
        if patrones & {'sequence', 'spatial'}: consejos.append('Evita secuencias y recorridos del teclado.')
        if patrones & {'date', 'regex'}: consejos.append('Evita fechas y años predecibles.')
        consejos.append('Añade palabras poco relacionadas; cambiar letras por símbolos no basta.')
    return FortalezaClave(puntuacion, NIVELES[puntuacion], tuple(consejos[:3]), formato_valido)
