# Instalación por equipo y HTTPS local

## Requisitos y alcance

- Python **3.11 de 64 bits**, Git y conexión para instalar dependencias.
- Una base Oracle 18c o posterior compatible, local o remota. Para el servidor local actual: XE 18c y `XEPDB1`.
- SQL*Plus en PATH para instalar y presentar el esquema. La app usa python-oracledb thin y no necesita Instant Client.
- Cámara/micrófono y permisos del navegador para probar biometría.

La comprobación actual se hace en Windows x64. Los scripts Python usan rutas relativas al proyecto;
la instalación de dependencias nativas en Linux/macOS debe validarse por plataforma. `dlib-bin` puede
no ofrecer un binario para todos los sistemas o arquitecturas: no sustituirlo ni actualizar Python a ciegas.

No copiar `.venv`, `source`, `.certs` ni secretos a otro PC. Cada entorno y CA se generan en el destino.
No se borraron los entornos existentes del workspace.

## 1. Crear o verificar el entorno virtual

En CMD desde la raíz del proyecto:

```bat
preparar_entorno.cmd
```

Equivalente:

```bat
py -3.11 scripts\preparar_entorno.py
```

En Linux/macOS, cuando las dependencias sean compatibles:

```sh
python3.11 scripts/preparar_entorno.py
.venv/bin/python scripts/diagnostico.py --sin-bd
```

El script conserva un `.venv` válido y se detiene si pertenece a otra versión/sistema.
`requirements.txt` fija las dependencias directas; `requirements-lock-windows-py311.txt` es el
snapshot completo del entorno Windows auditado, no un lock universal multiplataforma.

VS Code recibe `${workspaceFolder}/.venv` como intérprete inicial. Si ya eligió otro intérprete
anteriormente, usar **Python: Select Interpreter** y seleccionar el de `.venv` una vez.

## 2. Preparar Oracle y los secretos

Consultar [SQLPLUS_Y_SQLDEVELOPER.md](SQLPLUS_Y_SQLDEVELOPER.md). En el servidor local con permisos SYSDBA:

```bat
.venv\Scripts\python.exe scripts\preparar_oracle.py --os-auth --pdb XEPDB1
```

Con administrador y contraseña solicitada de forma oculta:

```bat
.venv\Scripts\python.exe scripts\preparar_oracle.py --admin SYSTEM --dsn localhost:1521/XEPDB1
```

Se crea un usuario nuevo, una contraseña aleatoria propia del equipo y `.streamlit/secrets.toml`.
Si hay usuario/configuración existente, el comando se detiene para no reemplazarlos.
Para una base remota ya preparada se puede copiar `secrets.toml.example` como `secrets.toml`
y completar sus valores en privado; no hace falta crear un usuario Oracle en cada PC cliente.

Prioridad de configuración: **variables del proceso > secrets de Streamlit > valores predeterminados**.
`ORACLE_CONTRASENA` no tiene valor predeterminado. No compartir el archivo de secretos ni poner la
contraseña en comandos, capturas o documentación pública.

Si el equipo ya tiene la base 001, actualizarla mediante `scripts/oracle.py migrar`, después de
que el administrador conceda CREATE TRIGGER. La aplicación actual requiere 008: auditoría con
contexto por sesión, clases, revisión manual, estados de detección, gestión y tercer rol administrativo.
`migrar` respalda el esquema, aplica las versiones pendientes y puede reejecutar 008.
La versión 007 incorpora sesiones únicas y revocación para todos los roles; ver
[PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md). Las sesiones previas requieren autenticarse una vez.
Detener la aplicación durante la migración y reiniciarla después.
No ejecutar otra vez `preparar_oracle.py` ni recrear el usuario existente.
La versión 008 añade excepciones biométricas y prepara una clave HMAC privada local.
Si se instala directamente con SQL*Plus, ejecutar después `scripts/preparar_identidad.py`.
En otro PC, conservar/restaurar la clave original `.local/claves/identidad.key` junto con los datos;
no está dentro del respaldo Oracle. Ver [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).
Ver [justificación e instrucciones de disparadores y PL/SQL](DISPARADORES_Y_PLSQL.md).
El registro docente requiere la autorización privada de `.local/ALTA_DOCENTE.md`; las altas
estudiantiles nuevas requieren código institucional. Ver [reglas de negocio](REGLAS_NEGOCIO.md)
y [respaldo y recuperación](RECUPERACION.md), incluida la clave privada de las copias V2.
El acceso administrativo requiere además `scripts/preparar_administracion.py`; crea una conexión
Oracle limitada y una cuenta inicial privada. Ver [ADMINISTRACION.md](ADMINISTRACION.md).

