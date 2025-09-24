from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging
from app.database import get_db
from app.schemas import (
    FotoOwlRequestMappingCreate, 
    FotoOwlRequestMappingResponse, 
    FotoOwlRequestMappingBulkInsert, 
    FotoOwlRequestMappingBulkResponse
)
from app.models import FotoOwlRequestMapping
from app.auth import verify_internal_auth

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/internal/fotoowl-request-mapping/bulk", response_model=FotoOwlRequestMappingBulkResponse)
async def bulk_insert_fotoowl_request_mappings(
    bulk_data: FotoOwlRequestMappingBulkInsert,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Bulk insert FotoOwl request mappings
    Requires internal service authentication
    
    For each event_id, fotoowl_unique_id should not repeat
    If fotoowl_unique_id already exists for the same event_id, it will be skipped
    """
    
    total_received = len(bulk_data.mappings)
    total_inserted = 0
    total_skipped = 0
    skipped_unique_ids = []
    
    try:
        for mapping_data in bulk_data.mappings:
            # Check if fotoowl_unique_id already exists for this event_id
            existing_mapping = db.query(FotoOwlRequestMapping).filter(
                FotoOwlRequestMapping.fotoowl_event_id == mapping_data.fotoowl_event_id,
                FotoOwlRequestMapping.fotoowl_unique_id == mapping_data.fotoowl_unique_id
            ).first()
            
            if existing_mapping:
                # Skip this mapping as fotoowl_unique_id already exists for this event_id
                total_skipped += 1
                skipped_unique_ids.append(mapping_data.fotoowl_unique_id)
                logger.info(f"Skipping duplicate fotoowl_unique_id {mapping_data.fotoowl_unique_id} for event_id {mapping_data.fotoowl_event_id}")
                continue
            
            # Create new mapping record
            new_mapping = FotoOwlRequestMapping(
                fotoowl_unique_id=mapping_data.fotoowl_unique_id,
                fotoowl_request_id=mapping_data.fotoowl_request_id,
                fotoowl_event_id=mapping_data.fotoowl_event_id,
                fotoowl_image_id=mapping_data.fotoowl_image_id,
                fotoowl_index_num=mapping_data.fotoowl_index_num,
                fotoowl_x1=mapping_data.fotoowl_x1,
                fotoowl_x2=mapping_data.fotoowl_x2,
                fotoowl_y1=mapping_data.fotoowl_y1,
                fotoowl_y2=mapping_data.fotoowl_y2,
                fotoowl_aria_ratio=mapping_data.fotoowl_aria_ratio
            )
            
            db.add(new_mapping)
            total_inserted += 1
        
        # Commit all insertions at once
        db.commit()
        
        logger.info(f"Bulk insert completed: {total_inserted} inserted, {total_skipped} skipped out of {total_received} received")
        
        return FotoOwlRequestMappingBulkResponse(
            total_received=total_received,
            total_inserted=total_inserted,
            total_skipped=total_skipped,
            skipped_unique_ids=skipped_unique_ids
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during bulk insert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during bulk insert: {str(e)}"
        )

@router.get("/internal/fotoowl-request-mapping/event/{event_id}", response_model=List[FotoOwlRequestMappingResponse])
async def get_fotoowl_request_mappings_by_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Get all FotoOwl request mappings for a specific event
    Requires internal service authentication
    """
    mappings = db.query(FotoOwlRequestMapping).filter(
        FotoOwlRequestMapping.fotoowl_event_id == event_id
    ).order_by(FotoOwlRequestMapping.fotoowl_index_num.asc()).all()
    
    return mappings

@router.get("/internal/fotoowl-request-mapping/{mapping_id}", response_model=FotoOwlRequestMappingResponse)
async def get_fotoowl_request_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Get a specific FotoOwl request mapping by ID
    Requires internal service authentication
    """
    mapping = db.query(FotoOwlRequestMapping).filter(FotoOwlRequestMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FotoOwl request mapping not found"
        )
    
    return mapping

@router.delete("/internal/fotoowl-request-mapping/event/{event_id}")
async def delete_fotoowl_request_mappings_by_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_auth)
):
    """
    Delete all FotoOwl request mappings for a specific event
    Requires internal service authentication
    """
    deleted_count = db.query(FotoOwlRequestMapping).filter(
        FotoOwlRequestMapping.fotoowl_event_id == event_id
    ).delete()
    
    db.commit()
    
    return {"message": f"Deleted {deleted_count} mappings for event_id {event_id}"}