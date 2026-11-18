from io import BytesIO
import unittest
from unittest.mock import patch

from PIL import Image

from src.utilidades.sesiones import (
    cerrar_sesion, iniciar_sesion, inicializar_sesion, obtener_actor, sesion_activa,
    misma_sesion, preparar_toma, contexto_vigente, reiniciar_toma,
    guardar_resultado, obtener_resultado, seleccionar_portal,
)
from src.utilidades.imagenes import agregar_foto
from src.servicios.asistencia import confirmar_resultado


def profesor(estado, actor=1):
    cerrar_sesion(estado=estado)
    iniciar_sesion("profesor", {"profesor_id": actor, "nombre": f"Profesor {actor}",
                               "usuario": f"p{actor}", "contrasena": "NO_GUARDAR"}, estado)


def propuesta(estado, contexto, origen="voz"):
    return guardar_resultado(contexto, [{"Nombre": "Estudiante", "Estado": "Presente"}],
        [{"materia_id": contexto["materia_id"], "estudiante_id": 7,
          "presente": True, "fecha_hora": "2026-11-11T10:00:00-05:00"}], origen, estado)


class SesionesTest(unittest.TestCase):
    def setUp(self):
        self.estado = {}
        profesor(self.estado)
        self.contexto = preparar_toma(10, self.estado, clase_id=100)

    def test_cierre_limpia_identidad_capturas_widgets_y_resultados(self):
        anterior = self.estado["sesion_token"]
        propuesta(self.estado, self.contexto)
        self.estado.update({"imagenes_asistencia": ["foto"], "auth_profesor_clave_login": "secreto",
                            "captura_camara_vieja": "archivo", "audio_asistencia_viejo": "voz",
                            "datos_estudiante": {"estudiante_id": 8}})
        cerrar_sesion("profesor", self.estado)
        self.assertFalse(self.estado["sesion_iniciada"])
        self.assertIsNone(self.estado["rol_usuario"])
        self.assertIsNone(obtener_actor(self.estado))
        self.assertNotEqual(anterior, self.estado["sesion_token"])
        self.assertEqual(set(self.estado), {"tipo_sesion", "sesion_iniciada", "rol_usuario", "sesion_token"})

    def test_login_de_otra_persona_no_hereda_hash_biometria_ni_propuestas(self):
        propuesta(self.estado, self.contexto)
        profesor(self.estado, 2)
        self.assertEqual(self.estado["datos_profesor"], {"profesor_id": 2, "nombre": "Profesor 2", "usuario": "p2"})
        self.assertIsNone(obtener_resultado(estado=self.estado))
        self.assertFalse(contexto_vigente(self.contexto, self.estado))
        cerrar_sesion(estado=self.estado)
        iniciar_sesion("estudiante", {"estudiante_id": 7, "nombre": "Alumno",
                                     "embedding_facial": [1], "embedding_voz": [2]}, self.estado)
        self.assertEqual(self.estado["datos_estudiante"], {"estudiante_id": 7, "nombre": "Alumno", "estado_verificacion": "PENDIENTE"})
        self.assertNotIn("datos_profesor", self.estado)

    def test_perfil_guardado_no_equivale_a_estar_autenticado(self):
        self.estado["sesion_iniciada"] = False
        self.assertFalse(sesion_activa("profesor", self.estado))
        inicializar_sesion(self.estado)
        self.assertNotIn("datos_profesor", self.estado)

    def test_sesion_anterior_sin_token_se_invalida(self):
        self.estado.pop("sesion_token")
        inicializar_sesion(self.estado)
        self.assertFalse(self.estado["sesion_iniciada"])

    def test_portal_invalido_se_recupera_sin_mostrar_pantalla_vacia(self):
        cerrar_sesion(estado=self.estado)
        self.estado["tipo_sesion"] = "invalido"
        inicializar_sesion(self.estado)
        self.assertIsNone(self.estado["tipo_sesion"])

    def test_seleccionar_otro_portal_conserva_identidad_actual(self):
        seleccionar_portal("estudiante", self.estado)
        self.assertEqual(self.estado["tipo_sesion"], "estudiante")
        self.assertEqual(obtener_actor(self.estado)[0], "profesor")

    def test_cambiar_materia_descarta_fotos_resultados_y_widgets(self):
        self.estado["imagenes_asistencia"].append("foto")
        self.estado["claves_subidas_procesadas"].add("hash")
        self.estado["captura_camara_anterior"] = "foto"
        propuesta(self.estado, self.contexto)
        nuevo = preparar_toma(20, self.estado)
        self.assertFalse(contexto_vigente(self.contexto, self.estado))
        self.assertTrue(contexto_vigente(nuevo, self.estado))
        self.assertEqual(self.estado["imagenes_asistencia"], [])
        self.assertEqual(self.estado["claves_subidas_procesadas"], set())
        self.assertNotIn("captura_camara_anterior", self.estado)
        self.assertIsNone(obtener_resultado(estado=self.estado))

    def test_rerun_de_misma_materia_conserva_trabajo(self):
        self.estado["imagenes_asistencia"].append("foto")
        resultado_id = propuesta(self.estado, self.contexto)
        nuevo = preparar_toma(10, self.estado, clase_id=100)
        self.assertEqual(nuevo, self.contexto)
        self.assertEqual(self.estado["imagenes_asistencia"], ["foto"])
        self.assertEqual(obtener_resultado(resultado_id, self.estado)["id"], resultado_id)

    def test_reiniciar_toma_cambia_claves_y_no_reutiliza_resultado(self):
        resultado_id = propuesta(self.estado, self.contexto)
        nuevo = reiniciar_toma(self.estado)
        self.assertEqual(nuevo["materia_id"], 10)
        self.assertNotEqual(nuevo["toma_id"], self.contexto["toma_id"])
        self.assertIsNone(obtener_resultado(resultado_id, self.estado))

    def test_dialogo_antiguo_no_actua_sobre_una_nueva_sesion_del_mismo_usuario(self):
        token = self.estado["sesion_token"]
        profesor(self.estado)
        self.assertFalse(misma_sesion("profesor", token, 1, self.estado))
        with self.assertRaises(PermissionError):
            propuesta(self.estado, self.contexto)

    def test_resultados_no_comparten_referencias_mutables(self):
        rid = propuesta(self.estado, self.contexto)
        obtenido = obtener_resultado(rid, self.estado)
        obtenido["registros"][0]["materia_id"] = 99
        self.assertEqual(obtener_resultado(rid, self.estado)["registros"][0]["materia_id"], 10)

    def test_confirmacion_consume_propuesta_y_no_admite_segunda_pulsacion(self):
        rid = propuesta(self.estado, self.contexto)
        with patch("src.servicios.asistencia.crear_asistencia", return_value=1) as guardar:
            self.assertEqual(confirmar_resultado(rid, self.estado), 1)
            self.assertEqual(guardar.call_args.kwargs, {"profesor_id": 1, "clase_id": 100,
                                                       "clave_confirmacion": rid, "origen": "voz"})
            with self.assertRaises(PermissionError):
                confirmar_resultado(rid, self.estado)
            guardar.assert_called_once()
        self.assertFalse(contexto_vigente(self.contexto, self.estado))

    def test_fallo_al_guardar_no_deja_propuesta_reintentable(self):
        rid = propuesta(self.estado, self.contexto)
        with patch("src.servicios.asistencia.crear_asistencia", side_effect=RuntimeError("Respuesta perdida")) as guardar:
            with self.assertRaises(RuntimeError):
                confirmar_resultado(rid, self.estado)
            with self.assertRaises(PermissionError):
                confirmar_resultado(rid, self.estado)
            guardar.assert_called_once()

    def test_no_confirma_resultados_de_otra_materia(self):
        rid = propuesta(self.estado, self.contexto)
        preparar_toma(20, self.estado)
        with patch("src.servicios.asistencia.crear_asistencia") as guardar:
            with self.assertRaises(PermissionError):
                confirmar_resultado(rid, self.estado)
            guardar.assert_not_called()


