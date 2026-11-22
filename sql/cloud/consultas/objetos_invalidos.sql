SELECT object_name, object_type, status FROM user_objects
WHERE status <> 'VALID' ORDER BY object_type, object_name;
