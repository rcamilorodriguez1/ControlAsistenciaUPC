"""Ciclo de sesión y pertenencia de las capturas/resultados a una toma concreta."""

from copy import deepcopy
from uuid import uuid4
import time
import math

import streamlit as st
from src.servicios import sesiones_servidor as servidor

INACTIVIDAD_SEGUNDOS = 30 * 60
DURACION_MAXIMA_SEGUNDOS = 8 * 60 * 60


def _tiempo_valido(estado):
    ahora = time.time()
    inicio, ultimo = estado.get('sesion_creada_en'), estado.get('sesion_actividad_en')
    return (type(inicio) in (int, float) and type(ultimo) in (int, float)
            and math.isfinite(inicio) and math.isfinite(ultimo)
            and 0 <= ahora - inicio < DURACION_MAXIMA_SEGUNDOS
            and 0 <= ahora - ultimo < INACTIVIDAD_SEGUNDOS)


def _estado(estado):
    return st.session_state if estado is None else estado


def _id_positivo(valor):
    if isinstance(valor, bool):
        raise ValueError("Identificador inválido.")
    numero = int(valor)
    if numero <= 0 or str(numero) != str(valor):
        raise ValueError("Identificador inválido.")
    return numero


def _limpiar_estado(destino=None, estado=None):
    estado = _estado(estado)
    if destino not in (None, "profesor", "estudiante", "administrador"):
        raise ValueError("Portal inválido.")
    for clave in list(estado):
        del estado[clave]
    estado.update(tipo_sesion=destino, sesion_iniciada=False, rol_usuario=None,
                  sesion_token=uuid4().hex)


def cerrar_sesion(destino=None, estado=None):
    actual = _estado(estado)
    if destino not in (None, 'profesor', 'estudiante', 'administrador'):
        raise ValueError('Portal inválido.')
    actor = _actor_local(actual)
    # Los estados explicitos se usan como modelo puro en las pruebas; el estado real siempre revoca en Oracle.
    if estado is None and actor is not None:
        servidor.cerrar(*actor)
    _limpiar_estado(destino, actual)


def limpiar_codigo_union():
    if "join-code" in st.query_params:
        del st.query_params["join-code"]


def salir_al_portal(destino=None):
    """Callback: se ejecuta antes de crear los widgets del siguiente render."""
    cerrar_sesion(destino)
    limpiar_codigo_union()


def seleccionar_portal(destino, estado=None):
    if destino not in ('profesor', 'estudiante', 'administrador'):
        raise ValueError('Portal inválido.')
    actual = _estado(estado)
    pagina = actual.get('_paginas_portal', {}).get(destino)
    actual['tipo_sesion'] = destino
    if estado is None and pagina is not None:
        parametros = {'join-code': st.query_params['join-code']} if 'join-code' in st.query_params else {}
        st.switch_page(pagina, query_params=parametros)


def _actor_local(estado=None):
    estado = _estado(estado)
    rol = estado.get("rol_usuario")
    if (estado.get("sesion_iniciada") is not True or not estado.get("sesion_token")
            or rol not in ("profesor", "estudiante", "administrador") or not _tiempo_valido(estado)):
        return None
    perfil = estado.get(f"datos_{rol}")
    if not isinstance(perfil, dict):
        return None
    try:
        actor_id = _id_positivo(perfil.get(f"{rol}_id"))
    except (TypeError, ValueError):
        return None
    return rol, actor_id, estado["sesion_token"]


def rechazar_sesion(mensaje, estado=None):
    actual = _estado(estado)
    destino = actual.get('tipo_sesion')
    if destino not in ('profesor','estudiante','administrador'): destino = None
    _limpiar_estado(destino, actual)
    actual['aviso_sesion'] = mensaje


def obtener_actor(estado=None, *, renovar=False):
    actor = _actor_local(estado)
    if actor is None: return None
    if estado is None:
        try: servidor.validar(*actor, renovar=renovar)
        except servidor.SesionInvalida as exc:
            rechazar_sesion(str(exc)); return None
    if renovar: _estado(estado)['sesion_actividad_en'] = time.time()
    return actor


