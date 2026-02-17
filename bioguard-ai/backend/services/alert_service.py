"""Alert generation and management service."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
from loguru import logger
from database.models import Alert
from database.db import SessionLocal


class AlertService:
    """Service for generating and managing disease outbreak alerts."""
    
    def __init__(self):
        """Initialize alert service."""
        self.db = SessionLocal()
    
    def create_alert(
        self,
        village_id: str,
        village_name: str,
        alert_level: str,
        risk_score: float,
        predicted_disease: str,
        trigger_reason: str,
        cases_at_risk: int = 0,
        triggered_by_sensor: bool = False,
        sensor_device_id: Optional[str] = None,
        sensor_reading_summary: Optional[str] = None,
        recommended_actions: Optional[list] = None,
        resources_required: Optional[dict] = None
    ) -> Alert:
        """Create a new alert."""
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            village_id=village_id,
            village_name=village_name,
            alert_level=alert_level,
            risk_score=risk_score,
            trigger_reason=trigger_reason,
            predicted_disease=predicted_disease,
            cases_at_risk=cases_at_risk,
            triggered_by_sensor=triggered_by_sensor,
            sensor_device_id=sensor_device_id,
            sensor_reading_summary=sensor_reading_summary,
            recommended_actions=recommended_actions or [],
            resources_required=resources_required or {},
            notification_sent=True,  # Simulated
            acknowledged=False,
            resolved=False
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"🚨 Alert created: {alert_level.upper()} for {village_name} (risk: {risk_score})")
        
        return alert
    
    def get_active_alerts(self) -> list[Alert]:
        """Get all unresolved alerts."""
        return self.db.query(Alert).filter(Alert.resolved == False).order_by(Alert.created_at.desc()).all()
    
    def get_alert_history(self, days: int = 30) -> list[Alert]:
        """Get alert history for last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return self.db.query(Alert).filter(Alert.created_at >= cutoff).order_by(Alert.created_at.desc()).all()
    
    def acknowledge_alert(self, alert_id: str, action_taken: str, notes: str, acknowledged_by: str = "System") -> Alert:
        """Acknowledge an alert."""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            alert.action_taken = action_taken
            alert.notes = notes
            self.db.commit()
            self.db.refresh(alert)
            logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> Alert:
        """Resolve an alert."""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.resolved = True
            alert.resolved_at = datetime.now()
            self.db.commit()
            self.db.refresh(alert)
            logger.info(f"✅ Alert {alert_id} resolved")
        return alert
    
    def get_alert_resources(self, alert_level: str, cases_at_risk: int, population: int = 20000) -> dict:
        """Calculate required resources for an alert."""
        
        if alert_level == "critical":
            ors_packets = max(500, cases_at_risk * 10)
            medical_staff = 8
            water_kits = 20
            chlorine_tablets = 1000
            cost_inr = 45000
        elif alert_level == "high":
            ors_packets = max(200, cases_at_risk * 8)
            medical_staff = 4
            water_kits = 10
            chlorine_tablets = 500
            cost_inr = 22000
        elif alert_level == "medium":
            ors_packets = max(100, cases_at_risk * 5)
            medical_staff = 2
            water_kits = 5
            chlorine_tablets = 250
            cost_inr = 12000
        else:
            ors_packets = 50
            medical_staff = 1
            water_kits = 2
            chlorine_tablets = 100
            cost_inr = 5000
        
        return {
            "ors_packets": ors_packets,
            "medical_staff": medical_staff,
            "water_testing_kits": water_kits,
            "chlorine_tablets": chlorine_tablets,
            "estimated_cost_inr": cost_inr,
            "nearest_medical_facility": "District Hospital",
            "response_time_estimate": "2-4 hours" if alert_level in ["critical", "high"] else "24-48 hours"
        }
    
    def seed_demo_alerts(self):
        """Seed database with demo alerts for presentation."""
        logger.info("📦 Seeding demo alerts...")
        
        # Clear existing alerts
        self.db.query(Alert).delete()
        self.db.commit()
        
        demo_alerts = [
            # Active CRITICAL alert
            {
                "village_id": "MH_SHA",
                "village_name": "Shahada",
                "alert_level": "critical",
                "risk_score": 91,
                "predicted_disease": "cholera",
                "trigger_reason": "Severe water contamination detected. Turbidity: 9.2 NTU, pH: 6.1. Multiple diarrhea cases reported.",
                "cases_at_risk": 67,
                "triggered_by_sensor": False,
                "recommended_actions": [
                    "🚨 IMMEDIATE: Deploy emergency medical team",
                    "💧 URGENT: Chlorinate all water sources",
                    "📦 Distribute 500+ ORS packets"
                ],
                "created_at": datetime.now() - timedelta(hours=2),
                "acknowledged": False,
                "resolved": False
            },
            # Active HIGH alert
            {
                "village_id": "UP_BAH",
                "village_name": "Bahraich",
                "alert_level": "high",
                "risk_score": 74,
                "predicted_disease": "typhoid",
                "trigger_reason": "Elevated TDS levels (542 ppm) and increased fever cases. Coliform count: 28 CFU.",
                "cases_at_risk": 31,
                "triggered_by_sensor": False,
                "recommended_actions": [
                    "⚠️ Deploy health workers for survey",
                    "💧 Chlorinate main water sources",
                    "📦 Distribute 200 ORS packets"
                ],
                "created_at": datetime.now() - timedelta(hours=6),
                "acknowledged": True,
                "acknowledged_at": datetime.now() - timedelta(hours=4),
                "acknowledged_by": "Dr. Sharma",
                "action_taken": "Health team dispatched, water testing initiated",
                "resolved": False
            },
            # Resolved CRITICAL
            {
                "village_id": "MH_DHA",
                "village_name": "Dharangaon",
                "alert_level": "critical",
                "risk_score": 88,
                "predicted_disease": "cholera",
                "trigger_reason": "RPI5-UNIT-002 detected turbidity spike: 8.7 NTU. AI predicted cholera outbreak.",
                "cases_at_risk": 42,
                "triggered_by_sensor": True,
                "sensor_device_id": "RPI5-UNIT-002",
                "sensor_reading_summary": "pH: 6.1, Turbidity: 8.7 NTU, TDS: 512 ppm",
                "recommended_actions": [
                    "🚨 Emergency chlorination deployed",
                    "📦 500 ORS kits distributed"
                ],
                "created_at": datetime.now() - timedelta(days=5),
                "acknowledged": True,
                "acknowledged_at": datetime.now() - timedelta(days=5, hours=2),
                "acknowledged_by": "DHO Office",
                "action_taken": "Emergency response activated, medical camp established",
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=2)
            },
            # More resolved alerts
            {
                "village_id": "MH_SHP",
                "village_name": "Shirpur",
                "alert_level": "medium",
                "risk_score": 58,
                "predicted_disease": "dysentery",
                "trigger_reason": "Moderate water quality decline, increased symptom reports",
                "cases_at_risk": 18,
                "created_at": datetime.now() - timedelta(days=8),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=4)
            },
            {
                "village_id": "UP_GON",
                "village_name": "Gonda",
                "alert_level": "medium",
                "risk_score": 52,
                "predicted_disease": "hepatitis_a",
                "trigger_reason": "Water quality index dropped to 48. Monitoring required.",
                "cases_at_risk": 12,
                "created_at": datetime.now() - timedelta(days=12),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=7)
            },
            {
                "village_id": "MH_YAW",
                "village_name": "Yawal",
                "alert_level": "high",
                "risk_score": 72,
                "predicted_disease": "cholera",
                "trigger_reason": "Contamination event detected after heavy rainfall",
                "cases_at_risk": 28,
                "created_at": datetime.now() - timedelta(days=15),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=8)
            },
            {
                "village_id": "MH_CHO",
                "village_name": "Chopda",
                "alert_level": "low",
                "risk_score": 35,
                "predicted_disease": "none",
                "trigger_reason": "Marginal water quality, preventive monitoring",
                "cases_at_risk": 5,
                "created_at": datetime.now() - timedelta(days=18),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=16)
            },
            {
                "village_id": "UP_BAL",
                "village_name": "Balrampur",
                "alert_level": "low",
                "risk_score": 32,
                "predicted_disease": "none",
                "trigger_reason": "Routine surveillance alert",
                "cases_at_risk": 3,
                "created_at": datetime.now() - timedelta(days=22),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=20)
            },
            {
                "village_id": "MH_PAC",
                "village_name": "Pachora",
                "alert_level": "medium",
                "risk_score": 48,
                "predicted_disease": "dysentery",
                "trigger_reason": "Seasonal risk elevation during monsoon",
                "cases_at_risk": 14,
                "created_at": datetime.now() - timedelta(days=25),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=18)
            },
            {
                "village_id": "UP_SHR",
                "village_name": "Shravasti",
                "alert_level": "low",
                "risk_score": 28,
                "predicted_disease": "none",
                "trigger_reason": "Preventive monitoring post-intervention",
                "cases_at_risk": 2,
                "created_at": datetime.now() - timedelta(days=30),
                "acknowledged": True,
                "resolved": True,
                "resolved_at": datetime.now() - timedelta(days=27)
            }
        ]
        
        for alert_data in demo_alerts:
            alert = Alert(**alert_data)
            self.db.add(alert)
        
        self.db.commit()
        logger.info(f"✅ Seeded {len(demo_alerts)} demo alerts")


# Global alert service instance
alert_service = AlertService()
