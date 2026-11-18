# Navegación pública y sesiones globales — base 007 y ampliación 008

Ampliación del 17 de noviembre de 2026: el estudiante dispone de una alternativa autorizada
cuando no puede completar la biometría. El broker confirma método/estado y apertura de sesión
en una transacción; revocación y vencimiento se validan en servidor. Los otros roles conservan
sus métodos y restricciones. Guía vigente: [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).
El inventario y resultados 007 que aparecen más abajo documentan la entrega histórica.

Los cambios de autenticación, navegación y revocación se aplican a **profesores, estudiantes
y administradores**. Se conservan los métodos actuales de contraseña/rostro y las reglas
académicas de materias, matrícula, revisión y asistencia.

## Interfaz

Los selectores de materia y clase usan altura de 44 px, texto Arial de 16 px y ancho máximo
de 720 px, con padding, bordes y foco accesible comunes. Las reglas están limitadas a
`selector_academico_*`, incluido el componente React Aria de la versión instalada de Streamlit.
El selector vacío muestra **Selecciona una clase**, sin traducir identificadores o estados
persistidos. Los textos nativos no configurables siguen dependiendo del framework; no se
parchearon sus archivos instalados.

**Crear nueva materia** tiene fondo verde institucional, texto blanco y estados hover, focus,
active y disabled. Los botones secundarios conservan su jerarquía.

## Inicio y cierre de sesión

Revisión del 12 de noviembre de 2026, que sustituye el comportamiento anterior de Inicio.
El logosímbolo original y la acción de casa **Inicio** son enlaces nativos a `/`.
Inicio aparece una sola vez en los portales y se omite en la portada pública. El logotipo
conserva su descripción accesible, sin añadir otro texto visible de Inicio.
La portada mantiene el mismo contenido para visitantes y usuarios autenticados, sin redirección
automática. `/inicio` es un alias que también renderiza la portada directamente.

El router registra `/docente`, `/estudiante` y `/administracion`. Cada ruta muestra el acceso
del portal o su panel, únicamente si la sesión validada tiene el rol correspondiente. Elegir
una URL no establece un rol ni crea un token. Regresar al portal propio reutiliza su sesión.
La identidad (`rol_usuario`, perfil y token) es independiente de la vista (`tipo_sesion`).
Inicio conserva identidad, contexto académico, materia, clase, capturas y propuestas.

**Causa del rebote anterior:** `/inicio` ejecutaba `ir_al_inicio()` y `st.switch_page()` al
portal, mientras la inicialización imponía el rol autenticado como vista. Se eliminaron esa
redirección intermedia y la asociación entre vista e identidad. La portada ahora se renderiza
como una página real, sin rebote al panel ni un contenedor vacío creado por esa redirección.

Los enlaces QR mantienen `join-code`: desde la portada se ofrece continuar explícitamente
al portal estudiantil; la inscripción se ejecuta únicamente dentro de ese portal autenticado.
Un profesor o administrador conserva su identidad al abrir una invitación de estudiante.

## Conflicto entre portales y menú de cuenta

El login de otro portal sigue visible. El envío queda deshabilitado (incluida la cámara
estudiantil) y, debajo del formulario, aparece **Ya tienes una sesión activa** con el portal
real. No se abren modales ni se cierra la sesión al navegar.

- **Volver a mi portal** valida la sesión y navega al portal de su rol, conservando el token.
- **Cerrar sesión actual** revoca el token real en Oracle, elimina el estado autenticado y
  mantiene la ruta solicitada. El aviso desaparece y el acceso vuelve a estar habilitado.

`src/servicios/autenticacion.py` impide autenticar o registrar otra cuenta y abrir otro token
cuando la sesión web identificada ya tiene un actor válido. Lo aplican los servicios de acceso
docente, administrativo, registro estudiantil, recuperación y apertura de sesión. La utilidad
central también rechaza sustituir una identidad por otra, aunque se invoque sin el formulario.
Los permisos académicos y validaciones transaccionales de Oracle se mantienen.

