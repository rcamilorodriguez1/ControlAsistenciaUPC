# Recuperación de acceso docente

Confirmación del usuario: **12 de noviembre de 2026**, el flujo «Olvidé mi contraseña» funciona
correctamente. Esto se registra por separado de las pruebas técnicas y no cierra el resto del frontend.

En el portal del profesor, **Olvidé mi contraseña** abre un formulario independiente con
usuario, autorización docente privada, contraseña nueva y confirmación. Se muestra el medidor
de fortaleza y la coincidencia en vivo. Volver al acceso limpia los campos; completar el cambio
regresa al login, sin autenticar automáticamente.

Se utiliza la misma autorización privada de alta docente (`PROFESOR_CLAVE_ALTA`, documentada
localmente en `.local/ALTA_DOCENTE.md`). Esta autorización permite restablecer cuentas docentes:
debe seguir bajo control administrativo, sin publicarse ni distribuirse como un dato ordinario
del perfil. El formulario no muestra la contraseña anterior.

## Validación y seguridad

- La validación se realiza en `src/servicios/recuperacion_acceso.py`, reutilizando la autorización
  existente y la política de contraseñas de 8–72 bytes UTF-8. No se aceptan confirmaciones distintas.
- Cinco intentos fallidos bloquean la recuperación de ese usuario durante quince minutos.
  El límite es persistente en Oracle y no depende de la pestaña ni del navegador.
- Datos incorrectos, cuentas inexistentes o archivadas generan la misma respuesta general.
- Se guarda únicamente bcrypt. El cambio, la revocación de sesiones, la limpieza del bloqueo
  de login y el evento de auditoría se confirman en una sola transacción, sin reintentar el COMMIT.
- El evento `RESTABLECIMIENTO_CLAVE` identifica la cuenta y el método autorizado, sin guardar
  contraseña, hash, autorización ni vectores. El actor se registra como SISTEMA: el formulario
  de recuperación no prueba que quien opera sea el titular de la cuenta.
- La transacción bloquea primero la sesión y después la cuenta. Si no había registro de sesión,
  crea uno revocado para mantener ese orden también frente a un primer login concurrente.
- Al abrir una sesión docente se vuelve a comprobar que el hash usado para verificar la
  contraseña siga vigente. Una verificación anterior al cambio no puede abrir un acceso nuevo.

La recuperación usa el esquema 007 existente, sin otra migración ni cambios de credenciales
de cuentas reales durante las pruebas. El usuario debe volver a iniciar sesión con la nueva clave.

## Validación

**170 pruebas aprobadas**, con integración Oracle: `.local/pruebas_recuperacion_completas.log`.
Incluyen recuperación válida, autorización incorrecta, cuenta inexistente/archivada, bloqueo,
revocación, auditoría sin secretos, limpieza de campos y rechazo de una verificación antigua.

La instancia real `https://localhost:8501` se revisó en escritorio y móvil emulado con datos
sintéticos, sin enviar el formulario ni cambiar contraseñas:
`.local/frontend/93c0cf25985c/resultado.json` (once vistas).

Archivos principales: `src/componentes/recuperar_clave.py`,
`src/servicios/recuperacion_acceso.py`, `src/pantallas/pantalla_profesor.py`,
`src/utilidades/sesiones.py`, `src/servicios/sesiones_servidor.py`, `static/css/styles.css`,
`scripts/verificar_frontend.py` y pruebas de recuperación/sesiones.

## Estudiantes: trabajo separado y pendiente

Por decisión del usuario, no se añadió recuperación ni contraseña estudiantil en esta entrega.
Esa decisión corresponde a la entrega de recuperación docente. En la ampliación del 17 de noviembre,
008 añade una alternativa estudiantil autorizada con documento y contraseña para excepciones
biométricas. Su recuperación se realiza mediante renovación administrativa y comprobación del
documento; no se permite restablecer una clave presentando solo un número de cédula.
Ver [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).

La próxima revisión debe diseñar por separado el login institucional, el registro controlado,
el documento como identificador distinto del código institucional, la relación con la biometría
y la recuperación ante fallos. El número de documento por sí solo no acredita la identidad.
