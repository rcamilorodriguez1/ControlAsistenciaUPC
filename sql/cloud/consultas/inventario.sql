SELECT object_type, COUNT(*) AS cantidad FROM user_objects
WHERE object_type IN ('TABLE','VIEW','TRIGGER','PACKAGE','PACKAGE BODY')
GROUP BY object_type ORDER BY object_type;
