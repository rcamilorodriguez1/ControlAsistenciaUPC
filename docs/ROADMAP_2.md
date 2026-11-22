# Segundo roadmap de UPC Aula

Estado: registrado para después del cierre del [primer roadmap](ROADMAP.md).
Acuerdo del 21 de noviembre de 2026: primero completar organización y despliegue de la
versión actual; después mejorar frontend y diseño de la base. Este registro no autoriza
adelantar funcionalidades que el usuario dejó expresamente aplazadas.

## Objetivo

Mejorar la experiencia universitaria y revisar la distribución de responsabilidades entre
Python y Oracle sobre una versión desplegada y comprobada. Los cambios se harán mediante
migraciones nuevas, conservando datos, contratos de acceso y evidencia de las pruebas.

## Alternativa de alojamiento: Vercel y Render

El 22/11 el usuario pide considerar Vercel para la interfaz y Render para el backend,
o distribuir servicios entre otros proveedores, por las limitaciones del alojamiento.
Es una alternativa a evaluar, sin una decisión de migrar el servicio ya desplegado.

- La aplicación actual usa Streamlit para interfaz y servicios en el mismo proceso.
  Separar las pantallas requiere diseñar una interfaz independiente y una API, con
  autenticación, sesiones, subida de muestras y comunicación entre los dos dominios.
- Una distribución posible es interfaz en Vercel, API Python y biometría en Render,
  Oracle Autonomous para los datos y un proveedor de correo por API HTTPS.
- Trasladar la interfaz no acredita una reducción suficiente de memoria: los modelos
  faciales y de voz seguirían consumiendo recursos donde se ejecute la inferencia.
  El usuario confirma que la prioridad es **memoria y CPU del reconocimiento facial y de
  voz**, para la presentación. Medir consumo antes de elegir la distribución.
- La revisión estática confirma imports diferidos en `biometria_diferida.py` y reutilización
  mediante `st.cache_resource` en las dos canalizaciones. Falta medir el proceso con ambos
  modelos cargados, las capturas grandes y tomas simultáneas; no hay un fallo de memoria
  demostrado por los logs disponibles. La salud HTTP no acredita ese rendimiento.
- Render Free ofrece 512 MB y 0,1 CPU según la documentación consultada. Comprobar el
  plan real y observar **Metrics** en reposo, tras análisis facial y tras voz. Separar solo
  el motor biométrico en un servicio con recursos suficientes es otra opción a evaluar;
  permitiría conservar la interfaz Streamlit y el acceso Oracle en Render mientras se
  dimensiona el procesamiento, sin exigir primero un rediseño de las pantallas.
- Evaluar también el alojamiento completo: Vercel incorporó soporte de contenedores
  y WebSockets durante 2026. No descartarlo por afirmaciones antiguas sobre Python;
  verificar compatibilidad, duración de conexiones, cuotas y costo del plan elegido.
- Conservar el servicio Render/Oracle funcional mientras se compara y prueba la alternativa.

Referencias consultadas el 22/11:
[backends Python y contenedores en Vercel](https://vercel.com/blog/backends-on-vercel-python-containers-and-daemons),
[WebSockets en Vercel](https://vercel.com/changelog/websocket-support-is-now-in-public-beta),
[límites de funciones](https://vercel.com/docs/functions/limitations) y
[límites de Render Free](https://render.com/docs/free),
[planes de cómputo](https://render.com/docs/compute-plans) y
[métricas CPU/RAM](https://render.com/docs/service-metrics).

## Interfaz y experiencia de uso

- [ ] Revisar con el usuario las pantallas de los tres roles y cerrar la aceptación pendiente.
- [ ] Refinar tipografía, espaciado, jerarquía, formularios, tablas, mensajes y navegación.
- [ ] Comprobar escritorio, móvil, zoom reducido, teclado y accesibilidad entre navegadores.
- [ ] Completar las vistas de perfil y configuración que se acuerden para cada rol.
- [ ] Diseñar por separado el acceso institucional del estudiante y sus opciones de recuperación.
- [ ] Mantener como referencia la identidad UPC aprobada y el separador de Cerrar sesión,
  que el usuario calificó como «perfecto»; cualquier cambio posterior deberá justificarse.

## Responsabilidades de Oracle y Python

- [ ] Inventariar reglas de negocio que permanecen en servicios Python: cuentas, controles
  de intentos, recuperación, verificación excepcional, permisos y transacciones relacionadas.
- [ ] Decidir qué operaciones se concentran en procedimientos y funciones almacenados.
- [ ] Reutilizar o ampliar paquetes existentes antes de crear interfaces duplicadas.
- [ ] Definir contratos de entrada/salida, errores, bloqueo y COMMIT/ROLLBACK por operación.
- [ ] Revisar las consultas complejas para usar vistas y, cuando convenga, SYS_REFCURSOR.
- [ ] Mantener protección de contraseñas, biometría e interfaz en la capa apropiada; no
  trasladar procesamiento a Oracle únicamente para eliminar líneas de Python.
- [ ] Revisar las herramientas de respaldo/restauración y su SQL dinámico técnico, separado
  de las reglas de negocio. Conservar cifrado, autenticidad y manejo seguro de identificadores.

La extracción de consultas a `sql/consultas/` pertenece a la organización del primer
roadmap. **No equivale a trasladar reglas de negocio a Oracle**: esa decisión y su
implementación forman parte de esta segunda etapa.

## Paquetes, disparadores, tablas y vistas

- [ ] Revisar cohesión y permisos de los paquetes de asistencia, auditoría, clases,
  gestión, administración, sesiones y excepciones.
- [ ] Revisar cada disparador y su justificación; evitar repetir validaciones entre
  disparadores, paquetes y aplicación sin una razón explícita.
- [ ] Revisar tablas, tipos, relaciones, restricciones, índices y tratamiento de bajas.
- [ ] Verificar preservación del historial y trazabilidad de cambios administrativos.
- [ ] Revisar vistas de consulta y exposición de campos según el rol.
- [ ] Medir consultas con datos representativos antes de modificar índices o agregaciones.
- [ ] Versionar cambios nuevos posteriores a 008; no reinstalar encima del esquema existente.

## Pruebas y documentación

- [ ] Probar migraciones sobre copias de ensayo y preparar recuperación antes de aplicarlas.
- [ ] Comprobar permisos y reglas desde el backend, además de los controles visuales.
- [ ] Probar regresiones de sesiones, recuperación, asistencia, excepciones y auditoría.
- [ ] Actualizar diccionario de datos, diagrama, justificaciones y ejemplos de SQL/PLSQL.
- [ ] Actualizar el mockup y la memoria académica cuando la nueva edición esté estabilizada.

## Requisito retomado: excepción docente y correo estudiantil

El 22/11 el usuario retoma expresamente el apartado de excepciones en el portal docente
y el envío de la contraseña al correo del estudiante. Solicita recoger el correo en el
registro de alumnos nuevos y permitir añadirlo o cambiarlo desde el perfil de cuentas
existentes, conservándolo en Oracle. Es una demostración académica, no un servicio
oficial de la universidad. Los permisos, la verificación del correo y la entrega deben
implementarse y probarse; todavía no forman parte de la versión publicada.
Detalle: [excepciones y correo](EXCEPCIONES_BIOMETRICAS.md#requisito-retomado-autorización-docente-y-correo).

Este roadmap no está iniciado ni completado por registrar sus tareas. El progreso y las
aceptaciones futuras se anotarán por separado en `CAMBIOS.md` y `FRONTEND.md`.
