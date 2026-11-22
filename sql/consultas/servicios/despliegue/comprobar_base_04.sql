SELECT COUNT(DISTINCT table_name) FROM all_tab_privs
            WHERE table_schema=:esquema AND privilege='EXECUTE'
            AND table_name IN ('PKG_AUDITORIA','PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES','PKG_EXCEPCIONES_DOCENTES')
            AND (grantee=USER OR grantee IN (SELECT role FROM session_roles))
