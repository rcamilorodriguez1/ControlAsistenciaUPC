from urllib.parse import urlencode, urlsplit

from src.configuracion import obtener_configuracion

URL_APP_PREDETERMINADA = "https://localhost:8501"


def crear_enlace_union(codigo_materia, url_base=None):
    url_base = (url_base or obtener_configuracion("APP_BASE_URL", URL_APP_PREDETERMINADA)).strip().rstrip("/")
    try:
        partes_url = urlsplit(url_base)
        puerto = partes_url.port
    except ValueError as exc:
        raise ValueError("APP_BASE_URL contiene un host o puerto inválido.") from exc

    if (
        partes_url.scheme not in {"http", "https"}
        or not partes_url.netloc
        or not partes_url.hostname
        or partes_url.username is not None
        or partes_url.password is not None
        or puerto == 0
        or partes_url.query
        or partes_url.fragment
        or any(c.isspace() for c in url_base)
    ):
        raise ValueError("APP_BASE_URL debe ser una URL absoluta http:// o https://, sin credenciales, espacios, consulta ni fragmento.")

    return f"{url_base}/?{urlencode({'join-code': codigo_materia})}"
