from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
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
    Bulk insert FotoOwl request mappings using PostgreSQL bulk insert with chunking
    Requires internal service authentication
    
    For each event_id, fotoowl_index_num should not repeat
    If fotoowl_event_id + fotoowl_index_num + fotoowl_request_id triplet already exists, it will be skipped
    Uses chunked bulk inserts (500 records per chunk) for optimal performance
    """
    
    total_received = len(bulk_data.mappings)
    total_inserted = 0
    total_skipped = 0
    skipped_triplets = []
    CHUNK_SIZE = 500
    
    try:
        # Step 1: Filter out duplicates by checking existing triplets in bulk
        event_index_request_triplets = [(m.fotoowl_event_id, m.fotoowl_index_num, m.fotoowl_request_id) for m in bulk_data.mappings]
        
        if event_index_request_triplets:
            # Create a query to check all triplets at once
            triplets_str = ",".join([f"({event_id},{index_num},{request_id})" for event_id, index_num, request_id in event_index_request_triplets])
            existing_triplets_query = text(f"""
                SELECT fotoowl_event_id, fotoowl_index_num, fotoowl_request_id 
                FROM fotoowl_request_mapping 
                WHERE (fotoowl_event_id, fotoowl_index_num, fotoowl_request_id) IN (VALUES {triplets_str})
            """)
            
            existing_triplets_result = db.execute(existing_triplets_query).fetchall()
            existing_triplets = {(row[0], row[1], row[2]) for row in existing_triplets_result}
        else:
            existing_triplets = set()
        
        # Step 2: Filter out duplicates from the input
        new_mappings = []
        for mapping_data in bulk_data.mappings:
            triplet = (mapping_data.fotoowl_event_id, mapping_data.fotoowl_index_num, mapping_data.fotoowl_request_id)
            if triplet in existing_triplets:
                total_skipped += 1
                skipped_triplets.append({
                    "event_id": mapping_data.fotoowl_event_id, 
                    "index_num": mapping_data.fotoowl_index_num,
                    "request_id": mapping_data.fotoowl_request_id
                })
                logger.info(f"Skipping duplicate event_id {mapping_data.fotoowl_event_id} + index_num {mapping_data.fotoowl_index_num} + request_id {mapping_data.fotoowl_request_id} triplet")
            else:
                new_mappings.append(mapping_data)
        
        # Step 3: Bulk insert in chunks using PostgreSQL's bulk insert
        if new_mappings:
            for i in range(0, len(new_mappings), CHUNK_SIZE):
                chunk = new_mappings[i:i + CHUNK_SIZE]
                
                # Prepare bulk insert values
                values_list = []
                for mapping in chunk:
                    values_list.append(
                        f"({mapping.fotoowl_request_id}, {mapping.fotoowl_event_id}, "
                        f"{mapping.fotoowl_image_id}, {mapping.fotoowl_index_num}, "
                        f"{mapping.fotoowl_x1 if mapping.fotoowl_x1 is not None else 'NULL'}, "
                        f"{mapping.fotoowl_x2 if mapping.fotoowl_x2 is not None else 'NULL'}, "
                        f"{mapping.fotoowl_y1 if mapping.fotoowl_y1 is not None else 'NULL'}, "
                        f"{mapping.fotoowl_y2 if mapping.fotoowl_y2 is not None else 'NULL'}, "
                        f"{mapping.fotoowl_aria_ratio if mapping.fotoowl_aria_ratio is not None else 'NULL'}, "
                        f"NOW(), NOW())"
                    )
                
                # Execute bulk insert for this chunk
                bulk_insert_query = text(f"""
                    INSERT INTO fotoowl_request_mapping 
                    (fotoowl_request_id, fotoowl_event_id, fotoowl_image_id, fotoowl_index_num,
                     fotoowl_x1, fotoowl_x2, fotoowl_y1, fotoowl_y2, fotoowl_aria_ratio,
                     created_at, updated_at)
                    VALUES {','.join(values_list)}
                """)
                
                db.execute(bulk_insert_query)
                total_inserted += len(chunk)
                logger.info(f"Inserted chunk of {len(chunk)} records (total so far: {total_inserted})")
        
        # Commit all insertions
        db.commit()
        
        logger.info(f"Bulk insert completed: {total_inserted} inserted, {total_skipped} skipped out of {total_received} received")
        
        return FotoOwlRequestMappingBulkResponse(
            total_received=total_received,
            total_inserted=total_inserted,
            total_skipped=total_skipped,
            skipped_pairs=skipped_triplets
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