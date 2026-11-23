# Documento como identificación estudiantil — 011

El estudiante utiliza tipo y número de documento (CC, TI, CE o PA). El código
institucional deja de solicitarse en registro, perfil, acceso académico y alta
administrativa. El ID automático permanece como clave interna de las relaciones.

## Registro y cuentas existentes

Las altas públicas requieren nombre, documento y una muestra facial validada.
`PKG_GESTION.REGISTRAR_ESTUDIANTE` inserta cuenta y documento en la misma transacción.
Un documento duplicado revierte toda el alta, sin dejar una segunda cuenta parcial.

Las cuentas anteriores conservan ID, códigos históricos, matrículas, asistencias y
autorizaciones. No se interpreta un código antiguo como documento, aunque sea numérico.
El alumno puede entrar con su rostro y completar **Mi perfil → Configuración de mi
documento**. Gestión académica puede hacerlo en **Cuentas → Estudiante → Guardar
documento del estudiante**, comprobando la correspondencia de la identidad.

El perfil, los selectores docentes y las listas muestran el documento enmascarado.
Solo se conserva HMAC del tipo/número y los últimos cuatro caracteres en
VERIFICACION_ESTUDIANTES, también para alumnos sin excepción. El perfil guardado
en sesión y los eventos no incluyen el número completo; los formularios lo reciben
temporalmente para validarlo. La clave HMAC original se conserva.

## Acceso y cambios

El acceso excepcional normal sigue requiriendo documento, contraseña y autorización
vigente. El modo académico temporal pide el mismo documento y la clave común; no
requiere autorización excepcional individual. Se retiran las alternativas de código
institucional e ID de su formulario y backend. El alumno debe tener el documento
asociado previamente; no se puede identificar una cuenta cuyo documento se desconoce.

Completar/corregir documento exige sesión propia o administrativa, confirmación y
versión actual. La operación comprueba unicidad, revoca sesiones y la credencial
excepcional anterior y genera DOCUMENTO_ACTUALIZADO sin número completo. Las clases
y resultados no cambian. Un guardado idéntico conserva la versión y autorización.

El docente y Administración deben autorizar excepciones con el documento registrado.
Si hay una discrepancia, primero se corrige desde el perfil o Cuentas; una autorización
no sobrescribe silenciosamente la identidad anterior.

## Oracle y publicación

La migración 011 actualiza cuatro paquetes existentes y conserva 14 tablas, 140
columnas y 11 FK. No concede nuevos permisos al runtime: siguen siendo 53, y la
conexión administrativa sigue restringida a sus cinco paquetes y tres vistas.
El instalador/migradores y el preflight incluyen 001–011. No se vacían tablas.

Oracle local (XEPDB1) y Autonomous (UPCAula, usada por Render) son bases independientes.
Cada una tiene sus datos y configuración; un push no sincroniza filas entre ellas.
Se aplica la migración con respaldo cifrado previo en cada destino.

Las pruebas de página, cámara y reconocimiento quedan al usuario. El material PDF
009 conserva su edición histórica; esta guía documenta el comportamiento 011.
