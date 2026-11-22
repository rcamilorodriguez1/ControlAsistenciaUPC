# Diccionario de datos vigente

Generado desde el diccionario Oracle; no contiene registros de personas ni credenciales.

Versiones: 001, 002, 003, 004, 005, 006, 007, 008, 009. Captura UTC: 2026-11-22T23:09:17.970505+00:00.

[Visualización interactiva](base_datos/index.html) · [Explicación funcional](BASE_DE_DATOS.md) · [Conexión](CONEXION_BASE_DATOS.md)

PK = clave primaria; FK = clave foránea; UQ = unicidad. Las condiciones CHECK incluyen las reglas NOT NULL de Oracle. La identidad indica numeración global automática.

## ADMINISTRADORES

Administradores de aplicacion; alta privada, clave bcrypt y sin registro publico.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| ADMINISTRADOR_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada de la cuenta administrativa de la aplicación. |
| USUARIO | VARCHAR2(100 CHAR) | No | No |  |  | Identificador de acceso; la aplicación lo normaliza. |
| NOMBRE | VARCHAR2(200 CHAR) | No | No |  |  | Nombre legible de la persona o materia. |
| CONTRASENA | VARCHAR2(255 CHAR) | No | No |  |  | Hash bcrypt; no permite consultar la contraseña en texto. |
| ACTIVO | NUMBER(1,0) | No | No |  | 1 | 1: cuenta/materia activa; 0: archivada o deshabilitada. |
| CREADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación de la fila. |
| ACTUALIZADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante actualizado automáticamente por su trigger al hacer UPDATE. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_ADMINISTRADORES_ACTIVO | CHECK (ACTIVO): activo IN (0,1) | ENABLED / VALIDATED |
| PK_ADMINISTRADORES | PK (ADMINISTRADOR_ID) | ENABLED / VALIDATED |
| SYS_C0037155 | CHECK (ADMINISTRADOR_ID): "ADMINISTRADOR_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037156 | CHECK (USUARIO): "USUARIO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037157 | CHECK (NOMBRE): "NOMBRE" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037158 | CHECK (CONTRASENA): "CONTRASENA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037159 | CHECK (ACTIVO): "ACTIVO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037160 | CHECK (CREADO_EN): "CREADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037161 | CHECK (ACTUALIZADO_EN): "ACTUALIZADO_EN" IS NOT NULL | ENABLED / VALIDATED |

## AUDITORIA_ASISTENCIA

Instantaneas de correcciones y bajas; misma transaccion que la asistencia. Sin FK para conservar bajas en cascada.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| AUDITORIA_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada del evento de auditoría. |
| OPERACION | VARCHAR2(10 CHAR) | No | No |  |  | UPDATE relevante o DELETE; no registra el INSERT inicial. |
| ASISTENCIA_ID | NUMBER | No | No |  |  | ID histórico del registro afectado; se conserva sin FK. |
| MATERIA_ANTERIOR | NUMBER | No | No |  |  | Materia antes de la operación. |
| ESTUDIANTE_ANTERIOR | NUMBER | No | No |  |  | Estudiante antes de la operación. |
| FECHA_ANTERIOR | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Fecha de análisis anterior. |
| PRESENTE_ANTERIOR | NUMBER(1,0) | No | No |  |  | Decisión de asistencia anterior. |
| MATERIA_NUEVA | NUMBER | Sí | No |  |  | Materia después de la operación; nula en una baja. |
| ESTUDIANTE_NUEVO | NUMBER | Sí | No |  |  | Estudiante después de la operación; nulo en una baja. |
| FECHA_NUEVA | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Fecha de análisis posterior; nula en una baja. |
| PRESENTE_NUEVO | NUMBER(1,0) | Sí | No |  |  | Decisión posterior; nula en una baja. |
| OCURRIDO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación del evento histórico. |
| USUARIO_BD | VARCHAR2(128 CHAR) | No | No |  |  | Usuario técnico Oracle que ejecutó la operación, distinto del actor de la aplicación. |
| ACTOR_ROL | VARCHAR2(20 CHAR) | No | No |  |  | Rol declarado para la acción; puede incluir SISTEMA o NO_IDENTIFICADO en los historiales. |
| ACTOR_ID | NUMBER | Sí | No |  |  | Identidad declarada por la aplicacion o SQLPlus; no sustituye autenticacion. |
| MOTIVO | VARCHAR2(500 CHAR) | Sí | No |  |  | Justificación de la acción; debe excluir contraseñas y detalles médicos. |
| MODULO | VARCHAR2(64 CHAR) | Sí | No |  |  | Módulo técnico informado por la sesión Oracle. |
| IDENTIFICADOR_CLIENTE | VARCHAR2(64 CHAR) | Sí | No |  |  | Identificador técnico de cliente de la sesión Oracle. |
| CLASE_ANTERIOR | NUMBER | Sí | No |  |  | Clase anterior, conservada como dato histórico. |
| CLASE_NUEVA | NUMBER | Sí | No |  |  | Clase después de la operación; nula en una baja. |
| DETECTADO_ANTERIOR | NUMBER(1,0) | Sí | No |  |  | Detección inicial conservada al producirse el cambio/baja. |
| CORRECCION_INICIAL | NUMBER(1,0) | Sí | No |  |  | Bandera de revisión inicial del registro afectado. |
| MOTIVO_INICIAL | VARCHAR2(500 CHAR) | Sí | No |  |  | Motivo de la revisión inicial, distinto del motivo del cambio posterior. |
| REVISOR_INICIAL | NUMBER | Sí | No |  |  | Docente que realizó la revisión inicial. |
| ESTADO_ANTERIOR | VARCHAR2(20 CHAR) | Sí | No |  |  | Estado de detección original del registro afectado. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_AUDASIST_ANT | CHECK (PRESENTE_ANTERIOR): presente_anterior IN (0, 1) | ENABLED / VALIDATED |
| CK_AUDASIST_NUEVO | CHECK (PRESENTE_NUEVO): presente_nuevo IN (0, 1) | ENABLED / VALIDATED |
| CK_AUDASIST_OPERACION | CHECK (OPERACION): operacion IN ('UPDATE', 'DELETE') | ENABLED / VALIDATED |
| CK_AUDASIST_ROL | CHECK (ACTOR_ROL): actor_rol IN ('PROFESOR','ESTUDIANTE','ADMINISTRADOR','SISTEMA','NO_IDENTIFICADO') | ENABLED / VALIDATED |
| PK_AUDITORIA_ASISTENCIA | PK (AUDITORIA_ID) | ENABLED / VALIDATED |
| SYS_C0037076 | CHECK (AUDITORIA_ID): "AUDITORIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037077 | CHECK (OPERACION): "OPERACION" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037078 | CHECK (ASISTENCIA_ID): "ASISTENCIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037079 | CHECK (MATERIA_ANTERIOR): "MATERIA_ANTERIOR" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037080 | CHECK (ESTUDIANTE_ANTERIOR): "ESTUDIANTE_ANTERIOR" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037081 | CHECK (FECHA_ANTERIOR): "FECHA_ANTERIOR" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037082 | CHECK (PRESENTE_ANTERIOR): "PRESENTE_ANTERIOR" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037083 | CHECK (OCURRIDO_EN): "OCURRIDO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037084 | CHECK (USUARIO_BD): "USUARIO_BD" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037085 | CHECK (ACTOR_ROL): "ACTOR_ROL" IS NOT NULL | ENABLED / VALIDATED |

