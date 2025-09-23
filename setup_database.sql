-- FotoOwl Database Setup Script
-- Run this script in your local PostgreSQL to set up the database

-- Create database (uncomment if you need to create the database)
-- CREATE DATABASE fotoowl_db;

-- Connect to the database
\c fotoowl_db;

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- The tables will be created automatically by the FastAPI application
-- when it starts up using SQLAlchemy

-- Optional: Create a user specifically for this application (uncomment if needed)
-- CREATE USER fotoowl_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE fotoowl_db TO fotoowl_user;

COMMENT ON DATABASE fotoowl_db IS 'FotoOwl application database with vector search capabilities';