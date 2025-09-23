-- Production Database Setup for Echoo API
-- Run this script in your production PostgreSQL database
-- Commands to copy and paste into psql

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    selfie_url VARCHAR(500),
    selfie_cid VARCHAR(100),
    instagram_url VARCHAR(200),
    twitter_url VARCHAR(200),
    linkedin_url VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Images table (with nullable user_id)
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER,  -- Nullable for event-only images
    fotoowl_id INTEGER,
    fotoowl_url VARCHAR(500),
    filecoin_url VARCHAR(500),
    filecoin_cid VARCHAR(100),
    size INTEGER,
    description TEXT,
    image_encoding VARCHAR(50),
    event_id INTEGER,
    description_vector vector(512),  -- pgvector for description embeddings
    image_vector vector(512),        -- pgvector for image embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint (nullable)
    CONSTRAINT fk_images_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    fotoowl_event_id INTEGER UNIQUE NOT NULL,
    fotoowl_event_key VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_url VARCHAR(500),
    event_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Event Request Mapping table
CREATE TABLE IF NOT EXISTS event_request_mapping (
    id SERIAL PRIMARY KEY,
    fotoowl_event_id INTEGER NOT NULL,
    request_id INTEGER NOT NULL,
    request_key VARCHAR(100),
    user_id INTEGER NOT NULL,
    redirect_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_event_mapping_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_event_mapping_event FOREIGN KEY (fotoowl_event_id) REFERENCES events(fotoowl_event_id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate registrations
    CONSTRAINT unique_user_event UNIQUE (user_id, fotoowl_event_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id);
CREATE INDEX IF NOT EXISTS idx_images_fotoowl_id ON images(fotoowl_id);
CREATE INDEX IF NOT EXISTS idx_images_event_id ON images(event_id);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);
CREATE INDEX IF NOT EXISTS idx_events_fotoowl_event_id ON events(fotoowl_event_id);
CREATE INDEX IF NOT EXISTS idx_event_mapping_user_id ON event_request_mapping(user_id);
CREATE INDEX IF NOT EXISTS idx_event_mapping_fotoowl_event_id ON event_request_mapping(fotoowl_event_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_images_updated_at ON images;
CREATE TRIGGER update_images_updated_at 
    BEFORE UPDATE ON images 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify tables were created successfully
\dt

-- Show table structures
\d users
\d images
\d events
\d event_request_mapping

-- Show indexes
\di

COPY (
SELECT 
    'Database setup completed successfully!' as status,
    COUNT(*) FILTER (WHERE table_name = 'users') as users_table,
    COUNT(*) FILTER (WHERE table_name = 'images') as images_table,
    COUNT(*) FILTER (WHERE table_name = 'events') as events_table,
    COUNT(*) FILTER (WHERE table_name = 'event_request_mapping') as mapping_table
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'images', 'events', 'event_request_mapping')
) TO STDOUT WITH CSV HEADER;

-- Final verification query
SELECT 
    schemaname,
    tablename,
    hasindexes,
    hastriggers
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'images', 'events', 'event_request_mapping')
ORDER BY tablename;