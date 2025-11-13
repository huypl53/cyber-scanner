"""
Self-Healing Service for automated response to detected attacks.
Logs actions that would be taken in response to specific attack types.
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.database import AttackPrediction, SelfHealingAction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SelfHealingService:
    """Service for logging and executing (simulated) self-healing actions."""

    # Mapping of attack types to self-healing actions
    ATTACK_ACTION_MAP = {
        'DDoS': {
            'action_type': 'restart_service',
            'description': 'Restarting service: apache2',
            'params': {'service': 'apache2'}
        },
        'DoS Hulk': {
            'action_type': 'block_ip',
            'description': 'Blocking IP address: 192.168.1.1',
            'params': {'ip': '192.168.1.1'}
        },
        'PortScan': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: Port scanning detected',
            'params': {'message': 'Port scanning detected'}
        },
        'FTP-Patator': {
            'action_type': 'block_ip',
            'description': 'Blocking IP address: 192.168.1.2',
            'params': {'ip': '192.168.1.2'}
        },
        'DoS slowloris': {
            'action_type': 'restart_service',
            'description': 'Restarting service: nginx',
            'params': {'service': 'nginx'}
        },
        'DoS Slowhttptest': {
            'action_type': 'restart_service',
            'description': 'Restarting service: nginx',
            'params': {'service': 'nginx'}
        },
        'Bot': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: Bot activity detected',
            'params': {'message': 'Bot activity detected'}
        },
        'SSH-Patator': {
            'action_type': 'block_ip',
            'description': 'Blocking IP address: 192.168.1.3',
            'params': {'ip': '192.168.1.3'}
        },
        'Web Attack – Brute Force': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: Brute force attack detected',
            'params': {'message': 'Brute force attack detected'}
        },
        'Web Attack – XSS': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: XSS attack detected',
            'params': {'message': 'XSS attack detected'}
        },
        'Infiltration': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: Infiltration detected',
            'params': {'message': 'Infiltration detected'}
        },
        'Web Attack – Sql Injection': {
            'action_type': 'alert_admin',
            'description': 'Alert admin: SQL injection detected',
            'params': {'message': 'SQL injection detected'}
        },
        'BENIGN': {
            'action_type': 'log_only',
            'description': 'No action needed for BENIGN traffic',
            'params': {}
        },
        'DoS GoldenEye': {
            'action_type': 'restart_service',
            'description': 'Restarting service: apache2',
            'params': {'service': 'apache2'}
        }
    }

    def __init__(self):
        pass

    def log_action(
        self,
        attack_prediction: AttackPrediction,
        db: Session
    ) -> SelfHealingAction:
        """
        Log self-healing action for a detected attack.

        Args:
            attack_prediction: AttackPrediction object
            db: Database session

        Returns:
            SelfHealingAction database object
        """
        attack_type = attack_prediction.attack_type_name

        # Get action mapping for this attack type
        action_config = self.ATTACK_ACTION_MAP.get(
            attack_type,
            {
                'action_type': 'log_only',
                'description': f'No action defined for {attack_type}',
                'params': {}
            }
        )

        # Create action record
        action = SelfHealingAction(
            attack_prediction_id=attack_prediction.id,
            action_type=action_config['action_type'],
            action_description=action_config['description'],
            action_params=action_config['params'],
            status='logged',  # We're only logging, not executing
            execution_time=datetime.utcnow()
        )

        # Save to database
        db.add(action)
        db.commit()
        db.refresh(action)

        # Log the action
        logger.info(
            f"Self-healing action logged: {action_config['description']} "
            f"for attack type: {attack_type}"
        )

        return action

    def log_action_batch(
        self,
        attack_predictions: list[AttackPrediction],
        db: Session
    ) -> list[SelfHealingAction]:
        """
        Log self-healing actions for multiple attack predictions.

        Args:
            attack_predictions: List of AttackPrediction objects
            db: Database session

        Returns:
            List of SelfHealingAction objects
        """
        actions = []

        for attack_pred in attack_predictions:
            attack_type = attack_pred.attack_type_name

            action_config = self.ATTACK_ACTION_MAP.get(
                attack_type,
                {
                    'action_type': 'log_only',
                    'description': f'No action defined for {attack_type}',
                    'params': {}
                }
            )

            action = SelfHealingAction(
                attack_prediction_id=attack_pred.id,
                action_type=action_config['action_type'],
                action_description=action_config['description'],
                action_params=action_config['params'],
                status='logged',
                execution_time=datetime.utcnow()
            )
            actions.append(action)

        # Bulk save
        db.add_all(actions)
        db.commit()

        # Refresh all actions
        for action in actions:
            db.refresh(action)

        return actions

    def get_action_by_attack_prediction_id(
        self,
        attack_prediction_id: int,
        db: Session
    ) -> Optional[SelfHealingAction]:
        """Get self-healing action for specific attack prediction."""
        return db.query(SelfHealingAction).filter(
            SelfHealingAction.attack_prediction_id == attack_prediction_id
        ).first()

    def get_recent_actions(
        self,
        db: Session,
        limit: int = 100
    ) -> list[SelfHealingAction]:
        """Get recent self-healing actions."""
        return db.query(SelfHealingAction).order_by(
            SelfHealingAction.created_at.desc()
        ).limit(limit).all()

    def get_action_statistics(self, db: Session) -> Dict:
        """Get statistics about self-healing actions."""
        from sqlalchemy import func

        # Count actions by type
        action_counts = db.query(
            SelfHealingAction.action_type,
            func.count(SelfHealingAction.id).label('count')
        ).group_by(
            SelfHealingAction.action_type
        ).all()

        return {
            action_type: count
            for action_type, count in action_counts
        }