El menú nativo de cuenta tiene exactamente **Mi perfil**, **Configuración** y **Cerrar sesión**.
Desde el 17 de noviembre, **Mi perfil** está habilitado para estudiantes y abre la ruta privada
`/mi-perfil`; los demás roles conservan la opción deshabilitada. Configuración continúa como
«Próximamente». No se añadieron tablas ni edición de identidad. Casa y logotipo permanecen fuera
del menú. Consulta, métricas y permisos: [PERFIL_ESTUDIANTE.md](PERFIL_ESTUDIANTE.md).
El complemento local `static/js/cuenta.js` mueve el foco a la primera opción habilitada al
abrirse el popover: el componente nativo instalado mantenía el foco fuera de su contenido.
Escape y clic exterior siguen a cargo de Streamlit. El script contiene únicamente código
estático de accesibilidad: no lee contraseñas, tokens ni datos del usuario y no autoriza accesos.

### Corrección visual del encabezado y menú

Aceptación visual parcial: el usuario aprueba expresamente el último ajuste del separador de
Cerrar sesión y lo califica como «perfecto». Ese ajuste está cerrado. Los demás estados de
aceptación se mantienen en [FRONTEND.md](FRONTEND.md).

Se tomó la referencia proporcionada para la composición compacta; se conservan el logosímbolo
oficial, Arial y la paleta blanca/verde. La marca y las acciones usan un contenedor flexible
compartido: Inicio y Docente/Estudiante se alinean horizontalmente. En la portada se muestra
Gestión académica con el mismo tratamiento de navegación y, si corresponde, el acceso de cuenta.

El menú mide 224 px, con iconos Material locales existentes, filas sin bordes individuales,
texto a la izquierda, separador antes del cierre y hover discreto. Configuración y los perfiles
todavía no implementados conservan contraste legible y ayuda «Próximamente». Se conservan el foco,
Escape, clic exterior y las acciones originales. No se modificaron servicios, rutas ni
la política de sesiones para esta corrección visual.

Archivos de esta corrección: `src/componentes/encabezado.py`, `static/css/styles.css`,
`scripts/verificar_frontend.py`, este documento y `docs/FRONTEND.md`.
Regresiones comprobadas: ocho pruebas de navegación/sesión y 28 pruebas de interfaz aprobadas
(`.local/pruebas_encabezado.log`, `.local/pruebas_encabezado_interfaz.log`). La aceptación
visual del usuario sigue pendiente.

Validación visual final de esta corrección: **21 vistas autenticadas sintéticas**
(`.local/frontend/43c8224ccf4c/resultado.json`) y **10 vistas de la instancia HTTPS actualizada**
(`.local/frontend/c2873e2f33f7/resultado.json`), sin fallos. Incluye escritorio, 768/390/320 px,
ausencia de Inicio en portada, una única acción Inicio en portales, alineación horizontal,
marca sin recortes, menú de 224 px con iconos y separador, opciones legibles y cierre funcional.
También se comprobaron teclado, Tab, Escape, clic exterior y conservación de la sesión al navegar.

El logout revoca en Oracle el token presentado y, tras confirmarlo, elimina el estado local,
incluidos perfiles, campos, capturas y propuestas. Cerrar una pestaña reemplazada no revoca
la sesión nueva. No se reintenta automáticamente un COMMIT de resultado incierto.

## Registro de sesión única

La migración reejecutable **007** añade `SESIONES_USUARIO` y `PKG_SESIONES`, conservando
cuentas, materias e historial. El lanzador genera un respaldo cifrado antes de migrar.

- Una fila por **(rol, ID de cuenta)**; las cuentas de roles diferentes son independientes.
- Token opaco aleatorio de 256 bits, mantenido por el servidor. Oracle guarda solo SHA-256.
  Los mensajes no incluyen contraseñas ni tokens.
- Ocho horas de duración máxima y treinta minutos de inactividad, verificadas con el reloj
  de Oracle. La vigilancia periódica de treinta segundos no renueva la actividad.
