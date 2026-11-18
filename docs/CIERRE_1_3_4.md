# Cierre de los puntos 1, 3 y 4

11 de noviembre de 2026. Los números corresponden a la revisión actual del
[roadmap](ROADMAP.md), no a sus fases históricas.

Actualización posterior: el punto 2 de frontend ya está implementado. Esta página conserva
la evidencia del cierre anterior; el estado y las pruebas nuevas están en [FRONTEND.md](FRONTEND.md).

## Cambios entregados

| Punto | Resultado |
| --- | --- |
| 1: reconocimiento | Comparación facial por distancia y voz por coseno, rechazo absoluto y por margen, manejo de cero/una/pocas referencias y filtro de matrícula facial. Evaluador y propuesta de calibración disponibles. |
| 3: reglas de negocio | Migración 005, código institucional, campos y duplicados validados, autorización de altas docentes, límite de intentos, vencimiento de sesiones, archivo sin borrar historia y retirada de biometría. Acciones disponibles en los paneles. |
| 4: recuperación | Copias V2 cifradas/autenticadas, restauración solo en esquema vacío, comparación de datos/objetos/restricciones, continuidad de IDs y retención con consulta previa. Migración y restauración ensayadas en cuentas temporales. |

El esquema activo es UPC_ASISTENCIA/XEPDB1, con versiones 001–005: once tablas, once vistas,
cuatro paquetes con sus cuerpos y nueve disparadores. Las verificaciones no detectaron objetos
inválidos ni errores PL/SQL. La aplicación conserva su cuenta original; no se promovió una copia
recuperada como base activa. Al terminar las pruebas, las tablas de negocio siguen sin filas
de personas, clases o asistencias; los fixtures no quedaron guardados.

## Evidencia de validación

- Suite de regresión: 124 pruebas, incluidas integración Oracle, sesiones y pantallas de Streamlit.
  Resultado en `.local/pruebas005_final.log`. Las pruebas Oracle revierten sus fixtures.
- Diagnóstico de Python, dependencias y esquema: `.local/diagnostico005.log`.
- Verificación SQLPlus 005: `.local/verificacion005.log`.
- DDL actualizado: `exports/esquema_ddl.sql`, exportado mediante SQLPlus.
- Ensayo final de recuperación: `.local/ensayos/82E39B58824F/resultado.json`.
  Incluyó historia creada en 004, migración a 005, dos clases y tres asistencias, vectores
  sintéticos, Unicode, NULL, corrección auditada, decisión manual SIN_MUESTRA y retiro de matrícula.
  La restauración comparó todas las filas, el inventario de objetos y los estados de los triggers.
  Rechazó contraseña de cifrado incorrecta, manifiesto alterado, archivo alterado y destino ocupado.
  Verificó que las identidades nuevas no reutilizaran IDs eliminados. Ambas cuentas temporales
  UPC_RT del ensayo se eliminaron al terminar.
- Copia final de la base activa: `.local/respaldos/20261111T101222Z_44232a0a`, formato V2,
  once tablas y versiones 001–005; también verificada con `restaurar_oracle.py --solo-verificar`.
- Evaluador por línea de comandos: `.local/evaluacion005.json`, veinte consultas sintéticas.
  Demuestra el funcionamiento del evaluador; no acredita precisión con personas reales ni
  cambió los umbrales activos.
- Retención ejecutada en modo de consulta: cero copias candidatas; no se eliminaron respaldos.

Los directorios `.local/`, `.streamlit/secrets.toml`, `.certs/` y `exports/` contienen información
local o artefactos generados y están excluidos del repositorio. No se publicaron credenciales.

## Uso y límites

Reiniciar la aplicación después de la migración para renovar conexiones, módulos y estado de
paquetes Oracle. Las altas estudiantiles nuevas solicitan código institucional; las docentes
requieren la autorización privada guardada en `.local/ALTA_DOCENTE.md`. La clave de cifrado
de respaldos está en `.local/clave_respaldos.bin`: debe conservarse protegida e independientemente.

Las acciones de archivo y retirada biométrica están en **Administrar cuenta e historial**.
El archivo conserva datos académicos; retirar biometría elimina los vectores activos y cierra
la sesión, impidiendo el acceso facial hasta un eventual reingreso administrativo autorizado.
Las copias anteriores no se reescriben: al recuperar hay que reaplicar las retiradas posteriores.

Tras la entrega posterior de frontend, permanecen pendientes los puntos 5 (portabilidad y mantenimiento general),
6 (ensayo integral y dispositivos reales) y 7 (SQL Developer/Data Modeler). La calibración real,
diarización, múltiples muestras, protección contra reproducción, separación de cuentas Oracle
y políticas institucionales de conservación no se acreditan con estos ensayos sintéticos.
No se probó otra plataforma, recuperación a gran escala ni pérdida completa del servidor.

Detalle: [reconocimiento](RECONOCIMIENTO.md), [reglas de negocio](REGLAS_NEGOCIO.md),
[recuperación](RECUPERACION.md) y [justificación de disparadores](DISPARADORES_Y_PLSQL.md).
