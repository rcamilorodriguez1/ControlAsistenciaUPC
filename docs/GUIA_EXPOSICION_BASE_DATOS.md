# UPC | Aula: guía para la exposición de Base de Datos

Equipo: Rafael Camilo Rodriguez Ayala, Harold Steven Torres Diaz y Oscar William
Rivero Ordoñez. Docente: Amilkat Sierra Romano. Programa: Ingeniería de Sistemas.

## 1. Qué vamos a presentar

UPC Aula integra materias, matrículas, clases y decisiones de asistencia en Oracle.
Su valor para esta asignatura es demostrar cómo un modelo relacional, sus reglas y
sus transacciones sostienen una aplicación completa. El rostro y la voz apoyan la
propuesta; la decisión se revisa por el docente y se confirma con trazabilidad.

La presentación principal de la carpeta se centra en Base de Datos. La presentación
comercial anterior se conserva como material complementario para explicar el valor
del software. La memoria integral 1.2 documenta el sistema con mayor profundidad.

## 2. Problemática y formulación del problema

Un listado de nombres y marcas de presencia no explica a qué clase pertenece un dato,
cómo se obtuvo, quién lo revisó o por qué cambió. Si se mezclan horarios, matrículas y
resultados, aparecen duplicados y correcciones difíciles de justificar. Además, un
error de reconocimiento no debería convertirse automáticamente en ausencia.

**Pregunta del proyecto:** ¿cómo integrar el seguimiento por materia y clase, la
identificación de usuarios, la revisión docente y el historial, manteniendo la
integridad y evitando confundir errores técnicos con decisiones académicas?

Es una necesidad planteada en el desarrollo del proyecto. No se presenta como una
encuesta institucional ni como una medición estadística de los procesos de la UPC.

## 3. Objetivo general y objetivos específicos

**Objetivo general:** desarrollar una plataforma académica que integre asignaturas,
matrículas y sesiones de clase con el registro de asistencia, control de acceso,
revisión docente y trazabilidad en Oracle.

1. Modelar docentes, estudiantes, materias, matrículas, clases y resultados.
2. Aplicar PK, FK, UNIQUE y CHECK para conservar coherencia entre los datos.
3. Confirmar una clase mediante una transacción completa y controlar reintentos.
4. Guardar actor, motivo e historial de correcciones y cambios de gestión.
5. Conectar Python/Streamlit con Oracle mediante un driver y pools con permisos limitados.
6. Integrar detección facial/voz y acceso excepcional sin confundirlos con asistencia.
7. Mantener migraciones, consultas, diccionario, copias y documentación reproducibles.

## 4. Relación con Ingeniería de Sistemas

| Área del programa | Aplicación concreta en el proyecto |
| --- | --- |
| Bases de datos | Entidades, relaciones, claves, restricciones, JOIN, agregados, vistas, PL/SQL y transacciones. |
| Ingeniería de software | Requisitos, separación de capas, control de versiones, pruebas y documentación. |
| Programación | Servicios Python, validación de entradas, manejo de errores y contratos de operación. |
| Infraestructura y redes | Aplicación Docker en Render, HTTPS y conexión TCPS/TLS a Autonomous. |
| Seguridad | Sesiones revocables, roles, hashes, documento HMAC y permisos de cuentas técnicas. |
| Inteligencia artificial | Comparación facial y de voz como apoyo; tratamiento de fallos y revisión humana. |
| Operación y calidad | Respaldos cifrados, migraciones, recuperación, métricas y aceptación del usuario. |

Esta relación explica el aporte formativo del proyecto. No sustituye una equivalencia
oficial con el plan curricular de la universidad.

## 5. Modelo relacional y cardinalidades

El esquema 009 tiene **14 tablas, 140 columnas visibles y 11 claves foráneas físicas**.
Las seis entidades del núcleo académico son PROFESORES, ESTUDIANTES, MATERIAS,
MATERIA_ESTUDIANTES, CLASES y REGISTROS_ASISTENCIA.

- Un profesor administra cero o muchas materias; una materia tiene un profesor.
- Materias y estudiantes forman una relación N:M, resuelta con MATERIA_ESTUDIANTES.
- La matrícula usa PK compuesta: materia_id + estudiante_id.
- Una materia contiene clases. Una clase representa un horario concreto, no una foto.
- Una clase contiene resultados por estudiante; la unicidad impide dos resultados
  para el mismo alumno y clase.
- VERIFICACION_ESTUDIANTES tiene como máximo una fila por estudiante. La aprobación
  excepcional procede de Administración o de un docente con materia, con exclusión mutua.
- Historiales, eventos, límites, sesiones y versiones completan el modelo. Algunas
  referencias históricas son lógicas y no se dibujan como FK físicas.

El modelo de la carpeta muestra claves y campos guía. El diccionario contiene todas
las columnas. El archivo DDL 009 sirve para importar la estructura en Data Modeler.

## 6. Cómo explicar la normalización

La identidad del estudiante, la materia y el docente se conservan en tablas distintas.
MATERIA_ESTUDIANTES relaciona sus IDs, sin repetir nombres y contraseñas. Una asistencia
referencia la clase y el estudiante, en lugar de duplicar toda su información.

