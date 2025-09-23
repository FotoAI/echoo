from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import requests
import tempfile
import os
from urllib.parse import urlparse
from app.database import get_db
from app.schemas import EventRegistrationRequest, EventRegistrationResponse, RegisteredEventResponse, EventMatchedImagesRequest, ImageListResponse
from app.models import EventRequestMapping, User, Event, Image
from app.auth import get_current_user

router = APIRouter()

async def download_image_from_url(image_url: str) -> str:
    """Download image from URL and return local file path"""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Create temporary file with proper extension
        parsed_url = urlparse(image_url)
        file_extension = os.path.splitext(parsed_url.path)[1] or '.jpg'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(response.content)
            return temp_file.name
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}"
        )

async def call_fotoowl_api(event_id: int, key: str, image_file_path: str) -> dict:
    """Call FotoOwl API to create request"""
    try:
        fotoowl_api_url = "https://dev-api.fotoowl.ai/open/request"
        
        with open(image_file_path, 'rb') as image_file:
            files = {
                'file': image_file
            }
            data = {
                'event_id': str(event_id),
                'key': str(key)
            }
            
            response = requests.post(
                fotoowl_api_url,
                files=files,
                data=data,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to call FotoOwl API: {str(e)}"
        )
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(image_file_path):
                os.unlink(image_file_path)
        except:
            pass

