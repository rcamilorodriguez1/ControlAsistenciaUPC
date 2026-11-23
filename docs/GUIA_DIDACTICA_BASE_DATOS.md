# La base de datos desde cero: guía ilustrada

[Abrir el PDF completo](UPC_Aula_Base_de_Datos_Desde_Cero.pdf).

Edición del 23/11/2026, esquema Oracle **001–011**. Tiene **84 páginas**,
27 capítulos, índice navegable y 49 marcadores. Se entrega también una copia
idéntica en el Escritorio: `UPC_Aula_Base_de_Datos_Desde_Cero.pdf`.

## Cómo leerla

- Capítulos 1–8: tablas, filas, columnas, destinos local/cloud, documentos e IDs,
  tipos, claves y relaciones, con dibujos y ejemplos de Laura, Ana y Luis.
- Capítulos 9–10: fichas de las **14 tablas**, diccionario de **140 campos**,
  restricciones y las **11 relaciones físicas**. Cada ficha explica qué representa
  una fila, muestra un ejemplo y traduce las reglas a palabras sencillas.
- Capítulos 11–15: recorrido de una clase, transacciones, bloqueos, reintentos,
  consultas SELECT/JOIN, resúmenes y diferencia entre cambiar filas y estructura.
- Capítulos 16–20: **11 vistas**, **8 paquetes y sus 41 rutinas públicas**,
  **10 disparadores**, **37 índices** —incluidos los internos—, identidades y acceso.
  Las rutinas distinguen qué reciben y qué devuelven. Hay ejemplos para leer
  una llamada PL/SQL y las referencias `:OLD` / `:NEW` de un trigger.
- Capítulos 21–27: once migraciones, mapa de los archivos SQL, scripts Python de
  operación, respaldos/reinicio, historias completas, preguntas con respuestas
  y glosario. El mapa de archivos sirve como referencia durante el estudio.

Los párrafos son cortos y los gráficos son vectoriales, con tipografía Arial y
el logo original de la UPC. Se puede ampliar el PDF sin pixelar sus diagramas.
El aprendizaje con el usuario continúa; entregar el libro no equivale a dar
por estudiados todos sus temas.

## Fuente y alcance comprobados

Los metadatos proceden de una transacción de solo lectura en Autonomous 011:
[captura específica de esta guía](base_datos/catalogo_estudio_011.json).
Incluye tipos, obligatoriedad, valores predeterminados, PK/FK/UNIQUE/CHECK,
vistas, especificaciones públicas de paquetes, disparadores, índices e identidades.
Las explicaciones se contrastan con el SQL y los servicios del proyecto.

La guía explica el documento estudiantil incorporado en 011 y conserva la
distinción entre el código institucional legado y el ID interno. Aclara el
conteo tras el reinicio: **14 tablas existentes; 13 de datos vaciadas y
VERSIONES_ESQUEMA conservada con sus 11 versiones**.

Los nombres, IDs y filas de ejemplo son ficticios y se dibujan en el documento.
No se consultan filas de personas ni se insertan datos al generar el PDF.
La captura histórica 009 y los entregables anteriores de exposición se conservan.

## Regeneración

Exportador: [exportar_catalogo_estudio.py](../scripts/exportar_catalogo_estudio.py).
Requiere una configuración privada del propietario y solo acepta el esquema 011.
No publica DSN ni credenciales. Su argumento `--configuracion` apunta al TOML
privado; no se copian contraseñas a los comandos ni a esta guía.

Generador: [generar_guia_didactica_bd.py](../scripts/generar_guia_didactica_bd.py).
Lee el JSON local y los nombres de los archivos SQL; no necesita conectar con
Oracle. Requiere ReportLab y las fuentes Arial instaladas en Windows. En este PC,
las herramientas documentales están aisladas en `.local/herramientas_pdf`:

```powershell
$env:PYTHONPATH = (Resolve-Path .local/herramientas_pdf).Path
.\.venv\Scripts\python.exe scripts/generar_guia_didactica_bd.py
```

## Revisión de la entrega

- Cobertura comprobada de los 140 campos dentro de su ficha, las 41 rutinas y
  sus parámetros dentro de su paquete, las 11 vistas, 10 triggers y 37 índices.
- 49 marcadores y 98 enlaces internos válidos; ningún texto fuera de página.
- Revisión visual de las páginas, diagramas, diccionario y ejemplos PL/SQL.
- Comparación con 12 valores privados: ninguna coincidencia en el PDF, su texto
  extraído ni el catálogo exportado. El documento no contiene claves de acceso.
- Copia del Escritorio comprobada mediante SHA-256. Evidencia privada en
  `.local/guia_didactica/validacion_final.json`.
- Sin pruebas de página/cámara ni nuevas cuentas o datos en las bases.

Continuación: [roadmap de aprendizaje](ROADMAP_APRENDIZAJE_BASE_DATOS.md) y
[guía inicial por scripts](APRENDER_BASE_DATOS.md). La primera carga sigue
pendiente de estudiar y acordar con el usuario.
