# Segundo roadmap de UPC Aula

Estado: registrado para después del cierre del [primer roadmap](ROADMAP.md).
Acuerdo del 21 de noviembre de 2026: primero completar organización y despliegue de la
versión actual; después mejorar frontend y diseño de la base. Este registro no autoriza
adelantar funcionalidades que el usuario dejó expresamente aplazadas.

## Objetivo

Mejorar la experiencia universitaria y revisar la distribución de responsabilidades entre
Python y Oracle sobre una versión desplegada y comprobada. Los cambios se harán mediante
migraciones nuevas, conservando datos, contratos de acceso y evidencia de las pruebas.

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

## Requisitos que siguen aplazados

La entrega de la contraseña alternativa del estudiante por correo a través del profesor,
con una dinámica similar a `ALTA_DOCENTE`, continúa registrada sin implementar. Su flujo,
vigencia, recuperación y canal se definirán cuando se retome expresamente ese requisito.

Este roadmap no está iniciado ni completado por registrar sus tareas. El progreso y las
aceptaciones futuras se anotarán por separado en `CAMBIOS.md` y `FRONTEND.md`.