## 3. Arrancar con HTTPS real

```bat
iniciar.cmd
```

O directamente, también desde otros sistemas usando su Python de `.venv`:

```bat
.venv\Scripts\python.exe scripts\iniciar.py
```

El comando emite una CA y un certificado de servidor locales cuando hacen falta, y configura
TLS en Streamlit. Aplicación y QR apuntan a **https://localhost:8501**.
La sintaxis correcta es `https://`, con dos puntos; `https;//` no es una URL válida.
Cambiar solamente el texto del QR a HTTPS no configura cifrado: debe arrancarse con este comando.
La ejecución directa `streamlit run principal.py` no activa por sí sola los certificados.

La CA está en `.certs/ca.pem`; las claves privadas son `.certs/ca-key.pem` y `.certs/servidor-key.pem`.
El script **no instala certificados en el sistema ni modifica la confianza del navegador**.
Para quitar el aviso del navegador hay que confiar explícitamente en la CA de este equipo:

1. Abrir el administrador de certificados de usuario de Windows (`certmgr.msc`).
2. Importar **solo `.certs/ca.pem`** en las autoridades raíz de confianza del usuario.
3. Cerrar y abrir el navegador. Firefox puede requerir configurar su propio almacén de certificados.

Solo confiar en la CA que se acaba de generar para este proyecto. No importar claves privadas.
Si se comparte la CA pública con dispositivos de prueba, retirar esa confianza al terminar.
Los permisos de archivos de Windows no sustituyen las ACL del perfil: mantener las claves en el PC propio.

## 4. QR desde un teléfono u otro PC de la red

`localhost` siempre identifica el dispositivo que abre el enlace. Un QR con localhost **no lleva
al servidor desde el teléfono**. Obtener la IP LAN del PC y ejecutar, por ejemplo:

```bat
iniciar.cmd --escuchar 0.0.0.0 --url https://192.168.1.20:8501
```

Sustituir la IP de ejemplo por la del PC. El comando incluye esa IP en el certificado y aplica
la misma URL al QR. Ambos dispositivos deben estar en la misma red; el firewall debe permitir
el puerto 8501 en la red de prueba. Confiar en la CA pública del servidor en cada cliente para
que cámara y micrófono funcionen con un origen HTTPS confiable. No se modificó automáticamente el firewall.

Si la IP cambia, volver a arrancar con la nueva URL y generar nuevamente los QR. También puede
usarse un nombre de host resoluble en la red. Para HTTP explícito de desarrollo:

```bat
iniciar.cmd --http
```

## 5. Diagnóstico y parada

```bat
.venv\Scripts\python.exe scripts\diagnostico.py
.venv\Scripts\python.exe scripts\oracle.py verificar
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Con el servidor HTTPS iniciado:

```bat
.venv\Scripts\python.exe scripts\diagnostico.py --url https://localhost:8501
```

Parar la aplicación con **Ctrl+C** en la terminal que la inició. El comando de diagnóstico no
muestra contraseñas ni perfiles; comprueba importaciones, dependencias, esquema y función PL/SQL.
La confianza TLS de ese diagnóstico usa la CA local; no demuestra que el navegador ya confíe en ella.

Streamlit recomienda un proxy para TLS en producción. Este arranque es para desarrollo local y
demostraciones: [referencia oficial](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
