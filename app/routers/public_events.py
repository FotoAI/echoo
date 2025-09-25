from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import EventResponse
from app.models import Event, EventRequestMapping, User
from app.auth import get_current_user_optional

router = APIRouter()

@router.get("/getEventList", response_model=List[EventResponse])
async def get_event_list(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of events to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of events to skip")
):
    """
    Get list of all public events
    Authentication is optional - if authenticated, returns registration status for each event
    
    Optional parameters:
    - limit: Maximum number of events to return (1-100)
    - offset: Number of events to skip (for pagination)
    
    Returns events ordered by event_date descending (latest events first)
    If user is authenticated, includes 'registered' field indicating if user is registered for each event
    """
    
    # Start with base query for all events
    query = db.query(Event)
    
    # Order by event_date descending (latest events first), with null dates at the end
    query = query.order_by(Event.event_date.desc().nullslast())
    
    # Apply offset
    if offset > 0:
        query = query.offset(offset)
    
    # Apply limit
    if limit is not None:
        query = query.limit(limit)
    
    events = query.all()
    
    # If user is authenticated, check registration status for each event
    if current_user:
        # Get all event IDs that user is registered for
        registered_event_ids = db.query(EventRequestMapping.fotoowl_event_id).filter(
            EventRequestMapping.user_id == current_user.id
        ).all()
        registered_event_ids = {row[0] for row in registered_event_ids}
        
        # Add registration status to each event
        for event in events:
            if event.fotoowl_event_id and event.fotoowl_event_id in registered_event_ids:
                event.registered = True
            else:
                event.registered = False
    else:
        # If not authenticated, set registered to None for all events
        for event in events:
            event.registered = False
    
    return events

@router.get("/getEventList/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get a specific event by ID
    Authentication is optional - if authenticated, returns registration status for the event
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # If user is authenticated, check registration status
    if current_user:
        # Check if user is registered for this event
        registration = db.query(EventRequestMapping).filter(
            EventRequestMapping.user_id == current_user.id,
            EventRequestMapping.fotoowl_event_id == event.fotoowl_event_id
        ).first()
        
        event.registered = registration is not None
    else:
        # If not authenticated, set registered to None
        event.registered = None
    
    return event