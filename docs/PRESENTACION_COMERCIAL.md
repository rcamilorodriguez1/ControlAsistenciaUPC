# Presentación comercial de UPC | Aula

Edición 1.2 · 22/11/2026 · 20 diapositivas · formato 16:9.

- [PowerPoint editable](UPC_Aula_Presentacion_Comercial.pptx): textos, diagramas, tarjetas
  y tablas construidos con objetos nativos; incluye notas para la exposición.
- [Presentación en PDF](UPC_Aula_Presentacion_Comercial.pdf): versión de lectura y proyección.
- [Memoria integral 1.2](UPC_Aula_Documentacion_Integral.pdf): fundamento académico/técnico.

## Enfoque de la presentación

Es una presentación de producto para conversar con posibles aliados, responsables de
instituciones e inversionistas: problema, solución, capacidades, evidencia, hipótesis
comercial y propuesta de piloto. La estructura busca claridad de una presentación
empresarial sin atribuir ingresos, clientes, valoración o exactitud biométrica que
todavía no se han medido. El cierre pide un piloto; no presenta una oferta de acciones.

El ejemplo de un docente, un grupo y cuatro sesiones es un **alcance propuesto**, sujeto
a acuerdo. El modelo de licencia institucional, los beneficios de ahorro y los costos
unitarios son hipótesis a contrastar. Las cifras de 288/293/5 describen pruebas de
software; no son una medida de precisión facial ni una tasa de asistencia.

## Identidad UPC aplicada

Fuente: [Manual de Identidad Visual UPC 2010](../Proyecto_recursos/MANUAL%20DE%20IDENTIDAD%20VISUAL-UPC-2010.pdf).

- Logosímbolo original extraído del manual, sin reconstrucción, efectos o recoloración.
- Posición superior izquierda, proporción original y reserva alrededor de la imagen:
  páginas 23–26 y 94. En diapositivas oscuras se coloca sobre una superficie blanca.
- Arial y sus variantes para toda la presentación: página 34.
- Verde principal #007337, tomado de la muestra digital Pantone 356 del PDF; verde
  bosque, tintas verdes claras, blanco y neutros: páginas 38–39. Esa muestra digital
  no se presenta como conversión universal de Pantone para impresión.
- UPC Aula aparece como nombre ordinario del proyecto y se conserva separado del
  logosímbolo institucional; referencias de coexistencia: páginas 42–43.

La identidad comunica su origen académico; no declara representación empresarial ni
aprobación comercial oficial de la universidad. Los integrantes y el docente figuran
con sus nombres confirmados por el equipo.

## Guion orientativo

| Diapositiva | Propósito |
| --- | --- |
| 01 · Cada clase cuenta | Presentar la visión del producto. |
| 02 · El problema | Relacionar contexto, decisión e historial. |
| 03 · La solución | Explicar el recorrido de una clase. |
| 04 · Tres roles | Mostrar el valor para cada participante. |
| 05 · Revisión humana | Distinguir detección de decisión académica. |
| 06 · Producto | Diferenciar operación y perfil/agenda. |
| 07 · Continuidad | Explicar la autorización excepcional con vigencia. |
| 08 · Arquitectura | Separar Render de Oracle y las cuentas técnicas. |
| 09 · Fundamento técnico | Presentar el modelo y su estructura verificable. |
| 10 · Evidencia | Mostrar las pruebas y sus límites. |
| 11 · Madurez | Separar implementación, despliegue y piloto. |
| 12 · Entrada al mercado | Proponer una adopción acotada y progresiva. |
| 13 · Modelo de negocio | Plantear una licencia y acompañamiento como hipótesis. |
| 14 · Unidad económica | Definir qué costos y uso deben medirse. |
| 15 · Capacidades integradas | Explicar el diferencial del proceso completo. |
| 16 · Roadmap | Avanzar por puertas de evidencia. |
| 17 · Piloto | Formular una petición concreta para el siguiente paso. |
| 18 · Equipo | Identificar a los integrantes y la referencia docente. |
| 19 · Anexo de evidencia | Responder qué es hecho y qué está por validar. |
| 20 · Fuentes | Orientar a las referencias editables y al proyecto. |

Las notas del PowerPoint desarrollan el relato de cada diapositiva. Para una exposición
breve, reservar los dos anexos para preguntas y ajustar el tiempo con el equipo.

## Regeneración

Con el entorno opcional de [documentación](requirements-documentacion.txt):

```powershell
.\.local\venv-documentacion\Scripts\python.exe scripts\generar_presentacion.py
```

El generador usa Arial del equipo, por defecto `C:/Windows/Fonts`. En otra plataforma,
indicar `--fuentes` con un directorio autorizado que contenga arial.ttf, arialbd.ttf y
ariali.ttf. Las dependencias documentales no se añaden al runtime de Render.

El archivo PowerPoint es editable directamente. Regenerar sobrescribe los artefactos
con la versión del script; guardar aparte una copia si se realizan cambios manuales.

## Verificación

Se comprueban 20 páginas, texto extraíble, objetos dentro de los límites, cajas de texto,
notas, proporción y bytes del logotipo, metadatos y ausencia de secretos. Se revisan las
diapositivas mediante render del PDF, sin abrir la página de la aplicación ni usar cámara.
Las evidencias de maquetación quedan en `.local/presentacion/`.
