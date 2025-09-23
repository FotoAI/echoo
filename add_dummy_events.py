#!/usr/bin/env python3
"""
Script to add dummy data to the Events table
"""
import sys
import os
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Event, Base
from app.database import engine

def add_dummy_events():
    """Add dummy events to the database"""
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🎪 Adding dummy events to the database...")
        
        # Check if events already exist
        existing_events = db.query(Event).count()
        if existing_events > 0:
            print(f"ℹ️  Found {existing_events} existing events in the database")
            response = input("Do you want to add more dummy events? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        # Create dummy events
        dummy_events = [
            {
                "name": "TechConf 2024",
                "description": "The biggest technology conference of the year featuring AI, blockchain, and cutting-edge innovations. Join industry leaders and innovators for networking and learning.",
                "cover_image_url": "https://example.com/images/techconf2024-cover.jpg",
                "event_date": date(2024, 6, 15),
                "fotoowl_event_id": 1413,
                "fotoowl_event_key": "4631"
            },
            {
                "name": "Summer Music Festival",
                "description": "Three days of amazing music featuring top artists from around the world. Food trucks, art installations, and unforgettable performances.",
                "cover_image_url": "https://example.com/images/summer-music-fest-cover.jpg", 
                "event_date": date(2024, 7, 20),
                "fotoowl_event_id": 1414,
                "fotoowl_event_key": "4632"
            },
            {
                "name": "Photography Workshop",
                "description": "Learn from professional photographers in this intensive weekend workshop. Covers portrait, landscape, and street photography techniques.",
                "cover_image_url": "https://example.com/images/photography-workshop-cover.jpg",
                "event_date": date(2024, 5, 10),
                "fotoowl_event_id": 1415,
                "fotoowl_event_key": "4633"
            },
            {
                "name": "Food & Wine Expo",
                "description": "Discover culinary delights from renowned chefs and wineries. Tastings, cooking demonstrations, and gourmet experiences await.",
                "cover_image_url": "https://example.com/images/food-wine-expo-cover.jpg",
                "event_date": date(2024, 8, 5),
                "fotoowl_event_id": 1416,
                "fotoowl_event_key": "4634"
            },
            {
                "name": "Startup Pitch Competition",
                "description": "Watch innovative startups pitch their ideas to investors and industry experts. Network with entrepreneurs and potential partners.",
                "cover_image_url": "https://example.com/images/startup-pitch-cover.jpg",
                "event_date": date(2024, 9, 12),
                "fotoowl_event_id": 1417,
                "fotoowl_event_key": "4635"
            }
        ]
        
        events_added = 0
        for event_data in dummy_events:
            # Check if event with same fotoowl_event_id already exists
            existing = db.query(Event).filter(
                Event.fotoowl_event_id == event_data["fotoowl_event_id"]
            ).first()
            
            if not existing:
                new_event = Event(**event_data)
                db.add(new_event)
                events_added += 1
                print(f"✅ Added event: {event_data['name']}")
            else:
                print(f"⚠️  Event with FotoOwl ID {event_data['fotoowl_event_id']} already exists: {existing.name}")
        
        if events_added > 0:
            db.commit()
            print(f"\n🎉 Successfully added {events_added} new events to the database!")
        else:
            print("\n ℹ️ No new events were added (all already exist)")
        
        # Display all events
        print("\n📋 Current events in database:")
        all_events = db.query(Event).order_by(Event.event_date.desc().nullslast()).all()
        
        for event in all_events:
            print(f"   {event.id}: {event.name}")
            print(f"      Date: {event.event_date}")
            print(f"      FotoOwl ID: {event.fotoowl_event_id}")
            print(f"      Description: {event.description[:100]}...")
            print()
        
    except Exception as e:
        print(f"❌ Error adding dummy events: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_dummy_events()