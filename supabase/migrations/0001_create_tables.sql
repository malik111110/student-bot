-- ===============================================
-- PRODUCTION DATABASE MIGRATION V1.0
-- InfoSec Bot - Complete University Management System
-- ===============================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "unaccent"; -- For accent-insensitive search
CREATE EXTENSION IF NOT EXISTS btree_gist; -- required for EXCLUDE USING GIST on non-geometric types

-- ===============================================
-- CORE ACADEMIC STRUCTURE
-- ===============================================

-- Fields of Study (Information Security, Data Science, etc.)
CREATE TABLE fields_of_study (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE, -- 'INFOSEC', 'DATASCI', etc.
    description TEXT,
    duration_years INTEGER DEFAULT 2, -- Master duration
    total_credits INTEGER DEFAULT 120,
    department TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Academic Years and Semesters
CREATE TABLE academic_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL, -- '2025-2026'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    
    -- NOTE: CHECK constraints cannot contain subqueries in PostgreSQL. We
    -- enforce that at most one row can have is_current = TRUE using a
    -- partial unique index after the table is created.
);

-- Ensure only one academic period can be marked as current. This uses a
-- partial unique index on the boolean column for rows where it is TRUE.
CREATE UNIQUE INDEX IF NOT EXISTS unique_academic_period_current
    ON academic_periods ((is_current))
    WHERE is_current = TRUE;

CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    academic_period_id UUID REFERENCES academic_periods(id) ON DELETE CASCADE,
    name TEXT NOT NULL, -- 'Fall 2024', 'Spring 2025'
    semester_number INTEGER CHECK (semester_number IN (1, 2)), -- 1 = Fall, 2 = Spring
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(academic_period_id, semester_number)
);

-- ===============================================
-- USER MANAGEMENT
-- ===============================================

-- Students Table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_number TEXT UNIQUE, -- University student ID
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    
    -- Academic Information
    field_of_study_id UUID NOT NULL REFERENCES fields_of_study(id),
    academic_year INTEGER NOT NULL CHECK (academic_year IN (1, 2)), -- M1, M2
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_graduation_date DATE,
    
    -- Bot Integration
    telegram_id BIGINT UNIQUE,
    telegram_username TEXT,
    preferred_language TEXT DEFAULT 'fr' CHECK (preferred_language IN ('fr', 'ar', 'en')),
    
    -- Status Management
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'graduated', 'dropped', 'on_leave')),
    warning_count INTEGER DEFAULT 0 CHECK (warning_count >= 0),
    
    -- Activity Tracking
    last_active TIMESTAMP WITH TIME ZONE,
    join_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Professors Table
CREATE TABLE professors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    -- Professional Information
    title TEXT DEFAULT 'Professor' CHECK (title IN ('Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer', 'Doctor')),
    department TEXT NOT NULL DEFAULT 'Computer Science',
    office_location TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===============================================
-- COURSE MANAGEMENT
-- ===============================================

-- Courses (Master level subjects)
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE, -- 'INFOSEC501', 'CRYPTO301'
    name TEXT NOT NULL,
    description TEXT,
    
    -- Academic Details
    credits INTEGER NOT NULL DEFAULT 3 CHECK (credits > 0),
    hours_per_week INTEGER DEFAULT 3 CHECK (hours_per_week > 0),
    course_type TEXT DEFAULT 'core' CHECK (course_type IN ('core', 'elective', 'project', 'internship')),
    
    -- Prerequisites
    prerequisite_courses UUID[], -- Array of course IDs
    
    -- Field Association
    field_of_study_id UUID NOT NULL REFERENCES fields_of_study(id),
    academic_year INTEGER NOT NULL CHECK (academic_year IN (1, 2)), -- M1, M2
    semester INTEGER NOT NULL CHECK (semester IN (1, 2)), -- Fall, Spring
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Course Assignments (Professor -> Course mapping)
CREATE TABLE course_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    professor_id UUID NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    
    -- Assignment Details
    role TEXT DEFAULT 'instructor' CHECK (role IN ('instructor', 'co_instructor', 'assistant')),
    max_students INTEGER DEFAULT 50,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    assigned_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(course_id, professor_id, semester_id)
);

-- Student Enrollments
CREATE TABLE student_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_assignment_id UUID NOT NULL REFERENCES course_assignments(id) ON DELETE CASCADE,
    
    -- Enrollment Details
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'completed', 'failed', 'withdrawn')),
    
    -- Final Grade
    final_grade DECIMAL(4,2), -- 0.00 to 20.00
    grade_letter TEXT CHECK (grade_letter IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    
    UNIQUE(student_id, course_assignment_id)
);

