"""Plan de retención: conservar 30 días y al menos 7 copias V2 verificadas."""
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import shutil
from _comun import RAIZ, usar_entorno


def main():
    usar_entorno()
    from src.base_datos.recuperacion import verificar, clave_local
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true', help='Eliminar solo las copias candidatas autenticadas; por defecto solo informa.')
    args = parser.parse_args()
    raiz = (RAIZ / '.local' / 'respaldos').resolve()
    clave = clave_local(RAIZ / '.local' / 'clave_respaldos.bin')
    copias = []
    for ruta in raiz.iterdir():
        if ruta.is_symlink() or not ruta.is_dir() or ruta.resolve().parent != raiz: continue
        try:
            manifiesto, _ = verificar(ruta, clave)
            if manifiesto['formato'] != 2 or manifiesto.get('objetos_invalidos_origen'): continue
            fecha = datetime.fromisoformat(manifiesto['creado_en'])
            if fecha.tzinfo is None: raise ValueError('Fecha sin zona horaria.')
            copias.append((fecha, ruta))
        except (OSError, ValueError, KeyError):
            print('Conservado sin cambios (requiere revisión):', ruta.name)
    copias.sort(reverse=True)
    limite = datetime.now(timezone.utc) - timedelta(days=30)
    candidatos = [ruta for fecha, ruta in copias[7:] if fecha < limite]
    for ruta in candidatos:
        # Verificar el destino absoluto inmediatamente antes de cada eliminación recursiva.
        if ruta.is_symlink() or ruta.resolve().parent != raiz or raiz != (RAIZ / '.local' / 'respaldos').resolve():
            raise ValueError('Destino fuera de la carpeta de respaldos.')
        verificar(ruta, clave)
        if args.aplicar: shutil.rmtree(ruta)
        print('Eliminado:' if args.aplicar else 'Candidato:', ruta.name)
    print('Copias V2 verificadas:', len(copias), '| Candidatas:', len(candidatos), '| Modo:', 'aplicado' if args.aplicar else 'solo consulta')


if __name__ == '__main__': main()
