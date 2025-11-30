"""
Configuration API endpoints.
Manages IP whitelist and data source configuration.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.ip_whitelist import IPWhitelistService
from app.services.config_service import ConfigService
from app.models.schemas import (
    IPWhitelistCreate,
    IPWhitelistUpdate,
    IPWhitelistResponse,
    DataSourceConfigUpdate,
    DataSourceConfigResponse,
)

router = APIRouter()


# ========== IP Whitelist Endpoints ==========

@router.get("/whitelist", response_model=List[IPWhitelistResponse])
async def get_ip_whitelist(
    active_only: bool = Query(default=False, description="Return only active IPs"),
    db: Session = Depends(get_db),
):
    """
    Get all whitelisted IP addresses.

    Args:
        active_only: If True, return only active IPs

    Returns:
        List of whitelisted IPs
    """
    service = IPWhitelistService(db)
    whitelist = service.get_all(active_only=active_only)
    return whitelist


@router.post("/whitelist", response_model=IPWhitelistResponse, status_code=201)
async def add_ip_to_whitelist(
    data: IPWhitelistCreate,
    db: Session = Depends(get_db),
):
    """
    Add an IP address to the whitelist.

    Args:
        data: IP address and optional description

    Returns:
        Created whitelist entry

    Raises:
        HTTPException: If IP is invalid or already exists
    """
    service = IPWhitelistService(db)

    try:
        whitelist_entry = service.add_ip(
            ip=data.ip_address,
            description=data.description,
            created_by=None,  # TODO: Add authentication and use actual user
        )
        return whitelist_entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/whitelist/{ip_id}", response_model=IPWhitelistResponse)
async def get_ip_whitelist_entry(
    ip_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific whitelist entry by ID.

    Args:
        ip_id: ID of the whitelist entry

    Returns:
        Whitelist entry

    Raises:
        HTTPException: If entry not found
    """
    service = IPWhitelistService(db)
    entry = service.get_by_id(ip_id)

    if not entry:
        raise HTTPException(status_code=404, detail=f"IP whitelist entry not found: {ip_id}")

    return entry


@router.patch("/whitelist/{ip_id}", response_model=IPWhitelistResponse)
async def update_ip_whitelist_entry(
    ip_id: int,
    data: IPWhitelistUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a whitelist entry (description or active status).

    Args:
        ip_id: ID of the entry to update
        data: Fields to update

    Returns:
        Updated whitelist entry

    Raises:
        HTTPException: If entry not found
    """
    service = IPWhitelistService(db)
    updated_entry = service.update_ip(ip_id, data)

    if not updated_entry:
        raise HTTPException(status_code=404, detail=f"IP whitelist entry not found: {ip_id}")

    return updated_entry


@router.delete("/whitelist/{ip_id}")
async def delete_ip_from_whitelist(
    ip_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove an IP address from the whitelist.

    Args:
        ip_id: ID of the entry to delete

    Returns:
        Success message

    Raises:
        HTTPException: If entry not found
    """
    service = IPWhitelistService(db)
    deleted = service.delete_ip(ip_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"IP whitelist entry not found: {ip_id}")

    return {"message": f"IP whitelist entry {ip_id} deleted successfully"}


# ========== Data Source Configuration Endpoints ==========

@router.get("/sources", response_model=List[DataSourceConfigResponse])
async def get_data_sources(
    db: Session = Depends(get_db),
):
    """
    Get all data source configurations.

    Returns:
        List of all data source configs
    """
    service = ConfigService(db)
    sources = service.get_all_sources()
    return sources


@router.get("/sources/{source_name}", response_model=DataSourceConfigResponse)
async def get_data_source(
    source_name: str,
    db: Session = Depends(get_db),
):
    """
    Get configuration for a specific data source.

    Args:
        source_name: Name of the data source

    Returns:
        Data source configuration

    Raises:
        HTTPException: If source not found
    """
    service = ConfigService(db)
    source = service.get_source(source_name)

    if not source:
        raise HTTPException(status_code=404, detail=f"Data source not found: {source_name}")

    return source


@router.patch("/sources/{source_name}", response_model=DataSourceConfigResponse)
async def update_data_source(
    source_name: str,
    data: DataSourceConfigUpdate,
    db: Session = Depends(get_db),
):
    """
    Update data source configuration (enable/disable and parameters).

    Args:
        source_name: Name of the data source
        data: New configuration

    Returns:
        Updated data source configuration

    Raises:
        HTTPException: If source not found
    """
    service = ConfigService(db)

    # Update source status
    updated_source = service.update_source_status(
        source_name=source_name,
        is_enabled=data.is_enabled,
        config_params=data.config_params,
    )

    if not updated_source:
        raise HTTPException(status_code=404, detail=f"Data source not found: {source_name}")

    # TODO: Trigger service start/stop based on new status
    # This will be implemented in Phase 4 and 5 when we add the actual services

    return updated_source
