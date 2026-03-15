"""
Export API endpoints.
Allows exporting realtime traffic data as CSV.
"""
import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import TrafficData, ThreatPrediction, AttackPrediction
from app.models.model_loaders import (
    ATTACK_CLASSIFICATION_FEATURES,
    THREAT_DETECTION_FEATURES,
)

router = APIRouter()

MAX_RANGE = timedelta(hours=2)


def _parse_dt(value: str) -> datetime:
    """Parse ISO datetime string, ensuring timezone-aware UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/export/realtime")
async def export_realtime(
    start: str = Query(..., description="ISO 8601 start time"),
    end: str = Query(..., description="ISO 8601 end time"),
    format: str = Query("features_only", pattern="^(features_only|with_predictions)$"),
    count_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Export realtime traffic data as CSV or return count for preview."""
    try:
        start_dt = _parse_dt(start)
        end_dt = _parse_dt(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601.")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="end must be after start")

    if (end_dt - start_dt) > MAX_RANGE:
        raise HTTPException(status_code=400, detail="Time range exceeds 2-hour maximum")

    query = db.query(TrafficData).filter(
        TrafficData.created_at >= start_dt,
        TrafficData.created_at <= end_dt,
        TrafficData.source == "realtime",
    ).order_by(TrafficData.created_at.asc())

    if count_only:
        count = query.count()
        result = {
            "count": count,
            "time_range": {"start": start, "end": end},
        }
        if count > 10000:
            result["warning"] = "Large export"
        if count == 0:
            raise HTTPException(status_code=404, detail="No data found in this time range")
        return result

    records = query.all()
    if not records:
        raise HTTPException(status_code=404, detail="No data found in this time range")

    # Determine feature set from first record
    features = records[0].features or {}
    feature_count = len(features)
    if feature_count >= 35:
        feature_names = ATTACK_CLASSIFICATION_FEATURES
    else:
        feature_names = THREAT_DETECTION_FEATURES

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    headers = list(feature_names)
    if format == "with_predictions":
        headers += ["is_attack", "prediction_score", "attack_type_name", "confidence"]
    writer.writerow(headers)

    # Batch-load predictions if needed
    record_ids = [r.id for r in records]
    threat_map = {}
    attack_map = {}
    if format == "with_predictions":
        threats = db.query(ThreatPrediction).filter(
            ThreatPrediction.traffic_data_id.in_(record_ids)
        ).all()
        threat_map = {t.traffic_data_id: t for t in threats}

        attacks = db.query(AttackPrediction).filter(
            AttackPrediction.traffic_data_id.in_(record_ids)
        ).all()
        attack_map = {a.traffic_data_id: a for a in attacks}

    for record in records:
        row = [record.features.get(f, "") for f in feature_names]
        if format == "with_predictions":
            tp = threat_map.get(record.id)
            ap = attack_map.get(record.id)
            row += [
                tp.is_attack if tp else "",
                tp.prediction_score if tp else "",
                ap.attack_type_name if ap else "",
                ap.confidence if ap else "",
            ]
        writer.writerow(row)

    output.seek(0)
    filename = f"realtime-export-{start_dt.strftime('%Y%m%dT%H%M%S')}-{end_dt.strftime('%Y%m%dT%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
