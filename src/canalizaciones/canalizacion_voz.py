from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import librosa
import streamlit as st
from src.servicios.resultado_audio import ResultadoAudio
import logging
from src.utilidades.biometria import MuestraInvalida, normalizar_vector_voz
from src.utilidades.muestra_voz import (cargar_audio_seguro, validar_tramo_voz, FRECUENCIA,
                                       MIN_VOZ_REGISTRO, MIN_VOZ_SEGMENTO)
from src.servicios.identificacion import ClasificadorReferencias

_logger = logging.getLogger(__name__)


@st.cache_resource
def cargar_codificador_voz():
    return VoiceEncoder()


def obtener_embedding_voz(audio_bytes):
    # Una grabacion enviada e invalida bloquea el alta; no se omite silenciosamente.
    audio = cargar_audio_seguro(audio_bytes, registro=True)
    audio = validar_tramo_voz(audio, minimo=MIN_VOZ_REGISTRO)
    try:
        wav = preprocess_wav(audio)
        if len(wav) < FRECUENCIA * MIN_VOZ_REGISTRO or not np.isfinite(wav).all():
            raise MuestraInvalida('La grabación no conserva suficiente voz tras quitar los silencios.', 'VOZ_INSUFICIENTE')
        return normalizar_vector_voz(cargar_codificador_voz().embed_utterance(wav)).tolist()
    except MuestraInvalida:
        raise
    except Exception as exc:
        _logger.error('Fallo al generar muestra de voz: tipo=%s', type(exc).__name__)
        raise MuestraInvalida('No se pudo procesar la voz. Repite la grabación antes de crear el perfil.', 'ERROR_PROCESAMIENTO') from None


def identificar_hablante(nuevo_embedding, diccionario_candidatos, umbral=None, margen=None):
    if nuevo_embedding is None or not diccionario_candidatos:
        return None, 0.0
    resultado = ClasificadorReferencias(diccionario_candidatos, 'voz').identificar(
        nuevo_embedding, umbral=umbral, margen=margen)
    return resultado.identidad, resultado.valor if resultado.valor is not None else 0.0


def procesar_audio_masivo(audio_bytes, diccionario_candidatos, umbral=None):
    etapa = 'entrada'
    try:
        if not audio_bytes:
            return ResultadoAudio.fallido('AUDIO_VACIO')
        if not diccionario_candidatos:
            return ResultadoAudio('SIN_MUESTRAS')
        candidatos = {sid: normalizar_vector_voz(vector) for sid, vector in diccionario_candidatos.items()}
        # Las referencias no cambian entre intervenciones de esta grabación.
        modelo = ClasificadorReferencias(candidatos, 'voz')
        etapa = 'decodificacion'
        audio, sr = cargar_audio_seguro(audio_bytes), FRECUENCIA
        etapa = 'segmentacion'
        segmentos = librosa.effects.split(audio, top_db=30)

        resultados_identificados = {}
        procesados = 0
        codificador = None

        for inicio, fin in segmentos:

            if(fin-inicio) < sr * MIN_VOZ_SEGMENTO:
                continue

            audio_segmento =  audio[inicio:fin]
            # Evitar convertir silencio puro en un resultado negativo válido.
            if not np.any(audio_segmento):
                continue
            etapa = 'preprocesamiento'
            try:
                audio_segmento = validar_tramo_voz(audio_segmento, minimo=MIN_VOZ_SEGMENTO)
            except MuestraInvalida:
                continue
            wav = preprocess_wav(audio_segmento)
            if len(wav) < sr * MIN_VOZ_SEGMENTO:
                continue
            etapa = 'codificacion'
            if codificador is None:
                codificador = cargar_codificador_voz()
            embedding = normalizar_vector_voz(codificador.embed_utterance(wav))

            etapa = 'comparacion'
            coincidencia = modelo.identificar(embedding, umbral=umbral)
            id_candidato = coincidencia.identidad
            puntaje = coincidencia.valor if id_candidato is not None and coincidencia.valor is not None else 0.0
            if not np.isfinite(puntaje):
                return ResultadoAudio.fallido('PUNTAJE_INVALIDO')
            procesados += 1

            if id_candidato:
                if id_candidato not in resultados_identificados or puntaje > resultados_identificados[id_candidato]:
                    resultados_identificados[id_candidato] = puntaje

        if not procesados:
            return ResultadoAudio.fallido('SIN_SEGMENTOS_ANALIZABLES')
        return ResultadoAudio('COMPLETADO', resultados_identificados)

    except MuestraInvalida as exc:
        return ResultadoAudio.fallido(exc.codigo)
    except Exception as exc:
        # No registrar audio, vectores ni mensajes de terceros que puedan incluirlos.
        _logger.error('Fallo de análisis de voz: etapa=%s tipo=%s', etapa, type(exc).__name__)
        return ResultadoAudio.fallido('ERROR_PROCESAMIENTO')
