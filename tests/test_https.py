from datetime import datetime, timezone
from pathlib import Path
import ssl
import sys
import tempfile
import unittest

from cryptography import x509

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from preparar_https import preparar_certificados


class CertificadosTest(unittest.TestCase):
    def test_certificado_para_localhost_y_lan_firmado_por_ca_local(self):
        with tempfile.TemporaryDirectory() as carpeta:
            certificado, clave, ca = preparar_certificados(['192.168.1.25'], carpeta)
            cert = x509.load_pem_x509_certificate(certificado.read_bytes())
            raiz = x509.load_pem_x509_certificate(ca.read_bytes())
            cert.verify_directly_issued_by(raiz)
            self.assertGreater(cert.not_valid_after_utc, datetime.now(timezone.utc))
            sans = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            self.assertIn('localhost', sans.get_values_for_type(x509.DNSName))
            self.assertIn('192.168.1.25', [str(ip) for ip in sans.get_values_for_type(x509.IPAddress)])
            contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            contexto.load_cert_chain(certificado, clave)
            numero = cert.serial_number
            preparar_certificados(['192.168.1.25'], carpeta)
            self.assertEqual(x509.load_pem_x509_certificate(certificado.read_bytes()).serial_number, numero)


if __name__ == '__main__':
    unittest.main()
