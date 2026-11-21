# Pie académico editorial

El pie reproduce la referencia elegida: franja horizontal con zona de desarrolladores
verde bosque (53 %) y referencia académica verde esmeralda (47 %), títulos Georgia cursiva,
créditos sans-serif, divisiones internas y banda inferior. La curva izquierda y las variaciones
tonales se dibujan con CSS; el contenido sigue siendo HTML accesible y seleccionable.

## Alcance y colocación

Se aplica a todos los apartados, según la indicación directa del usuario: portada, accesos,
recuperación y paneles. El router conserva exactamente sus rutas y ejecuta la vista dentro
del contexto visual `pie_pagina_global()`. Este contexto añade un único pie al terminar el
contenido, después de avisos e invitaciones, también cuando un formulario retorna tras validar.

Las llamadas existentes a `pie_pagina_inicio()` y `pie_pagina_panel()` se conservan para
compatibilidad y para vistas aisladas. Un `ContextVar` limita el aplazamiento al render actual;
no se guarda nada en la sesión del usuario ni se cambia la autenticación.

## Edición de créditos

Editar únicamente `src/interfaz/creditos_academicos.py`:

| Campo | Uso |
| --- | --- |
| `estudiantes` | Lista de participantes; inicialmente tres entradas «Nombre Apellido» |
| `docente` | Nombre del docente; inicialmente «Nombre Apellido» |
| `asignatura` | Título académico; inicialmente «Base de Datos» |
| `programa` | Inicialmente «Ingeniería de Sistemas» |
| `anio` | Banda inferior; inicialmente «2026» |

No se inventaron nombres. El componente escapa todos los datos antes de construir HTML.
El título académico añade su punto final de presentación automáticamente.

## Estilos y adaptación

Los estilos se limitan a `upc-academic-footer` y sus descendientes, salvo dos ajustes de su
área de página: se reserva el espacio del scroll vertical y se elimina el padding inferior
blanco después del cierre. Desde la revisión del 21/11, un `ResizeObserver` compartido en
`static/js/diseno.js` publica el ancho útil real de `stMain` en `--upc-ancho-contenido`.
El pie utiliza esa medida para ancho y centrado, con `100cqi` como alternativa inicial.
Así se evita incluir la reserva de la barra de desplazamiento, que producía un desborde
de 4 px en Firefox en el equipo verificado. El observador se actualiza al redimensionar;
no oculta barras ni cambia el flujo normal del pie.

En escritorio conserva 53/47 y las áreas internas horizontales. En tablet reorganiza las
áreas internas; en móvil apila desarrolladores y referencia académica y usa divisores
horizontales. La banda inferior conserva sus dos extremos y admite ajuste en anchos reducidos.

Las variables `--academic-left`, `--academic-left-deep`, `--academic-left-light`,
`--academic-right`, `--academic-right-light`, `--academic-band`, `--academic-text`,
`--academic-label`, `--academic-divider` y `--academic-decoration` permiten adaptar el pie
a un futuro tema. No se implementó modo oscuro ni selector de tema. Las fuentes son locales;
no se añadieron bibliotecas, imágenes de texto ni peticiones externas.

## Archivos

- `src/componentes/pie_pagina.py`: HTML y coordinación del render único.
- `src/interfaz/creditos_academicos.py`: datos editables centralizados.
- `src/interfaz/navegacion.py`: cierre visual después de la vista; rutas intactas.
- `static/css/styles.css`: composición, variables y reglas responsive del pie.
- `static/js/diseno.js` y `src/componentes/encabezado.py`: observación y carga compartida del ancho útil.
- `scripts/verificar_frontend.py`: mediciones de ancho, tipografía, proporciones y recortes.
- `scripts/_frontend_mediciones.py` y `scripts/verificar_firefox.py`: criterios comunes y revisión con Gecko.
- `tests/preview_frontend.py`: ajuste del fixture aislado para terminar la vista y conservar sus enlaces.
- `docs/FRONTEND.md` y este documento: estado y guía de edición.

## Validación

La revisión del 21/11 confirma el ancho y centrado del pie en Firefox, Edge, Chrome y Brave,
con 173 vistas correctas en la matriz final. El detalle y los límites de automatización están
en [FRONTEND.md](FRONTEND.md#firefox-y-edge-revisión-entre-navegadores-21112026).
Los registros siguientes corresponden a la implementación inicial.

- 123 pruebas aprobadas; 50 pruebas de integración Oracle omitidas deliberadamente.
  Registro: `.local/pruebas_pie_academico_final.log`.
- 45 vistas de paneles sintéticos y navegación sin fallos:
  `.local/frontend/4cd293b1aaea/resultado.json`.
- 14 vistas de portada, accesos y recuperación, incluidos 768, 390 y 320 px:
  `.local/frontend/e628a466ddfd/resultado.json`.
- Dos vistas de registro estudiantil con captura sintética y Oracle bloqueado:
  `.local/frontend/9f180c307146/resultado.json`.
- Verificación final de la instancia HTTPS activa: 15 vistas de portada, acceso administrativo,
  accesos, registro y recuperación docente, incluidos tamaños móviles:
  `.local/frontend/4a4c4d8ec524/resultado.json`. No se reinició el servidor ni se iniciaron sesiones.
- Escape de datos HTML, un único pie tras una invitación y pie presente después de un error
  de formulario administrativo comprobados con `.local/comprobar_pie.py`.

Las pruebas verifican el ancho útil completo, proporción de zonas, fuentes cursivas regulares,
banda completa, textos sin recortes y ausencia de scroll horizontal. Las regresiones de
encabezado, menú, separador aprobado, diálogos y navegación continúan pasando. Esta verificación
no sustituye la aceptación visual del usuario; el frontend sigue abierto.
