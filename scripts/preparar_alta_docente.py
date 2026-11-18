"""Prepara el codigo de autorizacion docente local; nunca lo imprime."""
import json
import secrets
import tomllib
from _comun import RAIZ


def main():
    ruta = RAIZ / '.streamlit/secrets.toml'
    valores = tomllib.loads(ruta.read_text(encoding='utf-8'))
    codigo = valores.get('PROFESOR_CLAVE_ALTA')
    if not codigo:
        codigo = secrets.token_urlsafe(24)
        with ruta.open('a',encoding='utf-8') as f:
            f.write('\nPROFESOR_CLAVE_ALTA = '+json.dumps(codigo)+'\n')
    destino = RAIZ / '.local/ALTA_DOCENTE.md'
    destino.parent.mkdir(exist_ok=True)
    destino.write_text('# Autorización docente local — privado\n\nCódigo para el formulario de alta de profesores:\n\n`'
                       +codigo+'`\n\nNo publicar ni incluir en capturas o repositorios.\n',encoding='utf-8')
    destino.chmod(0o600)
    print('Autorización privada preparada en .local/ALTA_DOCENTE.md; no se mostró su contenido.')


if __name__=='__main__': main()
