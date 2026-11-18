# Documentación de UPC | Aula

Este directorio reúne las decisiones, justificaciones, instrucciones de uso y resultados de
verificación del proyecto. El registro resumido de entregas está en [CAMBIOS.md](CAMBIOS.md).

## Por dónde empezar

| Necesidad | Documento |
| --- | --- |
| Consultar los cambios realizados | [Registro de cambios](CAMBIOS.md) |
| Saber qué está implementado y qué falta | [Roadmap](ROADMAP.md) |
| Distinguir lo probado de lo aprobado por el usuario | [Seguimiento del frontend](FRONTEND.md) |
| Instalar, ejecutar y comprobar HTTPS | [Instalación](INSTALACION.md) |
| Utilizar la última entrega de excepciones biométricas | [Excepciones biométricas](EXCEPCIONES_BIOMETRICAS.md) |

## Guías por área

| Área | Documentos |
| --- | --- |
| Identidad visual, zoom y pie académico | [Identidad](IDENTIDAD_VISUAL.md), [zoom](ZOOM.md), [pie](PIE_ACADEMICO.md) |
| Autenticación, navegación y sesiones | [Portal y sesiones](PORTAL_Y_SESIONES.md), [recuperación de acceso](RECUPERACION_ACCESO.md) |
| Administración y reglas de negocio | [Administración](ADMINISTRACION.md), [reglas](REGLAS_NEGOCIO.md) |
| Perfil académico del estudiante | [Mi perfil](PERFIL_ESTUDIANTE.md) |
| Capturas y reconocimiento biométrico | [Validación de muestras](VALIDACION_MUESTRAS.md), [reconocimiento](RECONOCIMIENTO.md) |
| Clases y revisión de asistencia | [Clases](CLASES_Y_REVISION.md), [estados de detección](ESTADOS_DETECCION.md) |
| Disparadores, PL/SQL y presentación de Oracle | [Justificación de disparadores](DISPARADORES_Y_PLSQL.md), [SQL*Plus y SQL Developer](SQLPLUS_Y_SQLDEVELOPER.md) |
| Copias, restauración y migraciones | [Recuperación](RECUPERACION.md) |
| Evidencia de entregas anteriores | [Validación inicial](VALIDACION_INICIAL.md), [cierre de puntos 1, 3 y 4](CIERRE_1_3_4.md) |

## Dónde se guarda cada cosa

- **`docs/`**: documentación del proyecto y seguimiento de aceptación.
- **`sql/` y `sql/migraciones/`**: scripts ejecutables y versiones del esquema Oracle.
- **`tests/`**: pruebas automatizadas reproducibles.
- **`.local/`**: evidencias locales, capturas, informes de pruebas, respaldos y archivos privados.
  Las guías enlazan sus rutas cuando corresponde; esta carpeta está excluida de Git.
- **Oracle, `eventos_gestion`**: historial de acciones de la aplicación, incluidas las validaciones
  y autorizaciones excepcionales. La auditoría de uso es distinta del registro de cambios del código.

Cada nueva entrega debe registrar en `CAMBIOS.md` su alcance, guía, validación y pendientes,
actualizar el roadmap y mantener el detalle técnico en su guía temática. Las pruebas automáticas
y la aprobación del usuario se registran por separado. La documentación compartible contiene
rutas e instrucciones; las contraseñas, claves privadas y documentos personales permanecen fuera.