@router.post("/register-event", response_model=EventRegistrationResponse)
async def register_for_event(
    registration_data: EventRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register user for a FotoOwl event
    Requires user authentication and only event_id
    Automatically retrieves event key from Events table
    Uses user's selfie_url to upload image to FotoOwl API
    """
    
    # Check if user already registered for this event
    existing_registration = db.query(EventRequestMapping).filter(
        EventRequestMapping.user_id == current_user.id,
        EventRequestMapping.fotoowl_event_id == registration_data.event_id
    ).first()
    
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already registered for event {registration_data.event_id}"
        )
    
    # Check if user has a selfie_url
    if not current_user.selfie_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have a selfie uploaded before registering for events"
        )
    
    # Get event key from Events table
    event = db.query(Event).filter(Event.fotoowl_event_id == registration_data.event_id).first()
    if not event or not event.fotoowl_event_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found or missing event key for event_id {registration_data.event_id}"
        )
    
    try:
        # Download image from user's selfie_url
        image_file_path = await download_image_from_url(current_user.selfie_url)
        
        # Call FotoOwl API with event key from database
        fotoowl_response = await call_fotoowl_api(
            registration_data.event_id,
            event.fotoowl_event_key,  # Use key from events table
            image_file_path
        )
        
        # Validate FotoOwl API response
        if not fotoowl_response.get('ok'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FotoOwl API returned error response"
            )
        
        fotoowl_data = fotoowl_response.get('data', {})
        request_id = fotoowl_data.get('request_id')
        request_key = fotoowl_data.get('request_key')
        redirect_url = fotoowl_data.get('redirect_url')
        
        if not request_id or not request_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid response from FotoOwl API - missing request_id or request_key"
            )
        
        # Create event request mapping record
        event_mapping = EventRequestMapping(
            fotoowl_event_id=registration_data.event_id,
            request_id=request_id,
            request_key=request_key,
            user_id=current_user.id,
            redirect_url=redirect_url
        )
        
        db.add(event_mapping)
        db.commit()
        db.refresh(event_mapping)
        
        return event_mapping
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during event registration: {str(e)}"
        )

@router.get("/my-registrations")
async def get_user_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all event registrations for the authenticated user
    """
    registrations = db.query(EventRequestMapping).filter(
        EventRequestMapping.user_id == current_user.id
    ).order_by(EventRequestMapping.created_at.desc()).all()
    
    return registrations

@router.get("/registration/{event_id}")
async def get_event_registration(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific event registration for the authenticated user
    """
    registration = db.query(EventRequestMapping).filter(
        EventRequestMapping.user_id == current_user.id,
        EventRequestMapping.fotoowl_event_id == event_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registration found for event {event_id}"
        )
    
    return registration

@router.get("/my-registered-events", response_model=List[RegisteredEventResponse])
async def get_user_registered_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all events that the authenticated user has registered for
    Returns combined data from EventRequestMapping and Events tables
    """
    
    # Query to join EventRequestMapping with Events table
    # Left join because the event might not exist in our Events table
    query = db.query(
        EventRequestMapping.id.label('registration_id'),
        EventRequestMapping.fotoowl_event_id,
        EventRequestMapping.request_id,
        EventRequestMapping.request_key,
        EventRequestMapping.redirect_url,
        EventRequestMapping.created_at.label('registration_created_at'),
        Event.id.label('event_id'),
        Event.name.label('event_name'),
        Event.description.label('event_description'),
        Event.cover_image_url.label('event_cover_image_url'),
        Event.event_date,
        Event.fotoowl_event_key
    ).outerjoin(
        Event, EventRequestMapping.fotoowl_event_id == Event.fotoowl_event_id
    ).filter(
        EventRequestMapping.user_id == current_user.id
    ).order_by(
        EventRequestMapping.created_at.desc()
    )
    
    results = query.all()
    
    # Convert to response format
    registered_events = []
    for result in results:
        event_data = RegisteredEventResponse(
            registration_id=result.registration_id,
            request_id=result.request_id,
            request_key=result.request_key,
            redirect_url=result.redirect_url,
            registration_created_at=result.registration_created_at,
            event_id=result.event_id,
            event_name=result.event_name,
            event_description=result.event_description,
            event_cover_image_url=result.event_cover_image_url,
            event_date=result.event_date,
            fotoowl_event_id=result.fotoowl_event_id,
            fotoowl_event_key=result.fotoowl_event_key
        )
        registered_events.append(event_data)
    
    return registered_events

@router.get("/get-event-matched-image-list", response_model=List[ImageListResponse])
async def get_event_matched_image_list(
    event_id: int = Query(..., description="FotoOwl event ID"),
    page: int = Query(0, ge=0, description="Page number starting from 0"),
    page_size: int = Query(10, ge=-1, description="Number of images per page. Use -1 for all images"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get matched images from FotoOwl API for a specific event with pagination support
    
    1. Find user's registration for the event (get request_id automatically)
    2. Get registration details (request_key, event_key)
    3. Call FotoOwl API to get matched images with pagination
    4. Match FotoOwl images with our Images table
    5. Return images in same format as /images endpoint with image_url
    
    Pagination:
    - page: Starting from 0 (FotoOwl API format)
    - page_size: Number of images per page, -1 for all images
    """
    
    # Step 1: Find user's registration for the event (automatically get request_id)
    registration = db.query(EventRequestMapping).filter(
        EventRequestMapping.user_id == current_user.id,
        EventRequestMapping.fotoowl_event_id == event_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User is not registered for event {event_id}. Please register first."
        )
    
    # Step 2: Get event key from Events table (if available)
    event = db.query(Event).filter(Event.fotoowl_event_id == event_id).first()
    event_key = event.fotoowl_event_key if event else None
    
    if not event_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event key not found for event {event_id}"
        )
    
    # Step 3: Call FotoOwl API to get matched images
    try:
        fotoowl_api_url = "https://dev-api.fotoowl.ai/open/event/image-list"
        
        params = {
            'event_id': event_id,
            'page': page,
            'page_size': page_size,
            'key': event_key,
            'request_id': registration.request_id,  # Automatically retrieved from registration
            'request_key': registration.request_key
        }
        
        response = requests.get(
            fotoowl_api_url,
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        fotoowl_data = response.json()
        
        if not fotoowl_data.get('ok', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FotoOwl API returned error response"
            )
        
        # Extract image list from response
        image_list = fotoowl_data.get('data', {}).get('image_list', [])
        
        if not image_list:
            # Return empty list if no images found
            return []
        
        # Step 4: Match FotoOwl images with our Images table
        # Get FotoOwl image IDs
        fotoowl_image_ids = [img['id'] for img in image_list]
        
        # Find matching images in our database
        our_images = db.query(Image).filter(
            Image.fotoowl_id.in_(fotoowl_image_ids)
        ).all()
        
        # Create a mapping of fotoowl_id to our image data
        our_images_map = {img.fotoowl_id: img for img in our_images}
        
        # Step 5: Build response combining FotoOwl data with our data
        response_images = []
        
        for fotoowl_img in image_list:
            fotoowl_id = fotoowl_img['id']
            our_image = our_images_map.get(fotoowl_id)
            
            if our_image:
                # Use our image data with computed image_url
                image_url = our_image.filecoin_url if our_image.filecoin_url else our_image.fotoowl_url
                
                image_dict = {
                    "id": our_image.id,
                    "name": our_image.name,
                    "user_id": our_image.user_id,
                    "fotoowl_id": our_image.fotoowl_id,
                    "fotoowl_url": our_image.fotoowl_url,
                    "filecoin_url": our_image.filecoin_url,
                    "filecoin_cid": our_image.filecoin_cid,
                    "size": our_image.size,
                    "height": our_image.height,
                    "width": our_image.width,
                    "description": our_image.description,
                    "image_encoding": our_image.image_encoding,
                    "event_id": our_image.event_id,
                    "image_url": image_url,  # Computed field
                    "created_at": our_image.created_at,
                    "updated_at": our_image.updated_at
                }
                response_images.append(ImageListResponse(**image_dict))
            else:
                # Create image record from FotoOwl data if not in our database
                # Use FotoOwl URL as both fotoowl_url and image_url
                fotoowl_url = fotoowl_img.get('img_url', '')
                
                image_dict = {
                    "id": None,  # External image not in our database
                    "name": fotoowl_img.get('name', ''),
                    "user_id": current_user.id,
                    "fotoowl_id": fotoowl_id,
                    "fotoowl_url": fotoowl_url,
                    "filecoin_url": None,
                    "filecoin_cid": None,
                    "size": fotoowl_img.get('size'),
                    "height": fotoowl_img.get('height'),
                    "width": fotoowl_img.get('width'),
                    "description": f"Matched image from event {event_id}",
                    "image_encoding": None,
                    "event_id": event_id,
                    "image_url": fotoowl_url,  # Use FotoOwl URL as image_url
                    "created_at": None,
                    "updated_at": None
                }
                
                response_images.append(ImageListResponse(**image_dict))
        
        return response_images
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to FotoOwl API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )