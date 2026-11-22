# Perfil y configuración del docente

El menú **Docente → Mi perfil** abre `/mi-perfil-docente`. La identidad se toma de
la sesión validada en servidor. La consulta contrasta ese actor con el contexto
Oracle; la dirección no permite elegir otro profesor.

- **Portal docente:** tomar asistencia, crear/compartir materias, revisar registros
  y gestionar excepciones de acceso.
- **Mi perfil:** identidad, catálogo propio completo (incluidas materias archivadas),
  calendario mensual, detalle diario y próximas diez sesiones. Las demás se consultan
  cambiando el mes. Los horarios se muestran en hora de Colombia.
- **Configuración:** archivo de materias y cuenta, con motivo y confirmación.
  El archivo conserva el historial; no es eliminación física.

Una clase futura aparece solo después de crear su fecha y hora. El calendario no
deduce una recurrencia semanal ni convierte una clase pendiente en asistencia. Las
clases confirmadas se distinguen de las programadas y de las pendientes del pasado.

El estudiante usa el portal para inscribirse/retirarse de materias y su perfil para
consultar asistencia, porcentajes y calendario histórico. El docente usa una agenda
con portada y lista de sesiones propias, sin el indicador personal de asistencia del
alumno. La repetición del nombre de una materia sirve a tareas diferentes en cada vista.

Verificación: 5 pruebas de perfil, 8 de navegación y revisión con datos sintéticos en
Orca; consulta compilada en Autonomous. La aceptación visual final corresponde al
usuario en Render. La ruta de configuración exige de nuevo la sesión docente activa.
