-- =================================================================
-- PRODUCTION DATABASE SETUP - ECHOO API
-- Copy and paste these commands into your production psql terminal
-- =================================================================

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create Users table
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

-- Step 3: Create Images table (with nullable user_id)
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER,
    fotoowl_id INTEGER,
    fotoowl_url VARCHAR(500),
    filecoin_url VARCHAR(500),
    filecoin_cid VARCHAR(100),
    size INTEGER,
    description TEXT,
    image_encoding VARCHAR(50),
    event_id INTEGER,
    description_vector vector(512),
    image_vector vector(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_images_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Step 4: Create Events table
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

-- Step 5: Create Event Request Mapping table
CREATE TABLE IF NOT EXISTS event_request_mapping (
    id SERIAL PRIMARY KEY,
    fotoowl_event_id INTEGER NOT NULL,
    request_id INTEGER NOT NULL,
    request_key VARCHAR(100),
    user_id INTEGER NOT NULL,
    redirect_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_mapping_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_event_mapping_event FOREIGN KEY (fotoowl_event_id) REFERENCES events(fotoowl_event_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_event UNIQUE (user_id, fotoowl_event_id)
);

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id);
CREATE INDEX IF NOT EXISTS idx_images_fotoowl_id ON images(fotoowl_id);
CREATE INDEX IF NOT EXISTS idx_images_event_id ON images(event_id);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);
CREATE INDEX IF NOT EXISTS idx_events_fotoowl_event_id ON events(fotoowl_event_id);
CREATE INDEX IF NOT EXISTS idx_event_mapping_user_id ON event_request_mapping(user_id);
CREATE INDEX IF NOT EXISTS idx_event_mapping_fotoowl_event_id ON event_request_mapping(fotoowl_event_id);

-- Step 7: Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 8: Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_images_updated_at ON images;
CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 9: Verify setup (optional)
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;