# Valor, beneficios y aporte académico de UPC | Aula

UPC | Aula propone centralizar el control de asistencia: inscripción de estudiantes,
programación de clases, propuesta de presencia mediante rostro o voz, revisión docente
y registro trazable en Oracle. Su valor académico está en integrar esas partes y poder
explicar cómo se relacionan los datos, las decisiones y los permisos.

Este documento utiliza goodwill como **valor, beneficios y aporte académico**, según
lo aclarado por el equipo. No asigna un precio al proyecto ni afirma una adopción oficial.

## Valor para cada participante

| Participante | Necesidad | Aporte del proyecto |
| --- | --- | --- |
| Docente | Preparar clases y consolidar asistencia sin duplicar tomas | Materias propias, agenda, análisis asistido y confirmación por clase |
| Estudiante | Conocer sus matrículas y asistencia | Portal de inscripción y perfil con historial y calendario |
| Estudiante con dificultad de acceso facial | Continuar usando el portal con una identidad comprobada | Excepción autorizada, contraseña con vigencia y revocación |
| Gestión académica | Conservar decisiones y revisar cambios | Roles, auditoría, archivo de cuentas/materias y consultas de historial |
| Equipo desarrollador | Demostrar una solución integradora y mantenerla | Código versionado, migraciones, pruebas y documentación reproducible |

## Beneficios y cómo comprobarlos

Los beneficios de ahorro de tiempo y mejora de seguimiento son hipótesis que requieren
medición. Una prueba satisfactoria con usuarios conocidos demuestra viabilidad de un
recorrido, pero no establece una tasa general de reconocimiento ni ahorro institucional.

| Beneficio esperado | Indicador propuesto | Evidencia necesaria |
| --- | --- | --- |
| Menos tiempo de consolidación | Minutos por clase frente a lista manual, con igual número de alumnos | Ensayo comparativo cronometrado y varias repeticiones |
| Menos duplicación | Clases confirmadas duplicadas por materia e instante | Consultas de unicidad y pruebas de reintento |
| Más trazabilidad | Correcciones con motivo, actor y fecha / total de correcciones | Auditoría de asistencia con datos de prueba |
| Mejor continuidad de acceso | Solicitudes resueltas y tiempo para autorizar una excepción | Ensayo docente/alumno y prueba de vencimiento/revocación |
| Uso viable de recursos | Pico de memoria, latencia y concurrencia durante análisis | Medición en el plan Render utilizado |
| Comprensión de la base | Participantes capaces de explicar una relación y una transacción | Presentación del catálogo y preguntas sobre casos concretos |

## Aporte a Base de Datos e Ingeniería de Sistemas

- **Modelado relacional:** entidades, relaciones y tabla asociativa de matrículas;
  separación entre clase programada, propuesta de detección y asistencia confirmada.
- **Integridad:** claves primarias/foráneas, unicidad y restricciones CHECK; la base
  participa en el cumplimiento de reglas y no depende únicamente de botones de la UI.
- **Transacciones y concurrencia:** control de versiones, bloqueos, rollback y operaciones
  idempotentes para evitar que un reintento duplique o sobrescriba una confirmación.
- **Seguridad aplicada:** identidad de la aplicación separada de cuentas técnicas,
  permisos limitados, hashes de contraseña, documento seudonimizado y transporte TLS.
- **Operación y recuperación:** migraciones, respaldo cifrado, historial de cambios y
  despliegue reproducible conectado a GitHub.
- **Integración de IA:** el modelo propone detecciones; el docente revisa y confirma.
  Se distingue SIN_MUESTRA de ausencia y un error técnico no confirma asistencia.

## Evidencia disponible y límites

El repositorio contiene pruebas de reglas, interfaz y operaciones con Oracle; el estado
actual se registra en [CAMBIOS](CAMBIOS.md) y los [roadmaps](ROADMAP.md). El catálogo y el
diccionario permiten explicar el esquema sin exponer personas o credenciales.

El proyecto está en etapa académica y de demostración. Falta un ensayo representativo
de iluminación, posiciones, voces, tamaño de grupo, concurrencia y recuperación en el
alojamiento final. No se han establecido métricas poblacionales de precisión, equidad o
aceptación institucional. La IA puede equivocarse: la revisión y la alternativa de
acceso forman parte del flujo, no eliminan esa limitación.

La contribución del equipo corresponde a Rafael Camilo Rodriguez Ayala, Harold Steven
Torres Diaz y Oscar William Rivero Ordoñez, con referencia académica del docente Amilkat
Sierra Romano, en Ingeniería de Sistemas. La presentación debe distinguir aportes del
equipo, bibliotecas empleadas y material institucional citado.