Ejemplo: el nombre del estudiante depende de estudiante_id y se guarda en ESTUDIANTES.
La fecha de matrícula corresponde a la relación materia/estudiante y se guarda en la
tabla intermedia. El nombre de una materia no se copia en cada resultado de asistencia.

Las instantáneas de auditoría y el responsable original de una clase conservan datos
del momento de la operación deliberadamente. Son decisiones de trazabilidad, no
otra tabla maestra. Para afirmar una forma normal sobre todo el esquema haría falta
documentar las dependencias funcionales; el diccionario por sí solo no es esa demostración.

## 7. Integridad: ejemplos que debemos poder defender

| Regla | Implementación o efecto |
| --- | --- |
| Identidad inequívoca | PK en cada entidad; Oracle genera los IDs numéricos. |
| Matrícula única | PK compuesta de MATERIA_ESTUDIANTES. |
| Resultado por alumno/clase | Restricción de unicidad en REGISTROS_ASISTENCIA. |
| Clase de la materia correcta | FK compuesta de clase_id + materia_id hacia CLASES. |
| Datos con estados admitidos | CHECK para actividad, detección, verificación y autorización. |
| Aprobador excepcional coherente | Administrador o docente con materia, nunca ambos cuando la excepción está activa. |
| Historia conservada | Archivo de cuentas/materias y registros de cambios en los flujos de aplicación. |

Una FK con cascada describe el borrado físico, pero la operación habitual de la web
usa archivo/retiro y conserva historia. Deshabilitar un botón no reemplaza una validación
en servidor o en la base de datos.

## 8. Vistas, paquetes y disparadores

El esquema tiene **11 vistas, 8 paquetes PL/SQL y 10 triggers**. Las vistas simplifican
consultas de materias, clases, resultados e historial; no son copias independientes
de las tablas ni sustituyen el control de filas por usuario.

| Paquete | Responsabilidad para explicar |
| --- | --- |
| PKG_AUDITORIA | Contexto de rol, actor y motivo en la conexión. |
| PKG_ASISTENCIA | Operaciones académicas, consultas y correcciones según el flujo. |
| PKG_GESTION | Materias, matrícula, archivo y gestión controlada de cuentas. |
| PKG_CLASES | Apertura/reutilización y confirmación de una clase. |
| PKG_ADMINISTRACION | Consultas y edición administrativa autorizada. |
| PKG_SESIONES | Apertura, validación, caducidad y revocación de sesiones. |
| PKG_EXCEPCIONES | Autorizaciones administrativas de acceso alternativo. |
| PKG_EXCEPCIONES_DOCENTES | Autorizaciones docentes para sus alumnos matriculados. |

Los triggers actualizan fechas/versiones, validan actividad, protegen identidad de
clases/resultados y crean historial. No todos los eventos se generan con un trigger:
los servicios y paquetes también escriben eventos explícitos de gestión e identidad.
Las versiones antiguas de los paquetes se conservan para reconstruir las migraciones;
la guía de SQL identifica las fuentes vigentes.

## 9. Transacciones e idempotencia

El docente prepara una propuesta completa, resuelve pendientes y confirma. El servidor
valida sesión, clase, propiedad y matrícula. Oracle bloquea los registros necesarios,
inserta los resultados y confirma la clase como una unidad. Ante un error se revierte
la operación; Python decide el COMMIT o ROLLBACK.

Un reintento válido con la misma clave y contenido devuelve la confirmación existente.
Una propuesta distinta para una clase confirmada se rechaza. Esto es idempotencia;
no se limita a ocultar dos veces el botón. Las versiones de edición rechazan cambios
basados en una lectura obsoleta.

## 10. Auditoría y seguridad

Una corrección conserva la detección y revisión original, y registra actor, fecha,
motivo y valores del cambio. La auditoría no se declara inmutable frente al propietario
Oracle: ese usuario tiene permisos de mantenimiento superiores a los del portal.

Se almacenan hashes de contraseña, no contraseñas recuperables. El documento de la
excepción se representa con HMAC y sus últimos cuatro caracteres. Las plantillas
biométricas siguen siendo datos sensibles aunque no se guarden fotos o audio en esas tablas.

La excepción permite entrar al portal, no marca asistencia. Su vigencia y revocación
se comprueban en el acceso y en las sesiones. La clave compartida de demostración se
asigna mediante autorización individual; el paquete para compartir no contiene su valor.

## 11. Cómo se conecta el programa

Navegador → HTTPS → Render/Streamlit → servicios → python-oracledb Thin/pool →
TCPS/TLS → Oracle Autonomous. SQL Developer es otro cliente de Oracle; no guarda una
segunda base ni recibe los datos de SQL*Plus.

| Cuenta técnica | Función |
| --- | --- |
| UPC_ASISTENCIA | Propietario: instalación, migración, respaldo y metadatos. |
| UPC_AULA_APP | Runtime ordinario con contrato de 53 permisos. |
| UPC_ADMIN_APP | Cinco EXECUTE y tres vistas de historial; sin DML directo de aprobación. |

