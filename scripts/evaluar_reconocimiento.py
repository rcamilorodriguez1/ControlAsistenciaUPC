import argparse
import json
from pathlib import Path

from _comun import usar_entorno


def main():
    usar_entorno()
    from src.servicios.evaluacion_reconocimiento import evaluar, calibrar
    parser = argparse.ArgumentParser(description='Evaluar referencias/consultas etiquetadas sin modificar los umbrales de la app.')
    parser.add_argument('conjunto', type=Path)
    parser.add_argument('--calibrar', action='store_true')
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    datos = json.loads(args.conjunto.read_text(encoding='utf-8'))
    resultado = {'evaluacion': evaluar(datos)}
    if args.calibrar:
        resultado['calibracion'] = calibrar(datos)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        with args.salida.open('x', encoding='utf-8') as archivo:
            archivo.write(texto)
    print(texto)


if __name__ == '__main__':
    main()
