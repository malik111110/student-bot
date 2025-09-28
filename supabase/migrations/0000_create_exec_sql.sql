CREATE OR REPLACE FUNCTION exec_sql(sql_string TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE sql_string;
END;
$$ LANGUAGE plpgsql;