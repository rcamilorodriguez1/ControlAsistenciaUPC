"""Verifica copias y restaura en un usuario Oracle VACIO; nunca borra el destino."""
import argparse
import getpass
import json
import os
from pathlib import Path

from _comun import RAIZ, usar_entorno


def main():
    usar_entorno()
    import oracledb
    from src.configuracion import obtener_configuracion
    from src.base_datos.recuperacion import verificar, restaurar, clave_local
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('respaldo',type=Path)
    parser.add_argument('--usuario-destino')
    parser.add_argument('--dsn',default=obtener_configuracion('ORACLE_DSN','localhost:1521/XEPDB1'))
    parser.add_argument('--clave-respaldo',type=Path,default=RAIZ/'.local/clave_respaldos.bin')
    parser.add_argument('--solo-verificar',action='store_true')
    args=parser.parse_args()
    manifiesto=json.loads((args.respaldo/'manifiesto.json').read_text(encoding='utf-8'))
    clave=clave_local(args.clave_respaldo) if manifiesto.get('formato')==2 else None
    manifiesto,_=verificar(args.respaldo,clave)
    if args.solo_verificar:
        print('Copia integra. Formato:',manifiesto['formato'],'Versiones:',manifiesto['versiones'],
              'Tablas:',len(manifiesto['tablas']))
        if manifiesto['formato']==1: print('Copia antigua sin autenticacion: solo inspeccion automatica; no se ejecuta su DDL.')
        return
    if not args.usuario_destino: parser.error('Indica el usuario destino vacio; no se usa la cuenta de la app por defecto.')
    password=os.environ.get('UPC_RESTAURACION_CLAVE') or getpass.getpass('Contrasena del usuario destino: ')
    with oracledb.connect(user=args.usuario_destino,password=password,dsn=args.dsn) as conn:
        print(json.dumps(restaurar(args.respaldo,clave,conn,usuario_esperado=args.usuario_destino),ensure_ascii=False))


if __name__=='__main__': main()
