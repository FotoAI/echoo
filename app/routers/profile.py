from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserProfile, UserProfileUpdate, InstagramPostResponse
from app.models import User, UserInstaPost
from app.auth import get_current_user
from app.instagram_service import instagram_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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