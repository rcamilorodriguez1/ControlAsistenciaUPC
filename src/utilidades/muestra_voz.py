"""Limites de archivos y actividad de voz antes de invocar el codificador."""

from io import BytesIO

import librosa
import numpy as np
import soundfile as sf
import webrtcvad

from src.utilidades.biometria import MuestraInvalida

FRECUENCIA = 16000
MIN_DURACION_REGISTRO = 3.0
MAX_DURACION_REGISTRO = 30.0
MAX_DURACION_ASISTENCIA = 180.0
MIN_VOZ_REGISTRO = 1.6
MIN_VOZ_SEGMENTO = 0.5
MIN_RMS = 10 ** (-50 / 20)  # -50 dBFS, antes de amplificar/normalizar.
MAX_FRACCION_SATURADA = 0.05
MIN_FRACCION_VOZ = 0.20


def comprobar_senal(audio):
    try:
        onda = np.asarray(audio, dtype=np.float32)
    except (TypeError, ValueError, OverflowError):
        raise MuestraInvalida('La grabación contiene audio inválido.', 'AUDIO_INVALIDO') from None
    if onda.ndim != 1 or onda.size == 0 or not np.isfinite(onda).all() or np.max(np.abs(onda)) > 1.00001:
        raise MuestraInvalida('La grabación contiene audio inválido.', 'AUDIO_INVALIDO')
    if np.mean(np.abs(onda) >= 0.999) > MAX_FRACCION_SATURADA:
        raise MuestraInvalida('La grabación está saturada. Aléjate un poco del micrófono y repite.', 'AUDIO_SATURADO')
    onda = onda - np.mean(onda, dtype=np.float64)
    if np.sqrt(np.mean(onda.astype(np.float64) ** 2)) < MIN_RMS:
        raise MuestraInvalida('La grabación está en silencio o tiene un volumen demasiado bajo.', 'SIN_SENAL')
    return onda.astype(np.float32)


def cargar_audio_seguro(datos, *, registro=False):
    limite = (10 if registro else 20) * 1024 * 1024
    if not isinstance(datos, bytes) or not datos or len(datos) > limite:
        raise MuestraInvalida(f'La grabación debe tener contenido y ocupar como máximo {limite // (1024 * 1024)} MB.', 'TAMANO_AUDIO')
    minimo = MIN_DURACION_REGISTRO if registro else MIN_VOZ_SEGMENTO
    maximo = MAX_DURACION_REGISTRO if registro else MAX_DURACION_ASISTENCIA
    try:
        with sf.SoundFile(BytesIO(datos)) as archivo:
            if (archivo.format not in ('WAV', 'WAVEX') or archivo.channels not in (1, 2)
                    or archivo.subtype not in ('PCM_16', 'PCM_24', 'PCM_32', 'FLOAT', 'DOUBLE')
                    or not 8000 <= archivo.samplerate <= 96000):
                raise MuestraInvalida('Usa una grabación WAV mono o estéreo entre 8 y 96 kHz.', 'FORMATO_AUDIO')
            duracion = archivo.frames / archivo.samplerate
            if not minimo <= duracion <= maximo:
                raise MuestraInvalida(f'La grabación debe durar entre {minimo:g} y {maximo:g} segundos.', 'DURACION_AUDIO')
            frecuencia = archivo.samplerate
            # El encabezado limita la lectura antes de descomprimir y reservar memoria.
            onda = archivo.read(frames=archivo.frames, dtype='float32', always_2d=True)
            if len(onda) != archivo.frames:
                raise MuestraInvalida('La grabación está incompleta. Vuelve a grabar.', 'AUDIO_INVALIDO')
    except (sf.LibsndfileError, RuntimeError, OSError, ValueError) as exc:
        if isinstance(exc, MuestraInvalida):
            raise
        raise MuestraInvalida('No se pudo leer la grabación WAV. Vuelve a grabar.', 'FORMATO_AUDIO') from exc
    onda = comprobar_senal(onda.mean(axis=1))
    if frecuencia != FRECUENCIA:
        onda = librosa.resample(onda, orig_sr=frecuencia, target_sr=FRECUENCIA)
    return comprobar_senal(onda)


def validar_tramo_voz(audio, *, minimo=MIN_VOZ_REGISTRO):
    onda = comprobar_senal(audio)
    muestras_ventana = FRECUENCIA * 30 // 1000
    ventanas = len(onda) // muestras_ventana
    if ventanas * 0.03 < minimo:
        raise MuestraInvalida(f'Graba al menos {minimo:g} segundos de voz clara.', 'VOZ_INSUFICIENTE')
    pcm = np.rint(np.clip(onda[:ventanas * muestras_ventana], -1, 1) * 32767).astype('<i2').tobytes()
    detector = webrtcvad.Vad(2)
    bytes_ventana = muestras_ventana * 2
    activas = sum(detector.is_speech(pcm[i * bytes_ventana:(i + 1) * bytes_ventana], FRECUENCIA)
                  for i in range(ventanas))
    if activas * 0.03 < minimo or activas / ventanas < MIN_FRACCION_VOZ:
        raise MuestraInvalida('No hay suficiente voz identificable. Graba una frase más larga y reduce el ruido.', 'VOZ_INSUFICIENTE')
    return onda