-- ===============================================
-- SCHEDULE MANAGEMENT
-- ===============================================

-- Time Slots for scheduling
CREATE TABLE time_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60
    ) STORED,
    
    CHECK (end_time > start_time)
);

-- Classrooms
CREATE TABLE classrooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE, -- 'Lab 1', 'Amphitheater A'
    building TEXT,
    floor INTEGER,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    
    -- Equipment
    has_projector BOOLEAN DEFAULT FALSE,
    has_computers BOOLEAN DEFAULT FALSE,
    computer_count INTEGER DEFAULT 0,
    is_lab BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Programs table (separate from fields_of_study)
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    department TEXT NOT NULL DEFAULT 'Computer Science',
    curriculum JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Class Sessions (Individual class meetings)
CREATE TABLE class_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_assignment_id UUID NOT NULL REFERENCES course_assignments(id) ON DELETE CASCADE,
    classroom_id UUID REFERENCES classrooms(id),
    
    -- Scheduling
    session_date DATE NOT NULL,
    time_slot_id UUID NOT NULL REFERENCES time_slots(id),
    
    -- Session Details
    session_type TEXT DEFAULT 'lecture' CHECK (session_type IN ('lecture', 'lab', 'tutorial', 'exam', 'project_defense')),
    title TEXT,
    description TEXT,
    
    -- Recurring Pattern
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern TEXT CHECK (recurrence_pattern IN ('weekly', 'biweekly', 'monthly') OR recurrence_pattern IS NULL),
    recurrence_end_date DATE,
    
    -- Status
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'postponed')),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure no double booking of classroom
    CONSTRAINT no_double_booking EXCLUDE USING GIST (
        classroom_id WITH =,
        session_date WITH =,
        time_slot_id WITH =
    ) WHERE (status != 'cancelled')
);

-- ===============================================
-- ASSESSMENT MANAGEMENT
-- ===============================================

-- Assessment Types and Grading
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_assignment_id UUID NOT NULL REFERENCES course_assignments(id) ON DELETE CASCADE,
    
    -- Assessment Details
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL CHECK (type IN ('exam', 'quiz', 'assignment', 'project', 'presentation', 'lab_work', 'midterm', 'final')),
    
    -- Grading
    total_points DECIMAL(6,2) NOT NULL CHECK (total_points > 0),
    weight_percentage DECIMAL(5,2) DEFAULT 10.00 CHECK (weight_percentage BETWEEN 0 AND 100),
    
    -- Scheduling
    due_date TIMESTAMP WITH TIME ZONE,
    start_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Instructions
    instructions TEXT,
    submission_format TEXT, -- 'pdf', 'code', 'presentation', etc.
    
    -- Status
    is_published BOOLEAN DEFAULT FALSE,
    allow_late_submission BOOLEAN DEFAULT FALSE,
    late_penalty_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual Student Results
CREATE TABLE student_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    
    -- Scores
    raw_score DECIMAL(6,2) CHECK (raw_score >= 0),
    -- percentage_score computed from raw_score and assessment.total_points.
    -- Cannot use subqueries in generated column expressions in PostgreSQL,
    -- so store it as a normal column and compute/update it via application
    -- logic or a trigger if desired.
    percentage_score DECIMAL(5,2),
    
    -- Submission Details
    submitted_at TIMESTAMP WITH TIME ZONE,
    submission_file_path TEXT,
    is_late BOOLEAN DEFAULT FALSE,
    
    -- Grading
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by UUID REFERENCES professors(id),
    feedback TEXT,
    
    -- Notifications
    student_notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(student_id, assessment_id)
);

-- ===============================================
-- EVENT MANAGEMENT
-- ===============================================

