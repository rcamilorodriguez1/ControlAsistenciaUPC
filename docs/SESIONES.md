# Sesiones, capturas y confirmación de asistencia

Actualizado: 11 de noviembre de 2026.

**Guía vigente: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md), versión 007.** Autenticación
y sesión única en Oracle para los tres roles, revocación y navegación nativa sin logout.
Las secciones siguientes se conservan como documentación histórica de 001–006; su política
de regreso al inicio, QR y ausencia de revocación global fue sustituida por 007.

## Identidad y cierre

`src/utilidades/sesiones.py` centraliza la identidad del usuario. Para abrir un panel
deben coincidir la sesión activa, el rol, el portal, un identificador de usuario válido
y el token de la sesión. Un perfil guardado por sí solo no permite abrir el panel.
El contexto de auditoría de Oracle utiliza esta misma validación.

Cada acceso crea un token nuevo y elimina el estado anterior. El cierre de sesión y
el regreso al inicio eliminan perfiles, contraseñas de formularios, capturas de cámara,
audio, fotos, claves de deduplicación y resultados pendientes. Se conserva únicamente
el destino del portal y el estado básico de una sesión nueva sin autenticar.
El perfil utilizado por el panel contiene ID, nombre y, en profesores, usuario;
no conserva el hash de contraseña ni los vectores biométricos recibidos durante el acceso.

Las sesiones antiguas sin token se invalidan al actualizar la aplicación y requieren
iniciar sesión otra vez. Los diálogos de creación, inscripción y asistencia comprueban
que siguen perteneciendo a la sesión que los abrió.

## Materia, toma y resultado

Cada toma tiene token de sesión, profesor, materia e identificador propio. Cambiar de
materia elimina el trabajo de la anterior; una recarga del script sobre la misma toma
conserva su trabajo. Confirmar, descartar o borrar las fotos renueva el identificador
de toma, borra las capturas y permite volver a subir el mismo archivo.

Las propuestas de voz y foto comparten una estructura con ID y contexto. Los diálogos
leen únicamente la propuesta vigente. Añadir una foto, reemplazar/borrar el audio o
ejecutar otro análisis invalida la propuesta anterior. Abrir el modo de voz también
invalida una propuesta facial. Si se cierra el diálogo facial sin decidir, el panel
permite volver a revisar el resultado pendiente.

Las fotografías se deduplican por SHA-256 del contenido, compartido entre cámara y
subida. Se admiten JPEG/PNG y se aplican estos límites antes de agregarlas a la toma:

| Recurso | Límite |
| --- | --- |
| Fotos por toma | 12 |
| Tamaño por foto | 10 MiB |
| Resolución por foto | 20 millones de píxeles |
| Archivos de fotos acumulados por toma | 60 MiB |
| Audio enviado al análisis de asistencia | 20 MiB |

Las imágenes se orientan según EXIF y se convierten a RGB. El límite de bytes de archivos
no representa un límite equivalente de memoria de imágenes descomprimidas. Los límites
de calidad, duración y silencio del audio, así como las capturas del registro biométrico,
requieren la revisión de reconocimiento prevista en la fase 4.

## Confirmación y Oracle

`src/servicios/asistencia.py` comprueba el ID del resultado y su contexto, consume la
propuesta y llama a `crear_asistencia` con el profesor autenticado. Dentro de la operación
Oracle se vuelve a consultar la propiedad de la materia y su matrícula actual, se rechazan
estudiantes duplicados, estados inválidos y fechas distintas dentro de una misma propuesta.
Si la matrícula cambió desde el análisis, se exige analizar nuevamente.

Desde 003, `PKG_CLASES` bloquea la materia/clase y adquiere un bloqueo SHARE de matrícula durante
la confirmación para impedir altas y retiros mientras compara la lista. Si hay otra escritura
de matrícula en curso, devuelve un aviso sin esperar indefinidamente.
El código de interfaz utiliza la ruta con profesor; el parámetro opcional de la utilidad
de base de datos se conserva para las herramientas y pruebas anteriores.

La propuesta se consume antes de escribir y no puede confirmarse dos veces. La operación
de guardado no reintenta automáticamente si pierde la conexión o la respuesta del COMMIT.
Ante un error incierto se pide revisar los registros antes de repetir el análisis.
La unicidad entre sesiones, pestañas y nuevos análisis está implementada en 003 mediante
`CLASES`, sus restricciones y el procedimiento idempotente. La toma temporal incluye ahora
el ID de clase y se invalida también al cambiar de clase dentro de la misma materia.
Modelo y revisión: [CLASES_Y_REVISION.md](CLASES_Y_REVISION.md).
Desde 004 un fallo no permite confirmar y un estudiante sin muestra requiere una decisión explícita
con motivo: [ESTADOS_DETECCION.md](ESTADOS_DETECCION.md).

## Navegación e inscripción

Los botones de acceso/registro cambian el formulario mediante callbacks y limpian sus
campos. El parámetro `join-code` se procesa antes de renderizar el portal. Si procede de
una sesión de profesor, se cierra esa identidad y se solicita el acceso como estudiante.
Mientras está pendiente la invitación, se desactiva el diálogo de inscripción manual.
Aceptar, rechazar o cerrar la invitación elimina únicamente `join-code`, conservando
otros parámetros de la URL. Se muestran mensajes de código inexistente y matrícula repetida.

## Verificación y límites

Las pruebas de `tests/test_sesiones.py` cubren identidad, cierre, cambio de usuario/materia,
diálogos antiguos, copias de resultados, consumo de propuestas y tratamiento de fotos.
`tests/test_sesiones_interfaz.py` ejecuta los portales con Streamlit AppTest y sustituye
las consultas y la IA: verifica navegación, cierre, invitaciones y resultados pendientes.
AppTest ejecuta el script completo; la confirmación de voz mantiene abierto el diálogo
durante esa ejecución. El rerun parcial del navegador requiere el ensayo manual indicado abajo.
La integración Oracle comprueba propietario incorrecto, duplicados, cambios de matrícula y
guardado válido. Sus fixtures terminan en rollback y no dejan filas de prueba.
La primera entrega de sesiones pasó 47 pruebas; la ampliación de clases añade pruebas de
concurrencia Oracle y revisión manual. Resultado actualizado en [CLASES_Y_REVISION.md](CLASES_Y_REVISION.md).

Desde PowerShell, para ejecutar también las pruebas que usan Oracle local:

```powershell
$env:UPC_TEST_ORACLE = '1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

La sesión pertenece a la conexión de Streamlit. El token es un marcador interno del estado;
no es una credencial persistente ni sustituye un proveedor de autenticación. No se añadió
caducidad por inactividad ni cierre global de todas las pestañas. Tampoco se modifica aquí
la clasificación facial/de voz ni el tratamiento de fallos de reconocimiento.

Queda el ensayo con dispositivos reales: iniciar sesión con un usuario, agregar capturas,
cambiar entre dos materias y cerrar sesión; entrar con otra persona y comprobar que no
hereda capturas ni resultados. Repetir confirmación y descarte con foto/voz, y abrir/cerrar
una invitación QR. Revisar finalmente los registros de Oracle y el historial de matrícula.
