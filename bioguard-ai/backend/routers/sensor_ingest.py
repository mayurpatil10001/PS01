"""Sensor data ingestion endpoint for Raspberry Pi devices."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User
from auth.auth import require_pi_sender
from ml.predictor import predictor
from services.alert_service import alert_service

router = APIRouter(prefix="/api/sensor-data", tags=["Sensor Ingestion"])


# Request/Response models
class SensorSubmission(BaseModel):
    device_id: str
    village_id: str
    ph_level: float
    turbidity_ntu: float
    tds_ppm: float
    water_temp_celsius: float
    air_temp_celsius: float
    humidity_percent: float
    flow_rate_lpm: float
    submitted_at: Optional[datetime] = None
    is_demo_data: bool = True
    demo_scenario: Optional[str] = None


class SensorSubmissionResponse(BaseModel):
    received: bool
    device_id: str
    village_id: str
    village_name: str
    prediction: dict
    alert_triggered: bool
    alert_level: Optional[str] = None
    message: str


class DemoScenario(BaseModel):
    id: str
    label: str
    description: str
    icon: str
    expected_alert: str
    values: dict


@router.post("/submit", response_model=SensorSubmissionResponse)
async def submit_sensor_data(
    submission: SensorSubmission,
    current_user: User = Depends(require_pi_sender),
    db: Session = Depends(get_db)
):
    """
    Submit sensor data from Raspberry Pi device.
    
    This endpoint:
    1. Validates device_id and village_id match the Pi's JWT token
    2. Stores raw reading in database (future enhancement)
    3. Runs ML prediction using the new sensor data
    4. Updates village's current prediction
    5. Checks if new alert should be generated
    6. Broadcasts via WebSocket to all Analyzer clients
    7. Returns prediction and alert status
    """
    # Validate device_id matches token
    if submission.device_id != current_user.device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device ID mismatch. Your token is for device {current_user.device_id}, but you submitted data for {submission.device_id}"
        )
    
    # Validate village_id matches token
    if submission.village_id != current_user.village_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Village ID mismatch. Your device is assigned to {current_user.village_id}, but you submitted data for {submission.village_id}"
        )
    
    # Set submission timestamp if not provided
    if not submission.submitted_at:
        submission.submitted_at = datetime.utcnow()
    
    # Run ML prediction for this village
    # The predictor will use the village_id to generate prediction
    prediction = predictor.predict(submission.village_id)
    
    # Check if we should create an alert
    alert_triggered = False
    alert_level = None
    new_alert = None
    
    # Create alert if risk score is high enough
    if prediction["risk_score"] >= 60:
        # Build sensor reading summary
        sensor_summary = (
            f"pH: {submission.ph_level}, "
            f"Turbidity: {submission.turbidity_ntu} NTU, "
            f"TDS: {submission.tds_ppm} ppm, "
            f"Water Temp: {submission.water_temp_celsius}°C"
        )
        
        # Build trigger reason
        trigger_reason = (
            f"Raspberry Pi sensor {submission.device_id} submitted new reading. "
            f"{sensor_summary}. "
        )
        
        if submission.is_demo_data and submission.demo_scenario:
            trigger_reason += f"Demo scenario: {submission.demo_scenario}. "
        
        trigger_reason += (
            f"ML model classified as {prediction['predicted_disease']} risk "
            f"with {prediction['confidence']}% confidence."
        )
        
        # Create alert
        new_alert = alert_service.create_alert(
            village_id=submission.village_id,
            village_name=current_user.village_name,
            alert_level=prediction["alert_level"],
            risk_score=prediction["risk_score"],
            predicted_disease=prediction["predicted_disease"],
            trigger_reason=trigger_reason,
            cases_at_risk=prediction["cases_predicted_next_7_days"],
            triggered_by_sensor=True,
            sensor_device_id=submission.device_id,
            sensor_reading_summary=sensor_summary,
            recommended_actions=prediction["recommended_actions"],
            resources_required=alert_service.get_alert_resources(
                prediction["alert_level"],
                prediction["cases_predicted_next_7_days"]
            )
        )
        
        alert_triggered = True
        alert_level = prediction["alert_level"]
    
    # Broadcast to WebSocket clients (if manager is available)
    # This will be handled by importing the manager from main.py
    try:
        from main import manager
        
        await manager.broadcast({
            "type": "sensor_update",
            "payload": {
                "device_id": submission.device_id,
                "village_id": submission.village_id,
                "village_name": current_user.village_name,
                "sensor_reading": {
                    "ph_level": submission.ph_level,
                    "turbidity_ntu": submission.turbidity_ntu,
                    "tds_ppm": submission.tds_ppm,
                    "water_temp_celsius": submission.water_temp_celsius,
                    "air_temp_celsius": submission.air_temp_celsius,
                    "humidity_percent": submission.humidity_percent,
                    "flow_rate_lpm": submission.flow_rate_lpm,
                    "submitted_at": submission.submitted_at.isoformat()
                },
                "updated_prediction": prediction,
                "new_alert": {
                    "alert_id": new_alert.alert_id,
                    "alert_level": new_alert.alert_level,
                    "risk_score": new_alert.risk_score,
                    "predicted_disease": new_alert.predicted_disease,
                    "trigger_reason": new_alert.trigger_reason
                } if new_alert else None,
                "submitted_by": "pi_sender",
                "is_demo_data": submission.is_demo_data,
                "demo_scenario": submission.demo_scenario,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        # WebSocket broadcast failed, but that's okay
        pass
    
    # Build response message
    message = f"Data received from {submission.device_id} for {current_user.village_name}. "
    if alert_triggered:
        message += f"{alert_level.upper()} alert triggered. "
    message += f"Risk score: {prediction['risk_score']}, Disease: {prediction['predicted_disease']}"
    
    return SensorSubmissionResponse(
        received=True,
        device_id=submission.device_id,
        village_id=submission.village_id,
        village_name=current_user.village_name,
        prediction=prediction,
        alert_triggered=alert_triggered,
        alert_level=alert_level,
        message=message
    )


@router.get("/demo-scenarios", response_model=list[DemoScenario])
async def get_demo_scenarios(current_user: User = Depends(require_pi_sender)):
    """
    Get available demo scenarios for Pi sender to simulate.
    
    Each scenario represents a different water quality condition
    that will trigger different alert levels.
    """
    scenarios = [
        DemoScenario(
            id="normal",
            label="Normal Conditions",
            description="Safe water quality, no disease risk",
            icon="✅",
            expected_alert="baseline",
            values={
                "ph_level": 7.2,
                "turbidity_ntu": 1.1,
                "tds_ppm": 312,
                "water_temp_celsius": 26.5,
                "air_temp_celsius": 28.3,
                "humidity_percent": 65.2,
                "flow_rate_lpm": 12.4
            }
        ),
        DemoScenario(
            id="high_turbidity",
            label="High Turbidity Warning",
            description="Turbidity spike detected, potential contamination",
            icon="⚠️",
            expected_alert="medium",
            values={
                "ph_level": 6.9,
                "turbidity_ntu": 5.8,
                "tds_ppm": 445,
                "water_temp_celsius": 27.1,
                "air_temp_celsius": 29.8,
                "humidity_percent": 72.5,
                "flow_rate_lpm": 10.2
            }
        ),
        DemoScenario(
            id="cholera_risk",
            label="Cholera Risk — CRITICAL",
            description="Dangerous water quality + symptom cluster detected",
            icon="🚨",
            expected_alert="critical",
            values={
                "ph_level": 6.1,
                "turbidity_ntu": 8.7,
                "tds_ppm": 512,
                "water_temp_celsius": 28.4,
                "air_temp_celsius": 31.2,
                "humidity_percent": 78.9,
                "flow_rate_lpm": 8.1
            }
        ),
        DemoScenario(
            id="typhoid_risk",
            label="Typhoid Risk — HIGH",
            description="Contaminated water source, rising fever cases",
            icon="🔴",
            expected_alert="high",
            values={
                "ph_level": 6.4,
                "turbidity_ntu": 4.2,
                "tds_ppm": 487,
                "water_temp_celsius": 27.8,
                "air_temp_celsius": 30.5,
                "humidity_percent": 75.3,
                "flow_rate_lpm": 9.3
            }
        ),
        DemoScenario(
            id="improving",
            label="Post-Intervention Recovery",
            description="Chlorination deployed, water quality improving",
            icon="📈",
            expected_alert="low",
            values={
                "ph_level": 7.0,
                "turbidity_ntu": 2.1,
                "tds_ppm": 380,
                "water_temp_celsius": 26.8,
                "air_temp_celsius": 28.9,
                "humidity_percent": 68.4,
                "flow_rate_lpm": 11.7
            }
        ),
        DemoScenario(
            id="critical_event",
            label="Emergency — Mass Outbreak",
            description="Extreme contamination, immediate response required",
            icon="💀",
            expected_alert="critical",
            values={
                "ph_level": 5.8,
                "turbidity_ntu": 12.4,
                "tds_ppm": 620,
                "water_temp_celsius": 29.2,
                "air_temp_celsius": 32.7,
                "humidity_percent": 82.1,
                "flow_rate_lpm": 6.8
            }
        )
    ]
    
    return scenarios
