"""Prepara la clave privada HMAC sin mostrarla. No sustituye claves perdidas en uso."""
from _comun import usar_entorno

if __name__ == '__main__':
    usar_entorno()
    from src.servicios.verificacion_identidad import preparar_clave
    preparar_clave()
    print('Clave privada de identidad preparada. Conserva una copia privada fuera del repositorio.')
