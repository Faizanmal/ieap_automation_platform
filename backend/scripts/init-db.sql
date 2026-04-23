-- Database initialization script
-- This runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional users if needed (optional)
-- CREATE USER ieap_readonly WITH PASSWORD 'readonly_password';
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO ieap_readonly;

-- Create indexes for full-text search (optional, for production optimization)
-- CREATE INDEX IF NOT EXISTS idx_users_email_trgm ON users USING gin (email gin_trgm_ops);