class FotosPorTomaTest(unittest.TestCase):
    def setUp(self):
        self.estado = {}
        profesor(self.estado)
        self.contexto = preparar_toma(10, self.estado, clase_id=100)
        self.roja = self.foto("red")
        self.azul = self.foto("blue")

    def foto(self, color):
        archivo = BytesIO()
        Image.new("RGB", (3, 2), color).save(archivo, format="PNG")
        archivo.name = "foto.png"
        return archivo

    def test_distingue_contenido_con_mismo_nombre_y_tamano(self):
        largo = max(len(self.roja.getvalue()), len(self.azul.getvalue()))
        self.roja = BytesIO(self.roja.getvalue().ljust(largo, b'\0'))
        self.azul = BytesIO(self.azul.getvalue().ljust(largo, b'\0'))
        self.roja.name = self.azul.name = "foto.png"
        self.assertTrue(agregar_foto(self.roja, self.contexto, self.estado))
        self.assertFalse(agregar_foto(self.roja, self.contexto, self.estado))
        self.assertTrue(agregar_foto(self.azul, self.contexto, self.estado))
        self.assertEqual(len(self.estado["imagenes_asistencia"]), 2)

    def test_se_puede_reutilizar_la_misma_foto_tras_descartar(self):
        agregar_foto(self.roja, self.contexto, self.estado)
        nuevo = reiniciar_toma(self.estado)
        self.assertTrue(agregar_foto(self.roja, nuevo, self.estado))

    def test_agregar_foto_invalida_la_propuesta_anterior(self):
        rid = propuesta(self.estado, self.contexto, "facial")
        agregar_foto(self.roja, self.contexto, self.estado)
        self.assertIsNone(obtener_resultado(rid, self.estado))

    def test_archivo_invalido_o_grande_no_modifica_la_toma(self):
        with self.assertRaises(ValueError):
            agregar_foto(BytesIO(b"archivo invalido"), self.contexto, self.estado)
        with patch("src.utilidades.imagenes.MAX_BYTES_FOTO", 5), self.assertRaises(ValueError):
            agregar_foto(self.roja, self.contexto, self.estado)
        self.assertEqual(self.estado["imagenes_asistencia"], [])

    def test_foto_de_un_dialogo_viejo_no_entra_en_la_nueva_materia(self):
        preparar_toma(20, self.estado)
        with self.assertRaises(PermissionError):
            agregar_foto(self.roja, self.contexto, self.estado)


if __name__ == "__main__":
    unittest.main()
