from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import EventResponse
from app.models import Event

router = APIRouter()

@router.get("/getEventList", response_model=List[EventResponse])
async def get_event_list(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of events to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of events to skip")
):
    """
    Get list of all public events
    No authentication required - this is a public API
    
    Optional parameters:
    - limit: Maximum number of events to return (1-100)
    - offset: Number of events to skip (for pagination)
    
    Returns events ordered by event_date descending (latest events first)
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
    return events

@router.get("/getEventList/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific event by ID
    No authentication required - this is a public API
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event