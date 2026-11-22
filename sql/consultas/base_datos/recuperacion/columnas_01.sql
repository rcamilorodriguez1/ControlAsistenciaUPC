SELECT column_name,data_type,virtual_column,identity_column
        FROM user_tab_cols WHERE table_name=:t AND hidden_column='NO' ORDER BY column_id