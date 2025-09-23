from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, func, Date
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    selfie_url = Column(String(500), nullable=True)
    selfie_cid = Column(String(100), nullable=True)
    selfie_height = Column(Integer, nullable=True)
    selfie_width = Column(Integer, nullable=True)
    instagram_url = Column(String(200), nullable=True)
    twitter_url = Column(String(200), nullable=True)
    linkedin_url = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=True, index=True)
    fotoowl_image_id = Column(Integer, nullable=True)
    fotoowl_url = Column(String(255), nullable=True)
    filecoin_url = Column(String(255), nullable=True)
    filecoin_cid = Column(String(255), nullable=True)
    size = Column(BigInteger, nullable=True)
    height = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    description = Column(String(512), nullable=True)
    image_encoding = Column(String(512), nullable=True)
    description_vector = Column(Vector(512), nullable=True)
    image_vector = Column(Vector(512), nullable=True)
    event_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EventRequestMapping(Base):
    __tablename__ = "event_request_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    fotoowl_event_id = Column(Integer, nullable=False, index=True)
    request_id = Column(Integer, nullable=False)
    request_key = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    redirect_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(255), nullable=True)
    cover_image_height = Column(Integer, nullable=True)
    cover_image_width = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    event_date = Column(Date, nullable=True)
    fotoowl_event_id = Column(Integer, nullable=True, index=True)
    fotoowl_event_key = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())