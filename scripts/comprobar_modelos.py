"""Comprueba modelos incluidos en dependencias sin cámara, red ni base de datos."""
from _comun import usar_entorno


def main():
    usar_entorno()
    import dlib
    import face_recognition_models as modelos
    import numpy as np
    import soundfile
    import torch
    import webrtcvad
    from resemblyzer import VoiceEncoder
    dlib.get_frontal_face_detector()
    dlib.shape_predictor(modelos.pose_predictor_model_location())
    dlib.face_recognition_model_v1(modelos.face_recognition_model_location())
    codificador = VoiceEncoder(device='cpu', verbose=False)
    vector = codificador.embed_utterance(np.zeros(16000, dtype=np.float32))
    if vector.shape != (256,) or not np.isfinite(vector).all():
        raise SystemExit('El modelo de voz no devolvió un vector válido.')
    webrtcvad.Vad(2).is_speech(b'\0' * 960, 16000)
    if not soundfile.available_formats():
        raise SystemExit('No se pudieron cargar los formatos de audio.')
    print('Modelos facial y de voz, audio y CPU comprobados. Torch:', torch.__version__)


if __name__ == '__main__':
    main()
