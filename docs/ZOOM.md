# Prueba de zoom de página

Se comprobó la instancia real `https://localhost:8501` con zoom nativo de Chromium al
100, 50, 33, 30 y 25 %. Cada caso utilizó un perfil nuevo y temporal; no se cambió el
zoom del perfil habitual ni se aplicó escalado CSS a la aplicación.

Se revisaron portada y accesos de profesor y estudiante, sin iniciar sesión ni enviar
formularios. Los cinco casos terminaron sin errores de interfaz, recortes horizontales,
imágenes rotas o deformación del logosímbolo. No se detectaron solicitudes externas.

| Zoom | Ancho visible del contenedor | Texto descriptivo visible |
| --- | --- | --- |
| 100 % | 1200 px | 17 px |
| 50 % | 600 px | 8,5 px |
| 33 % | 396 px | 5,61 px |
| 30 % | 360 px | 5,1 px |
| 25 % | 300 px | 4,25 px |

Las medidas visibles corresponden a una escala de dispositivo 1; el contenedor conserva
sus 1200 px CSS máximos. Al alejar, el navegador muestra más espacio CSS y reduce todo.
Por eso quedan márgenes amplios y textos diminutos. Esto limita la legibilidad aunque no
haya desbordamiento. Hacer el contenedor fluido ampliaría la distribución, pero no recuperaría
el tamaño del texto. No se modificó la interfaz ni se bloqueó/compensó el zoom del usuario.

Evidencias consolidadas: `.local/zoom/resultado.json`. Comparación navegable de capturas
al 100/50/30/25 %, con ventana fija de 1424 × 985 píxeles: `.local/zoom/comparacion.html`.
El caso de 33 % conserva su informe técnico aparte; el tamaño nativo de sus capturas no
se usa en la comparación. Los informes individuales están referenciados en el JSON consolidado.

Comando reproducible, usando exclusivamente un perfil aislado:

```powershell
.\.venv\Scripts\python.exe scripts\verificar_frontend.py --url https://localhost:8501 --zoom 25
```

La opción `--zoom` del verificador prepara la preferencia nativa antes de abrir el navegador
y comprueba `devicePixelRatio` y la ausencia de escalado pinch. Las capturas respetan el tamaño
físico del viewport. El lector de `DevToolsActivePort` espera a que Chromium termine de escribir
el archivo, evitando un bloqueo transitorio de lectura en Windows.

Referencias de implementación: [preferencias de zoom de Chromium](https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/ui/zoom/chrome_zoom_level_prefs.cc)
y [conversión de factor a nivel de zoom](https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/common/page/page_zoom.cc).
