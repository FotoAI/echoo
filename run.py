#!/usr/bin/env python3
"""
Simple script to run the Echoo FastAPI application locally
"""
import uvicorn
import os

if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded .env file for local development")
    except ImportError:
        print("python-dotenv not installed, skipping .env file")
    
    # Hardcoded configuration (non-sensitive)
    host = "0.0.0.0"
    port = 8000
    
    # Environment-based settings
    environment = os.getenv("ENVIRONMENT", "development")
    debug = environment == "development"
    
    print(f"Starting Echoo API on {host}:{port}")
    print(f"Environment: {environment}")
    print(f"Debug mode: {debug}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )