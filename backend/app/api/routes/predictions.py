"""
Predictions API endpoints.
Provides access to prediction history, statistics, and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.self_healing import SelfHealingService
from app.models.database import TrafficData
from app.models.schemas import (
    CompletePredictionResponse,
    PredictionStats,
    ThreatPredictionResponse,
    AttackPredictionResponse,
    SelfHealingActionResponse
)
from typing import List

router = APIRouter()


@router.get("/predictions/recent", response_model=List[CompletePredictionResponse])
async def get_recent_predictions(
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get recent predictions with complete data (traffic, threat, attack, action).
    """
    threat_detector = ThreatDetectorService()

    # Get recent threat predictions
    threat_predictions = threat_detector.get_recent_predictions(db, limit)

    # Build complete response
    predictions_response = []
    for threat_pred in threat_predictions:
        traffic_record = db.query(TrafficData).filter(
            TrafficData.id == threat_pred.traffic_data_id
        ).first()

        attack_pred = traffic_record.attack_prediction if traffic_record else None
        action = attack_pred.self_healing_action if attack_pred else None

        predictions_response.append(
            CompletePredictionResponse(
                traffic_data=traffic_record,
                threat_prediction=threat_pred,
                attack_prediction=attack_pred,
                self_healing_action=action
            )
        )

    return predictions_response


@router.get("/predictions/stats", response_model=PredictionStats)
async def get_prediction_statistics(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics about predictions.
    Includes threat detection stats, attack distribution, and recent predictions.
    """
    threat_detector = ThreatDetectorService()
    attack_classifier = AttackClassifierService()

    # Get threat statistics
    threat_stats = threat_detector.get_attack_statistics(db)

    # Get attack type distribution
    attack_distribution = attack_classifier.get_attack_type_distribution(db)

    # Get recent predictions
    recent_threat_preds = threat_detector.get_recent_predictions(db, 20)
    recent_predictions = []

    for threat_pred in recent_threat_preds:
        traffic_record = db.query(TrafficData).filter(
            TrafficData.id == threat_pred.traffic_data_id
        ).first()

        attack_pred = traffic_record.attack_prediction if traffic_record else None
        action = attack_pred.self_healing_action if attack_pred else None

        recent_predictions.append(
            CompletePredictionResponse(
                traffic_data=traffic_record,
                threat_prediction=threat_pred,
                attack_prediction=attack_pred,
                self_healing_action=action
            )
        )

    return PredictionStats(
        total_predictions=threat_stats['total_predictions'],
        total_attacks=threat_stats['total_attacks'],
        total_normal=threat_stats['total_normal'],
        attack_rate=threat_stats['attack_rate'],
        attack_type_distribution=attack_distribution,
        recent_predictions=recent_predictions
    )


@router.get("/predictions/threats", response_model=List[ThreatPredictionResponse])
async def get_threat_predictions(
    limit: int = Query(default=100, le=1000),
    attacks_only: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """
    Get threat detection predictions.
    Optionally filter to only show attacks.
    """
    threat_detector = ThreatDetectorService()
    predictions = threat_detector.get_recent_predictions(db, limit)

    if attacks_only:
        predictions = [p for p in predictions if p.is_attack]

    return predictions


@router.get("/predictions/attacks", response_model=List[AttackPredictionResponse])
async def get_attack_classifications(
    limit: int = Query(default=100, le=1000),
    attack_type: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Get attack classification predictions.
    Optionally filter by specific attack type.
    """
    attack_classifier = AttackClassifierService()
    predictions = attack_classifier.get_recent_predictions(db, limit)

    if attack_type:
        predictions = [p for p in predictions if p.attack_type_name == attack_type]

    return predictions


@router.get("/predictions/actions", response_model=List[SelfHealingActionResponse])
async def get_self_healing_actions(
    limit: int = Query(default=100, le=1000),
    action_type: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Get self-healing action logs.
    Optionally filter by action type.
    """
    self_healing = SelfHealingService()
    actions = self_healing.get_recent_actions(db, limit)

    if action_type:
        actions = [a for a in actions if a.action_type == action_type]

    return actions


@router.get("/predictions/attack-distribution")
async def get_attack_distribution(db: Session = Depends(get_db)):
    """Get distribution of attack types for visualization."""
    attack_classifier = AttackClassifierService()
    distribution = attack_classifier.get_attack_type_distribution(db)

    return {
        "distribution": distribution,
        "total_attacks": sum(distribution.values())
    }


@router.get("/predictions/action-distribution")
async def get_action_distribution(db: Session = Depends(get_db)):
    """Get distribution of self-healing action types."""
    self_healing = SelfHealingService()
    stats = self_healing.get_action_statistics(db)

    return {
        "distribution": stats,
        "total_actions": sum(stats.values())
    }


@router.get("/predictions/{traffic_data_id}")
async def get_prediction_by_id(
    traffic_data_id: int,
    db: Session = Depends(get_db)
):
    """Get complete prediction data for a specific traffic record."""
    traffic_record = db.query(TrafficData).filter(
        TrafficData.id == traffic_data_id
    ).first()

    if not traffic_record:
        raise HTTPException(status_code=404, detail="Traffic data not found")

    threat_pred = traffic_record.threat_prediction
    attack_pred = traffic_record.attack_prediction
    action = attack_pred.self_healing_action if attack_pred else None

    return CompletePredictionResponse(
        traffic_data=traffic_record,
        threat_prediction=threat_pred,
        attack_prediction=attack_pred,
        self_healing_action=action
    )
