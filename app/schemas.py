from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
from datetime import datetime, date

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    selfie_cid: Optional[str] = None
    selfie_url: Optional[str] = None
    selfie_height: Optional[int] = None
    selfie_width: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLoginResponse(BaseModel):
    message: str
    user: UserProfile
    
    class Config:
        from_attributes = True

# Image schemas
class ImageCreate(BaseModel):
    name: str
    user_id: Optional[int] = None
    is_selfie: Optional[bool] = False
    fotoowl_id: Optional[int] = None
    fotoowl_url: Optional[str] = None
    filecoin_url: Optional[str] = None
    cid: Optional[str] = None
    size: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    description: Optional[str] = None
    image_encoding: Optional[str] = None
    event_id: Optional[int] = None
    
    @validator('user_id')
    def validate_user_or_event_id(cls, user_id, values):
        """Either user_id or event_id must be present"""
        event_id = values.get('event_id')
        if user_id is None and event_id is None:
            raise ValueError('Either user_id or event_id must be provided')
        return user_id

class ImageUpdate(BaseModel):
    name: Optional[str] = None
    user_id: Optional[int] = None
    is_selfie: Optional[bool] = False
    fotoowl_id: Optional[int] = None
    fotoowl_url: Optional[str] = None
    filecoin_url: Optional[str] = None
    filecoin_cid: Optional[str] = None
    size: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    description: Optional[str] = None
    image_encoding: Optional[str] = None
    event_id: Optional[int] = None

class ImageResponse(BaseModel):
    id: int
    name: str
    user_id: Optional[int] = None
    fotoowl_id: Optional[int] = None
    fotoowl_url: Optional[str] = None
    filecoin_url: Optional[str] = None
    filecoin_cid: Optional[str] = None
    size: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    description: Optional[str] = None
    image_encoding: Optional[str] = None
    event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ImageListResponse(BaseModel):
    id: Optional[int] = None  # Allow None for images not in our database
    name: str
    user_id: Optional[int] = None
    fotoowl_id: Optional[int] = None
    fotoowl_url: Optional[str] = None
    filecoin_url: Optional[str] = None
    filecoin_cid: Optional[str] = None
    size: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    description: Optional[str] = None
    image_encoding: Optional[str] = None
    event_id: Optional[int] = None
    image_url: Optional[str] = None  # Computed field: filecoin_url or fotoowl_url
    created_at: Optional[datetime] = None  # Allow None for external images
    updated_at: Optional[datetime] = None  # Allow None for external images
    
    class Config:
        from_attributes = True

# Event Registration schemas
class EventRegistrationRequest(BaseModel):
    event_id: int  # This is the fotoowl_event_id from the frontend
    key: str

class EventRegistrationResponse(BaseModel):
    id: int
    fotoowl_event_id: int
    request_id: int
    request_key: str
    user_id: int
    redirect_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FotoOwlApiResponse(BaseModel):
    ok: bool
    data: dict

# Event schemas
class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    event_date: Optional[date] = None
    fotoowl_event_id: Optional[int] = None
    fotoowl_event_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RegisteredEventResponse(BaseModel):
    # Registration details
    registration_id: int
    request_id: int
    request_key: str
    redirect_url: Optional[str] = None
    registration_created_at: datetime
    
    # Event details (from Events table)
    event_id: Optional[int] = None  # Event table ID (may be None if event not in our Events table)
    event_name: Optional[str] = None
    event_description: Optional[str] = None
    event_cover_image_url: Optional[str] = None
    event_date: Optional[date] = None
    fotoowl_event_id: int  # From EventRequestMapping
    fotoowl_event_key: Optional[str] = None
    
    class Config:
        from_attributes = True

# Event matched images schemas
class EventMatchedImagesRequest(BaseModel):
    event_id: int  # fotoowl_event_id
    request_id: int

class FotoOwlImageData(BaseModel):
    id: int
    event_id: int
    name: str
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    img_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    med_url: Optional[str] = None
    high_url: Optional[str] = None

class FotoOwlImageListResponse(BaseModel):
    ok: bool
    data: dict  # Contains image_list array