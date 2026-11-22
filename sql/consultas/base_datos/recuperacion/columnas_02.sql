SELECT i.column_name,i.generation_type,s.last_number,s.increment_by
        FROM user_tab_identity_cols i JOIN user_sequences s ON s.sequence_name=i.sequence_name WHERE i.table_name=:t