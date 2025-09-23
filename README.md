# Echoo - FastAPI Backend with Event Management

A comprehensive FastAPI backend system with authentication, image management, event registration, and FotoOwl API integration.

## 🌟 Features

### Core Functionality
- **Dual Authentication System**: User Basic Auth + Internal Service Auth
- **Image Management**: PostgreSQL with pgvector extension support
- **Event Management**: Registration system with FotoOwl API integration
- **Flexible Data Model**: Nullable user_id for event-only images
- **Computed Fields**: Smart image_url prioritization (filecoin_url > fotoowl_url)
- **Simplified APIs**: User-friendly interfaces (like auto-finding request_id)

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI app entry point
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── auth.py              # Authentication logic
└── routers/
    ├── __init__.py
    ├── auth.py          # Authentication routes
    ├── profile.py       # Profile management routes
    └── images.py        # Image management routes
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start PostgreSQL with Docker

```bash
docker-compose up -d
```

This will start PostgreSQL with pgvector extension enabled.

### 3. Environment Variables

Copy `.env.example` to `.env` and update as needed:

```bash
cp .env.example .env
```

### 4. Initialize Database

```bash
alembic upgrade head
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 🚀 API Endpoints

### User APIs (Basic Auth Required)
```
GET  /api/v1/images                           - User's images with image_url
GET  /api/v1/getImageList                     - User's images with filters
GET  /api/v1/my-registered-events             - User's registered events
GET  /api/v1/get-event-matched-image-list     - Event matched images (simplified!)
POST /api/v1/register-event                   - Register for events
```

### Public APIs (No Auth)
```
GET  /api/v1/public/events                    - Browse available events
```

### Internal APIs (Internal Auth Required)
```
POST /api/v1/internal/images                  - Create images
GET  /api/v1/internal/images/{id}             - Get image by ID
PUT  /api/v1/internal/images/{id}             - Update images
```

### Key Feature: Simplified Event Matched Images
```http
GET /api/v1/get-event-matched-image-list?event_id=1413
```
✅ Only requires `event_id` - `request_id` found automatically!
✅ Full pagination support (`page`, `page_size`, `-1` for all)
✅ Built-in registration verification

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `password_hash` - Hashed password
- `name` - User's display name
- `instagram_url` - Instagram profile URL
- `twitter_url` - Twitter profile URL  
- `youtube_url` - YouTube profile URL
- `description` - User description
- `created_at`, `updated_at` - Timestamps

### Images Table
- `id` - Primary key (required)
- `name` - Image name (required)
- `fotoowl_id` - FotoOwl ID (optional)
- `fotoowl_url` - FotoOwl URL (optional)
- `filecoin_url` - Filecoin URL (optional)
- `description` - Image description (optional, max 512 chars)
- `image_encoding` - Image encoding (optional, max 512 chars)
- `description_vector` - Vector representation of description (512 dimensions)
- `image_vector` - Vector representation of image (512 dimensions)
- `event_id` - Event ID (optional)
- `created_at`, `updated_at` - Timestamps

## Authentication

### User Authentication
Uses HTTP Basic Authentication for user endpoints. Include username and password in the Authorization header.

### Internal Authentication
Uses separate HTTP Basic Authentication for internal service endpoints. Configure credentials in environment variables:
- `INTERNAL_USERNAME` (default: internal_service)
- `INTERNAL_PASSWORD` (default: internal_secret_key_2024)

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.