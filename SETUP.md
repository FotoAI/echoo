# FotoOwl FastAPI Setup Instructions

## Quick Local Setup (No Docker)

### 1. **Virtual Environment** ✅
```bash
python3 -m venv fotoowl_venv
source fotoowl_venv/bin/activate  # On Windows: fotoowl_venv\Scripts\activate
```

### 2. **Install Dependencies** ✅
```bash
pip install -r requirements.txt
```

### 3. **Environment Configuration**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual database credentials
nano .env  # or use your preferred editor
```

**Required .env values:**
```bash
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/your_database
# OR set individual components:
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fotoowl_db
```

### 4. **Local PostgreSQL Setup**
Since you have PostgreSQL installed locally, follow these steps:

**Step 1: Create Database and Enable Extensions**
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Run the setup script
\i setup_database.sql

# OR manually run these commands:
CREATE DATABASE fotoowl_db;
\c fotoowl_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

**Step 2: Install pgvector extension (if not already installed)**
```bash
# On macOS with Homebrew:
brew install pgvector

# On Ubuntu/Debian:
sudo apt install postgresql-16-pgvector

# On other systems, follow: https://github.com/pgvector/pgvector
```

**Step 3: Verify Extension**
```sql
-- In psql connected to fotoowl_db:
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 5. **Run the Application**
```bash
# Method 1: Using the run script
python run.py

# Method 2: Direct uvicorn
source fotoowl_venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. **Test the API**
- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health
- Root: http://127.0.0.1:8000/

## API Endpoints

### User Authentication
- `POST /api/v1/register` - Register new user
- `POST /api/v1/login` - Login with basic auth

### Profile Management (requires auth)
- `PUT /api/v1/profile` - Update profile
- `GET /api/v1/profile` - Get profile

### Internal APIs (separate auth)
- `POST /api/v1/internal/images` - Create image record
- `GET /api/v1/internal/images/{id}` - Get image by ID

## Authentication

### User Auth
Send username/password in Authorization header:
```bash
curl -u username:password http://localhost:8000/api/v1/login
```

### Internal Auth
Use credentials from .env:
```bash
curl -u internal_service:internal_secret_key_2024 http://localhost:8000/api/v1/internal/images
```