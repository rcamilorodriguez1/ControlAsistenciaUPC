# Despliegue de UPC Aula con Docker y Oracle Cloud

## Alternativa preparada: Render y Oracle Autonomous

El 22/11 se prepara Render como alojamiento alternativo a la VM de OCI. Autonomous
conserva la base de datos y sus cuentas técnicas. La importación de variables y el soporte
de la clave en texto no equivalen a un despliegue publicado ni a una construcción Linux
verificada. La configuración local conserva su destino y su clave binaria.

Primer intento en Render con `b775e9a`: la imagen se construyó y exportó correctamente.
El arranque se detuvo primero por APP_BASE_URL ausente y luego por la clave Base64,
que esa versión anterior solo podía leer como bytes binarios. La URL asignada es
`https://controlasistenciaupc.onrender.com`. Este resultado todavía no valida el
arranque de la versión actual, los permisos cloud ni los recorridos de los portales.

Crear un **Web Service**, región **Virginia**, repositorio del proyecto, rama `main`,
runtime **Docker**, Root Directory vacío y Dockerfile `./Dockerfile`. Mantener el comando
de arranque de la imagen; Render termina HTTPS, sin ejecutar el Compose de Caddy.

- Importar las variables privadas con **Add from .env**. El archivo preparado en este PC
  está en `.local/render/.env`, excluido de Git y del contexto Docker; contiene el perfil
  de ejecución cloud y la autorización docente, sin la contraseña de ADMIN ni del propietario.
- Definir `PORT=8501` y Health Check Path `/_stcore/health`. Registry Credential queda
  en **No credential** para construir el Dockerfile actual.
- En **Secret Files**, crear `identidad.key.b64` y pegar el contenido de
  `.local/render/identidad.key.b64`. Es Base64 de la clave original de 32 bytes,
  no una clave nueva ni un cifrado. Tratarlo como el mismo secreto.
- Añadir `IDENTIDAD_CLAVE_RUTA=/etc/secrets/identidad.key.b64` e
  `IDENTIDAD_CLAVE_FORMATO=base64`. El arranque y la verificación estudiantil decodifican
  el archivo directamente en memoria, conservando las huellas HMAC. Sin la opción de
  formato se sigue leyendo la clave binaria habitual. No se regeneran claves de texto ausentes.
- Completar `APP_BASE_URL` con la URL HTTPS real asignada al servicio. Autorizar en
  Autonomous los rangos de salida mostrados en **Connect > Outbound** para ese servicio.
- Publicar en GitHub los cambios de código que el servicio deba construir. Un commit
  únicamente local no está disponible para Render. Las credenciales permanecen privadas.

Pendientes: confirmar plan y memoria para los motores biométricos, construir y arrancar
la imagen, verificar Oracle desde Render, revisar archivos que necesiten persistencia y
ensayar los portales, HTTPS, cámara y micrófono. No se considera validado el servicio Free
para la aplicación completa. El endpoint de salud comprueba Streamlit; Oracle se valida
durante el arranque y no se consulta en cada petición de salud.

