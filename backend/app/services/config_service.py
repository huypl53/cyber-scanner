"""
Configuration Service
Manages data source configurations (enable/disable states and parameters).
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.database import DataSourceConfig
from app.models.schemas import DataSourceConfigUpdate

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing data source configuration"""

    # Default source configurations
    DEFAULT_SOURCES = [
        {
            "source_name": "packet_capture",
            "description": "Network packet capture from server interface",
            "is_enabled": False,
            "config_params": {"interface": "any", "buffer_size": 1000},
        },
        {
            "source_name": "external_kafka",
            "description": "External data providers via Kafka",
            "is_enabled": False,
            "config_params": {"topic": "external-traffic"},
        },
        {
            "source_name": "internal_kafka",
            "description": "Internal test data stream",
            "is_enabled": True,
            "config_params": {"topic": "network-traffic"},
        },
    ]

    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_configs()

    def _ensure_default_configs(self):
        """
        Initialize default data source configs if they don't exist.
        This is called on service initialization.
        """
        try:
            for source_config in self.DEFAULT_SOURCES:
                existing = (
                    self.db.query(DataSourceConfig)
                    .filter(DataSourceConfig.source_name == source_config["source_name"])
                    .first()
                )

                if not existing:
                    config = DataSourceConfig(**source_config)
                    self.db.add(config)
                    logger.info(f"Created default config for source: {source_config['source_name']}")

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error initializing default configs: {e}")

    def is_source_enabled(self, source_name: str) -> bool:
        """
        Check if a data source is enabled.

        Args:
            source_name: Name of the data source

        Returns:
            bool: True if enabled, False otherwise
        """
        try:
            config = (
                self.db.query(DataSourceConfig)
                .filter(DataSourceConfig.source_name == source_name)
                .first()
            )
            return config.is_enabled if config else False
        except Exception as e:
            logger.error(f"Error checking if source {source_name} is enabled: {e}")
            return False

    def get_source(self, source_name: str) -> Optional[DataSourceConfig]:
        """
        Get configuration for a specific data source.

        Args:
            source_name: Name of the data source

        Returns:
            Optional[DataSourceConfig]: Configuration or None if not found
        """
        try:
            return (
                self.db.query(DataSourceConfig)
                .filter(DataSourceConfig.source_name == source_name)
                .first()
            )
        except Exception as e:
            logger.error(f"Error fetching source config for {source_name}: {e}")
            return None

    def get_all_sources(self) -> List[DataSourceConfig]:
        """
        Get all data source configurations.

        Returns:
            List[DataSourceConfig]: List of all source configs
        """
        try:
            return self.db.query(DataSourceConfig).order_by(DataSourceConfig.source_name).all()
        except Exception as e:
            logger.error(f"Error fetching all source configs: {e}")
            return []

    def update_source_status(
        self, source_name: str, is_enabled: bool, config_params: Optional[Dict[str, Any]] = None
    ) -> Optional[DataSourceConfig]:
        """
        Enable or disable a data source.

        Args:
            source_name: Name of the data source
            is_enabled: New enabled state
            config_params: Optional configuration parameters to update

        Returns:
            Optional[DataSourceConfig]: Updated config or None if not found
        """
        try:
            config = self.get_source(source_name)
            if not config:
                logger.warning(f"Data source not found: {source_name}")
                return None

            # Update status
            old_status = config.is_enabled
            config.is_enabled = is_enabled

            # Update config params if provided
            if config_params is not None:
                config.config_params = config_params

            self.db.commit()
            self.db.refresh(config)

            logger.info(
                f"Updated {source_name}: {'enabled' if is_enabled else 'disabled'} (was {'enabled' if old_status else 'disabled'})"
            )
            return config
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating source {source_name}: {e}")
            return None

    def get_enabled_sources(self) -> List[DataSourceConfig]:
        """
        Get all enabled data sources.

        Returns:
            List[DataSourceConfig]: List of enabled sources
        """
        try:
            return (
                self.db.query(DataSourceConfig)
                .filter(DataSourceConfig.is_enabled == True)
                .all()
            )
        except Exception as e:
            logger.error(f"Error fetching enabled sources: {e}")
            return []

    def get_config_param(self, source_name: str, param_key: str) -> Optional[Any]:
        """
        Get a specific configuration parameter for a data source.

        Args:
            source_name: Name of the data source
            param_key: Key of the parameter to retrieve

        Returns:
            Optional[Any]: Parameter value or None if not found
        """
        try:
            config = self.get_source(source_name)
            if config and config.config_params:
                return config.config_params.get(param_key)
            return None
        except Exception as e:
            logger.error(f"Error getting config param {param_key} for {source_name}: {e}")
            return None

    def update_config_param(
        self, source_name: str, param_key: str, param_value: Any
    ) -> Optional[DataSourceConfig]:
        """
        Update a specific configuration parameter.

        Args:
            source_name: Name of the data source
            param_key: Key of the parameter to update
            param_value: New value for the parameter

        Returns:
            Optional[DataSourceConfig]: Updated config or None if not found
        """
        try:
            config = self.get_source(source_name)
            if not config:
                return None

            if config.config_params is None:
                config.config_params = {}

            config.config_params[param_key] = param_value
            self.db.commit()
            self.db.refresh(config)

            logger.info(f"Updated {source_name} config param: {param_key}={param_value}")
            return config
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating config param for {source_name}: {e}")
            return None