El docente, estudiante y administrador de la web son identidades de la aplicación,
distintas de esas cuentas Oracle. Antes de operar se valida su sesión y se establece
el contexto de actor. El pool reutiliza conexiones y limpia el contexto al devolverlas.
La URL pública de Render no es el DSN de Oracle. Los archivos privados del proyecto
original contienen la configuración; el material de exposición contiene sus nombres
y explicación, sin valores de conexión ni claves.

## 12. Demostración SQL sugerida

Usar primero el archivo **01_consultas_para_exponer.sql**. Sus consultas muestran:

1. Usuario/esquema, versiones y estado de objetos.
2. Tablas y columnas del diccionario Oracle.
3. PK/FK y sus columnas de origen/destino.
4. Matrícula por materia mediante JOIN, GROUP BY y COUNT, incluyendo materias vacías.
5. Resultados agregados por clase; diferencia entre confirmada y pendiente.
6. Vistas, paquetes, triggers y firmas públicas.

El segundo archivo usa variables enlazadas para profundizar en una materia o clase.
En SQL Developer ejecutar una sentencia con F9 e introducir los binds solicitados.
La carpeta de instalación contiene DDL y migraciones, separados del guion de consultas.
No se reinstala sobre la base existente para dibujar el modelo.

Si no hay internet o Oracle no responde, abrir el modelo PDF, el diccionario y el
catálogo HTML. Esos archivos permiten explicar las estructuras sin conectar. La
demostración con datos reales y el último despliegue quedan al usuario.

## 13. Guion de 12–15 minutos, ajustable

| Tramo | Qué demostrar |
| --- | --- |
| Inicio | Problema, usuarios y objetivo. Vender la utilidad del software con un caso de clase. |
| Modelo | Entidades, N:M, tabla intermedia, claves y cardinalidades. |
| Reglas | Unicidad, FK compuesta, estados y conservación del historial. |
| Operación | Transacción, reintento, paquetes, triggers y auditoría. |
| Integración | Driver, pool, Render/Oracle y separación de cuentas/roles. |
| Evidencia | 293 pruebas: 288 aprobadas y 5 omitidas; distinguir software de precisión biométrica. |
| Cierre | Aporte a Ingeniería de Sistemas, beneficios por medir y propuesta de piloto. |

Reparto sugerido: un integrante explica problema/modelo; otro SQL, integridad y PL/SQL;
otro integración, evidencia y valor. Adaptarlo a la intervención de cada integrante.

## 14. Preguntas para ensayar

| Pregunta | Respuesta breve |
| --- | --- |
| ¿Por qué una tabla de clases? | Para identificar el horario y confirmar una única toma, independiente de cuántas fotos se analicen. |
| ¿Cómo resuelven N:M? | Con MATERIA_ESTUDIANTES y su PK materia_id + estudiante_id. |
| ¿Por qué FK compuesta? | Impide asociar un resultado con una clase que pertenece a otra materia. |
| ¿Qué sucede si falla una inserción? | Se revierte la confirmación completa; no se guardan unas asistencias y otras no. |
| ¿Qué diferencia hay entre vista y tabla? | La vista almacena una consulta; la tabla conserva filas. |
| ¿Por qué paquete y no todo Python? | Las reglas transaccionales se validan también junto a los datos; Python coordina interfaz, muestras y flujo. |
| ¿Qué hace un trigger aquí? | Aplica reglas automáticas concretas o genera historia cuando ocurre la operación definida. |
| ¿Qué sucede con SIN_MUESTRA? | Requiere decisión manual con motivo; no equivale a ausencia. |
| ¿La excepción marca asistencia? | No. Autoriza el acceso; la clase sigue su confirmación independiente. |
| ¿Oracle vive en Render? | No. Render ejecuta Python y se conecta por TCPS a Autonomous. |
| ¿Cada estudiante tiene usuario Oracle? | No. Su identidad web se valida en el servidor; las conexiones usan cuentas técnicas. |
| ¿Las 288 pruebas miden precisión facial? | No. Son pruebas de software; la evaluación biométrica real sigue pendiente. |
| ¿Qué valor comercial tiene? | Integra seguimiento y trazabilidad; el ahorro, costos y disposición de pago se medirán en un piloto. |

## 15. Estado, fuentes y preparación final

Estado técnico documentado: Oracle 001–009, 14 tablas, 140 columnas, 11 FK, 11 vistas,
8 paquetes y 10 triggers. Memoria 1.2 y evidencias del 22/11/2026. Las pruebas de la
página y la biometría corresponden al usuario; este PC no dispone de cámara.

Fuentes del proyecto: INFORME_PROYECTO.md, BASE_DE_DATOS.md, DICCIONARIO_DATOS.md,
CONEXION_BASE_DATOS.md, CAMBIOS.md y los scripts versionados 001–009. La identidad
gráfica sigue el Manual de Identidad Visual UPC 2010.

Para mañana: abrir antes el PowerPoint/PDF, probar con el usuario el acceso a la web
y a la conexión Oracle prevista, identificar qué consultas se mostrarán y ensayar
las respuestas anteriores. El paquete offline queda como respaldo de la exposición.
