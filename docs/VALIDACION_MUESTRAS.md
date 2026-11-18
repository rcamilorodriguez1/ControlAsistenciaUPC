# Validación de muestras — punto 3

Implementado el 11 de noviembre de 2026. Se mantienen las versiones Oracle 001–004; este cambio
valida capturas y descriptores en Python, sin alterar el esquema ni reescribir biometría existente.

## Registro y acceso facial

El acceso lee la captura con los mismos límites de archivo que el registro, aplica la orientación
EXIF y convierte la imagen a RGB uint8. La captura de acceso/registro debe contener exactamente un
rostro completo. El detector vuelve a ejecutarse al crear la cuenta: no basta con que una foto anterior
haya tenido un rostro. No se toma silenciosamente el primer descriptor de una lista con varias personas.
Las fotos grupales de asistencia siguen permitiendo varios rostros.

| Comprobación | Límite inicial |
| --- | --- |
| Formato de captura | JPEG o PNG legible |
| Archivo | Hasta 10 MiB |
| Dimensiones de imagen | Mínimo 96 × 96; máximo 20 millones de píxeles |
| Rostros en acceso/registro | Exactamente uno |
| Caja del rostro de registro/acceso | Al menos 80 × 80 y completamente dentro de la imagen |
| Descriptor facial | Vector de 128 números reales finitos, sin booleanos, no nulo |

El descriptor facial conserva su escala. Aplicarle normalización L2 cambiaría las distancias
euclidianas y los umbrales que utiliza actualmente el reconocimiento con dlib.

## Registro de voz

La voz continúa siendo opcional. Si no se graba, se puede crear un perfil solo con rostro. Si se envía
una grabación, se valida y debe ser utilizable antes de insertar la cuenta; un error no se convierte
en `embedding_voz=None` para continuar silenciosamente. El usuario puede repetir o eliminar esa grabación.

| Comprobación | Límite inicial |
| --- | --- |
| Formato | WAV/WAVEX PCM de 16/24/32 bits o float; mono o estéreo |
| Archivo de registro | Hasta 10 MiB |
| Duración de registro | Entre 3 y 30 segundos |
| Frecuencia de entrada | Entre 8 y 96 kHz; se convierte a mono y 16 kHz |
| Volumen antes de normalizar | RMS mínimo de −50 dBFS, después de quitar el componente continuo |
| Saturación | Se rechaza si más del 5 % de las muestras alcanza magnitud 0,999 |
| Actividad vocal | WebRTC VAD modo 2, ventanas de 30 ms; mínimo aproximado de 1,6 s de voz y 20 % de ventanas activas |
| Salida del preprocesamiento | Al menos 1,6 s y valores finitos antes de invocar el codificador |
| Vector de voz | 256 números reales finitos, sin booleanos, no nulo; se normaliza a norma L2 unitaria |

Los límites se comprueban en el encabezado antes de leer todo el audio. Se rechazan archivos corruptos,
señales vacías, excesivamente débiles, saturadas o sin suficiente actividad vocal. La normalización de
volumen no se usa para rescatar una señal en silencio. La cuantización temporal del VAD es de 30 ms.

Estos son límites operativos iniciales, no umbrales de precisión medidos con los dispositivos del
usuario. El VAD detecta actividad probablemente vocal; no demuestra identidad, voz en vivo ni rechazo
perfecto de ruido/música. La calibración y el ensayo real siguen al final, como se acordó.

## Consumo de muestras y guardado

`src/servicios/registro_estudiante.py` coordina captura, rostro único, extracción, validación de
vectores y alta. `crear_estudiante` vuelve a validar los descriptores antes de adquirir una conexión
Oracle, incluso si otra herramienta Python invoca directamente esa función. El JSON se serializa sin
permitir NaN/Infinity. El alta no se reintenta automáticamente después de un COMMIT incierto.

Las voces se normalizan antes de guardarse y al compararse con referencias antiguas; esta última
normalización ocurre en memoria, sin reescribir perfiles existentes. Los descriptores faciales
guardados se validan al construir el modelo. Un vector corrupto bloquea el análisis en vez de producir
una ausencia. El propietario del esquema conserva acceso SQL directo; estas comprobaciones no son
nuevas restricciones SQL y no pueden validar retrospectivamente la captura original que ya no se guarda.

Después del alta solo se invalida el clasificador facial. No se vacía `st.cache_resource` completo
ni se ejecuta entrenamiento después del COMMIT: un fallo de entrenamiento no debe presentar un alta
ya realizada como si hubiera fallado. La revisión del clasificador con cero/uno/pocos estudiantes
sigue siendo el siguiente trabajo.

Para asistencia por voz se permite hasta 20 MiB y 180 s; cada segmento debe contener al menos unos
0,5 s de voz y pasar las comprobaciones de señal/VAD antes de codificarse. Si ningún segmento resulta
utilizable, devuelve análisis fallido, nunca una lista automática de ausencias. Las pausas separan
segmentos de energía; eso no equivale a separar hablantes que se solapan.

## Comprobaciones realizadas

Las pruebas cubren tipos/dimensiones de vectores, norma y conservación de escala facial, WAV inválido,
silencio, duración, saturación, VAD sin voz suficiente, RGB, imagen corrupta, rostro pequeño/recortado,
cero/varios rostros y rechazo antes de llamar a Oracle. AppTest comprueba el formulario: una voz
silenciosa no crea el perfil y, al eliminarla, se permite el alta sin voz; varios rostros tampoco crean
cuenta. La integración Oracle guarda vectores válidos, verifica su contenido/norma y revierte el fixture.

No se utilizan capturas reales ni se mide precisión con estas pruebas. Quedan pendientes calibración,
iluminación/desenfoque/poses, el clasificador con pocos perfiles y el ensayo de dispositivos.
Resultado local: **106 pruebas aprobadas**, incluida integración Oracle con rollback. La dependencia
directa SoundFile queda fijada en `requirements.txt` y ya estaba presente en el entorno auditado.

Fuentes del contrato: [Resemblyzer: dimensión y parámetros](https://github.com/resemble-ai/Resemblyzer/blob/master/resemblyzer/hparams.py),
[normalización del codificador](https://github.com/resemble-ai/Resemblyzer/blob/master/resemblyzer/voice_encoder.py)
y [dlib: descriptores faciales y distancia euclidiana](https://dlib.net/face_recognition.py.html).
