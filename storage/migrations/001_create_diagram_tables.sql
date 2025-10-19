-- =====================================================
-- Diagram Microservice v2 - Database Schema
-- =====================================================
-- This migration creates tables for storing diagram metadata
-- and caching information in Supabase PostgreSQL.
--
-- Run this in your Supabase SQL editor to set up the schema.
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Generated Diagrams Table
-- =====================================================
-- Stores metadata for all generated diagrams
CREATE TABLE IF NOT EXISTS generated_diagrams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    diagram_type TEXT NOT NULL,
    url TEXT NOT NULL, -- Supabase Storage URL
    generation_method TEXT NOT NULL CHECK (
        generation_method IN ('svg_template', 'mermaid', 'python_chart', 'custom')
    ),
    request_params JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    generation_time_ms INTEGER,
    tokens_used INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_session_id 
    ON generated_diagrams(session_id);
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_user_id 
    ON generated_diagrams(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_type 
    ON generated_diagrams(diagram_type);
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_created_at 
    ON generated_diagrams(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_method 
    ON generated_diagrams(generation_method);
CREATE INDEX IF NOT EXISTS idx_generated_diagrams_user_type 
    ON generated_diagrams(user_id, diagram_type);

-- Add comment
COMMENT ON TABLE generated_diagrams IS 'Stores metadata for all generated diagrams with URLs to Supabase Storage';

-- =====================================================
-- Diagram Cache Table
-- =====================================================
-- Caches diagram lookups for reuse
CREATE TABLE IF NOT EXISTS diagram_cache (
    cache_key TEXT PRIMARY KEY,
    diagram_id UUID REFERENCES generated_diagrams(id) ON DELETE CASCADE,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Index for cache cleanup
CREATE INDEX IF NOT EXISTS idx_diagram_cache_expires 
    ON diagram_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_diagram_cache_last_accessed 
    ON diagram_cache(last_accessed DESC);

-- Add comment
COMMENT ON TABLE diagram_cache IS 'Caches diagram requests for faster retrieval';

-- =====================================================
-- Diagram Sessions Table (Optional)
-- =====================================================
-- Tracks diagram generation sessions
CREATE TABLE IF NOT EXISTS diagram_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    diagram_count INTEGER DEFAULT 0,
    total_generation_time_ms INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    closed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_diagram_sessions_user_id 
    ON diagram_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_diagram_sessions_created_at 
    ON diagram_sessions(created_at DESC);

-- Add comment
COMMENT ON TABLE diagram_sessions IS 'Tracks diagram generation sessions for analytics';

-- =====================================================
-- Update Triggers
-- =====================================================
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for generated_diagrams
DROP TRIGGER IF EXISTS update_generated_diagrams_updated_at ON generated_diagrams;
CREATE TRIGGER update_generated_diagrams_updated_at 
    BEFORE UPDATE ON generated_diagrams
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for diagram_sessions
DROP TRIGGER IF EXISTS update_diagram_sessions_updated_at ON diagram_sessions;
CREATE TRIGGER update_diagram_sessions_updated_at 
    BEFORE UPDATE ON diagram_sessions
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Row Level Security (RLS)
-- =====================================================
-- Enable RLS on tables
ALTER TABLE generated_diagrams ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagram_sessions ENABLE ROW LEVEL SECURITY;

-- Policies for generated_diagrams
CREATE POLICY "Users can view own diagrams" ON generated_diagrams
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can create own diagrams" ON generated_diagrams
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own diagrams" ON generated_diagrams
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own diagrams" ON generated_diagrams
    FOR DELETE USING (auth.uid()::text = user_id);

-- Policies for diagram_sessions
CREATE POLICY "Users can view own sessions" ON diagram_sessions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can create own sessions" ON diagram_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own sessions" ON diagram_sessions
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Cache policies (cache is shared but linked to user diagrams)
CREATE POLICY "Users can view cache for own diagrams" ON diagram_cache
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM generated_diagrams 
            WHERE generated_diagrams.id = diagram_cache.diagram_id 
            AND generated_diagrams.user_id = auth.uid()::text
        )
    );

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_diagram_stats(p_user_id TEXT)
RETURNS TABLE (
    total_diagrams BIGINT,
    unique_types BIGINT,
    total_generation_time_ms BIGINT,
    cache_hit_rate FLOAT,
    most_used_type TEXT,
    most_used_method TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_diagrams,
        COUNT(DISTINCT diagram_type)::BIGINT as unique_types,
        SUM(generation_time_ms)::BIGINT as total_generation_time_ms,
        AVG(CASE WHEN cache_hit THEN 1.0 ELSE 0.0 END)::FLOAT as cache_hit_rate,
        MODE() WITHIN GROUP (ORDER BY diagram_type) as most_used_type,
        MODE() WITHIN GROUP (ORDER BY generation_method) as most_used_method
    FROM generated_diagrams
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM diagram_cache 
    WHERE expires_at < TIMEZONE('utc', NOW());
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Storage Bucket Creation (Run via Supabase Dashboard)
-- =====================================================
-- Note: Storage bucket creation should be done via Supabase dashboard
-- or using the Storage API. The SQL below is for reference:
--
-- INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
-- VALUES (
--     'diagrams',
--     'diagrams', 
--     true,
--     5242880, -- 5MB limit
--     ARRAY['image/svg+xml']::text[]
-- );

-- =====================================================
-- Sample Data (Optional - for testing)
-- =====================================================
-- Uncomment to insert sample data for testing

-- INSERT INTO generated_diagrams (
--     session_id, user_id, diagram_type, url, generation_method, 
--     request_params, metadata, quality_score, generation_time_ms
-- ) VALUES (
--     'test-session-001',
--     'test-user-001',
--     'cycle_3_step',
--     'https://example.supabase.co/storage/v1/object/public/diagrams/test.svg',
--     'svg_template',
--     '{"content": "Step 1\nStep 2\nStep 3", "theme": {"primaryColor": "#3B82F6"}}'::JSONB,
--     '{"template_used": "cycle_3_step.svg"}'::JSONB,
--     0.95,
--     150
-- );

-- =====================================================
-- Grants (if needed for service role)
-- =====================================================
GRANT ALL ON generated_diagrams TO service_role;
GRANT ALL ON diagram_cache TO service_role;
GRANT ALL ON diagram_sessions TO service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO service_role;