-- Events (Conferences, Workshops, Deadlines, etc.)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    
    -- Event Classification
    event_type TEXT NOT NULL CHECK (event_type IN ('lecture', 'exam', 'workshop', 'conference', 'social', 'deadline', 'announcement', 'meeting', 'defense')),
    category TEXT DEFAULT 'general' CHECK (category IN ('academic', 'social', 'administrative', 'general', 'urgent')),
    
    -- Timing
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN end_date IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (end_date - start_date)) / 60
            ELSE NULL
        END
    ) STORED,
    
    -- Location
    location TEXT,
    classroom_id UUID REFERENCES classrooms(id),
    is_online BOOLEAN DEFAULT FALSE,
    meeting_url TEXT,
    
    -- Audience
    field_of_study_id UUID REFERENCES fields_of_study(id), -- NULL = all fields
    academic_year INTEGER CHECK (academic_year IN (1, 2)), -- NULL = all years
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Registration
    requires_registration BOOLEAN DEFAULT FALSE,
    max_participants INTEGER,
    registration_deadline TIMESTAMP WITH TIME ZONE,
    
    -- Organization
    created_by UUID REFERENCES professors(id),
    organizer_name TEXT,
    organizer_email TEXT,
    
    -- Status
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'ongoing', 'completed', 'cancelled', 'postponed')),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event Participants (for registration-required events)
CREATE TABLE event_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES professors(id) ON DELETE CASCADE,
    
    -- Registration Details
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'registered' CHECK (status IN ('registered', 'attended', 'no_show', 'cancelled')),
    
    -- Contact Info (for external participants)
    external_participant_name TEXT,
    external_participant_email TEXT,
    
    -- Metadata
    attended_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    UNIQUE(event_id, student_id),
    UNIQUE(event_id, professor_id),
    
    -- Ensure either student_id or professor_id or external participant info is provided
    CHECK (
        (student_id IS NOT NULL AND professor_id IS NULL) OR
        (student_id IS NULL AND professor_id IS NOT NULL) OR
        (student_id IS NULL AND professor_id IS NULL AND external_participant_name IS NOT NULL)
    )
);

-- ===============================================
-- BOT PERSONALITY & INTERACTIONS
-- ===============================================

-- User Profiles for Bot Personalization
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    
    -- Personal Preferences
    nickname TEXT,
    preferred_name TEXT, -- How they like to be addressed
    preferred_communication_style TEXT DEFAULT 'formal' CHECK (preferred_communication_style IN ('formal', 'casual', 'friendly', 'mentor')),
    
    -- Personality Insights (JSON for flexibility)
    personality_traits JSONB DEFAULT '{}',
    interests TEXT[],
    study_habits JSONB DEFAULT '{}',
    
    -- Engagement Metrics
    friendship_level INTEGER DEFAULT 0 CHECK (friendship_level BETWEEN 0 AND 100),
    interaction_count INTEGER DEFAULT 0,
    help_requests_count INTEGER DEFAULT 0,
    achievements_earned INTEGER DEFAULT 0,
    
    -- Notification Preferences
    notification_preferences JSONB DEFAULT '{
        "grades": true,
        "events": true,
        "reminders": true,
        "achievements": true,
        "study_groups": true
    }',
                    preferred_notification_times TIME[] DEFAULT ARRAY['09:00:00'::time, '14:00:00'::time, '20:00:00'::time],
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student Memory System (for bot conversations)
CREATE TABLE student_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Memory Classification
    memory_type TEXT NOT NULL CHECK (memory_type IN ('personal', 'academic', 'social', 'goal', 'problem', 'achievement', 'preference')),
    key_info TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    
    -- Importance and Freshness
    importance_score INTEGER DEFAULT 5 CHECK (importance_score BETWEEN 1 AND 10),
    last_referenced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reference_count INTEGER DEFAULT 1,
    
    -- Expiry
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===============================================
-- GAMIFICATION SYSTEM
-- ===============================================

-- Achievement Definitions
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon TEXT DEFAULT '🏆',
    
    -- Achievement Details
    category TEXT DEFAULT 'general' CHECK (category IN ('academic', 'social', 'engagement', 'special', 'general')),
    rarity TEXT DEFAULT 'common' CHECK (rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')),
    points INTEGER DEFAULT 10 CHECK (points >= 0),
    
    -- Requirements (JSON for flexibility)
    requirements JSONB NOT NULL DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student Achievement Records
CREATE TABLE student_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    
    -- Achievement Details
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress_data JSONB DEFAULT '{}', -- For tracking progress towards achievement
    
    -- Notification
    notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(student_id, achievement_id)
);

-- ===============================================
-- MODERATION SYSTEM
-- ===============================================