- El acceso nuevo reemplaza atómicamente al anterior. PK y bloqueos de fila resuelven también
  dos primeros accesos simultáneos: solo un token queda vigente.
- Validación en cada rerun y diálogo, más una comprobación dentro de la conexión de cada
  operación protegida. El bloqueo se mantiene hasta finalizar la transacción: un reemplazo
  espera a una operación que ya estaba autorizada; no autoriza operaciones nuevas del token viejo.
- La sesión anterior muestra que fue reemplazada al interactuar o en la comprobación periódica.
  Las cuentas inactivas, sesiones caducadas o cerradas no autorizan operaciones.

`src/servicios/sesiones_servidor.py` y `src/utilidades/sesiones.py` centralizan la política.
Los adaptadores Oracle de ejecución y administración validan antes de las operaciones.
Una sesión ya válida entra directamente en su propio portal. Puede visitar la portada o el
login de otro portal sin cambiar de rol. Para autenticar otra cuenta debe cerrarse la actual.

Los estados explícitos de las utilidades permiten probar el modelo puro. La interfaz real usa
el estado del servidor y el repositorio Oracle; los fixtures sustituyen ese repositorio
explícitamente y no añaden una opción de omitirlo en la aplicación.

La conexión administrativa limitada recibe EXECUTE sobre `PKG_SESIONES`, sin acceso directo
a la tabla ni nuevos privilegios DBA. Los clientes SQL del propietario siguen siendo herramientas
de confianza; esta política regula las sesiones de la aplicación, no los logins de SQL*Plus.
Inventario 007: 13 tablas, 11 vistas, seis paquetes con sus cuerpos y diez disparadores.

## Recuperación y límites

La sesión sigue ligada al estado de Streamlit; no se introduce un segundo sistema de SSO
ni cookies persistentes. Una conexión nueva o reiniciar el servidor puede requerir autenticación.
La exclusividad entre roles se aplica dentro de la sesión web que identifica el servidor.
No identifica a una misma persona entre navegadores o pestañas con sesiones independientes.
En esos casos sí se mantiene la sesión única por cuenta en Oracle: un nuevo login de esa
cuenta sustituye su token anterior, cualquiera que sea el navegador o dispositivo.
Las sesiones previas a 007, sin registro Oracle, requieren iniciar sesión una vez tras actualizar.
Oracle debe estar disponible: un fallo de validación no concede acceso.

No se confía en el evento de cerrar el navegador; las ventanas abandonadas caducan. Revocar
no borra los datos que alguien ya haya visto o descargado. La recuperación verifica la copia
y después revoca sus registros de sesión para no reactivar tokens antiguos; informa el número
en `sesiones_revocadas` y conserva los datos académicos.

## Archivos principales y validación

Archivos modificados en esta revisión de navegación (sin cambios SQL ni dependencias):

| Área | Archivos de esta revisión |
| --- | --- |
| Rutas e identidad | `principal.py`, `src/interfaz/navegacion.py`, `src/utilidades/sesiones.py` |
| Componentes | `src/componentes/encabezado.py`, nuevo `src/componentes/conflicto_sesion.py`, `static/css/styles.css`, nuevo `static/js/cuenta.js` |
| Accesos | `src/pantallas/pantalla_profesor.py`, `src/pantallas/pantalla_estudiante.py`, `src/pantallas/pantalla_administrador.py` |
| Validación de acceso en servidor | Nuevo `src/servicios/autenticacion.py`, `src/servicios/sesiones_servidor.py`, `src/servicios/registro_estudiante.py`, `src/servicios/recuperacion_acceso.py`, `src/base_datos/bd.py`, `src/base_datos/administracion.py` |
| Pruebas | `tests/test_navegacion_global.py`, `tests/test_sesiones.py`, `tests/test_sesiones_interfaz.py`, `tests/test_contexto_auditoria.py`, `tests/test_administracion_interfaz.py`, `tests/test_frontend.py`, `tests/preview_frontend.py`, `scripts/verificar_frontend.py` |
| Documentación | Este documento, `docs/FRONTEND.md`, `docs/ROADMAP.md` |