def ir_al_inicio():
    """Abrir la página pública sin modificar la identidad ni sus borradores."""
    pagina = st.session_state.get('_pagina_inicio')
    st.session_state['tipo_sesion'] = None
    limpiar_codigo_union()
    if pagina is not None:
        st.switch_page(pagina)


def sesion_incompatible(rol):
    actor = obtener_actor()
    return actor if actor and actor[0] != rol else None


def volver_a_mi_portal():
    actor = obtener_actor(renovar=True)
    if actor:
        seleccionar_portal(actor[0])


def sesion_activa(rol, estado=None):
    actor = obtener_actor(estado, renovar=True)
    return actor is not None and actor[0] == rol


def misma_sesion(rol, token, actor_id=None, estado=None):
    actor = obtener_actor(estado, renovar=True)
    return bool(actor and actor[0] == rol and actor[2] == token
                and (actor_id is None or actor[1] == actor_id))


def inicializar_sesion(estado=None):
    modelo = estado
    estado = _estado(estado)
    destino = estado.get("tipo_sesion")
    if destino not in (None, "profesor", "estudiante", "administrador"):
        destino = None
    if not estado.get("sesion_token") or estado.get("tipo_sesion") != destino:
        # Las sesiones de la implementación anterior no tienen resultados atribuibles.
        cerrar_sesion(destino, estado)
    elif estado.get("sesion_iniciada") and obtener_actor(modelo, renovar=True) is None:
        aviso = estado.get('aviso_sesion','La sesión caducó o cambió. Inicia sesión nuevamente.')
        _limpiar_estado(destino, estado)
        estado['aviso_sesion'] = aviso
    elif not estado.get("sesion_iniciada") and any(
            estado.get(k) is not None for k in ("rol_usuario", "datos_profesor", "datos_estudiante", "datos_administrador")):
        cerrar_sesion(destino, estado)
    if _actor_local(estado) is not None:
        estado['sesion_actividad_en'] = time.time()


def iniciar_sesion(rol, perfil, estado=None):
    if rol not in ("profesor", "estudiante", "administrador"):
        raise ValueError("Rol inválido.")
    actor_id = _id_positivo(perfil.get(f"{rol}_id"))
    actual = obtener_actor(estado)
    if actual is not None:
        if actual[:2] != (rol, actor_id):
            from src.servicios.autenticacion import ConflictoSesion
            raise ConflictoSesion('Cierra la sesión actual antes de autenticar otra cuenta.')
        return actual[2]
    opciones = {'prueba_identidad': perfil.get('_prueba_identidad')} if rol=='estudiante' else {}
    token = servidor.abrir(rol, actor_id, perfil.get('contrasena') if rol=='profesor' else None, **opciones) if estado is None else uuid4().hex
    # El panel no necesita guardar el hash ni los vectores biométricos en sesión.
    datos = {f"{rol}_id": actor_id, "nombre": perfil["nombre"]}
    if rol == 'estudiante' and perfil.get('codigo_institucional'):
        datos['codigo_institucional'] = perfil['codigo_institucional']
    if rol == 'estudiante':
        prueba = perfil.get('_prueba_identidad')
        datos['estado_verificacion'] = ({'EXCEPCION':'EXCEPCIONAL', 'BIOMETRIA':'BIOMETRICA_COMPLETA',
                                       'PRUEBA_ACADEMICA':'PRUEBA_ACADEMICA'}.get(prueba.metodo, 'PENDIENTE')) if prueba else 'PENDIENTE'
    if rol in ("profesor", "administrador"):
        datos["usuario"] = perfil["usuario"]
    estado = _estado(estado)
    _limpiar_estado(rol, estado)
    estado.update(sesion_iniciada=True, rol_usuario=rol)
    estado.update(sesion_creada_en=time.time(), sesion_actividad_en=time.time())
    estado[f"datos_{rol}"] = datos
    estado['sesion_token'] = token
    return token


