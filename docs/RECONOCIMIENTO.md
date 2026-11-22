# Reconocimiento: referencias, rechazo y evaluación

Actualizado el 11 de noviembre de 2026. Corresponde al punto 1 de la revisión actual.

El clasificador facial compara los descriptores de dlib directamente por distancia euclídea.
Se retiró el SVM que podía quedar sin entrenar con pocos estudiantes. Cero referencias produce
un resultado vacío; una referencia permite reconocer y rechazar; varias se comparan por distancia.
Los vectores inválidos producen un error visible de análisis y no una asistencia automática.

La coincidencia exige dos condiciones: superar el umbral absoluto y mantener suficiente margen
frente a la siguiente identidad. Un empate se rechaza. La voz utiliza similitud coseno con las
mismas condiciones. Una distancia o similitud no representa un porcentaje de certeza.

| Configuración | Valor inicial | Regla |
| --- | --- | --- |
| FACIAL_UMBRAL | 0.55 | Distancia máxima |
| FACIAL_MARGEN | 0.05 | Separación mínima entre las dos mejores identidades |
| VOZ_UMBRAL | 0.65 | Similitud mínima |
| VOZ_MARGEN | 0.05 | Separación mínima entre las dos mejores identidades |

Se pueden configurar en el entorno o en `.streamlit/secrets.toml`. Son valores iniciales;
no constituyen una calibración medida en esta institución. La evaluación genera una propuesta
y nunca modifica automáticamente estos valores.

Para fotografías de una materia se comparan todas las referencias faciales activas y después
se exige que la identidad ganadora pertenezca a su matrícula. Así un estudiante conocido de otra
materia no se reasigna a la persona más parecida de la lista. En voz se utilizan las referencias
de la matrícula y se aplican umbral y margen; debe medirse especialmente la confusión con voces
externas en el ensayo final. El acceso facial del estudiante sigue siendo una identificación
biométrica sin prueba de presencia real: una fotografía podría engañarla.

## Uso de memoria de las capturas en Render

El 22/11 se optimiza el almacenamiento temporal de fotos de asistencia. La sesión conserva
el original JPEG/PNG comprimido y una miniatura de hasta 480 píxeles por lado. La galería
usa la miniatura; el análisis abre una foto cada vez a resolución original, aplica la misma
orientación EXIF y conversión RGB y libera la imagen al terminar. No se reescala la entrada
al reconocimiento ni se modifican los modelos, los umbrales o los permisos de matrícula.
Se mantienen 12 fotos, 10 MB/20 MP por foto y 60 MB de originales por toma.

Una comparación local con un JPEG sintético de 2048 × 1536 pasó de 9.437.184 bytes RGB
a 2.428.600 bytes de original y miniatura: 74,27 % menos almacenamiento de esa captura.
Los píxeles analizados resultaron idénticos. Es una muestra de almacenamiento, no una
medición de RSS ni una promesa de reducción del proceso Render. Evidencia privada:
`.local/hosting/optimizacion_fotos.json`. No se guardaron fotografías de personas.

Verificación: 22 pruebas de sesiones y 19 de interfaz, incluido un caso que distingue
miniatura y original para garantizar que la IA recibe la imagen completa. Faltan mediciones
en Render con varias capturas y usuarios; las pruebas iniciales que el usuario hizo con
un familiar se comunican como satisfactorias, sin convertirlas en una tasa de precisión.

## Reutilización y lectura de audio

En una toma de voz se prepara un único clasificador de referencias y se reutiliza para
todas las intervenciones. Se mantienen los mismos candidatos, normalizaciones, umbral,
margen y puntajes; no se repite la construcción del clasificador por cada segmento.
La función de identificación individual conserva su interfaz anterior.

La lectura WAV conserva una onda mono y decodifica como máximo 65.536 muestras por
bloque, evitando conservar además el audio estéreo completo. Se usa la misma media de
canales, frecuencia final de 16 kHz, comprobación de señal y límites de duración/tamaño.
Una prueba compara exactamente la onda resultante con la lectura completa anterior;
otra comprueba varias intervenciones y un único clasificador. Se conservan los rechazos
de silencio, saturación, muestras ausentes y análisis fallido.

Regresión del conjunto: 276 pruebas, 207 aprobadas y 69 integraciones omitidas, sin fallos.
Evidencia privada: `.local/hosting/pruebas_optimizacion.json` y su log. La comprobación
con dlib real usa únicamente una imagen sintética sin rostros y no consulta Oracle.

Las mejoras limitan almacenamiento temporal y trabajo repetido. No cambian dlib,
Resemblyzer/PyTorch ni sus modelos; no acreditan memoria suficiente para cualquier
concurrencia en Render. La medición del proceso y el ensayo con dispositivos siguen pendientes.

## Evaluar y proponer umbrales

```powershell
.\.venv\Scripts\python.exe scripts\evaluar_reconocimiento.py .local\conjunto.json --calibrar --salida .local\evaluacion.json
```

El archivo contiene `origen` (`sintetico` o `consentido`), `modalidad` (`facial` o `voz`),
`referencias` (objetos con `id` y `vector`) y `consultas` (objetos con `esperado` y `vector`).
`esperado: null` identifica una persona desconocida. Los vectores tienen 128 valores faciales
o 256 de voz. Para datos reales se exige además `consentimiento: true`; esta marca registra la
declaración del responsable del conjunto y no acredita por sí misma la obtención del consentimiento.

El informe cuenta aciertos, falsos rechazos, falsas aceptaciones de desconocidos y confusiones
entre identidades conocidas. FAR y FRR se calculan sobre sus respectivos grupos; si falta uno,
su tasa se informa como `null`. La propuesta exige al menos diez consultas conocidas y diez
desconocidas y un objetivo FAR máximo de 0.01. Si ningún ajuste lo satisface, no hay propuesta.
El informe no incluye los vectores; el conjunto de entrada sigue siendo privado.

Las pruebas automáticas cubren cero, una y pocas referencias, desconocidos, empates, matrícula,
vectores corruptos y el evaluador. Se usan datos sintéticos para verificar el software.
La precisión real requiere muestras consentidas variadas, separar calibración de evaluación,
medir FAR/FRR/confusiones e incluir ruido, iluminación y dispositivos distintos. Esa medición,
la diarización de voces solapadas, múltiples muestras y protección contra reproducción quedan
en la etapa final de reconocimiento avanzado y pruebas reales. No se declara una precisión medida.