## CLASES

Clase identificada por materia e instante UTC; una confirmacion durable compartida por pestañas.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| CLASE_ID | NUMBER | No | Sí | PK, UQ | Identidad Oracle | PK generada para una sesión académica. |
| MATERIA_ID | NUMBER | No | No | FK, UQ, UQ |  | FK a materias; interviene en la unicidad del horario. |
| PROFESOR_ID | NUMBER | No | No |  |  | Responsable al crear la clase, conservado como instantanea. |
| FECHA_HORA | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Inicio de la clase con zona horaria; fecha que utiliza el calendario. |
| INSTANTE_UTC | TIMESTAMP(6) | Sí | No | UQ | SYS_EXTRACT_UTC("FECHA_HORA") | Columna virtual SYS_EXTRACT_UTC(fecha_hora), usada en la unicidad. |
| LOTE_LEGADO | NUMBER | No | No | UQ | 0 | 0 para clases nuevas; ocurrencias historicas duplicadas se conservan en lotes 1,2,... |
| ESTADO | VARCHAR2(12 CHAR) | No | No |  | 'BORRADOR' | BORRADOR o CONFIRMADA. |
| ORIGEN | VARCHAR2(12 CHAR) | No | No |  | 'PENDIENTE' | PENDIENTE, FACIAL, VOZ o LEGADO. |
| CLAVE_CONFIRMACION | VARCHAR2(32 CHAR) | Sí | No | UQ |  | Clave hexadecimal de propuesta (32 caracteres) para reconocer reintentos. |
| PROPUESTA_CONFIRMADA | CLOB | Sí | No |  |  | Carga canonica de la confirmacion para reconocer reintentos; sin biometria. |
| REGISTROS_CONFIRMADOS | NUMBER | No | No |  | 0 | Cantidad al confirmar; inmutable para clases normales ya confirmadas. |
| CREADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación de la fila. |
| CONFIRMADO_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Instante en que quedó confirmada; nulo en borrador. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_CLASES_CANTIDAD | CHECK (REGISTROS_CONFIRMADOS): registros_confirmados>=0 AND registros_confirmados=TRUNC(registros_confirmados) | ENABLED / VALIDATED |
| CK_CLASES_CONFIRMADA | CHECK (ESTADO, ORIGEN, CLAVE_CONFIRMACION, PROPUESTA_CONFIRMADA, CONFIRMADO_EN):                  (estado='BORRADOR' AND origen='PENDIENTE' AND clave_confirmacion IS NULL AND propuesta_confirmada IS NULL AND confirmado_en IS NULL)                 OR (estado='CONFIRMADA' AND origen='LEGADO' AND clave_confirmacion IS NULL AND confirmado_en IS NOT NULL)                 OR (estado='CONFIRMADA' AND origen IN ('FACIAL','VOZ') AND LENGTH(clave_confirmacion)=32 AND clave_confirmacion IS NOT NULL AND propuesta_confirmada IS NOT NULL AND confirmado_en IS NOT NULL) | ENABLED / VALIDATED |
| CK_CLASES_ESTADO | CHECK (ESTADO): estado IN ('BORRADOR','CONFIRMADA') | ENABLED / VALIDATED |
| CK_CLASES_JSON | CHECK (PROPUESTA_CONFIRMADA): propuesta_confirmada IS JSON | ENABLED / VALIDATED |
| CK_CLASES_LOTE | CHECK (LOTE_LEGADO, ORIGEN): lote_legado>=0 AND lote_legado=TRUNC(lote_legado) AND (lote_legado=0 OR origen='LEGADO') | ENABLED / VALIDATED |
| CK_CLASES_ORIGEN | CHECK (ORIGEN): origen IN ('PENDIENTE','FACIAL','VOZ','LEGADO') | ENABLED / VALIDATED |
| FK_CLASES_MATERIA | FK (MATERIA_ID) → MATERIAS(MATERIA_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| PK_CLASES | PK (CLASE_ID) | ENABLED / VALIDATED |
| SYS_C0037105 | CHECK (CLASE_ID): "CLASE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037106 | CHECK (MATERIA_ID): "MATERIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037107 | CHECK (PROFESOR_ID): "PROFESOR_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037108 | CHECK (FECHA_HORA): "FECHA_HORA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037109 | CHECK (LOTE_LEGADO): "LOTE_LEGADO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037110 | CHECK (ESTADO): "ESTADO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037111 | CHECK (ORIGEN): "ORIGEN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037112 | CHECK (REGISTROS_CONFIRMADOS): "REGISTROS_CONFIRMADOS" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037113 | CHECK (CREADO_EN): "CREADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| UQ_CLASES_CONFIRMACION | UNIQUE (CLAVE_CONFIRMACION) | ENABLED / VALIDATED |
| UQ_CLASES_INSTANTE | UNIQUE (MATERIA_ID, INSTANTE_UTC, LOTE_LEGADO) | ENABLED / VALIDATED |
| UQ_CLASES_MATERIA | UNIQUE (CLASE_ID, MATERIA_ID) | ENABLED / VALIDATED |

## ESTUDIANTES

Perfiles estudiantiles y vectores biometricos JSON; no guarda fotos ni audio.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| ESTUDIANTE_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada por Oracle para la cuenta estudiantil. |
| NOMBRE | VARCHAR2(200 CHAR) | No | No |  |  | Nombre legible de la persona o materia. |
| EMBEDDING_FACIAL | CLOB | Sí | No |  |  | Vector facial de 128 dimensiones serializado como JSON. |
| EMBEDDING_VOZ | CLOB | Sí | No |  |  | Vector de hablante de 256 dimensiones serializado como JSON, opcional. |
| CREADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación de la fila. |
| ACTUALIZADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion. |
| ACTIVO | NUMBER(1,0) | No | No |  | 1 | 1: cuenta/materia activa; 0: archivada o deshabilitada. |
| CODIGO_INSTITUCIONAL | VARCHAR2(50 CHAR) | Sí | No |  |  | Identificador unico. NULL solo para perfiles heredados/administrativos pendientes de completar. |
| VERSION_EDICION | NUMBER | No | No |  | 0 | Contador de edición que incrementa el trigger; detecta formularios obsoletos. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_ESTUDIANTES_ACTIVO | CHECK (ACTIVO): activo IN (0,1) | ENABLED / VALIDATED |
| CK_ESTUDIANTES_CODIGO | CHECK (CODIGO_INSTITUCIONAL): codigo_institucional IS NULL OR REGEXP_LIKE(codigo_institucional,'^[A-Z0-9][A-Z0-9_.-]{0,49}$') | ENABLED / VALIDATED |
| CK_ESTUDIANTES_FACIAL_JSON | CHECK (EMBEDDING_FACIAL): embedding_facial IS JSON | ENABLED / VALIDATED |
| CK_ESTUDIANTES_VOZ_JSON | CHECK (EMBEDDING_VOZ): embedding_voz IS JSON | ENABLED / VALIDATED |
| PK_ESTUDIANTES | PK (ESTUDIANTE_ID) | ENABLED / VALIDATED |
| SYS_C0037047 | CHECK (ESTUDIANTE_ID): "ESTUDIANTE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037048 | CHECK (NOMBRE): "NOMBRE" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037049 | CHECK (CREADO_EN): "CREADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037103 | CHECK (ACTUALIZADO_EN): "ACTUALIZADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037137 | CHECK (ACTIVO): "ACTIVO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037165 | CHECK (VERSION_EDICION): "VERSION_EDICION" IS NOT NULL | ENABLED / VALIDATED |

## EVENTOS_GESTION

Trazabilidad de gestión de cuentas, materias y verificaciones de identidad.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| EVENTO_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada de la bitácora general. |
| ENTIDAD | VARCHAR2(20 CHAR) | No | No |  |  | Tipo de objeto afectado: cuenta, materia, auditoría o verificación. |
| ENTIDAD_ID | NUMBER | No | No |  |  | ID interpretado según entidad; 0 puede representar identidad todavía desconocida. |
| ACCION | VARCHAR2(30 CHAR) | No | No |  |  | Nombre de la operación registrada por el paquete/servicio. |
| MOTIVO | VARCHAR2(500 CHAR) | No | No |  |  | Justificación de la acción; debe excluir contraseñas y detalles médicos. |
| ACTOR_ROL | VARCHAR2(20 CHAR) | No | No |  |  | Rol declarado para la acción; puede incluir SISTEMA o NO_IDENTIFICADO en los historiales. |
| ACTOR_ID | NUMBER | Sí | No |  |  | Identificador del actor, interpretado según el rol; no es una FK polimórfica. |
| OCURRIDO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación del evento histórico. |
| VALORES_ANTERIORES | CLOB | Sí | No |  |  | Instantanea JSON administrativa sin hashes ni biometria. |
| VALORES_NUEVOS | CLOB | Sí | No |  |  | JSON opcional con campos seleccionados después de editar. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_EVENTOS_ANTES_JSON | CHECK (VALORES_ANTERIORES): valores_anteriores IS JSON | ENABLED / VALIDATED |
| CK_EVENTOS_DESPUES_JSON | CHECK (VALORES_NUEVOS): valores_nuevos IS JSON | ENABLED / VALIDATED |
| PK_EVENTOS_GESTION | PK (EVENTO_ID) | ENABLED / VALIDATED |
| SYS_C0037143 | CHECK (EVENTO_ID): "EVENTO_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037144 | CHECK (ENTIDAD): "ENTIDAD" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037145 | CHECK (ENTIDAD_ID): "ENTIDAD_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037146 | CHECK (ACCION): "ACCION" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037147 | CHECK (MOTIVO): "MOTIVO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037148 | CHECK (ACTOR_ROL): "ACTOR_ROL" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037149 | CHECK (OCURRIDO_EN): "OCURRIDO_EN" IS NOT NULL | ENABLED / VALIDATED |

## HISTORIAL_MATRICULAS

Eventos de alta y retiro posteriores a la migracion; no elimina historia al borrar entidades.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| HISTORIAL_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada del evento de matrícula. |
| ACCION | VARCHAR2(10 CHAR) | No | No |  |  | ALTA o RETIRO. |
| MATERIA_ID | NUMBER | No | No |  |  | Materia de la matrícula histórica; sin FK. |
| ESTUDIANTE_ID | NUMBER | No | No |  |  | Estudiante de la matrícula histórica; sin FK. |
| MATRICULADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Fecha de alta de esa relación de matrícula. |
| OCURRIDO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación del evento histórico. |
| USUARIO_BD | VARCHAR2(128 CHAR) | No | No |  |  | Usuario técnico Oracle que ejecutó la operación, distinto del actor de la aplicación. |
| ACTOR_ROL | VARCHAR2(20 CHAR) | No | No |  |  | Rol declarado para la acción; puede incluir SISTEMA o NO_IDENTIFICADO en los historiales. |
| ACTOR_ID | NUMBER | Sí | No |  |  | Identidad declarada por la aplicacion o SQLPlus; no sustituye autenticacion. |
| MOTIVO | VARCHAR2(500 CHAR) | Sí | No |  |  | Justificación de la acción; debe excluir contraseñas y detalles médicos. |
| MODULO | VARCHAR2(64 CHAR) | Sí | No |  |  | Módulo técnico informado por la sesión Oracle. |
| IDENTIFICADOR_CLIENTE | VARCHAR2(64 CHAR) | Sí | No |  |  | Identificador técnico de cliente de la sesión Oracle. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_HISTMAT_ACCION | CHECK (ACCION): accion IN ('ALTA', 'RETIRO') | ENABLED / VALIDATED |
| CK_HISTMAT_ROL | CHECK (ACTOR_ROL): actor_rol IN ('PROFESOR','ESTUDIANTE','ADMINISTRADOR','SISTEMA','NO_IDENTIFICADO') | ENABLED / VALIDATED |
| PK_HISTORIAL_MATRICULAS | PK (HISTORIAL_ID) | ENABLED / VALIDATED |
| SYS_C0037091 | CHECK (HISTORIAL_ID): "HISTORIAL_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037092 | CHECK (ACCION): "ACCION" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037093 | CHECK (MATERIA_ID): "MATERIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037094 | CHECK (ESTUDIANTE_ID): "ESTUDIANTE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037095 | CHECK (MATRICULADO_EN): "MATRICULADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037096 | CHECK (OCURRIDO_EN): "OCURRIDO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037097 | CHECK (USUARIO_BD): "USUARIO_BD" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037098 | CHECK (ACTOR_ROL): "ACTOR_ROL" IS NOT NULL | ENABLED / VALIDATED |

## LIMITES_ACCESO

Ventana de intentos por SHA256 de usuario; no almacena claves ni nombres de acceso.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| CLAVE | VARCHAR2(64 CHAR) | No | No | PK |  | PK: huella del identificador/ámbito de acceso, no la contraseña. |
| INTENTOS | NUMBER | No | No |  | 0 | Número de fallos en la ventana vigente. |
| VENTANA_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Inicio de la ventana de recuento. |
| BLOQUEADO_HASTA | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Fin del bloqueo; nulo si no se impuso. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_LIMITES_INTENTOS | CHECK (INTENTOS): intentos>=0 AND intentos=TRUNC(intentos) | ENABLED / VALIDATED |
| PK_LIMITES_ACCESO | PK (CLAVE) | ENABLED / VALIDATED |
| SYS_C0037139 | CHECK (INTENTOS): "INTENTOS" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037140 | CHECK (VENTANA_EN): "VENTANA_EN" IS NOT NULL | ENABLED / VALIDATED |

## MATERIAS

Materias y secciones administradas por un profesor.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| MATERIA_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada por Oracle para la materia/sección. |
| CODIGO_MATERIA | VARCHAR2(50 CHAR) | No | No | UQ |  | Código único de la materia/sección, normalizado por la aplicación. |
| NOMBRE | VARCHAR2(200 CHAR) | No | No |  |  | Nombre legible de la persona o materia. |
| SECCION | VARCHAR2(100 CHAR) | Sí | No |  |  | Nombre o código descriptivo del grupo; no referencia otra tabla de grupos. |
| PROFESOR_ID | NUMBER | No | No | FK |  | FK al profesor responsable de la materia. |
| CREADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación de la fila. |
| ACTUALIZADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion. |
| ACTIVO | NUMBER(1,0) | No | No |  | 1 | 1: cuenta/materia activa; 0: archivada o deshabilitada. |
| VERSION_EDICION | NUMBER | No | No |  | 0 | Contador de edición que incrementa el trigger; detecta formularios obsoletos. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_MATERIAS_ACTIVO | CHECK (ACTIVO): activo IN (0,1) | ENABLED / VALIDATED |
| FK_MATERIAS_PROFESOR | FK (PROFESOR_ID) → PROFESORES(PROFESOR_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| PK_MATERIAS | PK (MATERIA_ID) | ENABLED / VALIDATED |
| SYS_C0037053 | CHECK (MATERIA_ID): "MATERIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037054 | CHECK (CODIGO_MATERIA): "CODIGO_MATERIA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037055 | CHECK (NOMBRE): "NOMBRE" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037056 | CHECK (PROFESOR_ID): "PROFESOR_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037057 | CHECK (CREADO_EN): "CREADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037104 | CHECK (ACTUALIZADO_EN): "ACTUALIZADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037138 | CHECK (ACTIVO): "ACTIVO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037166 | CHECK (VERSION_EDICION): "VERSION_EDICION" IS NOT NULL | ENABLED / VALIDATED |
| UQ_MATERIAS_CODIGO | UNIQUE (CODIGO_MATERIA) | ENABLED / VALIDATED |

## MATERIA_ESTUDIANTES

Relacion muchos a muchos entre estudiantes y materias.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| MATERIA_ID | NUMBER | No | No | FK, PK |  | Parte de la PK compuesta y FK a materias. |
| ESTUDIANTE_ID | NUMBER | No | No | FK, PK |  | Parte de la PK compuesta y FK a estudiantes. |
| MATRICULADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Fecha de alta de esa relación de matrícula. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| FK_ME_ESTUDIANTE | FK (ESTUDIANTE_ID) → ESTUDIANTES(ESTUDIANTE_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| FK_ME_MATERIA | FK (MATERIA_ID) → MATERIAS(MATERIA_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| PK_MATERIA_ESTUDIANTES | PK (MATERIA_ID, ESTUDIANTE_ID) | ENABLED / VALIDATED |
| SYS_C0037061 | CHECK (MATERIA_ID): "MATERIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037062 | CHECK (ESTUDIANTE_ID): "ESTUDIANTE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037063 | CHECK (MATRICULADO_EN): "MATRICULADO_EN" IS NOT NULL | ENABLED / VALIDATED |

## PROFESORES

Cuentas docentes; la contrasena contiene un hash bcrypt.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| PROFESOR_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada por Oracle para la cuenta docente. |
| USUARIO | VARCHAR2(100 CHAR) | No | No | UQ |  | Identificador de acceso; la aplicación lo normaliza. |
| CONTRASENA | VARCHAR2(255 CHAR) | No | No |  |  | Hash bcrypt; no permite consultar la contraseña en texto. |
| NOMBRE | VARCHAR2(200 CHAR) | No | No |  |  | Nombre legible de la persona o materia. |
| CREADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de creación de la fila. |
| ACTUALIZADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion. |
| ACTIVO | NUMBER(1,0) | No | No |  | 1 | 1: cuenta/materia activa; 0: archivada o deshabilitada. |
| VERSION_EDICION | NUMBER | No | No |  | 0 | Contador de edición que incrementa el trigger; detecta formularios obsoletos. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_PROFESORES_ACTIVO | CHECK (ACTIVO): activo IN (0,1) | ENABLED / VALIDATED |
| PK_PROFESORES | PK (PROFESOR_ID) | ENABLED / VALIDATED |
| SYS_C0037040 | CHECK (PROFESOR_ID): "PROFESOR_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037041 | CHECK (USUARIO): "USUARIO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037042 | CHECK (CONTRASENA): "CONTRASENA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037043 | CHECK (NOMBRE): "NOMBRE" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037044 | CHECK (CREADO_EN): "CREADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037102 | CHECK (ACTUALIZADO_EN): "ACTUALIZADO_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037136 | CHECK (ACTIVO): "ACTIVO" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037164 | CHECK (VERSION_EDICION): "VERSION_EDICION" IS NOT NULL | ENABLED / VALIDATED |
| UQ_PROFESORES_USUARIO | UNIQUE (USUARIO) | ENABLED / VALIDATED |

## REGISTROS_ASISTENCIA

Resultados individuales de las tomas de asistencia.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| ASISTENCIA_ID | NUMBER | No | Sí | PK | Identidad Oracle | PK generada del resultado individual. |
| MATERIA_ID | NUMBER | No | No | FK, FK |  | Identificador de la materia/sección. |
| ESTUDIANTE_ID | NUMBER | No | No | FK, UQ |  | Identificador del estudiante. |
| FECHA_HORA | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Instante del analisis; el horario de clase esta en CLASES.FECHA_HORA. |
| PRESENTE | NUMBER(1,0) | No | No |  | 0 | Decisión final: 1 asistió, 0 no asistió. |
| CLASE_ID | NUMBER | No | No | FK, UQ |  | Clase del resultado; participa en la FK compuesta clase/materia y en la unicidad por estudiante. |
| PRESENTE_DETECTADO | NUMBER(1,0) | Sí | No |  |  | NULL cuando no hay muestra; nunca usar NVL para convertirlo en ausencia. |
| CORREGIDO_MANUAL | NUMBER(1,0) | No | No |  | 0 | Correccion previa a la primera confirmacion; las ediciones posteriores se auditan con el disparador. |
| MOTIVO_CORRECCION | VARCHAR2(500 CHAR) | Sí | No |  |  | Motivo de la revisión manual antes de confirmar. |
| REVISADO_POR | NUMBER | Sí | No |  |  | Docente de esa revisión inicial; referencia lógica sin FK. |
| REVISADO_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Instante de la revisión manual inicial. |
| ESTADO_DETECCION | VARCHAR2(20 CHAR) | No | No |  |  | Resultado original: PRESENTE/AUSENTE o SIN_MUESTRA. Un fallo global no se confirma. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_ASISTENCIA_PRESENTE | CHECK (PRESENTE): presente IN (0, 1) | ENABLED / VALIDATED |
| CK_RA_CORREGIDO | CHECK (CORREGIDO_MANUAL): corregido_manual IN (0,1) | ENABLED / VALIDATED |
| CK_RA_DETECCION_COHERENTE | CHECK (PRESENTE_DETECTADO, ESTADO_DETECCION, CORREGIDO_MANUAL):          (estado_deteccion='SIN_MUESTRA' AND presente_detectado IS NULL AND corregido_manual=1)         OR (estado_deteccion='PRESENTE' AND presente_detectado IS NOT NULL AND presente_detectado=1)         OR (estado_deteccion='AUSENTE' AND presente_detectado IS NOT NULL AND presente_detectado=0) | ENABLED / VALIDATED |
| CK_RA_DETECTADO | CHECK (PRESENTE_DETECTADO): presente_detectado IN (0,1) | ENABLED / VALIDATED |
| CK_RA_ESTADO_DETECCION | CHECK (ESTADO_DETECCION): estado_deteccion IN ('PRESENTE','AUSENTE','SIN_MUESTRA') | ENABLED / VALIDATED |
| CK_RA_REVISION | CHECK (CORREGIDO_MANUAL, MOTIVO_CORRECCION, REVISADO_POR, REVISADO_EN):          (corregido_manual=0 AND motivo_correccion IS NULL AND revisado_por IS NULL AND revisado_en IS NULL)         OR (corregido_manual=1 AND TRIM(motivo_correccion) IS NOT NULL AND revisado_por IS NOT NULL AND revisado_en IS NOT NULL) | ENABLED / VALIDATED |
| FK_RA_CLASE_MATERIA | FK (CLASE_ID, MATERIA_ID) → CLASES(CLASE_ID, MATERIA_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| FK_RA_ESTUDIANTE | FK (ESTUDIANTE_ID) → ESTUDIANTES(ESTUDIANTE_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| FK_RA_MATERIA | FK (MATERIA_ID) → MATERIAS(MATERIA_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| PK_REGISTROS_ASISTENCIA | PK (ASISTENCIA_ID) | ENABLED / VALIDATED |
| SYS_C0037067 | CHECK (ASISTENCIA_ID): "ASISTENCIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037068 | CHECK (MATERIA_ID): "MATERIA_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037069 | CHECK (ESTUDIANTE_ID): "ESTUDIANTE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037070 | CHECK (FECHA_HORA): "FECHA_HORA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037071 | CHECK (PRESENTE): "PRESENTE" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037125 | CHECK (CORREGIDO_MANUAL): "CORREGIDO_MANUAL" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037126 | CHECK (CLASE_ID): "CLASE_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037133 | CHECK (ESTADO_DETECCION): "ESTADO_DETECCION" IS NOT NULL | ENABLED / VALIDATED |
| UQ_RA_CLASE_ESTUDIANTE | UNIQUE (CLASE_ID, ESTUDIANTE_ID) | ENABLED / VALIDATED |

## SESIONES_USUARIO

Una sesion vigente por rol/cuenta. Solo SHA-256 del token, nunca el token original ni contrasenas.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| ROL | VARCHAR2(20 CHAR) | No | No | PK |  | Parte de PK: PROFESOR, ESTUDIANTE o ADMINISTRADOR. |
| ACTOR_ID | NUMBER | No | No | PK |  | Parte de PK: ID de la cuenta dentro de su rol; referencia lógica. |
| TOKEN_HASH | VARCHAR2(64 CHAR) | No | No |  |  | SHA-256 hexadecimal del token de sesión, nunca su valor original. |
| CREADA_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Inicio de la sesión que ocupa actualmente la fila. |
| ACTIVIDAD_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Última actividad validada para calcular inactividad. |
| EXPIRA_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  |  | Vencimiento absoluto de la sesión (ocho horas en la política actual). |
| REVOCADA_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Instante de revocación; nulo mientras no se haya revocado explícitamente. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_SESIONES_ACTOR | CHECK (ACTOR_ID): actor_id>0 AND actor_id=TRUNC(actor_id) | ENABLED / VALIDATED |
| CK_SESIONES_FECHAS | CHECK (EXPIRA_EN, ACTIVIDAD_EN, CREADA_EN): expira_en>creada_en AND actividad_en>=creada_en | ENABLED / VALIDATED |
| CK_SESIONES_HASH | CHECK (TOKEN_HASH): REGEXP_LIKE(token_hash,'^[a-f0-9]{64}$','c') | ENABLED / VALIDATED |
| CK_SESIONES_ROL | CHECK (ROL): rol IN ('PROFESOR','ESTUDIANTE','ADMINISTRADOR') | ENABLED / VALIDATED |
| PK_SESIONES_USUARIO | PK (ROL, ACTOR_ID) | ENABLED / VALIDATED |
| SYS_C0037171 | CHECK (ROL): "ROL" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037172 | CHECK (ACTOR_ID): "ACTOR_ID" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037173 | CHECK (TOKEN_HASH): "TOKEN_HASH" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037174 | CHECK (CREADA_EN): "CREADA_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037175 | CHECK (ACTIVIDAD_EN): "ACTIVIDAD_EN" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037176 | CHECK (EXPIRA_EN): "EXPIRA_EN" IS NOT NULL | ENABLED / VALIDATED |

## VERIFICACION_ESTUDIANTES

Autorizacion excepcional separada del ultimo metodo de verificacion. Documento HMAC y contraseña bcrypt; nunca documento completo.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| ESTUDIANTE_ID | NUMBER | No | No | FK, PK |  | PK compartida y FK a estudiantes: como máximo una fila por estudiante. |
| DOCUMENTO_HUELLA | VARCHAR2(64 CHAR) | Sí | No | UQ |  | HMAC-SHA-256 de tipo/número normalizado; único cuando existe. |
| TIPO_DOCUMENTO | VARCHAR2(2 CHAR) | Sí | No |  |  | CC, TI, CE o PA. |
| DOCUMENTO_FINAL | VARCHAR2(4 CHAR) | Sí | No |  |  | Últimos cuatro caracteres para mostrar el documento enmascarado. |
| CLAVE_HASH | VARCHAR2(255 CHAR) | Sí | No |  |  | Bcrypt de la contraseña alternativa; se retira al revocar. |
| EXCEPCION_ACTIVA | NUMBER(1,0) | No | No |  | 0 | 1 habilita el permiso sujeto a vigencia/cuenta; 0 lo deshabilita. |
| CATEGORIA | VARCHAR2(20 CHAR) | Sí | No |  |  | FISICA, MEDICA, TECNICA o ADMINISTRATIVA; no es un diagnóstico. |
| REFERENCIA | VARCHAR2(100 CHAR) | Sí | No |  |  | Referencia administrativa del expediente de autorización. |
| AUTORIZADO_POR | NUMBER | Sí | No | FK |  | FK al administrador que aprobó o renovó. |
| AUTORIZADO_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Fecha de aprobación/renovación. |
| EXPIRA_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Fin de la autorización; la interfaz exige vigencia de 1 a 365 días. |
| ESTADO_VERIFICACION | VARCHAR2(25 CHAR) | No | No |  | 'PENDIENTE' | Resultado del último acceso confirmado: PENDIENTE, BIOMETRICA_COMPLETA o EXCEPCIONAL. |
| VERIFICADO_EN | TIMESTAMP(6) WITH TIME ZONE | Sí | No |  |  | Instante de esa verificación; nulo si está PENDIENTE. |
| FACTORES_VERIFICADOS | NUMBER(2,0) | No | No |  | 0 | Cantidad de factores biométricos comprobados en ese acceso. |
| FACTORES_REQUERIDOS | NUMBER(2,0) | No | No |  | 1 | Cantidad mínima de factores de la política registrada para ese acceso. |
| VERSION_CREDENCIAL | NUMBER | No | No |  | 0 | Contador para concurrencia e invalidación de pruebas/credenciales anteriores. |
| AUTORIZADO_DOCENTE_POR | NUMBER | Sí | No | FK |  | Docente que autoriza el acceso alternativo; no es una confirmacion de asistencia. |
| MATERIA_AUTORIZACION_ID | NUMBER | Sí | No | FK |  | Materia propia con matricula vigente al emitir o renovar la credencial de acceso. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| CK_VERIFICACION_ACTIVA | CHECK (EXCEPCION_ACTIVA): excepcion_activa IN (0,1) | ENABLED / VALIDATED |
| CK_VERIFICACION_APROBADA | CHECK (DOCUMENTO_FINAL, AUTORIZADO_EN, MATERIA_AUTORIZACION_ID, DOCUMENTO_HUELLA, TIPO_DOCUMENTO, AUTORIZADO_DOCENTE_POR, CLAVE_HASH, EXCEPCION_ACTIVA, CATEGORIA, REFERENCIA, AUTORIZADO_POR): excepcion_activa=0 OR (documento_huella IS NOT NULL AND tipo_documento IS NOT NULL AND          documento_final IS NOT NULL AND clave_hash IS NOT NULL AND categoria IS NOT NULL AND          referencia IS NOT NULL AND autorizado_en IS NOT NULL AND          ((autorizado_por IS NOT NULL AND autorizado_docente_por IS NULL AND materia_autorizacion_id IS NULL) OR           (autorizado_por IS NULL AND autorizado_docente_por IS NOT NULL AND materia_autorizacion_id IS NOT NULL))) | ENABLED / VALIDATED |
| CK_VERIFICACION_CATEGORIA | CHECK (CATEGORIA): categoria IN ('FISICA','MEDICA','TECNICA','ADMINISTRATIVA') | ENABLED / VALIDATED |
| CK_VERIFICACION_ESTADO | CHECK (ESTADO_VERIFICACION): estado_verificacion IN ('PENDIENTE','BIOMETRICA_COMPLETA','EXCEPCIONAL') | ENABLED / VALIDATED |
| CK_VERIFICACION_FACTORES | CHECK (FACTORES_VERIFICADOS, FACTORES_REQUERIDOS): factores_verificados BETWEEN 0 AND 3 AND factores_requeridos BETWEEN 1 AND 3 | ENABLED / VALIDATED |
| CK_VERIFICACION_HUELLA | CHECK (DOCUMENTO_HUELLA): REGEXP_LIKE(documento_huella,'^[a-f0-9]{64}$','c') | ENABLED / VALIDATED |
| CK_VERIFICACION_RESULTADO | CHECK (FACTORES_VERIFICADOS, VERIFICADO_EN, ESTADO_VERIFICACION, FACTORES_REQUERIDOS):              (estado_verificacion='PENDIENTE' AND verificado_en IS NULL AND factores_verificados=0) OR             (estado_verificacion='EXCEPCIONAL' AND verificado_en IS NOT NULL AND factores_verificados=0) OR             (estado_verificacion='BIOMETRICA_COMPLETA' AND verificado_en IS NOT NULL AND factores_verificados>=factores_requeridos) | ENABLED / VALIDATED |
| CK_VERIFICACION_TIPO | CHECK (TIPO_DOCUMENTO): tipo_documento IN ('CC','TI','CE','PA') | ENABLED / VALIDATED |
| CK_VERIFICACION_VERSION | CHECK (VERSION_CREDENCIAL): version_credencial>=0 AND version_credencial=TRUNC(version_credencial) | ENABLED / VALIDATED |
| FK_VERIFICACION_ADMIN | FK (AUTORIZADO_POR) → ADMINISTRADORES(ADMINISTRADOR_ID) · ON DELETE NO ACTION | ENABLED / VALIDATED |
| FK_VERIFICACION_DOCENTE | FK (AUTORIZADO_DOCENTE_POR) → PROFESORES(PROFESOR_ID) · ON DELETE NO ACTION | ENABLED / VALIDATED |
| FK_VERIFICACION_EST | FK (ESTUDIANTE_ID) → ESTUDIANTES(ESTUDIANTE_ID) · ON DELETE CASCADE | ENABLED / VALIDATED |
| FK_VERIFICACION_MATERIA | FK (MATERIA_AUTORIZACION_ID) → MATERIAS(MATERIA_ID) · ON DELETE NO ACTION | ENABLED / VALIDATED |
| PK_VERIFICACION_EST | PK (ESTUDIANTE_ID) | ENABLED / VALIDATED |
| SYS_C0037182 | CHECK (EXCEPCION_ACTIVA): "EXCEPCION_ACTIVA" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037183 | CHECK (ESTADO_VERIFICACION): "ESTADO_VERIFICACION" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037184 | CHECK (FACTORES_VERIFICADOS): "FACTORES_VERIFICADOS" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037185 | CHECK (FACTORES_REQUERIDOS): "FACTORES_REQUERIDOS" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037186 | CHECK (VERSION_CREDENCIAL): "VERSION_CREDENCIAL" IS NOT NULL | ENABLED / VALIDATED |
| UQ_VERIFICACION_DOC | UNIQUE (DOCUMENTO_HUELLA) | ENABLED / VALIDATED |

## VERSIONES_ESQUEMA

Versiones de instalacion y futuras migraciones aplicadas.

| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| VERSION | VARCHAR2(20 BYTE) | No | No | PK |  | PK textual de la migración, por ejemplo 008. |
| DESCRIPCION | VARCHAR2(200 BYTE) | No | No |  |  | Resumen de la versión instalada. |
| APLICADO_EN | TIMESTAMP(6) WITH TIME ZONE | No | No |  | SYSTIMESTAMP | Instante de aplicación de la migración. |

| Restricción | Regla | Estado |
| --- | --- | --- |
| PK_VERSIONES_ESQUEMA | PK (VERSION) | ENABLED / VALIDATED |
| SYS_C0037037 | CHECK (DESCRIPCION): "DESCRIPCION" IS NOT NULL | ENABLED / VALIDATED |
| SYS_C0037038 | CHECK (APLICADO_EN): "APLICADO_EN" IS NOT NULL | ENABLED / VALIDATED |
