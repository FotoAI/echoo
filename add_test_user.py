#!/usr/bin/env python3
"""
Script to add a test user to the database
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️  python-dotenv not found, using system environment variables")

# Import our models
from app.models import User
from app.database import get_db, engine, SessionLocal

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """Create a test user"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("✅ Test user 'testuser' already exists!")
            print(f"   ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            print(f"   Name: {existing_user.name}")
            return existing_user
        
        # Create test user
        test_password = "testpass123"
        hashed_password = pwd_context.hash(test_password)
        
        test_user = User(
            username="testuser",
            password_hash=hashed_password,
            name="Test User",
            description="This is a test user for API testing"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("🎉 Test user created successfully!")
        print(f"   Username: testuser")
        print(f"   Password: {test_password}")
        print(f"   Name: {test_user.name}")
        print(f"   ID: {test_user.id}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Adding test user to database...")
    user = create_test_user()
    if user:
        print("\n📋 Test Credentials:")
        print("   Username: testuser")
        print("   Password: testpass123")
        print("\n🧪 Test the login API with:")
        print("   curl -u testuser:testpass123 http://localhost:8000/api/v1/login")