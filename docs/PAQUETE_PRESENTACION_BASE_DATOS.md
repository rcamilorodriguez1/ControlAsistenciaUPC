# Entrega del Escritorio para la exposición de Base de Datos

La carpeta **UPC_Aula_Presentacion_Base_de_Datos** del Escritorio reúne el material
para la exposición. Los originales permanecen en el proyecto. Se entrega también
un ZIP de la carpeta para transportarla a otro equipo.

## Entrada y orden

Abrir `00_EMPEZAR_AQUI.html`. El índice funciona sin internet y enlaza los archivos.
`00_LEER_PRIMERO.txt` conserva las mismas indicaciones en texto sencillo.

| Carpeta | Contenido |
| --- | --- |
| 01_Presentacion | Presentación principal de Base de Datos: 21 diapositivas en PowerPoint con notas y PDF. |
| 02_Documentacion | Memoria 1.2 de 87 páginas; guía de defensa de 8 páginas; problemática, objetivos y aporte a Ingeniería de Sistemas. |
| 03_Diccionario | PDF independiente de 30 páginas, Markdown y catálogo HTML interactivo. |
| 04_Modelo_relacional | Modelo 009 en PDF A3, PNG, SVG y Mermaid; DDL actual para Data Modeler. |
| 05_SQL | Dos guiones de solo lectura para exponer y copia separada del SQL original con instalación/migraciones. |
| 06_Conexion_y_valor | Conexión del programa, cuentas técnicas, goodwill y acceso público a Render. |
| 07_Codigo_fuente | Snapshot del repositorio publicado, expandido y en ZIP. |
| 08_Comercial_opcional | La presentación comercial anterior en PDF y PowerPoint, como apoyo. |
| 09_Identidad_UPC | Manual de identidad visual del proyecto. |

La presentación principal prioriza modelo relacional, N:M, normalización, claves,
restricciones, JOIN, vistas, paquetes, triggers, transacciones, auditoría y conexión.
El guion relaciona estas decisiones con Ingeniería de Sistemas y aporta preguntas
para ensayar la defensa. El valor comercial se explica como cierre del caso de uso.

## Consulta y conexión

PDF, imágenes, guía y catálogo funcionan sin internet. La web y las consultas reales
requieren conectividad y la configuración autorizada del equipo. La carpeta no
incluye contraseñas, documentos personales, biometría ni un volcado de filas.

El DDL se obtuvo mediante metadatos del esquema 009 y sirve para importación visual
en Data Modeler. Los guiones 01 y 02 son consultas; los originales de instalación y
migración están separados para conservar sus rutas y contexto de ejecución.

## Regeneración

Usar las dependencias opcionales de documentación y Arial. Desde el proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\exportar_modelo_presentacion.py
python scripts\generar_presentacion_base_datos.py
python scripts\generar_material_exposicion.py
python scripts\preparar_paquete_presentacion.py
```

Los tres últimos comandos se ejecutan con el intérprete del entorno documental.
El exportador usa la configuración privada existente y una transacción de solo lectura;
no crea tablas ni modifica datos. El preparador copia el material y crea un ZIP con
manifiesto SHA-256. Rechaza un destino existente para conservar sus archivos; se puede
indicar otro con `--destino`.

La copia del código procede de `git archive HEAD`, por lo que corresponde al commit
indicado en el manifiesto y no incluye `.local`, venv ni secretos ignorados por Git.
Las pruebas de la página y cámara siguen a cargo del usuario; esta entrega solo
genera y verifica documentos, scripts de consulta y copias de archivos.
