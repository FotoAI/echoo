from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database import get_db
from app.schemas import ImageCreate, ImageUpdate, ImageResponse, ImageListResponse
from app.models import Image, User, EventRequestMapping
from app.auth import verify_internal_auth, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/internal/images", response_model=ImageResponse)
async def create_image(
    image_data: ImageCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Internal API to create a new image record
    Requires internal service authentication
    Required fields: 'name' and 'user_id'. All others are optional
    
    If is_selfie=true, updates user's selfie_cid and selfie_url fields
    """
    
    # Create new image record
    new_image = Image(
        name=image_data.name,
        user_id=image_data.user_id,
        fotoowl_image_id=image_data.fotoowl_image_id,
        fotoowl_url=image_data.fotoowl_url,
        filecoin_url=image_data.filecoin_url,
        filecoin_cid=image_data.cid,
        size=image_data.size,
        height=image_data.height,
        width=image_data.width,
        description=image_data.description,
        image_encoding=image_data.image_encoding,
        event_id=image_data.event_id
    )
    
    db.add(new_image)
    
    # If this is a selfie and has a user_id, update the user's selfie fields
    logger.info(f"Selfie check: is_selfie={image_data.is_selfie}, user_id={image_data.user_id}")
    if image_data.is_selfie and image_data.user_id:
        logger.info(f"Updating selfie for user_id={image_data.user_id}")
        user = db.query(User).filter(User.id == image_data.user_id).first()
        if user:
            logger.info(f"Found user: {user.username}, updating selfie_cid={image_data.cid}, selfie_url={image_data.filecoin_url}")
            user.selfie_cid = image_data.cid
            user.selfie_url = image_data.filecoin_url
            user.selfie_height = image_data.height
            user.selfie_width = image_data.width
    else:
        logger.info(f"Not updating selfie: is_selfie={image_data.is_selfie}, user_id={image_data.user_id}")
    
    # Commit both image and user updates in a single transaction
    db.commit()
    db.refresh(new_image)
    
    return new_image

@router.get("/internal/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Internal API to get image by ID
    Requires internal service authentication
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return image

@router.put("/internal/images/{image_id}", response_model=ImageResponse)
async def update_image(
    image_id: int,
    image_data: ImageUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Internal API to update an existing image record by ID
    Requires internal service authentication
    Only provided fields will be updated
    
    If is_selfie=true, updates user's selfie_cid and selfie_url fields
    """
    
    # Find the existing image
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Update only the provided fields
    update_data = image_data.dict(exclude_unset=True, exclude={"is_selfie"})
    for field, value in update_data.items():
        setattr(image, field, value)
    
    # If this is a selfie and the image has a user_id, update the user's selfie fields
    logger.info(f"PUT Selfie check: is_selfie={image_data.is_selfie}, user_id={image.user_id}")
    if image_data.is_selfie and image.user_id:
        logger.info(f"PUT Updating selfie for user_id={image.user_id}")
        user = db.query(User).filter(User.id == image.user_id).first()
        if user:
            logger.info(f"PUT Found user: {user.username}, updating selfie_cid={image.filecoin_cid}, selfie_url={image.fotoowl_url}")
            # Use the updated image's current values for selfie fields
            user.selfie_cid = image.filecoin_cid
            user.selfie_url = image.fotoowl_url
            user.selfie_height = image.height
            user.selfie_width = image.width
        else:
            logger.error(f"PUT User with id {image.user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {image.user_id} not found"
            )
    else:
        logger.info(f"PUT Not updating selfie: is_selfie={image_data.is_selfie}, user_id={image.user_id}")
    
    # Commit both image and user updates in a single transaction
    db.commit()
    db.refresh(image)
    
    return image

# User-specific image endpoints (require user authentication)

@router.get("/images", response_model=List[ImageListResponse])
async def get_user_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all images for the authenticated user
    Requires user authentication
    Each image includes computed 'image_url' field: filecoin_url if available, otherwise fotoowl_url
    """
    images = db.query(Image).filter(Image.user_id == current_user.id).order_by(Image.created_at.desc()).all()
    
    # Convert to response format with computed image_url
    response_images = []
    for image in images:
        # Determine image_url: prioritize filecoin_url over fotoowl_url
        image_url = image.filecoin_url if image.filecoin_url else image.fotoowl_url
        
        image_dict = {
            "id": image.id,
            "name": image.name,
            "user_id": image.user_id,
            "fotoowl_image_id": image.fotoowl_image_id,
            "fotoowl_url": image.fotoowl_url,
            "filecoin_url": image.filecoin_url,
            "filecoin_cid": image.filecoin_cid,
            "size": image.size,
            "height": image.height,
            "width": image.width,
            "description": image.description,
            "image_encoding": image.image_encoding,
            "event_id": image.event_id,
            "image_url": image_url,  # Computed field
            "created_at": image.created_at,
            "updated_at": image.updated_at
        }
        response_images.append(ImageListResponse(**image_dict))
    
    return response_images

@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_user_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific image for the authenticated user
    Requires user authentication
    """
    image = db.query(Image).filter(
        Image.id == image_id, 
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or you don't have permission to access it"
        )
    
    return image

@router.get("/getImageList", response_model=List[ImageListResponse])
async def get_image_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of images to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of images to skip"),
    event_id: Optional[int] = Query(None, description="Filter by specific event_id")
):
    """
    Get image list for the authenticated user
    Requires user authentication
    
    By default (no filters), returns images where user_id matches the authenticated user.
    Each image includes computed 'image_url' field: filecoin_url if available, otherwise fotoowl_url
    
    Optional filters:
    - limit: Maximum number of images to return (1-100)
    - offset: Number of images to skip (for pagination)  
    - event_id: Filter by specific event_id
    """
    
    # Start with base query for user's images
    query = db.query(Image).filter(Image.user_id == current_user.id)
    
    # Apply event_id filter if provided
    if event_id is not None:
        query = query.filter(Image.event_id == event_id)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Image.created_at.desc())
    
    # Apply offset
    if offset > 0:
        query = query.offset(offset)
    
    # Apply limit
    if limit is not None:
        query = query.limit(limit)
    
    images = query.all()
    
    # Convert to response format with computed image_url
    response_images = []
    for image in images:
        # Determine image_url: prioritize filecoin_url over fotoowl_url
        image_url = image.filecoin_url if image.filecoin_url else image.fotoowl_url
        
        image_dict = {
            "id": image.id,
            "name": image.name,
            "user_id": image.user_id,
            "fotoowl_image_id": image.fotoowl_image_id,
            "fotoowl_url": image.fotoowl_url,
            "filecoin_url": image.filecoin_url,
            "filecoin_cid": image.filecoin_cid,
            "size": image.size,
            "height": image.height,
            "width": image.width,
            "description": image.description,
            "image_encoding": image.image_encoding,
            "event_id": image.event_id,
            "image_url": image_url,  # Computed field
            "created_at": image.created_at,
            "updated_at": image.updated_at
        }
        response_images.append(ImageListResponse(**image_dict))
    
    return response_images