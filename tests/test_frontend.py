from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


class FrontendTest(unittest.TestCase):
    def test_tarjetas_y_saludo_no_interpretan_html_de_datos(self):
        from src.componentes.tarjeta_materia import tarjeta_materia
        from src.componentes.encabezado import introduccion
        class Etiquetas(HTMLParser):
            def __init__(self): super().__init__(); self.tags = []
            def handle_starttag(self, tag, attrs): self.tags.append(tag)
        malicioso = '<img src=x onerror="alert(1)"><script>alert(1)</script>'
        with patch('streamlit.html') as render:
            tarjeta_materia(malicioso, malicioso, malicioso, [('', malicioso, malicioso)])
            introduccion('Panel', malicioso, malicioso)
        for llamada in render.call_args_list:
            parser = Etiquetas(); parser.feed(llamada.args[0])
            self.assertNotIn('img', parser.tags)
            self.assertNotIn('script', parser.tags)
            self.assertIn('&lt;img', llamada.args[0])

    def test_inicio_y_accesos_no_importan_las_dependencias_de_ia(self):
        raiz = Path(__file__).resolve().parents[1]
        codigo = '''
import json,sys
from streamlit.testing.v1 import AppTest
at=AppTest.from_file(sys.argv[1],default_timeout=45).run()
assert not at.exception
next(b for b in at.button if b.label=='Portal del Profesor').click().run()
assert not at.exception
next(b for b in at.button if b.label=='Registrarme en su lugar').click().run()
assert not at.exception
at._page_hash=at.session_state['_pagina_inicio']._script_hash
at.run()
next(b for b in at.button if b.label=='Portal del Estudiante').click().run()
assert not at.exception
print(json.dumps([m for m in ('torch','dlib','resemblyzer','face_recognition_models','librosa','sklearn') if m in sys.modules]))
'''
        resultado = subprocess.run([sys.executable, '-B', '-c', codigo, str(raiz / 'principal.py')],
            cwd=raiz, capture_output=True, text=True, encoding='utf-8', timeout=90)
        self.assertEqual(resultado.returncode, 0, resultado.stderr[-3000:])
        self.assertEqual(json.loads(resultado.stdout), [], 'El acceso no debe cargar los motores biométricos.')
