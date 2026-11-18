# Frontend: punto 2 de la revisión

## Mockup de referencia

El [mockup navegable](mockup/index.html), edición del 18/11/2026, organiza 18 pantallas o
estados de la interfaz implementada y sus recorridos mediante capturas originales anónimas
o sintéticas. Incluye versiones móviles donde están disponibles, navegación por teclado y
un catálogo consultable. Funciona como referencia documental independiente de la aplicación.
Su [guía](mockup/README.md) delimita el alcance y conserva la procedencia de las imágenes.
La validación del visor no agrega nuevas aprobaciones a la tabla de aceptación siguiente.

## Confirmaciones del usuario

La revisión del frontend continúa abierta. Estos estados reflejan la confirmación expresa del
usuario; las pruebas automáticas y capturas se registran por separado.

| Cambio | Estado confirmado por el usuario |
| --- | --- |
| Identidad actual UPC \| Aula | Le gusta el estado actual; habrá ajustes más adelante |
| Iconos y controles de contraseñas | Funcionamiento normal y correcto confirmado |
| Olvidé mi contraseña del docente | Funcionamiento confirmado |
| Separador de Cerrar sesión: alineación, separación y estabilidad visual | Aprobado y cerrado; el usuario lo califica como «perfecto» |
| Selectores docentes y Crear nueva materia | Pendiente de confirmación |
| Navegación mediante logotipo, Inicio y Cerrar sesión | Pendiente de confirmación |
| Presentación con zoom reducido | Pendiente de aceptación visual |
| Pie académico editorial compartido | Implementado y probado; pendiente de confirmación visual |
| Mi perfil del estudiante: resumen, materias y calendario | Implementado el 17/11/2026; pendiente de confirmación visual |
| Acceso excepcional estudiantil y gestión administrativa de verificaciones | Implementado el 17/11/2026; pendiente de confirmación del usuario |

Esta aceptación es parcial: no cierra el frontend ni confirma otras pantallas, roles o casos
que el usuario no haya revisado expresamente.
El último ajuste del separador de Cerrar sesión queda tachado como listo. Esta confirmación
visual no equivale a aprobar por separado todos los recorridos de navegación o cierre de sesión.

## Implementación y pruebas registradas

17 de noviembre de 2026: **Mi perfil** queda habilitado para el estudiante autenticado, con
estructura de perfil social académico, porcentaje acumulado, matrículas actuales, resumen de
presencias/ausencias, materias y calendario mensual. Consulta privada del servidor, sin cambiar
la autenticación ni crear tablas. Detalle y pruebas: [PERFIL_ESTUDIANTE.md](PERFIL_ESTUDIANTE.md).

Pie editorial académico implementado en todos los apartados, con la composición de la
referencia, créditos provisionales editables desde un archivo y un solo cierre al final de
cada vista. Guía, inventario y comprobaciones: [PIE_ACADEMICO.md](PIE_ACADEMICO.md).
La incorporación del pie no cambia la aprobación del separador de Cerrar sesión ni cierra
las revisiones pendientes del frontend.

Revisión exclusiva del separador de Cerrar sesión: `cierre_cuenta` agrupa la línea y el botón
con una referencia horizontal común. La línea toma los límites exteriores del resaltado,
incluyendo la reserva del foco existente (3 px de trazo y 3 px de distancia). El ancho se
deriva del contenedor y esa reserva; no se fija una longitud en píxeles. El botón mantiene
su ancho y sus estilos. Solo la línea se extiende hasta los límites de referencia.

El divisor se renderiza realmente como Markdown: su margen inferior nativo de −16 px colapsaba
su altura y hacía que invadiera el botón. La regla local neutraliza ese margen y mantiene una
fila independiente, separada 0,5 rem del botón. No usa su borde como divisor ni cambia con hover
o focus. No se modifica ninguna otra línea o botón de la aplicación.

Validación: 45 vistas sintéticas sin fallos (`.local/frontend/f1d3572169ec/resultado.json`),
con ancho de línea y contorno exterior de 222 px, botón de 210 px y separación vertical de
8 px (2 px libres respecto al foco). Comprobada la invariancia de posición relativa, ancho y
color con hover/focus en escritorio y móvil para ambos roles. Ocho pruebas existentes de
navegación aprobadas (`.local/pruebas_separador_cierre.log`). Producción: `encabezado.py` y
`styles.css`; mediciones en `verificar_frontend.py`. Aceptación visual confirmada por el usuario:
«este último el del cerrar sesión táchalo como perfecto». Este ajuste queda cerrado.

Revisión anterior de dos defectos de navegación (la corrección del separador queda sustituida
por la revisión exclusiva descrita arriba):

