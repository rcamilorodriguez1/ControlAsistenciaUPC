"""Emite certificados de desarrollo por PC sin modificar almacenes de confianza."""

import argparse
from datetime import datetime, timedelta, timezone
import ipaddress
from pathlib import Path

from _comun import RAIZ, usar_entorno


def preparar_certificados(nombres, carpeta=None):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    carpeta = Path(carpeta or RAIZ / '.certs')
    carpeta.mkdir(exist_ok=True, parents=True)
    ahora = datetime.now(timezone.utc)
    ca_ruta, ca_clave_ruta = carpeta / 'ca.pem', carpeta / 'ca-key.pem'
    if ca_ruta.exists() != ca_clave_ruta.exists():
        raise ValueError('La CA local esta incompleta. Conserva la carpeta aparte y genera otra CA.')
    if not ca_ruta.exists():
        ca_clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'UPC Asistencia - CA de desarrollo local')])
        ca = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre)
              .public_key(ca_clave.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(ahora - timedelta(minutes=5)).not_valid_after(ahora + timedelta(days=3650))
              .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
              .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                  key_encipherment=False, data_encipherment=False, key_agreement=False,
                  key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
              .sign(ca_clave, hashes.SHA256()))
        ca_clave_ruta.write_bytes(ca_clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        ca_clave_ruta.chmod(0o600)
        ca_ruta.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    else:
        ca = x509.load_pem_x509_certificate(ca_ruta.read_bytes())
        ca_clave = serialization.load_pem_private_key(ca_clave_ruta.read_bytes(), password=None)
        if ca.not_valid_after_utc <= ahora + timedelta(days=90):
            raise ValueError('La CA local esta por caducar. Renuevala y vuelve a confiar en su certificado publico.')
        if ca.public_key().public_numbers() != ca_clave.public_key().public_numbers():
            raise ValueError('La clave y el certificado de la CA no coinciden.')
    sans = []
    for nombre in sorted(set(['localhost', '127.0.0.1', '::1', *nombres])):
        try:
            sans.append(x509.IPAddress(ipaddress.ip_address(nombre)))
        except ValueError:
            sans.append(x509.DNSName(nombre.encode('idna').decode('ascii')))
    cert_ruta, clave_ruta = carpeta / 'servidor.pem', carpeta / 'servidor-key.pem'
    if cert_ruta.exists() and clave_ruta.exists():
        actual = x509.load_pem_x509_certificate(cert_ruta.read_bytes())
        clave_actual = serialization.load_pem_private_key(clave_ruta.read_bytes(), password=None)
        actuales = actual.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        if (actual.not_valid_after_utc > ahora + timedelta(days=7)
                and actual.issuer == ca.subject and all(s in actuales for s in sans)
                and actual.public_key().public_numbers() == clave_actual.public_key().public_numbers()):
            actual.verify_directly_issued_by(ca)
            return cert_ruta, clave_ruta, ca_ruta
    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    certificado = (x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')]))
        .issuer_name(ca.subject).public_key(clave.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(minutes=5)).not_valid_after(ahora + timedelta(days=90))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName(sans), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_clave, hashes.SHA256()))
    clave_ruta.write_bytes(clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    clave_ruta.chmod(0o600)
    cert_ruta.write_bytes(certificado.public_bytes(serialization.Encoding.PEM))
    return cert_ruta, clave_ruta, ca_ruta


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nombre', action='append', default=[], help='IP o nombre adicional del PC en la LAN.')
    args = parser.parse_args()
    _, _, ca = preparar_certificados(args.nombre)
    print('Certificados de desarrollo listos en .certs/. No se modifico la confianza del sistema.')
    print('Certificado publico de la CA para confiar en el navegador:', ca)
    print('Consulta docs/INSTALACION.md. No compartas archivos *key.pem.')


if __name__ == '__main__':
    main()
