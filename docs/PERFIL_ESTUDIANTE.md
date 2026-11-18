# Mi perfil del estudiante

Implementado el 17 de noviembre de 2026. Vista privada de consulta, con estructura de perfil
social adaptada al contexto académico: portada verde, avatar de iniciales, nombre/código,
indicador circular, resumen global, materias desplegables y calendario mensual.
No incorpora un feed social, edición de identidad, subida de fotografías ni configuración.

## Acceso y privacidad

El estudiante autenticado accede desde **Estudiante → Mi perfil**, en `/mi-perfil`.
Puede volver a su portal o al inicio conservando la sesión. La nueva página usa el router
nativo y las comprobaciones existentes de vigencia/revocación; no abre un token adicional.

El servicio obtiene la identidad del servidor. La consulta Oracle vuelve a comprobar el rol
ESTUDIANTE y su identificador contra `PKG_AUDITORIA`; los parámetros de URL no eligen la cuenta.
No se consultan contraseñas, fotografías ni vectores biométricos. Otros roles no pueden leer
este perfil; si visitan la ruta, se conserva el flujo de login estudiantil y conflicto existente.
Mi perfil de profesor/administrador y Configuración continúan reservados para una revisión futura.

## Reglas del resumen

- **Asistencia general** = asistidas / clases con registro confirmado × 100. Es una proporción
  acumulada de registros, no la media de los porcentajes de las asignaturas.
- **Materias matriculadas** cuenta las relaciones de matrícula actuales con materias activas.
- **Asistidas y perdidas** corresponden exclusivamente a decisiones finales 1/0 en clases
  CONFIRMADAS. Los borradores, análisis pendientes y días sin registro no producen ausencias.
- El acumulado incluye el historial conservado de materias retiradas/archivadas. Estas aparecen
  identificadas como **Histórica**, sin incrementar el contador de matrículas actuales.
- Sin registros se muestra «— / Sin registros»; se distingue de 0 %, que significa que todas
  las decisiones confirmadas son ausencias.

La extracción usa una única consulta de datos para obtener un conjunto consistente. La clase
se cuenta una vez por materia/ID; duplicados incompatibles se rechazan. No se introducen
migraciones ni cambios en las reglas de matrícula o confirmación de asistencia.

## Estados visuales

Umbrales editables en `src/servicios/perfil_estudiante.py`:

| Estado | Porcentaje |
| --- | --- |
| Excelente | ≥ 90 % |
| Aceptable | ≥ 80 % y < 90 % |
| En riesgo | < 80 %, con registros |
| Sin registros | Todavía no hay decisiones confirmadas |

Son referencias visuales indicadas en pantalla; no se presentan como reglas oficiales de
aprobación de la universidad y no modifican los registros académicos.

## Calendario

Meses y días en español, navegación anterior/siguiente y detalle desplegable por día.
La fecha corresponde a la **clase**, convertida a America/Bogota, no al momento del escaneo.

| Color | Significado |
| --- | --- |
| Verde | Asistió a todas las clases registradas del día |
| Rojo | Todas las clases registradas de ese día son ausencias |
| Ámbar | Día mixto, con presencias y ausencias |
| Neutro | Sin registros; no se contabiliza como ausencia |

La celda indica asistidas/total de clases con registro. Los textos, conteos y descripciones
accesibles complementan el color. El detalle lista asignatura, fecha/hora colombiana y decisión.
El indicador de hoy no modifica el estado de asistencia. Se contemplan meses bisiestos,
cambios de año y varias clases el mismo día.

## Implementación

| Área | Archivos |
| --- | --- |
| Consulta Oracle privada | `src/base_datos/perfil_estudiante.py` |
| Métricas, estados y autorización | `src/servicios/perfil_estudiante.py` |
| Vista y calendario | `src/pantallas/perfil_estudiante.py` |
| Ruta y entrada en el menú | `src/interfaz/navegacion.py`, `src/componentes/encabezado.py`, `principal.py` |
| Estilos responsive | `static/css/styles.css` |
| Pruebas | `tests/test_perfil_estudiante.py`, `tests/test_perfil_interfaz.py`, `tests/test_perfil_oracle.py`, `tests/soporte_perfil.py` |
| Verificación visual aislada | `tests/preview_frontend.py`, `scripts/verificar_frontend.py` |

Se reutilizan Material, Streamlit y la biblioteca estándar; el círculo se dibuja con CSS y
el calendario con HTML semántico. Los datos insertados en HTML se escapan. No se añadieron
dependencias ni recursos remotos. Los estilos quedan limitados al perfil.

## Validación

- **195 pruebas aprobadas**, incluidas las de Oracle: `.local/pruebas_perfil_completas.log`.
- Las pruebas reales de lectura comprueban aislamiento entre estudiantes, rol incorrecto,
  ausencia de datos, matrículas y mantenimiento del historial tras retirarse. Los fixtures
  no hacen COMMIT y revierten sus filas e historial al terminar.
- Pruebas de URL manipulada, sesión revocada, cierre real mediante el servicio existente,
  navegación sin token adicional, cálculo ponderado, duplicados, calendario y escape HTML.
- **52 vistas de navegador sin fallos**, con datos sintéticos y Oracle bloqueado:
  `.local/frontend/3551367e3691/resultado.json`. Perfil en escritorio, 768/390/320 px, materia
  desplegada, navegación mensual y cuenta sin registros. Se conserva la revisión de encabezado,
  menú, separador aprobado, footer, conflictos y diálogos.
- **12 vistas de la instancia HTTPS activa** sin fallos:
  `.local/frontend/0211bfa5eb4a/resultado.json`. Incluye el acceso directo a `/mi-perfil`
  sin sesión y con un ID ajeno en la URL: muestra el acceso estudiantil, sin datos privados.
  No se iniciaron sesiones en cuentas reales ni se reinició el servidor para esta comprobación.

No se alteraron datos de cuentas reales para la demostración. La aceptación visual del usuario
permanece pendiente; la implementación no cierra el resto de la revisión del frontend.