- **Scroll en Inicio:** el wrapper nativo `stElementContainer:has(> .stPageLink)` aplica
  márgenes verticales negativos de 6 px. Con la altura personalizada del enlace, su contenedor
  se reducía 12 px y desbordaba la fila `acciones_cabecera`, que usa `overflow-y: auto`.
  Se neutralizan esos márgenes exclusivamente dentro de `navegacion_inicio`, se normalizan
  los márgenes del enlace y su altura de línea. No se ocultan barras ni se cambia el overflow.
- **Separador de Cerrar sesión:** `stDivider` añadía `padding: 0 8px` al padding general del
  menú, acortando la línea 16 px. Se elimina únicamente ese padding adicional, conservando
  `margin: 5px 0`, el padding exterior y los bordes del elemento.

La corrección de producción solo modifica `static/css/styles.css`; las mediciones se añaden
al verificador existente `scripts/verificar_frontend.py`. Validación: 39 vistas sintéticas
(`.local/frontend/6ba766d2c6b1/resultado.json`) y 10 vistas HTTPS reales sin autenticarse
(`.local/frontend/b4c6c7d9a803/resultado.json`), sin fallos. Incluye hover, foco real y active
en ambos roles, antes/después de cerrar sesión y escritorio/móvil. El separador y el resaltado
miden 210 px y comparten exactamente izquierda y derecha; Inicio conserva centrados texto
e icono y sus contenedores ya no desbordan. No se reinició el servidor ni se cambió la lógica
de autenticación, sesión o navegación. La aceptación visual del usuario sigue pendiente.

Corrección visual del encabezado según la referencia del usuario: un único Inicio con casa
en los portales, ninguno en la portada; marca y acciones compartidas, Gestión académica
coherente y menú compacto de 224 px con iconos y separador. Las dos opciones futuras mantienen
legibilidad y siguen deshabilitadas. No cambia la autenticación, las rutas ni la exclusividad
de sesiones. Archivos y comprobaciones: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md).
La corrección está pendiente de confirmación visual del usuario.

Revisión del 12 de noviembre de 2026: portada pública incluso autenticado, rutas nativas
por portal, aviso bajo el login incompatible y menú de cuenta compartido por los tres roles.
Detalle vigente: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md). Su aceptación visual por el
usuario sigue pendiente; no cambia las confirmaciones de identidad, iconos y recuperación.

Implementado el 11 de noviembre de 2026. El rediseño inicial no requirió DDL sobre 005.
La ampliación posterior incorpora el acceso y panel administrativo con la migración 006;
ver [ADMINISTRACION.md](ADMINISTRACION.md). Las validaciones automáticas de cada ampliación
se detallan en sus documentos; no equivalen a confirmación del usuario.

## Presentación y navegación

El acceso docente incluye **Olvidé mi contraseña** con formulario independiente, autorización
privada, fortaleza y confirmación en vivo. Validación y alcance estudiantil aplazado:
[RECUPERACION_ACCESO.md](RECUPERACION_ACCESO.md).

Revisión 007 del portal docente y del encabezado de todos los roles: selectores acotados,
creación de materia primaria, logotipo/Inicio con navegación nativa y sesión única en servidor.
Guía vigente y límites: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md).

**Revisión vigente: UPC | Aula.** Se aplica el manual institucional de `Proyecto_recursos`,
con logosímbolos originales extraídos del PDF, Arial, blanco/verde y presentación asimétrica.
El detalle, inventario y archivos modificados están en [IDENTIDAD_VISUAL.md](IDENTIDAD_VISUAL.md).
Las revisiones siguientes describen el estado anterior y su validación histórica.

Revisión institucional: portada «SISTEMA DE GESTIÓN ACADÉMICA / Control de asistencia
académica.», descripción funcional solicitada y acceso administrativo «Gestión académica».
Se retiraron el eslogan y el título serif. La interfaz comparte Segoe UI (alternativa local Arial),
texto de 16 px, auxiliares de 14 px y pesos 400/600. Los títulos usan una escala común
(32/20/18 px; título principal de 28 px en móvil), sin estilos especiales de portada ni cursivas.
Los iconos conservan su fuente Material independiente. No se descargan fuentes externas.

Validación de esta revisión: cuatro pruebas del acceso administrativo aprobadas, diez vistas
de la instancia real HTTPS (`.local/frontend/f03f7fd48492/resultado.json`) y diez vistas de
paneles sintéticos (`.local/frontend/d7c74c27347d/resultado.json`). Sin recursos externos ni
errores de interfaz; se comprobaron los iconos, el foco, el medidor de contraseñas y el nombre
completo del acceso Gestión académica en escritorio y móvil emulado.

El inicio, los accesos, el registro y los paneles comparten la misma paleta verde, fondo claro,
encabezado, espaciado y tarjetas. Los botones distinguen acciones principales, alternativas y
acciones secundarias; ya no se transforman o agrandan al pasar el cursor. Se conservan las
claves de sesión, las confirmaciones y los controles de revisión de asistencia.

