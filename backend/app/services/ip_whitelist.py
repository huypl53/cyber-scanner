"""
IP Whitelist Service
Manages IP whitelist for external data providers with validation and CRUD operations.
"""

import ipaddress
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.database import IPWhitelist
from app.models.schemas import IPWhitelistCreate, IPWhitelistUpdate

logger = logging.getLogger(__name__)


class IPWhitelistService:
    """Service for managing IP whitelist operations"""

    def __init__(self, db: Session):
        self.db = db

    def is_ip_allowed(self, ip: str) -> bool:
        """
        Check if an IP address is in the whitelist and active.

        Args:
            ip: IP address to check (IPv4 or IPv6)

        Returns:
            bool: True if IP is whitelisted and active, False otherwise
        """
        try:
            record = (
                self.db.query(IPWhitelist)
                .filter(IPWhitelist.ip_address == ip, IPWhitelist.is_active == True)
                .first()
            )
            return record is not None
        except Exception as e:
            logger.error(f"Error checking IP whitelist for {ip}: {e}")
            return False

    def validate_ip_address(self, ip: str) -> bool:
        """
        Validate IP address format (IPv4 or IPv6).

        Args:
            ip: IP address string to validate

        Returns:
            bool: True if valid IP address, False otherwise
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def add_ip(
        self, ip: str, description: Optional[str] = None, created_by: Optional[str] = None
    ) -> IPWhitelist:
        """
        Add an IP address to the whitelist.

        Args:
            ip: IP address to add
            description: Optional description
            created_by: Optional user who created this entry

        Returns:
            IPWhitelist: Created whitelist entry

        Raises:
            ValueError: If IP is invalid or already exists
        """
        # Validate IP format
        if not self.validate_ip_address(ip):
            raise ValueError(f"Invalid IP address format: {ip}")

        # Check if already exists
        existing = self.db.query(IPWhitelist).filter(IPWhitelist.ip_address == ip).first()
        if existing:
            raise ValueError(f"IP address already exists in whitelist: {ip}")

        # Create new entry
        whitelist_entry = IPWhitelist(
            ip_address=ip, description=description, is_active=True, created_by=created_by
        )

        try:
            self.db.add(whitelist_entry)
            self.db.commit()
            self.db.refresh(whitelist_entry)
            logger.info(f"Added IP to whitelist: {ip}")
            return whitelist_entry
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database error adding IP {ip}: {e}")
            raise ValueError(f"Failed to add IP to whitelist: {ip}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error adding IP {ip}: {e}")
            raise

    def get_all(self, active_only: bool = False) -> List[IPWhitelist]:
        """
        Get all whitelisted IPs.

        Args:
            active_only: If True, return only active IPs

        Returns:
            List[IPWhitelist]: List of whitelist entries
        """
        try:
            query = self.db.query(IPWhitelist)
            if active_only:
                query = query.filter(IPWhitelist.is_active == True)
            return query.order_by(IPWhitelist.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching IP whitelist: {e}")
            return []

    def get_by_id(self, ip_id: int) -> Optional[IPWhitelist]:
        """
        Get whitelist entry by ID.

        Args:
            ip_id: ID of the whitelist entry

        Returns:
            Optional[IPWhitelist]: Whitelist entry or None
        """
        try:
            return self.db.query(IPWhitelist).filter(IPWhitelist.id == ip_id).first()
        except Exception as e:
            logger.error(f"Error fetching IP whitelist entry {ip_id}: {e}")
            return None

    def update_ip(self, ip_id: int, update_data: IPWhitelistUpdate) -> Optional[IPWhitelist]:
        """
        Update whitelist entry.

        Args:
            ip_id: ID of the entry to update
            update_data: Fields to update

        Returns:
            Optional[IPWhitelist]: Updated entry or None if not found
        """
        try:
            record = self.get_by_id(ip_id)
            if not record:
                return None

            # Update fields if provided
            if update_data.description is not None:
                record.description = update_data.description
            if update_data.is_active is not None:
                record.is_active = update_data.is_active

            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Updated IP whitelist entry {ip_id}")
            return record
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating IP whitelist entry {ip_id}: {e}")
            return None

    def delete_ip(self, ip_id: int) -> bool:
        """
        Delete IP from whitelist.

        Args:
            ip_id: ID of the entry to delete

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            record = self.get_by_id(ip_id)
            if not record:
                return False

            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted IP from whitelist: {record.ip_address} (ID: {ip_id})")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting IP whitelist entry {ip_id}: {e}")
            return False

    def get_count(self, active_only: bool = False) -> int:
        """
        Get count of whitelisted IPs.

        Args:
            active_only: If True, count only active IPs

        Returns:
            int: Count of IPs
        """
        try:
            query = self.db.query(IPWhitelist)
            if active_only:
                query = query.filter(IPWhitelist.is_active == True)
            return query.count()
        except Exception as e:
            logger.error(f"Error counting IP whitelist entries: {e}")
            return 0
