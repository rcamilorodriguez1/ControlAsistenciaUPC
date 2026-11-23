# Roadmap general de UPC | Aula

Actualizado el 22/11/2026. Este archivo es el punto de entrada; cada rama conserva
sus tareas y evidencias. El [roadmap anterior](ROADMAP_HISTORICO.md) permanece como
registro histórico, incluidos los pendientes de despliegue que siguen abiertos.

| Rama | Alcance | Estado |
| --- | --- | --- |
| [Frontend y backend](ROADMAP_FRONT_BACK.md) | Selector de clases, créditos, perfiles, configuración y excepciones docentes | Implementado y probado; aceptación en Render pendiente |
| [Base de datos y aporte académico](ROADMAP_BASE_DATOS.md) | Visualización, diccionario, conexión y goodwill | Entregables terminados; revisión académica del equipo pendiente |
| [Memoria y presentación](ROADMAP_DOCUMENTACION_PRESENTACION.md) | PDF 1.2 y presentación comercial con identidad UPC | Terminados y revisados: 87 páginas y 20 diapositivas |
| [Arquitectura y evolución](ROADMAP_2.md) | Calidad, recursos y ampliaciones posteriores dentro de Render | Propuestas; Vercel descartado |
| [Instalación y despliegue originales](ROADMAP_HISTORICO.md) | Completar las verificaciones funcionales pendientes de los puntos 5, 7 y 8 | Render Live; aceptación funcional pendiente |

## Forma de trabajo

1. Abrir una rama documental para cada área nueva y enlazarla aquí.
2. Cada tarea tiene criterio de cierre y evidencia; distinguir implementación,
   pruebas aisladas, comprobación con Oracle y aceptación del usuario en Render.
3. Registrar los cambios en [CAMBIOS.md](CAMBIOS.md), realizar commit local cada
   tres cambios menores (los mayores por separado) y push cada cinco cambios o
   al cerrar un punto del roadmap, según [la política vigente](README.md).
4. No borrar el historial al reorganizar: los pendientes se trasladan o enlazan.

## Decisiones actuales

- Solo Render para la aplicación; Oracle Autonomous para los datos. Vercel descartado.
- Las pruebas de la página, cámara y reconocimiento quedan a cargo del usuario. Este PC no tiene cámara.

- El portal sirve para operar; el perfil presenta identidad y actividad académica.
- El docente tendrá su agenda mensual y la configuración de su cuenta por separado.
- La excepción biométrica se entrega manualmente desde el portal docente. Queda
  sustituida la propuesta de correo; no se requiere proveedor ni correo del alumno.
- Los identificadores globales de clase no se muestran como numeración de pendientes.
- Goodwill significa valor, beneficios y aporte académico, sin valoración monetaria.

## Entregables de esta revisión

- [Perfil docente y configuración](PERFIL_DOCENTE.md) y [excepciones con entrega manual](EXCEPCIONES_BIOMETRICAS.md).
- [Mapa interactivo de las 14 tablas](base_datos/index.html), con búsqueda y relaciones.
- [Diccionario de 140 columnas](DICCIONARIO_DATOS.md), obtenido de Autonomous 009.
- [Conexión de la aplicación con Oracle](CONEXION_BASE_DATOS.md) y [goodwill](GOODWILL.md).

Verificación: 293 pruebas, 288 aprobadas y 5 omitidas por requerir una cuenta Oracle
temporal limitada. Oracle local y Autonomous 009 verificados con respaldos cifrados;
preflight con la cuenta de ejecución cloud real aprobado. La publicación en GitHub
no certifica por sí sola el nuevo despliegue de Render ni la aceptación de sus pantallas.
