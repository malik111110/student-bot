-- Sample migration for testing validation
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(64),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- test note: curriculum will be stored as JSONB
    curriculum JSONB
);

-- Test note: this constraint won't affect column validation
ALTER TABLE programs ADD CONSTRAINT programs_code_key UNIQUE (code);