Los indicadores se muestran juntos también en móvil; materias, formularios y acciones se
adaptan a una columna cuando falta espacio. Los cuadros de revisión, voz y QR disponen de
mayor anchura en escritorio. El QR incluye margen de lectura y aclara cuando el enlace es local
al mismo equipo. La configuración de URL/HTTPS anterior permanece vigente.

La marca actual usa los originales del manual en `static/img/upc/`; los pictogramas de módulos
siguen siendo SVG locales de `static/img/`. No se solicitan logos a ibb
ni fuentes a Google Fonts. Los textos usan las fuentes locales de Streamlit y del sistema.
Los iconos de Streamlit mantienen su propia fuente, incluidos mostrar/ocultar contraseña.
Se retiraron los márgenes negativos y las reglas que recoloreaban o cambiaban todos los hijos
de botones, alertas y controles multimedia. Las advertencias conservan sus colores semánticos.

## Arranque y carga

`principal.py` configura la página y carga `static/css/styles.css` antes de importar la pantalla
elegida. Ese archivo es la única hoja de estilos de la aplicación. `st.html` envía los estilos
al contenedor de eventos, sin añadir bloques vacíos entre los controles.

El destello anterior se debía a que los imports pesados retrasaban el CSS mientras el cliente
mostraba su barra de desarrollo. Se configuraron `client.toolbarMode="minimal"` y
`ui.hideTopBar=true` desde `.streamlit/config.toml`, además de desactivar estadísticas de uso.
Se verificó que la barra no apareciera durante el arranque normal y con CPU/red ralentizadas.
No se modificaron archivos instalados de Streamlit. Esta configuración se comprobó con 1.67.0;
hay que repetir la revisión visual al cambiar la versión, especialmente por los selectores CSS
y la opción interna `ui.hideTopBar`.

`biometria_diferida.py` carga las canalizaciones al analizar fotos o voz. El contrato
`ResultadoAudio` se separó del codificador para que los formularios no importen PyTorch,
Resemblyzer o dlib. Una prueba en un proceso nuevo comprueba que inicio, acceso y registro
docente y acceso estudiantil no importan esas dependencias. Al necesitarlas se conservan los
indicadores de progreso de cada operación. El primer análisis todavía puede tardar mientras
se inicializan los modelos; el cambio evita pagarlo al abrir la página.

## Datos y controles

La lista de materias del docente obtiene ambos contadores mediante agregaciones en una
consulta, en lugar de dos consultas adicionales por cada materia. La prueba Oracle comprueba
que dos matrículas y dos clases no multipliquen los conteos al unirse. Los indicadores de materias
activas e inscritos excluyen materias archivadas; las asistencias históricas permanecen disponibles.
No se midió el rendimiento con un volumen grande de datos.

Los textos de nombre, código, sección, estadísticas y saludo se escapan antes de insertarlos
en HTML. Se añadió una regresión con contenido HTML malicioso. Las sesiones y las políticas
de autorización siguen siendo las de [REGLAS_NEGOCIO.md](REGLAS_NEGOCIO.md).

Hay foco de teclado visible, se respeta la preferencia de movimiento reducido y los colores
de texto secundarios se ajustaron para superar contraste 4.5:1 sobre los fondos de las tarjetas
y la página. Esto no sustituye una auditoría completa de accesibilidad.

## Comprobaciones y evidencia

La suite actual termina con **133 pruebas aprobadas**, incluida integración Oracle con rollback
y el medidor de contraseñas. Log: `.local/pruebas_seguridad_claves_completas.log`.

```powershell
.\.venv\Scripts\python.exe scripts\verificar_frontend.py
.\.venv\Scripts\python.exe scripts\verificar_frontend.py --lento
.\.venv\Scripts\python.exe scripts\verificar_frontend.py --paneles
```

El comprobador abre Chrome/Brave sin ventana y con perfil nuevo, en una instancia HTTP de
prueba ligada exclusivamente a 127.0.0.1 y un puerto libre. Bloquea recursos HTTPS externos,
captura vistas a 1440 y 390 píxeles, comprueba desbordamientos, etiquetas recortadas, imágenes,
fuentes de iconos, navegación con Tab y los dos estados de contraseña. También observa el DOM
desde el primer documento para detectar la barra de desarrollo. Cierra solo sus procesos.

`--lento` simula CPU x4 y latencia de 120 ms. `--paneles` usa `tests/preview_frontend.py`,
con datos sintéticos y proveedor Oracle bloqueado: no añade entradas de prueba a la aplicación
ni permite escrituras a la base. Revisa materias, reportes, creación, QR y revisión de asistencia.