def cambiar_formulario_profesor(formulario):
    if formulario not in ("iniciar_sesion", "registrarse", "recuperar"):
        raise ValueError("Formulario inválido.")
    for clave in list(st.session_state):
        if clave.startswith("auth_profesor_"):
            del st.session_state[clave]
    st.session_state.tipo_ingreso_profesor = formulario


def invalidar_resultado(estado=None):
    estado = _estado(estado)
    estado.pop("resultado_asistencia", None)
    estado.pop("resultados_asistencia_voz", None)


def limpiar_asistencia(estado=None):
    estado = _estado(estado)
    for clave in list(estado):
        if clave.startswith(("captura_", "audio_asistencia_", "revision_")):
            del estado[clave]
    for clave in ("contexto_asistencia", "materia_asistencia_id", "pestana_foto"):
        estado.pop(clave, None)
    invalidar_resultado(estado)
    estado["imagenes_asistencia"] = []
    estado["claves_subidas_procesadas"] = set()
    estado["clave_camara_procesada"] = None
    estado["bytes_imagenes_asistencia"] = 0


def preparar_toma(materia_id, estado=None, *, clase_id=None):
    estado = _estado(estado)
    actor = obtener_actor(estado)
    if actor is None or actor[0] != "profesor":
        raise PermissionError("Inicia sesión como profesor para tomar asistencia.")
    materia_id = _id_positivo(materia_id)
    clase_id = _id_positivo(clase_id) if clase_id is not None else None
    actual = estado.get("contexto_asistencia")
    if not isinstance(actual, dict) or (
            actual.get("sesion_token"), actual.get("profesor_id"), actual.get("materia_id"), actual.get("clase_id")) != (
            actor[2], actor[1], materia_id, clase_id):
        limpiar_asistencia(estado)
        actual = {"sesion_token": actor[2], "profesor_id": actor[1],
                  "materia_id": materia_id, "clase_id": clase_id, "toma_id": uuid4().hex}
        estado["contexto_asistencia"] = actual
    estado["materia_asistencia_id"] = materia_id
    return dict(actual)


def contexto_vigente(contexto, estado=None):
    estado = _estado(estado)
    actor = obtener_actor(estado, renovar=True)
    return bool(isinstance(contexto, dict) and actor and actor[0] == "profesor"
                and contexto == estado.get("contexto_asistencia")
                and contexto.get("sesion_token") == actor[2]
                and contexto.get("profesor_id") == actor[1]
                and contexto.get("materia_id") == estado.get("materia_asistencia_id"))


def reiniciar_toma(estado=None):
    estado = _estado(estado)
    contexto = estado.get("contexto_asistencia")
    materia_id = contexto.get("materia_id") if isinstance(contexto, dict) else None
    limpiar_asistencia(estado)
    if materia_id is not None and sesion_activa("profesor", estado):
        return preparar_toma(materia_id, estado, clase_id=contexto.get("clase_id"))
    return None


def guardar_resultado(contexto, filas, registros, origen, estado=None):
    estado = _estado(estado)
    if not contexto_vigente(contexto, estado):
        raise PermissionError("La sesión o materia cambió. Vuelve a ejecutar el análisis.")
    if contexto.get("clase_id") is None:
        raise ValueError("Selecciona una clase antes de analizar la asistencia.")
    if origen not in ("facial", "voz") or not registros or len(filas) != len(registros):
        raise ValueError("El resultado de asistencia está incompleto.")
    if any(r["materia_id"] != contexto["materia_id"] for r in registros):
        raise ValueError("El resultado contiene otra materia.")
    resultado = {"id": uuid4().hex, "contexto": dict(contexto), "origen": origen,
                 "filas": deepcopy(filas), "registros": deepcopy(registros)}
    estado["resultado_asistencia"] = resultado
    return resultado["id"]


def obtener_resultado(resultado_id=None, estado=None):
    estado = _estado(estado)
    resultado = estado.get("resultado_asistencia")
    if not isinstance(resultado, dict) or not contexto_vigente(resultado.get("contexto"), estado):
        return None
    if resultado_id is not None and resultado.get("id") != resultado_id:
        return None
    return deepcopy(resultado)