Referencias: [Docker en Render](https://render.com/docs/docker),
[variables y archivos secretos](https://render.com/docs/configure-environment-variables),
[salud](https://render.com/docs/health-checks) e
[IP de salida](https://render.com/docs/outbound-ip-addresses).

## Plan de VM OCI registrado

Estado del 22 de noviembre de 2026: Autonomous UPCAULA ya tiene usuarios y esquema
001–008 instalados, con TLS y permisos administrativos verificados. El usuario confirma
que todavía no tiene una VM Compute. La aplicación se ejecutará con Docker en esa VM.

La cuenta de ejecución UPC_AULA_APP ya está creada y verificada, separada del propietario
UPC_ASISTENCIA y de la cuenta administrativa UPC_ADMIN_APP: 53 permisos comprobados,
55 sentencias analizadas y cero objetos propios. El perfil privado está preparado; la
aplicación local conserva su conexión anterior.

Actualización de infraestructura: la VCN `upc-aula-vcn` y la subred regional pública
`upc-aula-publica` están creadas. Los intentos de crear A1.Flex con 2 OCPU y 12 GB
devolvieron falta de capacidad en AD-1, AD-2 y AD-3 de Ashburn. No hay VM creada ni IP
asignada confirmada. La puerta `upc-aula-igw` aparece Available, la ruta hacia ella está
confirmada por el usuario y las capturas muestran SSH restringido y HTTP/HTTPS públicos.
La conectividad efectiva sigue pendiente de ensayo con la VM.
El [orden de continuación sin VM](ROADMAP.md#continuación-mientras-no-haya-capacidad-compute)
permite avanzar en red, permisos, configuración y validación Linux mientras se reintenta.

La organización inicial de consultas está completa y la aplicación conserva su
conexión local mientras se prepara el servidor. La imagen y Compose están preparados;
falta construirlos y probarlos en Linux real. No se ha publicado la aplicación.

El [primer roadmap](ROADMAP.md) cubre estos entregables. Las mejoras posteriores de
frontend y diseño de la base están registradas en el [segundo roadmap](ROADMAP_2.md).

## Arquitectura preparada

```text
Navegador con cámara y micrófono
    │ HTTPS / WebSocket, dominio público, puerto 443
    ▼
Caddy en la máquina Linux
    │ HTTP privado, puerto 8501
    ▼
UPC Aula: Streamlit y servicios Python en un contenedor
    │ TCPS: TLS o mTLS, cuentas del proyecto
    ▼
Oracle Autonomous Database
```

Streamlit ejecuta la interfaz y el backend existentes. No hace falta agregar otro backend
ni convertir el proyecto a una API. GitHub conserva el código y puede construir la imagen
mediante Actions; GitHub Pages sirve contenido estático y no ejecuta este programa.

El contenedor está preparado para Linux x86-64 y ARM64, con Python 3.11 y PyTorch CPU.
Las dependencias directas conservan las versiones de `requirements.txt`; el modelo facial
conserva su revisión Git. Las dependencias transitivas y las imágenes base se resuelven al
construir: para una entrega definitiva, conservar la imagen por su digest y el `pip freeze`
de esa construcción. El lock de Windows no debe instalarse dentro de Linux.

Una VM Linux en OCI permite alojar el contenedor cerca de Oracle Cloud. Antes de crearla,
comprobar en la consola la capacidad disponible y que VM, disco, IP y base estén dentro
de la asignación gratuita de la cuenta. La disponibilidad y las condiciones de Always Free
pueden cambiar; no se promete alojamiento permanente sin costo. Una instancia con 1 GB
de memoria deja poco margen para los motores biométricos. Medir memoria y concurrencia
durante el ensayo antes de elegir el tamaño final.

## Archivos de despliegue

| Archivo | Función |
| --- | --- |
| `Dockerfile` | Construcción en dos etapas; ejecución como UID/GID 10001, sin compiladores en la imagen final. |
| `.dockerignore` | Incluye código y recursos necesarios; excluye venv, credenciales, certificados locales, documentación y datos privados. |
| `deploy/compose.yaml` | Aplicación y Caddy; solo el proxy publica 80/443. Estado persistente y configuración privada montada. |
| `deploy/compose.mtls.yaml` | Montaje adicional del wallet, exclusivamente para mTLS. |
| `deploy/Caddyfile` | Certificado público automático y proxy de HTTP/WebSocket. |
| `deploy/.env.example` | Dominio, correo del responsable del certificado y etiqueta de imagen. |
| `deploy/secrets.produccion.toml.example` | Plantilla sin credenciales reales para Oracle y autorizaciones privadas. |
| `scripts/iniciar_produccion.py` | Valida configuración, Oracle y permisos antes de iniciar. No instala ni migra la base. |
| `scripts/comprobar_modelos.py` | Carga modelos facial y de voz en CPU sin personas, cámara ni Oracle. |
| `sql/cloud/00_crear_usuarios.sql` | Crea las dos cuentas técnicas en una Autonomous nueva, conectado como ADMIN. |
| `sql/cloud/01_permisos_administracion.sql` | Concede los permisos administrativos limitados desde el propietario. |
| `scripts/crear_administrador.py` | Crea explícitamente la primera cuenta administrativa web, con contraseña solicitada sin eco. |
| `scripts/preparar_ejecucion_cloud.py` | Crea el runtime separado mediante ADMIN interactivo; conserva el propietario y verifica el contrato de permisos. |
| `sql/cloud/06_crear_usuario_ejecucion.sql`, `07_permisos_ejecucion.sql`, `08_verificar_ejecucion.sql` | Creación parametrizada, grants mínimos y verificador del runtime. |
| `.github/workflows/contenedor.yml` | Comprobación manual en Linux x64 y ARM64; no publica ni despliega. |

## 1 Preparar infraestructura

Se necesita una VM Linux con Docker Engine y el plugin Compose, acceso SSH, un dominio o
subdominio cuyo DNS apunte a su IP pública y una Autonomous Database disponible. Caddy
necesita recibir conexiones por 80 y 443 para emitir y renovar el certificado. Limitar SSH a
los orígenes administrativos; no publicar 8501 ni un puerto Oracle de la VM.

### Crear la primera VM del proyecto

En la consola OCI, abrir **Compute → Instances → Create instance**, manteniendo la región
**US East (Ashburn)**. El usuario confirmó que aún no tiene una instancia Compute.

| Campo | Configuración inicial propuesta |
| --- | --- |
| Name | `upc-aula-app` |
| Image | Ubuntu 24.04 LTS compatible con la arquitectura seleccionada |
| Shape | `VM.Standard.A1.Flex`, si hay capacidad gratuita disponible |
| Recursos | 2 OCPU y 12 GB de memoria, dentro de la asignación publicada de A1 Always Free |
| Boot volume | 50 GB, revisando que el total de volúmenes de la cuenta siga dentro de su cuota |
| Networking | VCN con salida a Internet, subred pública y una IPv4 pública para la VM |
| SSH | Generar un par o cargar una clave pública propia; conservar la privada fuera del repositorio |

Antes de crear, comprobar en la consola que los recursos sean elegibles para Always Free
y que no se agreguen servicios de pago. La capacidad A1 no está garantizada; si aparece
`Out of host capacity`, revisar otro dominio de disponibilidad de Ashburn o reintentar después.
La VM de 1 GB no es la opción preparada para probar los motores biométricos de esta aplicación.

Permitir TCP 22 desde la IP administrativa y TCP 80/443 para la página pública mediante
las reglas de red de OCI. No publicar 8501: Compose lo mantiene entre la aplicación y Caddy.
Añadir la IP de salida de la VM a la lista de acceso de Autonomous, conservando la del PC.

### Red preparada durante los intentos de creación

La subred pública regional usa `10.0.0.0/24` dentro de la VCN `10.0.0.0/16`.
Se creó `upc-aula-igw` sin asociación opcional de tabla de rutas en la propia puerta.
El usuario confirmó añadir `0.0.0.0/0 → Internet Gateway → upc-aula-igw` en la tabla
utilizada por la subred. No confundir esa ruta con el enrutamiento avanzado de entrada
de la puerta de enlace.

La lista de seguridad asociada muestra estas reglas de entrada con estado
(`Stateless: No`), todas con puerto de origen All cuando corresponde:

| Uso | Origen | Protocolo / destino |
| --- | --- | --- |
| SSH administrativo | IP pública administrativa actual `/32` | TCP / 22 |
| HTTP y certificados | `0.0.0.0/0` | TCP / 80 |
| HTTPS | `0.0.0.0/0` | TCP / 443 |
| Fragmentación / MTU | `0.0.0.0/0` | ICMP tipo 3, código 4 |
| Errores internos de red | `10.0.0.0/16` | ICMP tipo 3 |

La salida conserva la regla con estado hacia `0.0.0.0/0` para todos los protocolos.
Si cambia la IP administrativa, actualizar el origen SSH. La IP real no se registra aquí.
Esta revisión de consola no sustituye comprobar la habilitación del gateway, asociación
de la tabla, IP pública, firewall del sistema y conectividad desde una VM existente.

Con la VM disponible, conectar por SSH como `ubuntu`, instalar Docker Engine y el plugin
Compose según la [guía oficial de Ubuntu](https://docs.docker.com/engine/install/ubuntu/),
y verificar `sudo docker version` y `sudo docker compose version`. Los siguientes apartados
se ejecutan dentro de esa VM, no en el PowerShell del PC.

Referencias: [crear una instancia OCI](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm)
y [recursos Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

En Oracle Cloud, limitar el acceso a la base a la IP de salida de la VM o a la red privada
correspondiente. Permitir desde la VM el puerto TCPS indicado en la conexión Oracle, DNS
y HTTPS saliente. No usar una regla de acceso universal a la base como sustituto de la ACL.

Los navegadores accederán por el dominio HTTPS. No deben importar `.certs/ca.pem`: esa CA
pertenece únicamente al desarrollo local. Cámara y micrófono se autorizan en cada navegador.

## 2 Preparar una base nueva

Estos pasos se ejecutan **en una Autonomous nueva de ensayo**, antes de importar datos.
No ejecutar el instalador inicial encima del esquema local existente.

**En la UPCAULA actual la instalación 001–008 ya está completada.** No repetir la creación de
usuarios ni el instalador inicial. Desde el PC puede comprobarse con
`scripts/preparar_oracle_cloud.py --verificar`. El comando `--continuar` solo se utiliza
para recuperar una instalación parcial revisada, como se explica en [INSTALACION.md](INSTALACION.md).

1. Conectar como `ADMIN` desde SQLcl o SQL*Plus y ejecutar
   `@sql/cloud/00_crear_usuarios.sql`. Requiere ejecutar desde la raíz del repositorio.
   Solicita las contraseñas con `PASSWORD`, sin almacenarlas en el SQL. Crea
   `UPC_ASISTENCIA` con cuota de 100 MB en `DATA` y los privilegios de creación requeridos,
   y `UPC_ADMIN_APP` con `CREATE SESSION`. La cuota debe revisarse según el volumen real.
2. Conectar como `UPC_ASISTENCIA` y ejecutar `@oracle_scripts.sql`. Instala las versiones
   001–008, incluidas tablas, relaciones, vistas, paquetes y disparadores existentes.
3. En esa misma conexión ejecutar `@sql/cloud/01_permisos_administracion.sql`.
   Concede EXECUTE en cuatro paquetes y SELECT en tres vistas a `UPC_ADMIN_APP`, sin
   edición directa de tablas. En la nube son permisos directos equivalentes al rol local.
4. Revisar los resultados de los verificadores incluidos en la instalación. No debe haber
   objetos inválidos ni errores ORA/PLS. Conservar el resultado del ensayo en un lugar privado.

SQL Developer puede conectarse a la misma Autonomous. Para ejecutar el árbol de scripts,
usar su modo de ejecución de scripts y el directorio de trabajo de la raíz; SQLcl/SQL*Plus
evita ambigüedades con las rutas de los `@sql/...`. No usar en Autonomous el preparador
local `scripts/preparar_oracle.py` ni `scripts/preparar_administracion.py`: requieren el
entorno XE/SYSDBA. Los nuevos scripts no borran ni reemplazan usuarios existentes.

`exports/modelo_008.sql` sirve para visualizar la estructura, no para instalar la aplicación:
no sustituye los paquetes ni las migraciones. Ver [base de datos](BASE_DE_DATOS.md).

La cuenta `UPC_AULA_APP` está completada en la UPCAULA actual. No repetir su creación.
Puede revisarse con `scripts/preparar_ejecucion_cloud.py --verificar`. En otra instalación
nueva el preparador pide ADMIN sin guardarlo y conserva el propietario para mantenimiento.
Instrucciones y recuperación: [cuenta de ejecución](CUENTA_EJECUCION.md).

## 3 Configurar el servidor Linux

Los siguientes comandos son **Bash en la VM**, desde la raíz del repositorio. No ejecutarlos
en PowerShell. El repositorio contiene únicamente código compartible; los valores privados
se preparan directamente en el servidor o se transfieren por un canal privado.

```bash
cp deploy/.env.example deploy/.env
# Editar APP_HOST y ACME_EMAIL antes de continuar.
nano deploy/.env

sudo install -d -m 0700 deploy/private
sudo install -d -o 10001 -g 10001 -m 0700 deploy/private/state
sudo install -o 10001 -g 10001 -m 0600 \
  deploy/secrets.produccion.toml.example deploy/private/secrets.toml
sudoedit deploy/private/secrets.toml

DC=(sudo docker compose --env-file deploy/.env -f deploy/compose.yaml)
```

Completar el archivo privado con las dos contraseñas Oracle de **ejecución** y administración
limitada, usando `.local/oracle_cloud/credenciales_ejecucion.toml` como fuente privada.
Configurar `ORACLE_USUARIO=UPC_AULA_APP` y `ORACLE_ESQUEMA=UPC_ASISTENCIA`; no colocar
la contraseña propietaria en la configuración normal del servidor. Añadir la autorización de alta docente
y la cadena de conexión real. La contraseña administrativa web se crea en el paso siguiente:
es diferente de la contraseña técnica `ORACLE_ADMIN_CONTRASENA`.

Compose deriva `APP_BASE_URL` de `APP_HOST`; así el proxy, los enlaces QR y la comprobación
de origen utilizan el mismo dominio. Las variables del proceso tienen prioridad sobre
`KEY_FILE` y sobre `secrets.toml`. `KEY_FILE` permite indicar un archivo de texto con un
secreto, por ejemplo `ORACLE_CONTRASENA_FILE=/run/secrets/oracle_password`; elimina solo
los saltos de línea finales. El archivo binario HMAC se configura por su ruta, no con `_FILE`.

### Conexión TLS sin wallet

Usar `ORACLE_TLS_MODO="tls"` y copiar de **Database Connection** la cadena TLS del servicio
`*_low`, con protocolo `tcps`. Configurar en Autonomous el acceso TLS y la ACL de la VM.
No copiar `localhost:1521/XEPDB1`. Se mantiene la comprobación del nombre del servidor;
un DSN con TCP o con esa comprobación deshabilitada se rechaza.

### Alternativa mTLS con wallet

Descomprimir por un canal privado el wallet de Autonomous en `deploy/private/wallet`;
debe contener `tnsnames.ora` y `ewallet.pem`. Dar acceso de lectura al UID 10001 sin hacerlo
público. Por ejemplo, después de transferirlo:

```bash
sudo chown -R 10001:10001 deploy/private/wallet
sudo find deploy/private/wallet -type d -exec chmod 0700 {} +
sudo find deploy/private/wallet -type f -exec chmod 0600 {} +
DC+=(-f deploy/compose.mtls.yaml)
```

En el archivo privado establecer `ORACLE_TLS_MODO="mtls"`, el alias `*_low` de
`tnsnames.ora` como `ORACLE_DSN`, `ORACLE_WALLET_DIRECTORIO="/run/oracle-wallet"`
y `ORACLE_WALLET_CONTRASENA`. Esta última es la contraseña del wallet, distinta de las
contraseñas de los usuarios Oracle. Ambos pools usan el mismo transporte TLS/mTLS.

## 4 Construir y preparar las claves

```bash
"${DC[@]}" config --quiet
"${DC[@]}" build app
"${DC[@]}" run --rm --no-deps --entrypoint python app scripts/comprobar_modelos.py
```

Para una **base nueva sin documentos registrados**, generar su primera clave de identidad:

```bash
"${DC[@]}" run --rm --no-deps --entrypoint python app scripts/preparar_identidad.py
```

La primera cuenta web administrativa se prepara explícitamente desde el PC con el perfil
propietario y `crear_administrador.py --config-oracle`, según la [guía](CUENTA_EJECUCION.md#alta-administrativa-y-operación).
La cuenta runtime no tiene INSERT en administradores. El preparador pide una contraseña
fuerte sin eco, registra el alta y rechaza sustituir una cuenta existente; no se ejecuta
automáticamente durante el arranque de la aplicación.

Para **trasladar una base existente**, antes de iniciar transferir su clave ORIGINAL
`.local/claves/identidad.key` a `deploy/private/state/claves/identidad.key`, con propietario
10001:10001 y modo 0600. Conservar también la clave original de los respaldos cifrados,
si se trasladan esos respaldos. Son claves diferentes. No regenerar la clave HMAC: los
documentos se identifican con ella y Oracle no permite reconstruirla a partir de sus huellas.

El traslado de datos requiere un ensayo de restauración/exportación compatible con
Autonomous y comprobación de recuentos y relaciones. Ver [recuperación](RECUPERACION.md).
No se ha ejecutado una migración XE → Autonomous en esta entrega. Conservar el entorno
local y su copia hasta aceptar el resultado; no apuntar dos instalaciones independientes
a copias divergentes de los mismos datos institucionales.

## 5 Comprobar y arrancar

```bash
"${DC[@]}" run --rm --no-deps app --comprobar --sin-bd
"${DC[@]}" run --rm --no-deps app --comprobar
"${DC[@]}" up -d --no-build
"${DC[@]}" ps
"${DC[@]}" logs --tail=100 app proxy
```

La primera comprobación revisa el dominio, credenciales presentes, TCPS, tamaños de pools y
la existencia de la clave de 32 bytes. La segunda añade consultas de solo lectura a Oracle:
versiones 001–008, objetos inválidos, disparadores deshabilitados y permisos administrativos.
El arranque real siempre comprueba Oracle; `--sin-bd` solo se admite con `--comprobar`.

La aplicación escucha dentro de Docker en 0.0.0.0:8501, conserva el tema y desactiva el
observador de archivos. CORS y XSRF permanecen habilitados. El certificado público termina
en Caddy; el tramo HTTP entre contenedores no se expone en la VM. El healthcheck HTTP
comprueba que Streamlit responde, **no** la disponibilidad continua de Oracle. Una caída
posterior de la base necesita seguimiento operativo además de ese healthcheck.

Los máximos propuestos son cuatro conexiones del pool principal y dos del administrativo,
por proceso. Reservar margen para SQL Developer, tareas y respaldos; no escalar a varias
réplicas sin revisar el límite global de Oracle y la afinidad de WebSocket/sesiones Streamlit.
Esta configuración prepara una sola instancia de la aplicación.

## 6 Ensayo antes de aceptar la publicación

- Certificado válido en el dominio, redirección HTTP → HTTPS y WebSocket estable.
- Portada, iconos y estilos en Chrome, Firefox, Edge y móvil; permisos reales de cámara
  y micrófono sobre HTTPS. Las verificaciones locales no sustituyen esta prueba de red.
- Acceso/cierre por los tres roles, sesión única, caducidad, recuperación docente e Inicio.
- QR abierto desde otro dispositivo: debe contener el dominio público.
- Matrícula, clase, revisión y consultas administrativas; verificar auditoría en Oracle.
- Documento y acceso excepcional conservados al migrar, sin cambiar la clave HMAC.
- Reinicio del contenedor y de la VM: claves y datos deben mantenerse.
- Respaldo cifrado, copia externa privada de claves y restauración en un destino de ensayo.
- Memoria, tiempos de reconocimiento y concurrencia con el tamaño real de la VM.

La separación de propietario y ejecución está implementada, ensayada con una cuenta
temporal en XE y verificada en la cuenta definitiva cloud. El pool administrativo ya
usa su cuenta limitada. Falta incorporar el perfil de ejecución al servidor y completar
el ensayo productivo; la cuenta técnica preparada no equivale a publicar la aplicación.

## Operación y actualización

`deploy/private/state` persiste fuera de la imagen: contiene la clave de identidad y puede
contener claves/copias cifradas creadas por las herramientas existentes. Las tablas y la
auditoría persisten en Oracle. Los volúmenes `caddy_data` y `caddy_config` conservan los
certificados del proxy. Incluir lo necesario en la política de recuperación; no eliminar
volúmenes con `down -v` como procedimiento normal de actualización.

Antes de una actualización, realizar y comprobar un respaldo. Construir una imagen con
una etiqueta propia `AULA_VERSION`, ejecutar las comprobaciones y recrear `app`.
No se ejecutan migraciones SQL automáticamente al arrancar. Si una entrega requiere una
migración, aplicarla explícitamente con mantenimiento y revisar la compatibilidad antes de
volver a una imagen anterior. Volver a una imagen no revierte un esquema ni sus datos.

En GitHub, el flujo **Comprobar contenedor Linux** se inicia manualmente desde Actions
después de subir estos archivos. Construye en x64/ARM64, carga modelos en CPU, ejecuta
pruebas sin Oracle, prueba el servidor HTTP y guarda las versiones instaladas. No solicita
secretos de producción ni publica imágenes. Revisar la cuota de Actions de la cuenta antes
de ejecutarlo. Un resultado correcto del flujo valida la imagen en sus runners; el ensayo
con el endpoint Oracle y el dominio sigue siendo necesario.

## Verificación de esta preparación

Tras la organización de consultas se aprobaron 182 pruebas en Windows; 64 pruebas de
integración Oracle quedaron omitidas. Se analizaron 65 consultas de lectura del catálogo
en Oracle Cloud mediante `Cursor.parse`, sin ejecutarlas ni modificar datos. La suite
pasó sin cargar las credenciales locales. Se comprobaron los
modelos facial/voz en CPU, las dependencias instaladas, la sintaxis Python/TOML, las dos
configuraciones Compose y el preflight sin conexión. Un servidor HTTP en un puerto de
prueba respondió 200 en `/` y `/_stcore/health` con los argumentos de producción.

La CLI de Compose utilizada para validar los archivos es la oficial 5.8.0, descargada en
`.local/hosting` y contrastada con la huella publicada. Docker Engine no está instalado;
la construcción Linux y el recorrido HTTPS de destino continúan pendientes. Los SQL
de Autonomous ya están instalados y verificados. Las evidencias de preparación están en
`.local/hosting/` y las de organización en `.local/reorganizacion/`, excluidas de Git.

## Fuentes técnicas

- [Streamlit en Docker](https://docs.streamlit.io/deploy/tutorials/docker): servidor y healthcheck.
- [Conexiones de python-oracledb](https://python-oracledb.readthedocs.io/en/stable/user_guide/connection_handling.html#connecting-to-oracle-cloud-autonomous-databases): thin, TLS y wallet mTLS.
- [Usuarios en Autonomous](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/manage-users-create.html): administración mediante ADMIN y cuotas.
- [PyTorch CPU](https://docs.pytorch.org/get-started/locally/): selección del paquete de cómputo.
- [Recursos Always Free de OCI](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm): condiciones y disponibilidad del alojamiento.
