"""Prepara la clave académica privada y dos variables para importar en Render."""
import argparse
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import re
import secrets
import tomllib
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]


def preparar(hasta, *, activar_local=False):
    limite = datetime.fromisoformat(hasta)
    if limite.tzinfo is None or limite <= datetime.now(timezone.utc):
        raise ValueError('Indica una fecha futura ISO 8601 con zona horaria.')
    privado = RAIZ / '.local'
    privado.mkdir(exist_ok=True)
    env = privado / 'prueba_academica.env'
    clave = None
    if env.exists():
        for linea in env.read_text(encoding='utf-8').splitlines():
            if linea.startswith('ESTUDIANTE_CLAVE_MAESTRA='):
                clave = linea.partition('=')[2]
    clave = clave or secrets.token_urlsafe(24)+'!Aa1'
    valores = {'ESTUDIANTE_CLAVE_MAESTRA':clave, 'ESTUDIANTE_CLAVE_MAESTRA_HASTA':limite.isoformat()}
    env.write_text(''.join(k+'='+v+'\n' for k,v in valores.items()),encoding='utf-8')
    instrucciones = privado / 'CLAVE_MAESTRA_ESTUDIANTE.md'
    instrucciones.write_text('# Clave maestra estudiantil — prueba académica privada\n\n'
        f'Clave común:\n\n`{clave}`\n\n'
        f'Válida hasta **{limite.astimezone(ZoneInfo("America/Bogota")).isoformat()}**, hora de Colombia.\n\n'
        '## Uso en Render\n\n'
        '1. Environment → Add from .env: importar `.local/prueba_academica.env`.\n'
        '2. Guardar las variables y desplegar el último commit. Oracle debe estar en 010.\n'
        '3. Portal del estudiante → No puedo completar la validación biométrica → Demostración académica.\n'
        '4. Seleccionar Código institucional o ID interno, introducir su valor y esta clave común.\n\n'
        'No necesita cámara, documento registrado ni autorización excepcional individual.\n'
        'El estado y los eventos quedan como PRUEBA_ACADEMICA; no se marca asistencia.\n'
        'Las cuentas sin código institucional pueden usar su ID interno. Las archivadas no acceden.\n'
        'Al vencer, retirar la clave o cambiarla, se rechazan nuevas entradas y las sesiones de prueba.\n'
        'Para desactivar antes: eliminar ambas variables en Render y guardar.\n\n'
        'Archivo privado: no copiar al ZIP público, repositorio o capturas.\n',encoding='utf-8')
    if activar_local:
        ruta = RAIZ / '.streamlit/secrets.toml'
        texto = ruta.read_text(encoding='utf-8')
        datos = tomllib.loads(texto)
        for k,v in valores.items():
            linea = k+' = '+json.dumps(v)
            if k in datos:
                texto = re.sub(r'^'+re.escape(k)+r'\s*=.*$',lambda m:linea,texto,flags=re.M)
            else:
                texto = texto.rstrip()+'\n'+linea+'\n'
        assert all(tomllib.loads(texto)[k] == v for k,v in valores.items())
        ruta.write_text(texto,encoding='utf-8')
    print(json.dumps({'instrucciones':str(instrucciones),'variables_render':str(env),
        'hasta':limite.isoformat(),'activado_local':activar_local},ensure_ascii=False))


def main():
    manana=datetime.now(ZoneInfo('America/Bogota')).date()+timedelta(days=1)
    por_defecto=datetime.combine(manana,time(23,59,59),ZoneInfo('America/Bogota')).isoformat()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hasta',default=por_defecto)
    p.add_argument('--activar-local',action='store_true')
    args=p.parse_args()
    preparar(args.hasta,activar_local=args.activar_local)


if __name__=='__main__':main()
