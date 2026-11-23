# Clave común para la demostración estudiantil

Decisión del 22/11/2026: durante la presentación se permite entrar a cualquier
estudiante activo mediante código institucional o ID interno y una clave común, incluso sin
documento registrado, biometría o autorización excepcional individual.

## Preparación y uso

Oracle debe tener la migración `010_prueba_academica.sql`. Conserva las 14 tablas,
140 columnas y 11 FK; amplía dos CHECK para el estado `PRUEBA_ACADEMICA`.
El instalador y los migradores incluyen 010; el arranque comprueba 001–010.

```powershell
.\.venv\Scripts\python.exe scripts\preparar_prueba_academica.py --activar-local
```

El generador crea `.local/CLAVE_MAESTRA_ESTUDIANTE.md` y
`.local/prueba_academica.env`. No muestra la contraseña en consola. Conserva la
clave si ya existe y, por defecto, fija el cierre al final del día siguiente en
America/Bogota. Se puede indicar otra fecha con `--hasta`, siempre con zona horaria.
`--activar-local` añade solamente los dos valores al archivo privado de Streamlit.

En Render, importar **solo** `.local/prueba_academica.env` desde Environment →
Add from .env, guardar las variables y desplegar el commit actualizado:

- `ESTUDIANTE_CLAVE_MAESTRA`: secreto común privado, entre 12 y 72 bytes.
- `ESTUDIANTE_CLAVE_MAESTRA_HASTA`: límite ISO 8601 con zona horaria.

En Portal del estudiante → **No puedo completar la validación biométrica** aparece
**Demostración académica** mientras ambos valores son válidos. Seleccionar código
institucional o ID interno, introducirlo y utilizar la clave común. No se necesita
cámara ni documento. Las cuentas archivadas se rechazan; las heredadas sin código
pueden acceder por su ID interno.
Quien conoce la clave puede acceder al portal de cualquier estudiante activo cuyo
código conozca durante la vigencia configurada.

## Sesión y auditoría

El acceso guarda el estado y método `PRUEBA_ACADEMICA`, cero factores biométricos y
fecha de verificación. No registra una asistencia ni concede roles docentes o
administrativos. La interfaz muestra expresamente el método académico.

Se conserva la autorización excepcional normal: este acceso no cambia aprobador,
documento, contraseña alternativa, vigencia ni bandera de excepción. El último
método de acceso y la versión sí cambian, como ocurre al abrir las otras sesiones.

Se registran `CREDENCIAL_VALIDADA`, `ACCESO_VERIFICADO` y los fallos con el método
académico, sin guardar la clave ni el código en el motivo. La apertura es atómica
y utiliza pruebas firmadas de 90 segundos, cuenta activa y versión de un solo uso.
Cinco fallos bloquean el identificador durante quince minutos.

Los tokens de prueba quedan ligados al estudiante, clave y fecha. La validación
ordinaria y la validación dentro de operaciones protegidas comprueban su firma y
vigencia. Retirar/cambiar la clave o cambiar la fecha invalida las sesiones de
prueba anteriores. Vencer el modo impide nuevas entradas y el uso de esos tokens.
Las sesiones ordinarias no dependen de esta configuración.

Para desactivar antes, eliminar ambas variables y guardar la configuración en
Render. El formulario desaparece. Los eventos y el último estado permanecen como
historia; un acceso normal posterior registra su método real.

## Comprobación técnica

Pruebas unitarias cubren modo apagado, fecha ausente/sin zona/vencida, clave errónea,
cuentas inactivas, tokens alterados, cruce de roles/cuentas, rotación, versión y
presentación del estado en la sesión. Las integraciones usan cuentas sintéticas
propias y limpian sus filas; comprueban dos alumnos sin excepción, auditoría,
bloqueo, replay, desactivación y acceso biométrico posterior.

Las pruebas de página/cámara siguen a cargo del usuario. Los archivos privados
quedan fuera de Git y del paquete público de exposición. Los PDF del esquema 009
conservan su edición; este documento registra la ampliación 010.