-- Violation Tracking
CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Violation Details
    violation_type TEXT NOT NULL CHECK (violation_type IN ('spam', 'inappropriate_language', 'harassment', 'cheating', 'off_topic', 'disrespectful', 'other')),
    description TEXT NOT NULL,
    severity TEXT DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    
    -- Context
    context_data JSONB DEFAULT '{}', -- Message IDs, chat context, etc.
    reported_by TEXT, -- Professor, bot, peer
    
    -- Resolution
    action_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES professors(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===============================================
-- NOTIFICATION SYSTEM
-- ===============================================

-- Notification Queue
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Recipients
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES professors(id) ON DELETE CASCADE,
    
    -- Content
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('grade', 'event', 'reminder', 'achievement', 'violation', 'general', 'urgent', 'deadline')),
    
    -- Priority and Scheduling
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Delivery
    delivery_method TEXT DEFAULT 'telegram' CHECK (delivery_method IN ('telegram', 'email', 'both')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered BOOLEAN DEFAULT FALSE,
    
    -- User Interaction
    read_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Related Data
    related_table TEXT, -- 'assessments', 'events', etc.
    related_id UUID, -- Foreign key to related record
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure either student_id or professor_id is provided
    CHECK (
        (student_id IS NOT NULL AND professor_id IS NULL) OR
        (student_id IS NULL AND professor_id IS NOT NULL)
    )
);

-- ===============================================
-- INDEXES FOR PERFORMANCE
-- ===============================================

