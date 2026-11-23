# Documentación de UPC | Aula

Este directorio reúne las decisiones, justificaciones, instrucciones de uso y resultados de
verificación del proyecto. El registro resumido de entregas está en [CAMBIOS.md](CAMBIOS.md).

## Por dónde empezar

| Necesidad | Documento |
| --- | --- |
| Leer la memoria académica y técnica completa | [Documentación integral 1.2 en PDF](UPC_Aula_Documentacion_Integral.pdf) |
| Presentar el producto a aliados o posibles inversionistas | [Presentación comercial y guion](PRESENTACION_COMERCIAL.md) |
| Llevar todo a la exposición de Base de Datos | [Paquete del Escritorio y orden de exposición](PAQUETE_PRESENTACION_BASE_DATOS.md) |
| Explorar las pantallas y sus recorridos por rol | [Mockup navegable](mockup/index.html) · [Alcance](mockup/README.md) |
| Consultar los cambios realizados | [Registro de cambios](CAMBIOS.md) |
| Consultar el plan general y sus ramas | [General](ROADMAP.md), [frontend/backend](ROADMAP_FRONT_BACK.md), [base de datos](ROADMAP_BASE_DATOS.md) |
| Consultar propuestas de arquitectura y el plan anterior | [Evolución](ROADMAP_2.md), [histórico](ROADMAP_HISTORICO.md) |
| Distinguir lo probado de lo aprobado por el usuario | [Seguimiento del frontend](FRONTEND.md) |
| Instalar, ejecutar y comprobar HTTPS | [Instalación](INSTALACION.md) |
| Preparar Render con Oracle Autonomous | [Despliegue en la nube](DESPLIEGUE.md) |
| Separar la cuenta de ejecución del propietario Oracle | [Cuenta de ejecución, permisos y preparación cloud](CUENTA_EJECUCION.md) |
| Entender cada tabla, relación, consulta y disparador actual | [Funcionamiento de la base de datos](BASE_DE_DATOS.md) |
| Explorar las tablas sin conectar a Oracle | [Catálogo interactivo](base_datos/index.html) · [diccionario vigente](DICCIONARIO_DATOS.md) |
| Explicar la conexión y el aporte del proyecto | [Conexión](CONEXION_BASE_DATOS.md) · [goodwill](GOODWILL.md) |
| Consultar el perfil y la configuración del docente | [Perfil docente](PERFIL_DOCENTE.md) |
| Utilizar la última entrega de excepciones biométricas | [Excepciones biométricas](EXCEPCIONES_BIOMETRICAS.md) |
| Entrar con clave común durante la presentación académica | [Modo temporal de prueba estudiantil, esquema 010](PRUEBA_ACADEMICA.md) |
| Sustituir el código institucional por documento | [Documento estudiantil: registro, perfil y acceso, esquema 011](DOCUMENTO_ESTUDIANTIL.md) |

## Contexto del proyecto y orden de publicación

Al retomar el trabajo, leer este índice, las entradas recientes de [CAMBIOS.md](CAMBIOS.md),
la secuencia actual de [ROADMAP.md](ROADMAP.md) y la guía del área modificada. Estos
documentos mantienen el contexto dentro del proyecto; las copias antiguas de
`.local/publicacion/` y `.local/README.upc.md` son material histórico, no la documentación
vigente. El PDF conserva la edición indicada hasta que se regenere expresamente.

Orden aclarado por el usuario el 22 de noviembre de 2026:

1. **MD con los cambios:** registrar qué cambió, motivo, pruebas y límites en CAMBIOS.md;
   actualizar la guía correspondiente y ROADMAP.md si cambia el estado o la continuación.
   Guardar las evidencias privadas en `.local/`, sin copiar sus secretos a los MD.
2. **Commit local:** revisar el diff y los archivos preparados, ejecutar las comprobaciones
   que correspondan y guardar código y documentación juntos en Git. Un commit deja un
   punto de referencia local y todavía no publica nada en GitHub ni en Render.
3. **Push:** publicar los commits en la rama de GitHub con la cadencia indicada abajo.
   Con Auto-Deploy **On Commit**, Render construye la versión publicada en `main`.
   Confirmar el commit desplegado y su resultado antes de registrar el servicio como operativo.

Variables y archivos secretos se administran por separado en Render y permanecen fuera
del repositorio.

### Cadencia de commits y push

Instrucción vigente del usuario, 22/11/2026; sustituye la espera de confirmación para cada push:

- **Commit cada 3 cambios menores** terminados y comprobados. Un cambio es una unidad
  lógica de trabajo, no cada archivo, línea, prueba o MD actualizado para documentarla.
- Los cambios menores incluyen ajustes acotados de documentación, editor o presentación,
  sin alterar los flujos, las reglas de negocio ni los contratos de acceso o despliegue.
- Un cambio mayor modifica comportamiento relevante, seguridad, esquema, dependencias
  o despliegue. Se guarda en un commit propio al terminar y comprobarlo, sin esperar
  a acumular otros dos cambios. El agente clasifica cada cambio según su impacto.
