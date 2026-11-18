# UPC | Aula: identidad y presentación

La interfaz utiliza la identidad oficial de la Universidad Popular del Cesar y presenta
**UPC | Aula** como nombre de la plataforma, en texto ordinario y separado del logosímbolo.
No se creó un símbolo universitario alternativo.

## Referencia y recursos

Se revisaron los tres archivos de `Proyecto_recursos`; el manual consta de 98 páginas.
Las secciones aplicadas son: reserva y composición (páginas 23–26), variantes y limitaciones
(28–29), tipografía (34), colores (38–39), coexistencia de identificadores (42–43), usos
correctos (45), página web (87) y recomendaciones (94).

La marca horizontal de 1369 × 474 px y la vertical de 641 × 544 px se extrajeron como imágenes
originales del propio PDF. No se reconstruyeron sus letras ni símbolos. Se conserva el color,
la composición, el aspecto y el formato JPEG originales. Los archivos y sus huellas están en
[static/img/upc/README.md](../static/img/upc/README.md). El encabezado muestra el logosímbolo
completo a 176 px, con 16 px de reserva; en móvil, 128 px y 12 px. Esa reserva supera una unidad
X de su retícula. El fondo de la marca permanece blanco.

Se prioriza Arial, autorizada en la página 34, con alternativas Helvetica/sans-serif y sin
descargas de fuentes. La tipografía propia del logosímbolo sigue dentro de la imagen original.
El verde principal `#007337` procede del relleno digital de la muestra Pantone 356 del PDF
(página 38); esta referencia describe ese documento, no una conversión universal de Pantone.
Se emplean blanco, neutros y superficies verdes suaves para los controles. Los estados de
error y advertencia mantienen sus colores funcionales.

## Composición

- Encabezado compartido compacto: logotipo a la izquierda, reserva y separación del nombre
  de plataforma, universidad debajo y navegación de Gestión académica a la derecha.
- Presentación con el texto solicitado: «UNIVERSIDAD POPULAR DEL CESAR», «Gestión y seguimiento
  académico.» y «Consulta de asignaturas, registro de sesiones y seguimiento de la actividad
  académica.». El lema «Educación y Futuro» ocupa una posición secundaria.
- Distribución asimétrica en escritorio, una columna en móvil. Accesos por rol con superficies
  planas, líneas de referencia y botones de tamaño de contenido, sin sombras ni esquinas amplias.
- Eliminados el calendario genérico del encabezado/favicon, los eslóganes anteriores, las
  reiteraciones del título en el pie y el bloque decorativo de tres pasos.
- El foco visible, los iconos nativos y las acciones de los botones se mantienen. No se
  modificaron formularios, servicios, datos, credenciales, rutas ni reglas de negocio.

Contrastes calculados: verde/blanco 5,99:1; texto auxiliar/blanco 6,19:1; texto auxiliar/superficie
suave 5,68:1; texto principal/blanco 12,11:1. El favicon se reduce por el navegador y no sustituye
el logosímbolo legible del encabezado. Ningún recurso necesita rutas absolutas del equipo.

## Archivos de esta revisión

| Archivo | Cambio |
| --- | --- |
| `principal.py` | Título de pestaña UPC \| Aula y recurso institucional del favicon |
| `src/componentes/encabezado.py` | Marca original, nombre de plataforma y navegación compacta |
| `src/pantallas/pantalla_inicio.py` | Nueva presentación, lema y accesos por rol |
| `src/componentes/pie_pagina.py` | Pie institucional sin repetir el título funcional |
| `static/css/styles.css` | Paleta, Arial, composición, proporciones, reserva y responsive |
| `.streamlit/config.toml` | Tema nativo acorde con la identidad |
| `tests/preview_frontend.py` | Favicon de las vistas sintéticas coherente con la aplicación |
| `scripts/verificar_frontend.py` | Inspección de marca y revisión adicional a 320/390/768 px |
| `static/img/upc/` | Dos recursos originales del manual y procedencia documentada |
| `docs/FRONTEND.md` y este documento | Registro del diseño y validaciones |

Las herramientas de lectura del PDF se usaron de forma aislada en `.local`; no se añadieron
dependencias al entorno de ejecución ni se cambiaron los archivos de requirements.

## Verificación

- Seis pruebas existentes de frontend y acceso administrativo aprobadas:
  `.local/pruebas_upc_aula.log`.
- Instancia real `https://localhost:8501`: diez vistas con formularios, teclado, fortaleza de
  contraseñas e iconos; `.local/frontend/8247baaeaae7/resultado.json`.
- Diez vistas de paneles y diálogos sintéticos, con Oracle bloqueado:
  `.local/frontend/98674d6568ee/resultado.json`.
- Presentación a 1440, 768, 390 y 320 px; logotipo con proporciones originales y reserva,
  navegación a la derecha sin recorte, sin errores ni recursos externos:
  `.local/frontend/fdf2878a5943/resultado.json`.
- Comparación binaria de ambos archivos con las imágenes incrustadas del PDF: idénticos.

La instancia activa se reinició para cargar el nuevo tema y los componentes actualizados.
La revisión móvil es emulada; no sustituye el ensayo posterior con dispositivos físicos.

Prueba posterior de zoom nativo al 100/50/33/30/25 %: [ZOOM.md](ZOOM.md). Sin fallos de
distribución; a porcentajes extremos disminuye la legibilidad y aumentan los márgenes aparentes.
