# Roadmap general de UPC | Aula

Actualizado el 22/11/2026. Este archivo es el punto de entrada; cada rama conserva
sus tareas y evidencias. El [roadmap anterior](ROADMAP_HISTORICO.md) permanece como
registro histórico, incluidos los pendientes de despliegue que siguen abiertos.

| Rama | Alcance | Estado |
| --- | --- | --- |
| [Frontend y backend](ROADMAP_FRONT_BACK.md) | Selector de clases, créditos, perfiles, configuración y excepciones docentes | En ejecución |
| [Base de datos y aporte académico](ROADMAP_BASE_DATOS.md) | Visualización, diccionario, conexión y goodwill | En ejecución |
| [Arquitectura y evolución](ROADMAP_2.md) | Alternativas de alojamiento, rediseño y ampliaciones posteriores | Propuestas; no compromisos de despliegue |
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

- El portal sirve para operar; el perfil presenta identidad y actividad académica.
- El docente tendrá su agenda mensual y la configuración de su cuenta por separado.
- La excepción biométrica se entrega manualmente desde el portal docente. Queda
  sustituida la propuesta de correo; no se requiere proveedor ni correo del alumno.
- Los identificadores globales de clase no se muestran como numeración de pendientes.
- Goodwill significa valor, beneficios y aporte académico, sin valoración monetaria.
