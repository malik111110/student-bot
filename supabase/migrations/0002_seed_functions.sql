-- ===============================================
-- SEEDING FUNCTIONS (no real-data embedded)
-- This migration creates SQL functions used by external scripts to import
-- professors, programs and students from JSON payloads. The actual data
-- remains in the `data/` directory and is not embedded here.
-- ===============================================

-- Insert or get field_of_study by code
CREATE OR REPLACE FUNCTION upsert_field_of_study(_code TEXT, _name TEXT, _description TEXT, _department TEXT)
RETURNS UUID AS $$
DECLARE
    fos_id UUID;
BEGIN
    SELECT id INTO fos_id FROM fields_of_study WHERE code = _code;
    IF fos_id IS NULL THEN
        INSERT INTO fields_of_study (name, code, description, department)
        VALUES (_name, _code, _description, _department)
        RETURNING id INTO fos_id;
    END IF;
    RETURN fos_id;
END;
$$ LANGUAGE plpgsql;

-- Insert professor if not exists, return id
CREATE OR REPLACE FUNCTION insert_or_get_professor(_first_name TEXT, _last_name TEXT, _email TEXT)
RETURNS UUID AS $$
DECLARE
    prof_id UUID;
BEGIN
    SELECT id INTO prof_id FROM professors WHERE email = _email;
    IF prof_id IS NULL THEN
        INSERT INTO professors (first_name, last_name, email)
        VALUES (_first_name, _last_name, _email)
        RETURNING id INTO prof_id;
    END IF;
    RETURN prof_id;
END;
$$ LANGUAGE plpgsql;

-- Insert or get program record stored as JSONB (keeps programs flexible)
CREATE OR REPLACE FUNCTION insert_program(_code TEXT, _payload JSONB)
RETURNS UUID AS $$
DECLARE
    p_id UUID;
BEGIN
    -- Insert into the new programs table
    SELECT id INTO p_id FROM programs WHERE code = _code;
    IF p_id IS NULL THEN
        INSERT INTO programs (name, code, description, department, curriculum)
        VALUES (
            (_payload->>'name')::TEXT,
            _code,
            (_payload->>'description')::TEXT,
            COALESCE((_payload->>'department')::TEXT, 'Computer Science'),
            COALESCE((_payload->'curriculum'), '{}'::JSONB)
        ) RETURNING id INTO p_id;
    END IF;
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;

-- Insert student from structured params (keeps sensitive data out of migrations)
CREATE OR REPLACE FUNCTION insert_student_record(
    _student_number TEXT,
    _first_name TEXT,
    _last_name TEXT,
    _email TEXT,
    _field_code TEXT,
    _academic_year INTEGER DEFAULT 1,
    _telegram_id BIGINT DEFAULT NULL,
    _telegram_username TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    s_id UUID;
    fos_id UUID;
BEGIN
    -- resolve field_of_study
    SELECT id INTO fos_id FROM fields_of_study WHERE code = _field_code LIMIT 1;
    IF fos_id IS NULL THEN
        RAISE EXCEPTION 'Unknown field_of_study code: %', _field_code;
    END IF;

    -- avoid duplicate by student_number or email
    IF _student_number IS NOT NULL THEN
        SELECT id INTO s_id FROM students WHERE student_number = _student_number;
    END IF;
    IF s_id IS NULL AND _email IS NOT NULL THEN
        SELECT id INTO s_id FROM students WHERE email = _email;
    END IF;

    IF s_id IS NULL THEN
        INSERT INTO students (student_number, first_name, last_name, email, field_of_study_id, academic_year)
        VALUES (_student_number, _first_name, _last_name, _email, fos_id, _academic_year)
        RETURNING id INTO s_id;
    END IF;
    RETURN s_id;
END;
$$ LANGUAGE plpgsql;

-- Utility RPC to insert a batch of students from JSON array
CREATE OR REPLACE FUNCTION rpc_import_students(_students JSONB)
RETURNS JSONB AS $$
DECLARE
    item JSONB;
    out JSONB := '[]'::JSONB;
    rec JSONB;
    sid UUID;
BEGIN
    FOR item IN SELECT * FROM jsonb_array_elements(_students) LOOP
        sid := insert_student_record(
            (item->>'student_number'),
            (item->>'first_name'),
            (item->>'last_name'),
            (item->>'email'),
            (item->>'field_code'),
            COALESCE((item->>'academic_year')::INTEGER, 1),
            CASE WHEN item ? 'telegram_id' THEN (item->>'telegram_id')::BIGINT ELSE NULL END,
            item->>'telegram_username'
        );
        rec := jsonb_build_object('student_number', item->>'student_number', 'id', sid::TEXT);
        out := out || jsonb_build_array(rec);
    END LOOP;
    RETURN out;
END;
$$ LANGUAGE plpgsql;
