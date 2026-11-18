# Respaldo, restauración y migraciones

Punto 4 de la revisión, implementado el 11 de noviembre de 2026.

Ampliación 008, 17 de noviembre de 2026: las autorizaciones y estados de verificación se incluyen
en la copia Oracle. Su clave HMAC `.local/claves/identidad.key` se conserva y restaura **por separado**,
además de la clave de cifrado de respaldos. No generar otra para una base que ya tiene documentos.
El cargador usa un cursor por tabla para evitar reutilizar parámetros tipados de una tabla vacía.
Ensayo 008 aprobado, con datos de excepción y revocación de sesiones tras restaurar:
`.local/ensayos/76D3DD47D0A3/resultado.json`.

## Crear y comprobar una copia

```powershell
.\.venv\Scripts\python.exe scripts\oracle.py respaldar
.\.venv\Scripts\python.exe scripts\restaurar_oracle.py .local\respaldos\NOMBRE_COPIA --solo-verificar
```

Las copias nuevas usan formato 2: datos por tabla y DDL cifrados con AES-GCM, manifiesto
autenticado mediante HMAC-SHA256 y claves derivadas distintas. El manifiesto identifica usuario,
PDB, versiones, columnas y recuentos; ese inventario queda legible, los datos y DDL quedan cifrados.
La lectura de datos utiliza una transacción de solo lectura consistente. No ejecutar cambios DDL
simultáneos durante el respaldo; este mecanismo no protege frente a una migración concurrente.

La clave de 32 bytes se encuentra en `.local/clave_respaldos.bin`. Es privada y hay que guardar
una copia independiente y protegida de ella: perderla impide recuperar las copias V2. Quien posea
la clave y el respaldo puede leer datos, hashes de contraseñas y biometría. No incluir la clave
en el mismo paquete que se comparte. `.local/` está excluida del repositorio; los permisos chmod
de Python no sustituyen la revisión de permisos NTFS del equipo.

Los respaldos antiguos V1 siguen presentes y contienen JSONL en claro. La herramienta permite
comprobar sus SHA-256, pero no acredita su autoría ni ejecuta automáticamente su DDL. No se
convierten ni eliminan solos. Existe una copia V2 del estado anterior a 005, además de copias
nuevas. Un respaldo interrumpido sin manifiesto completo no es utilizable. Las copias de un
esquema con objetos inválidos se rechazan al restaurar.

## Restaurar en un esquema nuevo

Crear primero una cuenta Oracle vacía, con cuota suficiente y privilegios de crear sesión,
tablas, vistas, procedimientos, secuencias y disparadores, en el PDB correcto. Después:

```powershell
.\.venv\Scripts\python.exe scripts\restaurar_oracle.py .local\respaldos\NOMBRE_COPIA --usuario-destino UPC_RECUPERACION --dsn localhost:1521/XEPDB1
```

Solicita la contraseña del destino sin mostrarla ni pasarla en argumentos. Para una clave
de respaldo guardada en otra ubicación, añadir `--clave-respaldo RUTA_PRIVADA`.

La restauración exige que el usuario coincida con el solicitado, que no sea SYS/SYSTEM ni
CDB$ROOT y que no tenga objetos. No borra ni reemplaza una base existente. Valida firma,
checksums, cifrado y datos antes del primer DDL. Restaura tablas y filas antes de FK y disparadores,
reconstruye índices, comentarios, paquetes y vistas y verifica compilación, restricciones
y huellas de todas las filas. Conserva JSON/CLOB, NULL, caracteres Unicode, fechas con offset
y fracciones, IDs y secuencias de identidad sin reutilizar números eliminados.

Oracle hace COMMIT implícito en DDL. Un fallo posterior deja un destino parcial, que debe
permanecer aislado y no utilizarse como base activa. El script no intenta borrarlo; un administrador
debe revisar y recrear únicamente ese destino antes de repetir. El origen no se toca.
La cuenta destino debe usarse exclusivamente para la restauración mientras se ejecuta.

Antes de cambiar la configuración activa: validar la aplicación contra el esquema recuperado,
reaplicar retiradas de biometría/archivos posteriores al respaldo y decidir el cambio de credenciales
de conexión. Esta entrega no cambia automáticamente la cuenta de la aplicación a una copia.

## Actualizar sin recrear

```powershell
.\.venv\Scripts\python.exe scripts\oracle.py migrar
.\.venv\Scripts\python.exe scripts\oracle.py verificar
```

`migrar` genera y verifica una copia V2 antes de aplicar los pasos faltantes hasta 007.
Las versiones se registran tras verificar la estructura; los scripts rechazan degradaciones.
Ante un DDL parcial, revisar el error y reanudar su migración reejecutable, conservando el respaldo.
`instalar` y `oracle_scripts.sql` son exclusivamente para esquemas nuevos. Ejecutar SQLPlus desde
la raíz del proyecto; los lanzadores Python establecen ese directorio.

## Retención y ensayo

Desde 007, la recuperación revoca las sesiones restauradas tras verificar la integridad de los
datos; no reactiva tokens antiguos de un respaldo. El informe incluye `sesiones_revocadas`.
Ensayo aprobado: `.local/ensayos/7A152BEC3263/resultado.json`, trece tablas restauradas,
una sesión sintética revocada y ambas cuentas temporales eliminadas.

```powershell
.\.venv\Scripts\python.exe scripts\retencion_respaldos.py
# Solo tras revisar los candidatos:
.\.venv\Scripts\python.exe scripts\retencion_respaldos.py --aplicar
```

La política inicial conserva treinta días y al menos las siete copias V2 completas y válidas
más recientes. El primer comando solo informa. La eliminación requiere `--aplicar` y se limita
a copias autenticadas dentro de `.local/respaldos`. V1, copias incompletas o inválidas y los
artefactos de `.local/ensayos` quedan fuera; requieren revisión manual. No hay tarea programada
ni copia externa automática: deben programarse según el entorno antes de un uso real.

El ensayo automatizado se ejecuta con:

```powershell
.\.venv\Scripts\python.exe scripts\ensayar_restauracion.py
```

Requiere SQLPlus y autenticación local `/ AS SYSDBA`, y solo admite Oracle local/XEPDB1.
Crea dos cuentas UPC_RT aleatorias, comprueba que no existan y elimina únicamente las cuentas
creadas por ese ensayo. Instala 004, inserta historia sintética, migra a 005 y 006 sin perderla, agrega
datos Unicode/biométricos sintéticos y decisiones manuales, respalda y restaura. Comprueba además
rechazo de clave incorrecta, archivos alterados y destino ocupado, así como continuidad de IDs.
La evidencia queda en `.local/ensayos/IDENTIFICADOR/resultado.json`, sin contraseñas ni vectores.

El ensayo 006 aprobado está en `.local/ensayos/9F563829CC52/resultado.json`: doce tablas
restauradas y ambos usuarios temporales eliminados. Los usuarios y roles Oracle externos al
esquema, como UPC_ADMIN_APP y UPC_ROL_ADMIN, no forman parte del respaldo lógico. Deben
prepararse y verificarse por separado tras restaurar en otro propietario; ver
[ADMINISTRACION.md](ADMINISTRACION.md).

Se verificó en Oracle XE 18c local. Es una prueba funcional con pocas filas sintéticas; no es
una medición de recuperación con grandes volúmenes, un ensayo de pérdida del servidor ni la
validación integral con hardware/otro PC, que permanecen aplazados.
