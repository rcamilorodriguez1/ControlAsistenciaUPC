SELECT table_name, privilege, grantable
FROM all_tab_privs WHERE table_schema=:esquema AND grantee=USER
ORDER BY table_name, privilege
