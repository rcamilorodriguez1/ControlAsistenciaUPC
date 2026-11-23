import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
limpieza=importlib.import_module('limpiar_datos_pruebas')


class LimpiezaDatosTest(unittest.TestCase):
    def planes(self):
        return [{'nombre':n,'conn':MagicMock(),'config':{},'versiones':[]} for n in ('local','autonomous')]

    def test_respaldos_y_verificaciones_completos_antes_de_confirmar(self):
        eventos=[];planes=self.planes()
        for p in planes:p['conn'].commit.side_effect=lambda n=p['nombre']:eventos.append('commit '+n)
        with patch.object(limpieza,'bloquear'),patch.object(limpieza,'contar',return_value={}), \
             patch.object(limpieza,'crear_respaldo',side_effect=lambda c,d:eventos.append('backup '+d.name)), \
             patch.object(limpieza,'borrar',side_effect=lambda c:eventos.append('delete') or {}), \
             patch.object(limpieza,'verificar_limpieza',side_effect=lambda c,v:eventos.append('verificar') or {}):
            limpieza.ejecutar_planes(planes,Path('privado'))
        self.assertLess(max(i for i,e in enumerate(eventos) if e.startswith('backup')),eventos.index('delete'))
        self.assertLess(max(i for i,e in enumerate(eventos) if e=='verificar'),next(i for i,e in enumerate(eventos) if e.startswith('commit')))

    def test_respaldo_fallido_no_borra_y_revierte_ambas(self):
        planes=self.planes()
        with patch.object(limpieza,'bloquear'),patch.object(limpieza,'contar',return_value={}), \
             patch.object(limpieza,'crear_respaldo',side_effect=RuntimeError('Fallo')),patch.object(limpieza,'borrar') as borrar:
            with self.assertRaises(RuntimeError):limpieza.ejecutar_planes(planes,Path('privado'))
        borrar.assert_not_called()
        for p in planes:p['conn'].commit.assert_not_called();p['conn'].rollback.assert_called_once()

    def test_verificacion_fallida_no_confirma_borrados(self):
        planes=self.planes()
        with patch.object(limpieza,'bloquear'),patch.object(limpieza,'contar',return_value={}), \
             patch.object(limpieza,'crear_respaldo'),patch.object(limpieza,'borrar',return_value={}), \
             patch.object(limpieza,'verificar_limpieza',side_effect=RuntimeError('No vacia')):
            with self.assertRaises(RuntimeError):limpieza.ejecutar_planes(planes,Path('privado'))
        for p in planes:p['conn'].commit.assert_not_called();p['conn'].rollback.assert_called_once()

    def test_borrado_no_toca_versiones_ni_desactiva_restricciones(self):
        conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
        limpieza.borrar(conn)
        sentencias=[c.args[0] for c in cur.execute.call_args_list]
        self.assertEqual(len(sentencias),13)
        self.assertFalse(any('VERSIONES_ESQUEMA' in s or 'ALTER ' in s or 'TRUNCATE ' in s for s in sentencias))
