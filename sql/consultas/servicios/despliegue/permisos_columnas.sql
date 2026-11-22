SELECT table_name, column_name, privilege, grantable
FROM all_col_privs WHERE table_schema=:esquema AND grantee=USER
ORDER BY table_name, column_name, privilege
