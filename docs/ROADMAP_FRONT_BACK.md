# Rama: frontend y backend

Depende del [roadmap general](ROADMAP.md). Solicitudes del 22/11/2026.

| ID | Tarea y criterio de cierre | Estado |
| --- | --- | --- |
| FB1 | Retirar #ID del selector; separar selección por docente/materia; conservar clases e historial | Implementado; 2 pruebas aisladas aprobadas |
| FB2 | Mover archivo de cuenta/materias a Configuración del docente; exigir su sesión | Implementado; navegación y sesión comprobadas |
| FB3 | Publicar los tres estudiantes y el docente indicados en el pie, con ajuste móvil | Implementado; revisión visual móvil |
| FB4 | Perfil docente privado: todas sus materias, agenda mensual y próximas clases persistidas | Implementado; 5 pruebas; consulta compilada en Autonomous |
| FB5 | Diferenciar portal de operaciones, perfil académico y configuración; acceso desde el menú de cuenta | Implementado; 8 pruebas de navegación |
| FB6 | Autorizar/renovar/revocar contraseña alternativa por docente para alumnos de sus materias, con vigencia, auditoría y entrega manual | Implementado; Oracle local y Autonomous 009 verificados |
| FB7 | Quitar iconos de ancla de encabezados manteniendo títulos y enlaces de navegación | Implementado; enlaces nativos de Inicio disponibles |

## Criterios transversales

- Separación de datos por identidad validada en servidor y pertenencia comprobada
  en Oracle; una URL o un selector no otorgan acceso a otra cuenta.
- El calendario refleja clases creadas. Un horario pendiente no confirma asistencia
  ni genera automáticamente clases semanales.
- Excepciones: contraseña protegida mediante hash, documento comprobado, caducidad,
  control de versiones, invalidación de sesiones y revocación. Sin correo automático.
- Pruebas de cambios de materia/rol, navegación, calendario vacío, meses sin clases,
  contenido escapado y permisos. Revisar escritorio y móvil con datos sintéticos.
- Implementación verificada no implica aceptación del usuario en producción.
