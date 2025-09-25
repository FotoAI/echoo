from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserProfile, UserProfileUpdate, InstagramPostResponse
from app.models import User, UserInstaPost
from app.auth import get_current_user
from app.instagram_service import instagram_service
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()

def normalize_instagram_url(instagram_input: str) -> str:
    """
    Normalize Instagram handle or URL to a proper Instagram URL
    Handles various formats:
    - @username -> https://www.instagram.com/username/
    - username -> https://www.instagram.com/username/
    - instagram.com/username -> https://www.instagram.com/username/
    - https://www.instagram.com/username/ -> https://www.instagram.com/username/
    
    Returns None if the input is invalid
    """
    if not instagram_input or not instagram_input.strip():
        return instagram_input
    
    try:
        # Remove leading @ if present and strip whitespace
        handle = instagram_input.strip().lstrip('@')
        
        # If it's already a full URL, extract the username
        if 'instagram.com' in handle:
            # Extract username from URL using regex
            match = re.search(r'instagram\.com/([^/?]+)', handle)
            if match:
                username = match.group(1)
            else:
                # If we can't extract username, return None (invalid)
                logger.warning(f"Could not extract username from Instagram URL: {instagram_input}")
                return None
        else:
            # It's just a username
            username = handle
        
        # Clean username (remove any trailing slashes or special chars)
        username = username.rstrip('/').split('/')[0].split('?')[0]
        
        # Validate username format (alphanumeric, dots, underscores only)
        if not re.match(r'^[a-zA-Z0-9._]+$', username) or len(username) < 1:
            logger.warning(f"Invalid Instagram username format: {username}")
            return None
        
        # Return normalized URL
        return f"https://www.instagram.com/{username}/"
        
    except Exception as e:
        logger.error(f"Error normalizing Instagram URL '{instagram_input}': {e}")
        return None

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    Requires basic authentication
    """
    # Normalize Instagram URL if provided
    if profile_data.instagram_url is not None:
        normalized_instagram_url = normalize_instagram_url(profile_data.instagram_url)
        if normalized_instagram_url is None:
            # Invalid Instagram URL format - log warning but don't fail the request
            logger.warning(f"Invalid Instagram URL format provided by user {current_user.id}: {profile_data.instagram_url}")
            # Set to None so it doesn't get updated
            profile_data.instagram_url = None
        else:
            profile_data.instagram_url = normalized_instagram_url
    
    # Check if instagram_url is being updated
    instagram_url_updated = False
    if profile_data.instagram_url is not None and profile_data.instagram_url != current_user.instagram_url:
        instagram_url_updated = True
    
    # Update user profile fields
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # If Instagram URL was updated, fetch and save Instagram posts
    if instagram_url_updated and current_user.instagram_url:
        try:
            logger.info(f"Fetching Instagram posts for user {current_user.id} with URL: {current_user.instagram_url}")
            result = await instagram_service.fetch_and_save_user_posts(
                db, current_user.id, current_user.instagram_url
            )
            logger.info(f"Instagram posts fetch result: {result}")
        except Exception as e:
            logger.error(f"Error fetching Instagram posts for user {current_user.id}: {e}")
            # Don't fail the profile update if Instagram fetch fails
            # The profile update was successful, Instagram fetch is optional
            # We could optionally add a field to track fetch status if needed
    
    return current_user

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information
    Requires basic authentication
    """
    return current_user

@router.get("/instagram-posts", response_model=list[InstagramPostResponse])
async def get_instagram_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's Instagram posts
    Requires basic authentication
    """
    posts = db.query(UserInstaPost).filter(
        UserInstaPost.user_id == current_user.id
    ).order_by(UserInstaPost.created_at.desc()).all()
    
    return posts