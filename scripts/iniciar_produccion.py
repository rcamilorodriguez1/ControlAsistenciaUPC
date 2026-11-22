"""Arranque detrás del proxy HTTPS público. --comprobar no inicia el servidor."""
import argparse
import os

from _comun import usar_entorno


def main():
    usar_entorno()
    from src.servicios.despliegue import validar_configuracion, comprobar_base, comando_streamlit
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comprobar', action='store_true')
    parser.add_argument('--sin-bd', action='store_true', help='Solo configuración; requiere --comprobar.')
    args = parser.parse_args()
    if args.sin_bd and not args.comprobar:
        parser.error('--sin-bd requiere --comprobar; no permite iniciar sin verificar Oracle.')
    try:
        host = validar_configuracion()
        if not args.sin_bd:
            comprobar_base()
    except ValueError as exc:
        # Nuestros errores contienen nombres de opciones, nunca sus valores privados.
        raise SystemExit(str(exc)) from None
    except Exception as exc:
        raise SystemExit('No se pudo comprobar el despliegue (' + type(exc).__name__ + '). Revisa conectividad y permisos Oracle.') from None
    print('Configuración de producción comprobada' + ('; Oracle pendiente.' if args.sin_bd else '; Oracle y permisos comprobados.'), flush=True)
    if not args.comprobar:
        comando = comando_streamlit(host)
        os.execv(comando[0], comando)


if __name__ == '__main__':
    main()
