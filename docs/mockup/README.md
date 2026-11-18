# Mockup navegable de UPC | Aula

**Edición 1.0 · 18 de noviembre de 2026.**

Abrir [index.html](index.html) en Brave, Chrome o Edge. Funciona directamente desde el
archivo, sin servidor, Oracle ni instalación adicional. Para compartirlo, copiar la carpeta
`docs/mockup` completa: incluye el catálogo, los recursos y sus capturas.

## Qué representa

Es un mockup documental retrospectivo de la implementación: reúne **18 pantallas o estados**
de UPC | Aula con **59 capturas originales**. La navegación agrupa los recorridos por rol,
permite cambiar de pantalla y muestra las versiones de escritorio y móvil disponibles.
Se conserva el diseño de la aplicación, sin recrear o redibujar sus controles.

La interfaz del visor ofrece búsqueda, Anterior/Siguiente, enlaces a los siguientes pasos,
selección de dispositivo y selección de contenido superior/inferior. Estas partes pueden
solaparse: son capturas de viewport, no un ensamblaje de página completa. Cada imagen puede
abrirse a su tamaño original para leerla con detalle.

Los formularios y botones dentro de las imágenes son referencias visuales. Las acciones del
recorrido cambian la captura mostrada; no autentican, capturan biometría, confirman asistencia,
editan datos, crean cuentas ni abren o cierran sesiones. Los distintos escenarios proceden de
fixtures independientes y no representan una misma sesión continua.

## Pantallas y recorridos

| Identificador | Pantalla o estado | Rol | Móvil disponible |
| --- | --- | --- | --- |
| inicio | Portada institucional | General | Sí |
| docente-acceso | Acceso docente | Docente | Sí |
| docente-registro | Registro docente | Docente | Sí |
| docente-recuperacion | Recuperación de contraseña | Docente | Sí |
| docente-asistencia | Preparación de asistencia | Docente | Sí |
| docente-revision | Revisión de resultados | Docente | No |
| docente-materias | Gestión de materias | Docente | Sí |
| docente-crear | Nueva materia | Docente | No |
| docente-compartir | Código y QR de inscripción | Docente | No |
| docente-registros | Registros de asistencia | Docente | No |
| estudiante-acceso | Acceso facial y alternativo | Estudiante | Sí |
| estudiante-panel | Portal del estudiante | Estudiante | Sí |
| estudiante-perfil | Mi perfil académico | Estudiante | Sí |
| estudiante-materias | Detalle por materia | Estudiante | Sí |
| estudiante-excepcional | Estado de verificación excepcional | Estudiante | Sí |
| admin-acceso | Acceso administrativo | Administración | No |
| admin-verificaciones | Gestión de verificaciones | Administración | Sí |
| cuenta-docente | Menú de cuenta | Docente | Sí |

Ejemplos de recorridos:

- **Docente:** Portada → Acceso → Preparación → Revisión; o Gestión de materias → Crear/Compartir.
- **Estudiante:** Portada → Acceso → Portal → Mi perfil → Detalle de materias.
- **Administración:** Portada → Acceso administrativo → Verificaciones → Estado excepcional.

La edición representa el módulo administrativo Verificación. Sus pantallas de Auditoría,
Cuentas y Materias quedan fuera de este catálogo. También quedan fuera el registro estudiantil,
la operación de cámara/micrófono y varias variantes de error. El login institucional general
del estudiante, el perfil docente y Configuración mantienen su estado pendiente en la aplicación.
El QR mostrado corresponde a una revisión sintética local; no es una invitación operativa.

La aceptación visual se conserva por pantalla en el visor y en [FRONTEND.md](../FRONTEND.md).
Preparar este catálogo no cierra revisiones pendientes ni declara nuevas funciones aceptadas.

## Procedencia de los recursos

| Revisión local | Contenido utilizado | Tipo |
| --- | --- | --- |
| ff5df33f8cc6 | Portada, acceso y registro docente, acceso administrativo | Aplicación sin autenticar |
| 69af3679e8ab | Portales, materias, revisión, perfil y menú | Componentes reales con datos sintéticos y Oracle bloqueado |
| 6f17f011b384 | Acceso alternativo, estado y consola de verificaciones | Componentes reales con datos sintéticos y Oracle bloqueado |
| 4a4c4d8ec524 | Recuperación docente | Recorrido sin enviar el restablecimiento, con valores de prueba |

Son revisiones anteriores con resultado `CORRECTO`, generadas por
`scripts/verificar_frontend.py`. La recuperación procede de una revisión previa a 008;
el resto corresponde a la revisión posterior de esa entrega. La fecha de edición del
catálogo no sustituye las fechas de captura ni representa una nueva ejecución de las pruebas
de negocio. No se incluyen capturas de cuentas reales autenticadas ni medios heredados del
proyecto de inspiración.

El logotipo de `recursos/logo-upc.jpg` es copia binaria del original integrado en
`static/img/upc/logo-horizontal-manual.jpg`, extraído del Manual de Identidad Visual UPC.
Se mantienen proporciones, colores y composición. Las 59 capturas se copian sin edición.

## Archivos y mantenimiento

- `index.html`: visor accesible, estilos, navegación y catálogo integrado para abrir sin servidor.
- `pantallas.json`: inventario legible, recorridos, variantes, origen y SHA-256 de cada imagen.
- `capturas/`: imágenes de referencia de escritorio y móvil.
- `recursos/logo-upc.jpg`: logotipo institucional original.

Los textos y destinos deben mantenerse iguales en el JSON y en el catálogo incorporado en
`index.html`. Una actualización visual de la aplicación requiere renovar las capturas
correspondientes; este visor no consulta la aplicación para actualizarse automáticamente.
Los enlaces permiten abrir una pantalla concreta, por ejemplo
`index.html#estudiante-perfil?vista=movil&parte=1`.

La revisión del visor comprueba imágenes, destinos, búsqueda, navegación, teclado y distribución
en navegador con anchos de 1440, 768, 390 y 320 px. Las evidencias locales se guardan en
`.local/mockup/`, fuera del contenido compartible. El detalle de esa verificación se registra
en [CAMBIOS.md](../CAMBIOS.md).
