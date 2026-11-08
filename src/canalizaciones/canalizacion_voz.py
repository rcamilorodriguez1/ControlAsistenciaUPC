from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io
import librosa
import streamlit as st

@st.cache_resource
def cargar_codificador_voz():
    return VoiceEncoder()


def obtener_embedding_voz(audio_bytes):
    try:
        codificador = cargar_codificador_voz()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio) # elimina ruidos y normaliza el audio

        embedding = codificador.embed_utterance(wav)
        return embedding.tolist() # vector de 256D aunque la imagen tenía solo 128 dimensiones

    except Exception as e:
        st.error("Ocurrió un error al reconocer la voz.")
        return None


def identificar_hablante(nuevo_embedding, diccionario_candidatos, umbral=0.65):
    if nuevo_embedding is None or not diccionario_candidatos:
        return None, 0.0

    mejor_id = None
    mejor_puntaje = -1.0

    for id_candidato, embedding_guardado in diccionario_candidatos.items():
        if embedding_guardado:
            similitud = np.dot(nuevo_embedding, embedding_guardado)
            if similitud > mejor_puntaje:
                mejor_puntaje = similitud
                mejor_id = id_candidato

    if mejor_puntaje >= umbral:
        return mejor_id, mejor_puntaje

    else:
        return None, mejor_puntaje


def procesar_audio_masivo(audio_bytes, diccionario_candidatos, umbral=0.65):

    try:
        codificador = cargar_codificador_voz()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        segmentos = librosa.effects.split(audio, top_db=30)

        resultados_identificados = {}

        for inicio, fin in segmentos:

            if(fin-inicio) < sr * 0.5:
                continue

            audio_segmento =  audio[inicio:fin]
            wav = preprocess_wav(audio_segmento) 
            embedding = codificador.embed_utterance(wav)

            id_candidato, puntaje = identificar_hablante(embedding, diccionario_candidatos, umbral)

            if id_candidato:
                if id_candidato not in resultados_identificados or puntaje > resultados_identificados[id_candidato]:
                    resultados_identificados[id_candidato] = puntaje

        return resultados_identificados

    except Exception as e:
        st.error(f"Ocurrió un error al reconocer las voces en bloque {e}")
        return {}            