**Resultado de la revisión actual:** 173 pruebas aprobadas con `UPC_TEST_ORACLE=1`,
incluidos los seis conflictos posibles entre los tres roles, conservación de sesión y borradores,
logout con revocación, bloqueo en servicios y regresiones académicas/recuperación.
Registro: `.local/pruebas_navegacion.log`. Diagnóstico de dependencias y Oracle correcto,
sin requisitos incompatibles; se mantiene el aviso conocido de `pkg_resources` del modelo facial.
La instancia real HTTPS pasó 14 vistas de portada, accesos, registro y recuperación, incluyendo
anchos móviles (`.local/frontend/c293e89d83c1/resultado.json`), sin enviar credenciales.
El ensayo autenticado final pasó 19 vistas (`.local/frontend/f9ab86a10b2f/resultado.json`):
inicio y logotipo, regreso al portal propio, ambos conflictos debajo del login, cierre y
habilitación del otro acceso; menú con opciones exactas, teclado/Tab, Escape y clic exterior.
Usa perfiles sintéticos y bloquea Oracle durante todo el proceso, incluidos los callbacks.
Después del ajuste final de accesibilidad pasaron nuevamente las ocho pruebas de navegación
(`.local/pruebas_navegacion_final.log`).
La comprobación final de la instancia activa debe verificar además que el complemento de
foco esté cargado; la revisión visual por sí sola no detecta un módulo Python antiguo en memoria.
Se reinició la instancia del proyecto y pasó la verificación final de siete vistas, exigiendo
que el complemento estuviera instalado (`.local/frontend/ef2ccffe7b90/resultado.json`).
La aceptación visual del usuario sigue pendiente. Cámara/micrófono físicos y el nuevo acceso
institucional del estudiante permanecen en sus revisiones aplazadas.

El inventario siguiente incluye además las entregas previas del esquema 007; sus resultados
históricos no sustituyen las pruebas de la revisión actual.

| Área | Archivos |
| --- | --- |
| Sesión y protección | `src/servicios/sesiones_servidor.py`, `src/utilidades/sesiones.py`, `src/base_datos/bd.py`, `src/base_datos/administracion.py` |
| Navegación | `principal.py`, `src/interfaz/navegacion.py`, `src/componentes/encabezado.py` |
| Interfaz | `src/pantallas/pantalla_profesor.py`, `src/componentes/selector_clase.py`, `src/pantallas/pantalla_administrador.py`, `static/css/styles.css` |
| Oracle | Migración 007, `sql/32_paquete_sesiones.sql`, `sql/33_verificar_sesiones.sql`, instalador, verificador y grants administrativos |
| Operación | `scripts/oracle.py`, `scripts/diagnostico.py`, `scripts/preparar_administracion.py`, `scripts/ensayar_restauracion.py`, `src/base_datos/recuperacion.py` |
| Pruebas | `tests/test_sesiones_servidor_integracion.py`, `tests/test_navegacion_global.py`, regresiones/fixtures existentes, `tests/preview_frontend.py`, `scripts/verificar_frontend.py` |

Las pruebas incluyen revocación real para los tres roles, ambas caducidades, cuentas inactivas,
roles distintos, dos accesos concurrentes y un reemplazo durante una operación en curso.
La interfaz comprueba Inicio/logout por rol, sesión reemplazada y conservación de capturas,
materia y clase. El ensayo aislado de recuperación verifica la revocación posterior al respaldo.


Resultados históricos: **162 pruebas aprobadas** (`.local/pruebas007_completas.log`); seis pruebas
Oracle de sesiones que recorren los tres roles; navegación nativa de escritorio/móvil en
13 vistas sintéticas (`.local/frontend/97a67e33ef3b/resultado.json`); revisión de la instancia
real (`.local/frontend/b589f189eb91/resultado.json`); restauración 007 con revocación verificada
(`.local/ensayos/7A152BEC3263/resultado.json`). Las pruebas de interfaz no escriben datos reales.
La verificación de cámara, micrófono y dispositivos físicos sigue perteneciendo al ensayo final.
