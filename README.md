# Control De Asistencia UPC

Aplicación web para tomar asistencia en clase con **reconocimiento facial** y **reconocimiento de voz**, con base de datos **Oracle XE** y **auditoría de cambios** para el profesor.

- **Estudiantes:** se registran con su rostro (y opcionalmente su voz), inician sesión con la cámara y se inscriben a materias con un código o un QR.
- **Profesores:** crean materias, comparten el código/QR y toman asistencia con fotos del salón o con una grabación de voz.
- **Auditor:** usuario Oracle de solo lectura que ve todos los datos y el historial de cambios (quién, cuándo, desde dónde, antes/después).

Tecnologías: Python · Streamlit · Oracle XE 18c/21c (`python-oracledb`) · dlib · scikit-learn · Resemblyzer · librosa.

---

## 1. Requisitos de cada PC

| Requisito | Detalle |
|---|---|
| **Windows 10/11** de 64 bits | También funciona en Linux/macOS (ver sección 7). |
| **Python 3.11 a 3.13** (recomendado **3.11**, el probado) | [python.org/downloads](https://www.python.org/downloads/). Marcar **"Add python.exe to PATH"**. Python 3.14 todavía **no** sirve (dlib/torch). |
| **Oracle Database XE 18c o 21c** | [oracle.com/database/technologies/xe-downloads.html](https://www.oracle.com/database/technologies/xe-downloads.html). Al instalar se define la contraseña de `SYSTEM`: **anótala**. |
| **SQL Developer** (o `sqlplus`, incluido con Oracle XE) | Para ejecutar el script de la base de datos. |
| **Internet** | Para instalar (~1 GB la primera vez) y al usar la app (logo, imágenes y fuentes se cargan de internet). |
| **Cámara web** (y micrófono para la voz) | El navegador pedirá permiso. |
| Git (opcional) | Solo para clonar; también se puede descargar el ZIP desde GitHub. |

> No se necesita Visual C++ ni Oracle Instant Client: `python-oracledb` funciona en modo *thin* (puro Python).

---

## 2. Descargar el proyecto

```powershell
git clone https://github.com/rcamilorodriguez1/ControlAsistenciaUPC.git
cd ControlAsistenciaUPC
```

O en GitHub: **Code → Download ZIP**, descomprimir y abrir la carpeta en una terminal.

---

## 3. Instalar dependencias (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1
```

El script busca un Python compatible, crea el entorno virtual `.venv`, instala las versiones exactas de `requirements.txt` y comprueba que todo importe. Al final debe decir **"Dependencias OK"**.

---

## 4. Crear la base de datos

El script principal es [`oracle_scripts_solo_sql.sql`](oracle_scripts_solo_sql.sql): **solo SQL, sin PL/SQL**.

> ⚠️ El script **borra y recrea** los usuarios `Asistencia_UPC` y `auditor`. Cierra la app antes de ejecutarlo.
> La primera vez, los `NOAUDIT`/`DROP` del inicio dan error porque no hay nada que borrar: es normal, el script continúa.

**Opción A – consola**
```powershell
sqlplus system@localhost:1521/XEPDB1 "@oracle_scripts_solo_sql.sql"
```
(pide la contraseña de `SYSTEM`; al terminar escribe `exit`).

**Opción B – SQL Developer**
1. Nueva conexión: usuario `SYSTEM`, la contraseña que pusiste al instalar Oracle, host `localhost`, puerto `1521`, **Nombre del servicio** `XEPDB1`.
2. Abrir `oracle_scripts_solo_sql.sql` y ejecutarlo como script con **F5** (*Run Script*, no *Run Statement*).

Al final se muestran **5 tablas**, **1 vista** y la política de auditoría activa.

| Usuario Oracle | Contraseña | Uso |
|---|---|---|
| `Asistencia_UPC` | `UPC123` *(contraseña estándar: cámbiala por la tuya)* | Lo usa la aplicación (dueño de las tablas) |
| `auditor` | `Auditor.123` *(contraseña estándar: cámbiala por la tuya)* | Profesor/auditor, **solo lectura** |

Comprobar la conexión:
```powershell
sqlplus Asistencia_UPC/UPC123@localhost:1521/XEPDB1
```

> Alternativa: [`oracle_scripts.sql`](oracle_scripts.sql) es una versión anterior con **PL/SQL** (triggers y tabla `auditoria` con datos antes/después) que usa el usuario `oscar`. Si la usas, pon `ORACLE_USUARIO = "oscar"` y su contraseña en `.streamlit/secrets.toml`.

---

## 5. Ejecutar la aplicación

```powershell
.\.venv\Scripts\streamlit.exe run principal.py
```

Se abre en el navegador en **http://localhost:8501**.

### Configuración opcional

Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` (este archivo **no** se sube a GitHub) y ajusta:

| Clave | Por defecto | Para qué |
|---|---|---|
| `ORACLE_USUARIO` | `Asistencia_UPC` | Usuario Oracle de la app |
| `ORACLE_CONTRASENA` | `UPC123` | Si la cambias, usa la misma en el `CREATE USER` del script SQL |
| `ORACLE_DSN` | `localhost:1521/XEPDB1` | Otro host/puerto/servicio de Oracle |
| `URL_APP` | `http://localhost:8501` | Dirección que va dentro del enlace y del QR de inscripción |

Tras cambiar `secrets.toml` hay que reiniciar la app (Ctrl+C y volver a ejecutar).

---

## 6. Auditoría (para el profesor)

Se usa la **auditoría unificada de Oracle** (política `pol_auditoria_asistencia`, creada solo con SQL). Cada `INSERT`, `UPDATE` y `DELETE` en las tablas de `Asistencia_UPC` queda en la vista del sistema `UNIFIED_AUDIT_TRAIL`, que **nadie puede modificar**. No aparece en el árbol de tablas de `Asistencia_UPC` porque pertenece a Oracle.

| Columna | Contenido |
|---|---|
| `event_timestamp` | Fecha y hora del cambio |
| `action_name`, `object_name` | Operación y tabla |
| `client_identifier` | Usuario de la app, p. ej. `profesor:jperez` o `estudiante:5:Ana Díaz` |
| `dbusername`, `os_username`, `userhost`, `client_program_name` | Desde dónde se hizo |
| `sql_text`, `sql_binds` | Sentencia ejecutada y sus valores |

No guarda los datos de "antes" de un `UPDATE`/`DELETE` (eso solo es posible con triggers PL/SQL, ver `oracle_scripts.sql`).

Conectado como `auditor` (`sqlplus auditor/Auditor.123@localhost:1521/XEPDB1`):

```sql
-- Historial de cambios (puede tardar unos segundos en aparecer)
SELECT event_timestamp, client_identifier AS usuario_app, dbusername, userhost AS equipo,
       action_name AS operacion, object_name AS tabla, sql_text, sql_binds
  FROM unified_audit_trail
 WHERE object_schema = 'ASISTENCIA_UPC'
 ORDER BY event_timestamp DESC;

-- Asistencia legible (nombres en vez de IDs)
SELECT * FROM Asistencia_UPC.vista_asistencia_detallada ORDER BY fecha_hora DESC;

-- Intentar modificar algo debe fallar con ORA-01031 (privilegios insuficientes)
DELETE FROM Asistencia_UPC.estudiantes;
```

---

## 7. Linux / macOS

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run principal.py
```

---

## 8. Usar el QR desde celulares

Con `URL_APP = http://localhost:8501` el QR **solo abre en el mismo PC**. Para celulares:

- Los navegadores **solo permiten cámara y micrófono en HTTPS** (o en `localhost`). Con `http://<IP>:8501` la página abre, pero el estudiante **no podrá iniciar sesión con su rostro**.
- Lo más práctico es un túnel HTTPS (p. ej. Cloudflare Tunnel o ngrok) y poner esa dirección `https://...` en `URL_APP`.
- Las redes de la universidad suelen aislar a los dispositivos entre sí, así que la IP local normalmente no funciona allí.

---

## 9. Problemas frecuentes

| Error | Causa / solución |
|---|---|
| `ORA-01017` usuario/contraseña no válidos | No se ejecutó el script SQL, se ejecutó en `XE` en vez de `XEPDB1`, o la contraseña de `secrets.toml` no coincide con la del script. |
| `ORA-01031` en `CREATE AUDIT POLICY` | Ejecuta el script como `SYS AS SYSDBA` en vez de `SYSTEM`. |
| `ORA-12514` / `DPY-6005` no se puede conectar | Oracle no está iniciado (servicios `OracleServiceXE` y `OracleOraDB…TNSListener`) o el servicio no se llama `XEPDB1`. |
| `ORA-01940` al ejecutar el script | La app sigue abierta y conectada como `Asistencia_UPC`: ciérrala y repite. |
| `No se encontro Python 3.11-3.13` | Instala Python 3.11 y marca "Add to PATH". |
| `Microsoft Visual C++ 14.0 is required` | Se instaló sin el script. Usa `instalar_windows.ps1`. |
| La cámara no se activa | Permite la cámara en el navegador; fuera de `localhost` se requiere HTTPS. |

---

## 10. Estructura

```
principal.py                  Punto de entrada de Streamlit
oracle_scripts.sql            Usuarios, tablas, auditoría, vista y permisos
instalar_windows.ps1          Instalador para Windows
requirements.txt              Dependencias con versiones fijas
src/
  base_datos/                 Conexión a Oracle y consultas
  canalizaciones/             Reconocimiento facial (dlib + SVM) y de voz (Resemblyzer)
  componentes/                Diálogos y elementos de la interfaz
  pantallas/                  Pantallas de inicio, estudiante y profesor
  interfaz/                   Estilos
```

---

## Créditos

Basado en **IntelliPresenceSync** de Mihir Gupta ([github.com/mihirgupta665/IntelliPresenceSync](https://github.com/mihirgupta665/IntelliPresenceSync)), publicado con licencia MIT. Esta versión fue adaptada a Oracle XE, traducida al español y ampliada con auditoría para la UPC.
