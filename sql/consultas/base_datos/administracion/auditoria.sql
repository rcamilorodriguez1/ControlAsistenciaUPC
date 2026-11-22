BEGIN {esquema}.pkg_administracion.auditoria(:tipo,
                TO_TIMESTAMP_TZ(:desde,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),
                TO_TIMESTAMP_TZ(:hasta,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),:limite,:salida); END;
