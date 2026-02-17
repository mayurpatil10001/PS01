"""Alerts API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.alert_service import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AcknowledgeRequest(BaseModel):
    """Request model for acknowledging an alert."""
    action_taken: str
    notes: str
    acknowledged_by: str = "System User"


@router.get("/active")
async def get_active_alerts():
    """Get all active (unresolved) alerts."""
    alerts = alert_service.get_active_alerts()
    
    return [
        {
            "alert_id": alert.alert_id,
            "created_at": alert.created_at,
            "village_id": alert.village_id,
            "village_name": alert.village_name,
            "alert_level": alert.alert_level,
            "risk_score": alert.risk_score,
            "trigger_reason": alert.trigger_reason,
            "predicted_disease": alert.predicted_disease,
            "cases_at_risk": alert.cases_at_risk,
            "triggered_by_sensor": alert.triggered_by_sensor,
            "sensor_device_id": alert.sensor_device_id,
            "sensor_reading_summary": alert.sensor_reading_summary,
            "recommended_actions": alert.recommended_actions,
            "acknowledged": alert.acknowledged,
            "acknowledged_at": alert.acknowledged_at,
            "acknowledged_by": alert.acknowledged_by,
            "action_taken": alert.action_taken
        }
        for alert in alerts
    ]


@router.get("/history")
async def get_alert_history():
    """Get alert history for last 30 days."""
    alerts = alert_service.get_alert_history(days=30)
    
    return [
        {
            "alert_id": alert.alert_id,
            "created_at": alert.created_at,
            "village_id": alert.village_id,
            "village_name": alert.village_name,
            "alert_level": alert.alert_level,
            "risk_score": alert.risk_score,
            "trigger_reason": alert.trigger_reason,
            "predicted_disease": alert.predicted_disease,
            "cases_at_risk": alert.cases_at_risk,
            "triggered_by_sensor": alert.triggered_by_sensor,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at
        }
        for alert in alerts
    ]


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest):
    """Acknowledge an alert."""
    alert = alert_service.acknowledge_alert(
        alert_id=alert_id,
        action_taken=request.action_taken,
        notes=request.notes,
        acknowledged_by=request.acknowledged_by
    )
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "alert_id": alert_id,
        "acknowledged_at": alert.acknowledged_at,
        "acknowledged_by": alert.acknowledged_by
    }


@router.get("/resources/{alert_id}")
async def get_alert_resources(alert_id: str):
    """Get required resources for an alert."""
    alerts = alert_service.get_active_alerts() + alert_service.get_alert_history(days=30)
    alert = next((a for a in alerts if a.alert_id == alert_id), None)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    resources = alert_service.get_alert_resources(
        alert_level=alert.alert_level,
        cases_at_risk=alert.cases_at_risk
    )
    
    return resources
