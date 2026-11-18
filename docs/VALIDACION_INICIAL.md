# Verificación de la base del roadmap

Este informe conserva la evidencia original de la versión 001. La actualización posterior a 002,
sus disparadores y 17 pruebas se documentan en [DISPARADORES_Y_PLSQL.md](DISPARADORES_Y_PLSQL.md).

Fecha: 8 de noviembre de 2026. Equipo probado: Windows x64, Python 3.11.9, Oracle XE 18c,
SQL*Plus 18.4. La verificación no acredita todavía otros sistemas ni precisión biométrica.

## Resultado

- Usuario dedicado `UPC_ASISTENCIA`, servicio `localhost:1521/XEPDB1`.
- Acceso efectivo comprobado con SQL*Plus y python-oracledb thin.
- Seis tablas, siete vistas, especificación y cuerpo `PKG_ASISTENCIA` válidos.
- `USER_ERRORS` vacío y versión de esquema `001` registrada.
- Cinco tablas funcionales sin personas, matrículas ni asistencias después de las pruebas.
- Sin borrado de usuarios ni objetos anteriores; nueva instalación en un esquema propio.
- Clave aleatoria local, sin contraseña predeterminada en el código ni en los scripts públicos.
- Certificados de desarrollo creados por equipo; almacenes de confianza y firewall sin modificar.
- HTTPS real comprobado contra `/_stcore/health` y `/`: estado 200, certificado validado con la CA local.
- El servidor temporal de prueba se detuvo; para usar la app ejecutar `iniciar.cmd`.
- QR local: `https://localhost:8501/?join-code=...`, con caracteres del código codificados.
- Inicio y acceso docente sin excepciones con Streamlit AppTest.
- Venv existente validado; selección del venv comprobada desde otro directorio con Python global.
- Dependencias importadas y `pip check` sin conflictos declarados.
- DDL exportado a `exports/esquema_ddl.sql`; no contiene datos ni claves de conexión.

## Pruebas automatizadas

Seis pruebas pasan al habilitar la integración Oracle: prioridad de configuración, códigos QR,
rechazo de URLs inválidas, error de configuración antes de conectar, certificado firmado con SAN
para localhost/LAN, y flujo de integración PL/SQL/fechas.

Desde CMD:

```bat
set UPC_TEST_ORACLE=1
.venv\Scripts\python.exe -m unittest discover -s tests -v
set UPC_TEST_ORACLE=
```

La prueba de Oracle inserta fixtures con identificadores únicos y revierte sus filas al finalizar.
Los contadores de identidad de Oracle pueden avanzar aunque se haga rollback; no se reinician.
Sin esa variable la prueba de integración se omite y las otras cinco se ejecutan normalmente.

La prueba real comprueba rechazo de asistencia sin matrícula, rechazo de matrícula repetida,
porcentaje de asistencia y persistencia del offset `-05:00` con una sesión configurada en `+09:00`.

## Corrección adicional de fechas

Se comprobó que el driver devuelve `TIMESTAMP WITH TIME ZONE` como datetime sin `tzinfo` y que
el enlace datetime no conserva necesariamente el desplazamiento original. Para nuevas asistencias,
`bd.py` envía ISO con seis decimales y offset, usa `TO_TIMESTAMP_TZ` al insertar y `TO_CHAR` con
offset explícito al leer. Las fechas históricas sin zona de entrada mantienen la convención UTC
que ya documentaba el proyecto. La corrección no transforma filas de otros esquemas.

## Pendiente

Confiar en la CA en el navegador, probar captura real de cámara/micrófono y acceso desde teléfono,
ensayar una instalación limpia en otro PC y resolver las fases funcionales 2–6 del roadmap.
No se abrió ni se configuró SQL Developer: queda para la fase final solicitada.
Los modelos siguen avisando que usan `pkg_resources`; el pin de setuptools conserva compatibilidad
mientras se planifica sustituir o actualizar esas dependencias.