-- Students
CREATE INDEX idx_students_field_of_study ON students(field_of_study_id);
CREATE INDEX idx_students_telegram_id ON students(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX idx_students_status ON students(status);
CREATE INDEX idx_students_academic_year ON students(academic_year);

-- Professors
CREATE INDEX idx_professors_department ON professors(department);

-- Courses
CREATE INDEX idx_courses_field_of_study ON courses(field_of_study_id);
CREATE INDEX idx_courses_academic_year_semester ON courses(academic_year, semester);

-- Enrollments
CREATE INDEX idx_student_enrollments_student_id ON student_enrollments(student_id);
CREATE INDEX idx_student_enrollments_course ON student_enrollments(course_assignment_id);

-- Schedule
CREATE INDEX idx_class_sessions_date ON class_sessions(session_date);
CREATE INDEX idx_class_sessions_course ON class_sessions(course_assignment_id);
CREATE INDEX idx_class_sessions_classroom_date ON class_sessions(classroom_id, session_date);

-- Assessments
CREATE INDEX idx_assessments_course ON assessments(course_assignment_id);
CREATE INDEX idx_assessments_due_date ON assessments(due_date);
CREATE INDEX idx_student_results_student_id ON student_results(student_id);

-- Events
CREATE INDEX idx_events_start_date ON events(start_date);
CREATE INDEX idx_events_field_of_study ON events(field_of_study_id) WHERE field_of_study_id IS NOT NULL;
CREATE INDEX idx_events_type_status ON events(event_type, status);

-- Bot data
CREATE INDEX idx_user_profiles_student_id ON user_profiles(student_id);
CREATE INDEX idx_student_memories_student_id ON student_memories(student_id);
CREATE INDEX idx_student_memories_importance ON student_memories(importance_score DESC);

-- Notifications
CREATE INDEX idx_notifications_student_id ON notifications(student_id) WHERE student_id IS NOT NULL;
CREATE INDEX idx_notifications_scheduled_for ON notifications(scheduled_for);
CREATE INDEX idx_notifications_delivered ON notifications(delivered, scheduled_for);

-- ===============================================
-- TRIGGERS AND FUNCTIONS
-- ===============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_professors_updated_at BEFORE UPDATE ON professors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_class_sessions_updated_at BEFORE UPDATE ON class_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_student_results_updated_at BEFORE UPDATE ON student_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_violations_updated_at BEFORE UPDATE ON violations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment warning count on violations
CREATE OR REPLACE FUNCTION increment_warning_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE students 
    SET warning_count = warning_count + 1 
    WHERE id = NEW.student_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_warnings_on_violation 
    AFTER INSERT ON violations 
    FOR EACH ROW 
    EXECUTE FUNCTION increment_warning_count();

-- Function to auto-create user profile for new students
CREATE OR REPLACE FUNCTION create_user_profile_for_student()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (student_id, preferred_name)
    VALUES (NEW.id, NEW.first_name);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_user_profile_on_student_insert
    AFTER INSERT ON students
    FOR EACH ROW
    EXECUTE FUNCTION create_user_profile_for_student();

-- ===============================================
-- INITIAL DATA SEEDING
-- ===============================================

-- Fields of Study
-- Add the five primary fields requested by the user
INSERT INTO fields_of_study (name, code, description, department) VALUES
('Information Security', 'INFOSEC', 'Master in Information Security and Cybersecurity', 'Computer Science'),
('Intelligence Artificielle', 'AI', 'Master in Artificial Intelligence', 'Computer Science'),
('Data Science', 'DATASCI', 'Master in Data Science and Machine Learning', 'Computer Science'),
('Network and Distributed Systems', 'NDS', 'Master in Network and Distributed Systems', 'Computer Science'),
('Network and Information Systems', 'NIS', 'Master in Network and Information Systems', 'Computer Science')
ON CONFLICT (code) DO NOTHING;

-- Programs (separate records representing curricula)
INSERT INTO programs (name, code, description, department, curriculum) VALUES
('Master - Information Security', 'PRG_INFOSEC', 'Curriculum for Information Security master program', 'Computer Science', '{}'),
('Master - Artificial Intelligence', 'PRG_AI', 'Curriculum for Artificial Intelligence', 'Computer Science', '{}'),
('Master - Data Science', 'PRG_DATASCI', 'Curriculum for Data Science master program', 'Computer Science', '{}'),
('Master - Network and Distributed Systems', 'PRG_NDS', 'Curriculum for Network and Distributed Systems', 'Computer Science', '{}'),
('Master - Network and Information Systems', 'PRG_NIS', 'Curriculum for Network and Information Systems', 'Computer Science', '{}')
ON CONFLICT (code) DO NOTHING;

-- Current Academic Period
INSERT INTO academic_periods (name, start_date, end_date, is_current) VALUES
('2025-2026', '2025-09-01', '2026-06-30', TRUE);

-- Semesters for current period
INSERT INTO semesters (academic_period_id, name, semester_number, start_date, end_date, is_current)
SELECT 
    ap.id,
    'Fall 2025',
    1,
    '2025-09-01',
    '2026-01-31',
    TRUE
FROM academic_periods ap WHERE ap.is_current = TRUE;

INSERT INTO semesters (academic_period_id, name, semester_number, start_date, end_date)
SELECT 
    ap.id,
    'Spring 2026',
    2,
    '2026-02-01',
    '2026-06-30'
FROM academic_periods ap WHERE ap.is_current = TRUE;

-- Time Slots
INSERT INTO time_slots (start_time, end_time) VALUES
('08:30', '10:00'),
('10:00', '11:30'),
('11:30', '13:00'),
('14:00', '15:30'),
('15:30', '17:00');

-- (Classrooms are initialized above using batch inserts to create A1..A8, B1..B8,
-- TP labs, conference rooms and libraries.)

-- Labs (TP) two per building: A_TP1..A_TP2 and B_TP1..B_TP2
INSERT INTO classrooms (name, building, capacity, has_projector, has_computers, is_lab)
SELECT name, building, 30, TRUE, TRUE, TRUE FROM (
    SELECT 'A_TP' || g AS name, 'A' AS building FROM generate_series(1,2) g
    UNION ALL
    SELECT 'B_TP' || g AS name, 'B' AS building FROM generate_series(1,2) g
) s;

-- Conference rooms and libraries: one per building
INSERT INTO classrooms (name, building, capacity, has_projector, has_computers, is_lab) VALUES
('Conference Room A', 'A', 120, TRUE, FALSE, FALSE),
('Library A', 'A', 300, TRUE, FALSE, FALSE),
('Conference Room B', 'B', 120, TRUE, FALSE, FALSE),
('Library B', 'B', 300, TRUE, FALSE, FALSE);

-- Sample Achievements
INSERT INTO achievements (name, description, icon, category, rarity, points, requirements) VALUES
('First Steps', 'Joined the InfoSec family!', '👋', 'engagement', 'common', 10, '{"action": "join"}'),
('Early Bird', 'Active before 8 AM consistently for a week', '🌅', 'engagement', 'uncommon', 25, '{"early_messages": 7, "before_time": "08:00"}'),
('Night Owl', 'Active after 11 PM consistently for a week', '🦉', 'engagement', 'uncommon', 25, '{"late_messages": 7, "after_time": "23:00"}'),
('Helpful Soul', 'Helped 10 classmates with their questions', '🤝', 'social', 'rare', 50, '{"help_count": 10}'),
('Perfect Attendance', 'Never missed a class this month', '📚', 'academic', 'rare', 75, '{"attendance_rate": 1.0, "duration": "monthly"}'),
('Security Expert', 'Scored above 18/20 in all security assessments', '🔒', 'academic', 'epic', 100, '{"min_grade": 18, "subject": "security"}'),
('Social Butterfly', 'Most active in group discussions for a week', '🦋', 'social', 'uncommon', 30, '{"top_participant": true, "duration": "weekly"}'),
('Problem Solver', 'Solved 5 complex technical challenges', '🧩', 'academic', 'rare', 40, '{"complex_solutions": 5}');