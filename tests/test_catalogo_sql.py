import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.base_datos import consultas


class CatalogoSQLTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        consultas.cargar_sql.cache_clear()
        self.addCleanup(consultas.cargar_sql.cache_clear)
        parche = patch.object(consultas, 'RAIZ_CONSULTAS', self.raiz)
        parche.start(); self.addCleanup(parche.stop)

    def test_conserva_literal_y_parametros_sin_sustituir_datos(self):
        sql = '\n  SELECT nombre FROM profesores WHERE usuario=:usuario\n  '
        (self.raiz / 'consulta.sql').write_text(sql, encoding='utf-8')
        self.assertEqual(consultas.cargar_sql('consulta'), sql)

    def test_rechaza_rutas_fuera_del_catalogo_y_archivos_vacios(self):
        for nombre in ('../privado', '/tmp/privado', 'carpeta/../../privado', r'carpeta\privado', 'consulta.sql'):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                consultas.cargar_sql(nombre)
        (self.raiz / 'vacia.sql').write_text('  \n', encoding='utf-8')
        with self.assertRaises(ValueError):
            consultas.cargar_sql('vacia')

    def test_plantilla_solo_admite_identificadores_y_marcadores_exactos(self):
        (self.raiz / 'plantilla.sql').write_text('SELECT * FROM {esquema}.{vista} WHERE nombre=:nombre', encoding='utf-8')
        self.assertEqual(consultas.sql_con_identificadores('plantilla', esquema='"UPC_ASISTENCIA"', vista='v_materias'),
                         'SELECT * FROM "UPC_ASISTENCIA".v_materias WHERE nombre=:nombre')
        for valor in ('UPC; DROP TABLE profesores', 'usuario.tabla', "'usuario'", 'usuario--', 'usuario nombre'):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                consultas.sql_con_identificadores('plantilla', esquema=valor, vista='v_materias')
        with self.assertRaises(ValueError):
            consultas.sql_con_identificadores('plantilla', esquema='UPC_ASISTENCIA')
        with self.assertRaises(ValueError):
            consultas.sql_con_identificadores('plantilla', esquema='UPC_ASISTENCIA', vista='v_materias', extra='X')


class OrganizacionSQLTest(unittest.TestCase):
    def test_consultas_referenciadas_existen_en_el_catalogo_del_proyecto(self):
        raiz = Path(__file__).resolve().parents[1]
        nombres = set()
        for archivo in (raiz / 'src').rglob('*.py'):
            for nodo in ast.walk(ast.parse(archivo.read_text(encoding='utf-8'))):
                if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                        and nodo.func.id in ('cargar_sql', 'sql_con_identificadores')
                        and nodo.args and isinstance(nodo.args[0], ast.Constant)):
                    nombres.add(nodo.args[0].value)
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.assertTrue((raiz / 'sql/consultas' / (nombre + '.sql')).is_file())
        self.assertGreater(len(nombres), 70)

    def test_operaciones_de_negocio_no_definen_sentencias_en_python(self):
        raiz = Path(__file__).resolve().parents[1]
        archivos = [*sorted((raiz / 'src/base_datos').glob('*.py')),
                    *sorted((raiz / 'src/servicios').glob('*.py'))]
        for archivo in archivos:
            # La generación de DDL para respaldos sigue siendo una herramienta técnica;
            # su rediseño está registrado para la segunda etapa.
            if archivo.name == 'recuperacion.py':
                continue
            for nodo in ast.walk(ast.parse(archivo.read_text(encoding='utf-8'))):
                if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                        and nodo.func.attr in ('execute', 'executemany') and nodo.args):
                    self.assertNotIsInstance(nodo.args[0], (ast.Constant, ast.JoinedStr, ast.BinOp),
                                             f'SQL embebido en {archivo.name}:{nodo.lineno}')
