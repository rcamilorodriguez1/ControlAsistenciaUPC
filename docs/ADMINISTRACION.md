# Administración institucional

Implementada el 11 de noviembre de 2026, migración **006**. El texto superior «Gestión
académica» era decorativo. Ahora ese espacio contiene el botón **Gestión académica**, que abre
un acceso independiente de profesor y estudiante. No hay registro público de administradores.

Desde **007**, el administrador comparte la sesión única, revocación y navegación al inicio
de los demás roles. La conexión técnica tiene también EXECUTE sobre `PKG_SESIONES`.
Guía vigente: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md).

Desde **008**, el apartado **Verificación** permite consultar/exportar estados de identidad,
aprobar o revocar excepciones y dar de alta estudiantes sin biometría tras comprobar el documento.
El rol técnico recibe EXECUTE sobre `PKG_EXCEPCIONES`, sin DML directo sobre sus datos.
Guía: [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).

## Permisos del tercer rol

| Acción | Administración |
| --- | --- |
| Consultar auditoría de asistencia, matrículas y gestión | Sí, con periodo y límite |
| Exportar el resultado consultado | CSV UTF-8 con BOM, hasta 10 000 registros |
| Editar profesores | Nombre, usuario, estado activo y nueva contraseña opcional |
| Editar estudiantes | Nombre, código institucional y estado activo |
| Editar materias | Código, nombre, sección, estado y responsable si no existen clases |
| Archivar y reactivar cuentas/materias | Sí, con motivo e historial conservado |
| Editar/borrar auditoría o eliminar físicamente cuentas | Sin operaciones en el panel ni permisos directos en Oracle |
| Confirmar asistencia como profesor o ejecutar DDL/DBA | Sin permiso |

Las búsquedas muestran como máximo 500 coincidencias; deben acotarse por nombre, usuario o
código. En el selector de responsables se muestran hasta 500 profesores. Una materia con
clases conserva el docente original para no cambiar la autoría de su historia académica.

Cada modificación exige motivo y confirmación. El paquete PL/SQL bloquea la fila y compara
`VERSION_EDICION`: si otro proceso la modificó, se rechaza la escritura y se solicita recargar.
Los disparadores incrementan esa versión incluso para actualizaciones SQL directas.

Archivar un profesor también archiva sus materias activas, registrando cada una. Archivar un
estudiante retira sus matrículas actuales y elimina su biometría activa; conserva asistencias e
historial. Reactivar no recupera vectores borrados ni matrículas anteriores. Los códigos nulos
heredados pueden completarse; no se permite vaciar un código ya asignado.

## Auditoría y datos sensibles

`PKG_ADMINISTRACION` registra actor, motivo y valores anteriores/nuevos de los campos editables.
Un cambio de contraseña registra el evento, nunca su valor ni su hash. Las consultas no entregan
hashes ni vectores biométricos. Las fechas de auditoría incluyen su offset en formato ISO.
La preparación de un CSV deja un evento `EXPORTACION_CSV`; esto acredita su preparación,
no demuestra que el usuario haya guardado el archivo. Se neutralizan prefijos de fórmulas de
hojas de cálculo. La exportación contiene datos de cuentas y debe manejarse como información interna.

La sesión aplica los mismos límites de 30 minutos de inactividad y ocho horas de duración
máxima. El acceso bloquea quince minutos tras cinco intentos fallidos. Cada operación valida
en Oracle que la cuenta administrativa siga activa y limpia el contexto al devolver la conexión.

## Cuenta inicial y conexión técnica

En este PC se creó la cuenta de aplicación **admin.upc**. Su contraseña está exclusivamente en
`.local/ADMINISTRADOR.md`, archivo privado excluido de Git. No copiarla a esta documentación.
El botón Gestión académica utiliza esa cuenta; el usuario técnico Oracle no sirve como credencial
del formulario web.

El servidor utiliza una conexión separada **UPC_ADMIN_APP**, con el rol **UPC_ROL_ADMIN**:

- Privilegio de sistema: `CREATE SESSION`.
- `EXECUTE` sobre `PKG_AUDITORIA` y `PKG_ADMINISTRACION` del propietario del proyecto.
- `SELECT` sobre `V_AUDITORIA_ASISTENCIA`, `V_HISTORIAL_MATRICULAS` y `V_EVENTOS_GESTION`.

No recibe DML directo sobre tablas, lectura de contraseñas, privilegios de creación ni DBA.
Los paquetes se ejecutan con derechos de su propietario y comprueban el contexto administrativo.
Ese contexto es una declaración del servidor de confianza, no un mecanismo para dar las
credenciales técnicas a usuarios humanos. Las claves técnicas permanecen en
`.streamlit/secrets.toml`. Profesor y estudiante todavía utilizan el pool original del propietario;
la conexión local conserva esa configuración. Para cloud ya está implementado el runtime
`UPC_AULA_APP` con `ORACLE_ESQUEMA` explícito y permisos de columna; su creación y
verificación cloud se completaron el 22/11. La cuenta administrativa sigue separada. Ver
[cuenta de ejecución](CUENTA_EJECUCION.md).

## Preparación en otro equipo

Con Oracle local/XEPDB1, SQL*Plus disponible y autenticación Windows autorizada para SYS:

```powershell
# Con la aplicación detenida y su configuración Oracle ya preparada:
.\.venv\Scripts\python.exe scripts\oracle.py migrar
.\.venv\Scripts\python.exe scripts\preparar_administracion.py
.\.venv\Scripts\python.exe scripts\oracle.py verificar
.\iniciar.cmd
```

La migración conserva los datos y crea un respaldo cifrado previo. El preparador ejecuta
`sql/30_permisos_administracion.sql`, crea el rol y usuario técnico y habilita la cuenta inicial.
Guarda las claves en los archivos privados antes indicados, sin imprimirlas. Rechaza sustituir
usuarios o roles preexistentes; repetirlo sobre la configuración completada no cambia contraseñas.
Ante una preparación parcial debe revisarse el estado conservado en `.local/`, sin borrar cuentas.
El preparador inicial no ofrece altas ni edición de otros administradores desde la web.

## Verificación de esta entrega

- **150 pruebas** de Python, interfaz y Oracle: `.local/pruebas006_completas.log`.
- Acceso real con Brave aislado a **https://localhost:8501**, consulta de auditoría, CSV,
  cuentas, materias, escritorio/móvil emulado y cierre de sesión:
  `.local/frontend/c50d0f625498/resultado.json`. No se editaron los datos académicos existentes.
- Restauración 006 en dos esquemas temporales, migración con historia previa, control de
  integridad, continuidad de IDs y rechazo de alteraciones:
  `.local/ensayos/9F563829CC52/resultado.json`. Ambos esquemas temporales fueron eliminados.
- La conexión técnica real pudo consultar por el paquete; la lectura directa de contraseñas
  de profesores fue rechazada por Oracle (`ORA-00942`).

La instalación completa tiene **12 tablas, 11 vistas, cinco paquetes con sus cuerpos y diez
disparadores**. El respaldo lógico incluye el esquema, la tabla de administradores y sus datos;
no crea usuarios/roles externos ni conserva sus grants. Tras restaurar en otro propietario se
debe preparar y verificar de nuevo esa conexión técnica. Las pruebas no sustituyen el ensayo
pendiente con cámara, micrófono, usuarios reales y otro PC.
