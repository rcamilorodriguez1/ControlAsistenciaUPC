# Roadmap general de UPC | Aula

Actualizado el 23/11/2026. Este archivo es el punto de entrada; cada rama conserva
sus tareas y evidencias. El [roadmap anterior](ROADMAP_HISTORICO.md) permanece como
registro histórico, incluidos los pendientes de despliegue que siguen abiertos.

| Rama | Alcance | Estado |
| --- | --- | --- |
| [Aprendizaje de base de datos](ROADMAP_APRENDIZAJE_BASE_DATOS.md) | Reinicio autorizado de ambos destinos, carga gradual y explicación de cada script | AB1 y AB2.1 terminados: reinicio y guía PDF ilustrada 011 de 84 páginas; estudio y carga gradual pendientes |
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
- Para la presentación: [clave maestra académica temporal](PRUEBA_ACADEMICA.md),
  [documento registrado desde 011](DOCUMENTO_ESTUDIANTIL.md) y acceso a cualquier
  estudiante activo durante su vigencia, con estado y auditoría propios.

- El portal sirve para operar; el perfil presenta identidad y actividad académica.
- El docente tendrá su agenda mensual y la configuración de su cuenta por separado.
- La excepción biométrica se entrega manualmente desde el portal docente. Queda
  sustituida la propuesta de correo; no se requiere proveedor ni correo del alumno.
- Los identificadores globales de clase no se muestran como numeración de pendientes.
- Goodwill significa valor, beneficios y aporte académico, sin valoración monetaria.

## Entregables de esta revisión

- [Guía ilustrada desde cero, esquema 011](GUIA_DIDACTICA_BASE_DATOS.md): 84 páginas,
  14 tablas y 140 campos, vistas, paquetes, triggers, scripts y ejercicios.
- [Perfil docente y configuración](PERFIL_DOCENTE.md) y [excepciones con entrega manual](EXCEPCIONES_BIOMETRICAS.md).
- [Mapa interactivo de las 14 tablas](base_datos/index.html), con búsqueda y relaciones.
- [Diccionario de 140 columnas](DICCIONARIO_DATOS.md), obtenido de Autonomous 009.
- [Conexión de la aplicación con Oracle](CONEXION_BASE_DATOS.md) y [goodwill](GOODWILL.md).

Verificación: 293 pruebas, 288 aprobadas y 5 omitidas por requerir una cuenta Oracle
temporal limitada. Oracle local y Autonomous 009 verificados con respaldos cifrados;
preflight con la cuenta de ejecución cloud real aprobado. La publicación en GitHub
no certifica por sí sola el nuevo despliegue de Render ni la aceptación de sus pantallas.