- **Push cada 5 cambios terminados desde el último push, o al completar un punto del
  roadmap**, lo que ocurra primero. Al llegar al umbral, confirmar también los cambios
  pendientes aunque todavía no sumen tres menores, respetando MD → commit → push.
- La cadencia autoriza esas publicaciones sin pedir otra confirmación. Una petición
  explícita de commit o push puede adelantar el paso. Si una comprobación falla, corregirla
  antes de publicar y registrar el bloqueo; no marcar un punto como completo sin su evidencia.

Último lote preparado, contado desde `1391969`:

| Referencia | Estado |
| --- | --- |
| Base del lote | `1391969`, rama `main` |
| Cambios del lote | Documento en registro, perfil, administración y acceso de prueba; migración 011 y conservación de datos anteriores |
| Verificación | 155 pruebas técnicas aprobadas: 95 aisladas, 45 locales y 15 con conexiones limitadas de Autonomous; respaldos y esquema 011 correctos |
| Commit/push | Cierre de FB6.3; el hash final queda en Git y el seguimiento privado. La clave común sigue activándose con las dos variables privadas de Render |

Registrar el estado operativo del lote en `.local/publicacion/seguimiento.json`, con
los hashes verificados y los contadores pendientes. Tras cada commit, reiniciar el
contador de menores pendientes; tras cada push verificado, reiniciar el de cambios sin
publicar. Este MD conserva el corte del lote antes de confirmarlo: consultar Git y el
seguimiento privado para conocer el estado posterior sin crear un commit solo para
referenciar su propio hash. Actualizar ambos al completar una nueva unidad de trabajo;
el seguimiento pertenece al mismo cambio que registra.

## Memoria integral del proyecto

La [edición 1.2 en PDF](UPC_Aula_Documentacion_Integral.pdf), del 22 de noviembre de 2026,
actualiza la edición 1.1. Contiene **87 páginas** con portada y créditos completos,
índice numerado/navegable, marcadores y tablas A4 apaisadas para el diccionario.

Incluye Oracle 001–009, Render como alojamiento elegido, las tres cuentas técnicas,
53 permisos de runtime, perfiles/agenda docente, configuración y excepciones de
entrega manual. Distingue la evidencia Live anterior, las publicaciones posteriores
y las pruebas de la página/biometría que corresponden al usuario.

La memoria principal desarrolla problema, objetivos, arquitectura, seguridad, operación,
evidencia y valor. El anexo A explica funcionamiento y PL/SQL; el anexo B contiene
las 140 columnas y sus restricciones, desde el catálogo de Autonomous 009. Se
conserva la procedencia de cada evidencia, sin presentar los resultados históricos
como una nueva ejecución. No se incluyen valores de contraseñas ni documentos personales.

Fuentes editables: [memoria principal](INFORME_PROYECTO.md),
[guía funcional Oracle](BASE_DE_DATOS.md), [diccionario vigente](DICCIONARIO_DATOS.md)
y [maquetación HTML](UPC_Aula_Documentacion_Integral.html). La generación lee archivos
locales; no conecta con Oracle, abre la página de la aplicación ni utiliza una cámara.

También está disponible la [presentación comercial](PRESENTACION_COMERCIAL.md):
[PowerPoint editable](UPC_Aula_Presentacion_Comercial.pptx) y
[PDF de 20 diapositivas](UPC_Aula_Presentacion_Comercial.pdf). Usa identidad UPC,
notas para exponer, evidencia del producto y una propuesta de piloto; los beneficios
y el modelo comercial todavía no medidos se identifican como hipótesis.

### Regenerar la memoria

El generador compartido es [scripts/generar_documentacion.py](../scripts/generar_documentacion.py).
Lee únicamente las fuentes documentales y los recursos gráficos; no conecta con Oracle ni
ejecuta la aplicación. Requiere Python 3.11, las
[herramientas opcionales](requirements-documentacion.txt) y un navegador Chromium,
Chrome, Brave o Edge instalado. Las herramientas no se añaden al runtime del portal.

Desde la raíz del repositorio, usando un entorno dedicado para documentación:

```powershell
python -m venv .local/venv-documentacion
.\.local\venv-documentacion\Scripts\python.exe -m pip install -r docs/requirements-documentacion.txt
.\.local\venv-documentacion\Scripts\python.exe scripts/generar_documentacion.py
```

En Linux, el intérprete de ese entorno está en `.local/venv-documentacion/bin/python`.
El navegador se detecta en las ubicaciones habituales; puede indicarse con `--navegador`
o `AULA_NAVEGADOR_PDF`. Se usa un perfil headless temporal, separado del perfil personal.
El generador actualiza el HTML/PDF y guarda comprobaciones y muestras de páginas en
`.local/memoria_pdf/`. Antes de entregar, revisar contenido, índice, márgenes y privacidad;
la generación no sustituye la aceptación funcional ni el ensayo público.

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
