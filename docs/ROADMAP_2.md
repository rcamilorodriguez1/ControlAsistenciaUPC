# Rama de evolución de UPC Aula

Estado: propuestas posteriores enlazadas desde el [roadmap general](ROADMAP.md).
Acuerdo del 21 de noviembre de 2026: primero completar organización y despliegue de la
versión actual; después mejorar frontend y diseño de la base. Este registro no autoriza
adelantar funcionalidades que el usuario dejó expresamente aplazadas.

## Objetivo

Mejorar la experiencia universitaria y revisar la distribución de responsabilidades entre
Python y Oracle sobre una versión desplegada y comprobada. Los cambios se harán mediante
migraciones nuevas, conservando datos, contratos de acceso y evidencia de las pruebas.

<a id="alternativa-de-alojamiento-vercel-y-render"></a>

## Alojamiento: solo Render

Decisión vigente del 22/11: **se descarta Vercel**. Las pruebas y la presentación
utilizan la aplicación Streamlit completa en Render, con Oracle Autonomous para
los datos. La propuesta anterior de dividir frontend y backend queda cancelada;
no se prepara otra plataforma ni una API para separar las pantallas.

Se conservan las optimizaciones ya aplicadas: fotos originales comprimidas con
miniaturas de presentación, carga diferida y caché de modelos, clasificador de
voz reutilizado y lectura de audio por bloques. No se cambian los píxeles utilizados
para reconocer el rostro ni los criterios de decisión.

El usuario realiza las pruebas de la página, cámara y reconocimiento. Este PC no
tiene cámara; no se intenta confirmar una captura ni se da por validada la biometría
con las pruebas técnicas. Si se estudian recursos, se usarán las métricas del plan
Render existente y resultados aportados por el usuario.

[Evidencia técnica y límites de las optimizaciones](RECONOCIMIENTO.md#uso-de-memoria-de-las-capturas-en-render).

## Interfaz y experiencia de uso

- [ ] Revisar con el usuario las pantallas de los tres roles y cerrar la aceptación pendiente.
- [ ] Refinar tipografía, espaciado, jerarquía, formularios, tablas, mensajes y navegación.
- [ ] El usuario comprobará la página, cámara, reconocimiento y aceptación visual en Render.
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
- [ ] Versionar cambios nuevos posteriores a 009; no reinstalar encima del esquema existente.

## Pruebas y documentación

- [ ] Probar migraciones sobre copias de ensayo y preparar recuperación antes de aplicarlas.
- [ ] Comprobar permisos y reglas desde el backend, además de los controles visuales.
- [ ] Probar regresiones de sesiones, recuperación, asistencia, excepciones y auditoría.
- [ ] Actualizar diccionario de datos, diagrama, justificaciones y ejemplos de SQL/PLSQL.
- [ ] Actualizar el mockup y la memoria académica cuando la nueva edición esté estabilizada.

## Excepción docente: requisito trasladado a la rama vigente

La autorización docente y entrega manual se desarrollan en [FB6](ROADMAP_FRONT_BACK.md).
La decisión posterior del 22/11 sustituye el correo por una clave entregada personalmente;
no se requiere proveedor de correo ni registrar direcciones para este flujo.
Véase [excepciones biométricas](EXCEPCIONES_BIOMETRICAS.md).