Cada ejecución guarda `resultado.json`, capturas y log en `.local/frontend/IDENTIFICADOR/`.
Las capturas con sufijo `_inferior` muestran el final de páginas que requieren desplazamiento.
Las pruebas terminadas cubren siete vistas anónimas y diez vistas de paneles/diálogos. Las
capturas con perfiles sintéticos están identificadas como prueba.

Las siete vistas anónimas se verificaron en Chrome y Brave sobre Windows, también con CPU/red
ralentizadas. Los diez paneles/diálogos sintéticos se revisaron en Chrome. Evidencia final de
Brave: `.local/frontend/40922a72c729/resultado.json`; paneles: `.local/frontend/d84a8231d886/resultado.json`.
No se detectó barra de desarrollo durante el arranque, solicitudes externas, imágenes rotas,
iconos con fuente incorrecta ni etiquetas recortadas. Tab y mostrar/ocultar contraseña pasaron.

Estas comprobaciones no validan cámara/micrófono reales, biometría, un teléfono físico,
HTTPS del teléfono ni otros sistemas. Eso pertenece
al punto 6; portabilidad y mantenimiento general permanecen en 5 y SQL Developer en 7.

Para cargar el nuevo arranque en la aplicación habitual: detener con **Ctrl+C** y ejecutar
`.\iniciar.cmd` desde la raíz del proyecto en PowerShell.

## Fortaleza de contraseña en el registro docente

Los dos campos de contraseña del registro usan actualización en vivo tras una pausa de 300 ms.
Se retiró su contorno interno marrón, que se recortaba junto al botón de mostrar/ocultar.
El foco accesible ahora rodea el control completo en verde. Esta corrección se extendió a todos
los campos de texto: acceso docente, autorización, nombre y código del registro estudiantil.

Debajo de la contraseña se muestra una estimación de cinco niveles: Muy débil, Débil, Moderada,
Fuerte y Muy fuerte. Se utiliza [zxcvbn 4.5.0](https://pypi.org/project/zxcvbn/) instalado en el
venv y fijado en ambos archivos de dependencias. Detecta patrones como contraseñas comunes,
repeticiones, secuencias y datos del nombre/usuario; ofrece recomendaciones en español.
La recomendación de incorporar un medidor se recoge en la
[guía de autenticación de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

La valoración se ejecuta en el servidor local de la aplicación: el campo se sincroniza por
la conexión HTTPS existente. No se envía a Kaspersky ni a un servicio externo. No se añaden
registros o cachés de contraseñas. El resultado visible no incluye la contraseña ni tiempos
de descifrado. Los términos personales que usa el estimador se retiran de su diccionario global
al terminar cada evaluación y se aíslan mediante un bloqueo para evitar mezclar sesiones.

El indicador es orientativo; no consulta listas de filtraciones ni garantiza que una clave no
sea conocida. No cambia la política existente de aceptación: se siguen validando los límites
de 8–72 bytes UTF-8 y la ausencia de caracteres nulos. En el segundo campo se muestra, en vivo,
si ambas contraseñas coinciden, sin recortar espacios ni modificar el valor escrito.

Validación automática: **133 pruebas aprobadas**, incluidas cinco del estimador, una de su
integración en el registro y las regresiones anteriores. Log:
`.local/pruebas_seguridad_claves_completas.log`. El comprobador visual admite `--claves` para
escribir valores sintéticos y comprobar fuerza, coincidencia y foco sin enviar el formulario.
La revisión en Brave terminó correctamente; evidencia:
`.local/frontend/e60c4001453c/resultado.json`. Se comprobó la actualización sin pulsar Enter,
la ausencia del contorno marrón en ambos campos y las confirmaciones distintas e iguales.

## Verificar la instancia que utiliza el usuario

Se reprodujo un fallo de actualización en `https://localhost:8501`: esa instancia conservaba
el registro anterior sin medidor mientras los procesos nuevos de prueba sí mostraban el cambio.
Se reinició únicamente ese servidor y se activaron `server.runOnSave=true` y
`server.fileWatcherType="poll"` para la recarga durante el desarrollo.

La comprobación ahora puede apuntar al servidor existente, sin iniciarlo ni detenerlo:

```powershell
.\.venv\Scripts\python.exe scripts\verificar_frontend.py --url https://localhost:8501 --claves
```

La evidencia anterior al reinicio está en `.local/frontend/266008aa818d/resultado.json`.
La revisión posterior de la misma URL terminó correctamente en
`.local/frontend/0c1573d56e74/resultado.json`: medidor y coincidencia en vivo, diez vistas,
foco verde completo y ausencia del contorno interno en acceso y registro docente.

Para estudiante se usaron los campos reales del formulario con captura sintética y conexión
Oracle bloqueada, sin cámara real ni altas. Ambos campos pasaron en escritorio y móvil:
`.local/frontend/0fb4e275faea/resultado.json`. Esa prueba se reproduce con `--registro-estudiante`
y no añade accesos de prueba a `principal.py`.
