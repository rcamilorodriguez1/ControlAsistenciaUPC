# Documentación de UPC | Aula

Este directorio reúne las decisiones, justificaciones, instrucciones de uso y resultados de
verificación del proyecto. El registro resumido de entregas está en [CAMBIOS.md](CAMBIOS.md).

## Por dónde empezar

| Necesidad | Documento |
| --- | --- |
| Leer la memoria académica y técnica completa | [Documentación integral en PDF](UPC_Aula_Documentacion_Integral.pdf) |
| Explorar las pantallas y sus recorridos por rol | [Mockup navegable](mockup/index.html) · [Alcance](mockup/README.md) |
| Consultar los cambios realizados | [Registro de cambios](CAMBIOS.md) |
| Completar organización y despliegue de la versión actual | [Primer roadmap](ROADMAP.md) |
| Consultar las mejoras posteriores de frontend y base de datos | [Segundo roadmap](ROADMAP_2.md) |
| Distinguir lo probado de lo aprobado por el usuario | [Seguimiento del frontend](FRONTEND.md) |
| Instalar, ejecutar y comprobar HTTPS | [Instalación](INSTALACION.md) |
| Preparar Linux, HTTPS público y Oracle Cloud | [Despliegue en la nube](DESPLIEGUE.md) |
| Entender cada tabla, relación, consulta y disparador actual | [Funcionamiento de la base de datos](BASE_DE_DATOS.md) |
| Utilizar la última entrega de excepciones biométricas | [Excepciones biométricas](EXCEPCIONES_BIOMETRICAS.md) |

## Memoria integral del proyecto

La [edición 1.0 en PDF](UPC_Aula_Documentacion_Integral.pdf), del 18 de noviembre de 2026,
reúne el planteamiento, la justificación, los objetivos, los requisitos, la arquitectura,
los flujos por rol, la seguridad, la interfaz, la instalación, las evidencias y el roadmap.
Su anexo incorpora íntegra la guía de base de datos, con diccionario, relaciones,
disparadores, paquetes y consultas. Distingue implementación, verificación y aceptación.

Son **72 páginas**, con portada institucional, índice numerado y navegable, marcadores,
diagramas y tablas A4 apaisadas para el diccionario y las restricciones. El logotipo se
conserva tal como fue extraído del manual UPC; la captura corresponde a la portada local.
No contiene credenciales, registros personales ni claves privadas.

Fuentes editables: [memoria principal en Markdown](INFORME_PROYECTO.md),
[guía de base de datos](BASE_DE_DATOS.md) y [maquetación completa en HTML](UPC_Aula_Documentacion_Integral.html).
El HTML incorpora las imágenes y los diagramas, sin depender de rutas absolutas del equipo.
El PDF es una fotografía documental de esta edición; las guías temáticas y el roadmap
siguen registrando la evolución posterior.

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
| Modelo de datos completo y consultas de estudio | [Base de datos: guía detallada](BASE_DE_DATOS.md) |
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
