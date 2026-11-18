# Ausencia, sin muestra y análisis fallido — versión 004

Implementado el 11 de noviembre de 2026. La decisión académica final y el resultado del
reconocimiento son datos distintos.

| Resultado original | Qué significa | Decisión inicial y confirmación |
| --- | --- | --- |
| Presente | Análisis completado con coincidencia. | Presente; puede corregirse con motivo. |
| Ausente | Análisis completado sin coincidencia para un estudiante que tiene muestra. | Propuesta de ausente, sujeta a revisión; no es una medición de certeza de ausencia física. |
| Sin muestra | Falta el vector de voz o rostro del estudiante. | Pendiente. El profesor debe elegir presente/ausente y justificarlo, incluso si elige ausente. |
| Análisis fallido | Falló el procesamiento o no hubo segmentos analizables. | No confirmable. No se guarda asistencia ni se cierra la clase. Regrabar o usar otro método. |

## Flujo de voz

`procesar_audio_masivo` devuelve `ResultadoAudio`, con estado `COMPLETADO`, `SIN_MUESTRAS`
o `FALLIDO`; no devuelve el antiguo `{}` para ocultar excepciones. Un resultado completado sin
coincidencias sí puede contener puntajes vacíos y se distingue explícitamente de un fallo.
Si ocurre una excepción después de una coincidencia parcial, se descarta el análisis completo.

Se comprueba que haya audio/segmentos, que no sean silencio puro y que los valores básicos sean
finitos. No se convierte la ausencia de segmentos o un vector inválido en un resultado negativo.
Los errores registran etapa y tipo de excepción, sin audio, vectores ni mensajes de terceros.
El punto 3 amplía estos controles con [validación del registro y normalización de vectores](VALIDACION_MUESTRAS.md).
La evaluación de ruido y calidad con dispositivos reales, la calibración de umbrales y la
separación de hablantes continúan pendientes en el roadmap.

La interfaz rechaza respuestas con el formato antiguo, invalida cualquier propuesta anterior
antes de analizar y muestra los fallos en una tabla sin botón de confirmación. La capa de servicios
también rechaza `ANALISIS_FALLIDO`, aunque se intenten forzar decisiones manuales. Para un fallo
facial se informa el error y se descarta la propuesta anterior sin generar registros nuevos.
Un perfil facial sin muestra queda pendiente igual que uno sin voz.

El editor utiliza **Decisión: Pendiente / Presente / Ausente** en lugar de un checkbox: una casilla
sin marcar no permite distinguir ausencia de falta de decisión. Detección, fuentes e identificadores
siguen sin edición. Las decisiones pendientes y los motivos faltantes se rechazan antes de consumir
la propuesta, para que el profesor pueda completar la revisión.

## Oracle y compatibilidad

La migración `004_estados_deteccion.sql` añade `ESTADO_DETECCION`, permite `PRESENTE_DETECTADO=NULL`
solo para `SIN_MUESTRA` y conserva los registros anteriores como detecciones conocidas 0/1.
`PRESENTE` final sigue siendo obligatorio y limitado a 0/1: no se confirma una clase incompleta.
Una resolución de sin muestra exige `CORREGIDO_MANUAL=1`, motivo, autor y fecha. No se utiliza cero
como sustituto de la detección desconocida.

`PKG_CLASES` rechaza estados incoherentes, análisis fallidos y decisiones finales nulas. Las
restricciones también impiden insertar directamente una resolución automática sin muestra. Los
triggers conservan la detección original y añaden su estado a las instantáneas de auditoría de bajas
y correcciones; la comparación de valores nulos impide cambiar posteriormente un desconocido a cero.

Las solicitudes antiguas sin `estado_deteccion` se admiten solo si su `detectado` es un 0/1 conocido.
En Oracle 18c, la lectura de ese campo opcional desactiva temporalmente el error de clave ausente
y valida su tipo después. Los contratos nuevos envían el estado explícito.
La idempotencia de clases y su restricción única se conservan.

Desde la raíz, con la aplicación detenida:

```powershell
.\.venv\Scripts\python.exe -B scripts\oracle.py migrar
.\.venv\Scripts\python.exe -B scripts\oracle.py verificar
.\.venv\Scripts\python.exe -B scripts\oracle.py demostrar-estados
```

`migrar` verifica un respaldo privado antes de aplicar las versiones pendientes; 004 se puede
reejecutar. No ejecutar 003 manualmente sobre 004: se añadió una guardia contra esa degradación.
El laboratorio muestra el rechazo de fallo global y de sin muestra sin motivo, la resolución
manual que conserva `NULL` y un rollback final. No deja personas, asistencias ni historial de prueba.

Las vistas `V_REGISTROS_ASISTENCIA` y `V_AUDITORIA_ASISTENCIA` exponen el estado original, separado
del presente/ausente final. Los porcentajes continúan calculándose sobre las decisiones confirmadas.
Las instantáneas anteriores que no contenían detección original conservan su estado desconocido;
no se inventa información histórica.

## Verificación y límites

Las pruebas automáticas cubren excepciones en cada etapa, errores después de resultados parciales,
silencio puro, falta de segmentos, valores no finitos, resultados negativos válidos, estudiantes
sin muestra y bloqueo de confirmación. AppTest comprueba audio/rostro, el editor y la resolución
manual. Oracle comprueba el `NULL`, el motivo obligatorio, la auditoría, restricciones y rechazo
de fallos/decisiones pendientes, además de las regresiones de concurrencia de 003.

La precisión del clasificador y las condiciones reales de cámara/micrófono no se han validado
con estas pruebas. El ensayo real permanece al final, según lo acordado.
Resultado local: 81 pruebas aprobadas, migración 004 aplicada y reejecutada sin duplicar versión,
objetos válidos y laboratorio SQL*Plus completado con rollback de sus fixtures.

Referencia para la implementación JSON: [Oracle 18c: tipos JSON de PL/SQL](https://docs.oracle.com/en/database/oracle/oracle-database/18/arpls/json-types.html).
