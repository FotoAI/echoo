-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database if not exists (this runs automatically in docker-compose)
-- The database is already created by the POSTGRES_DB environment variable