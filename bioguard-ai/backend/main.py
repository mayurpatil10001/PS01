"""BioGuard AI - Main FastAPI application.

Water-borne disease outbreak early warning system for rural India.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config import settings
from database.db import init_db
from database.models import Alert
from ml.predictor import predictor
from ml.data_generator import VILLAGES
from sensors.sensor_manager import sensor_manager
from services.alert_service import alert_service

# Import routers
from routers import predictions, analytics, alerts, raspberry_pi

# Configure logging
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Background task for sensor updates
async def sensor_update_loop():
    """Background task that generates sensor readings and checks for anomalies."""
    while True:
        try:
            device_ids = sensor_manager.get_all_device_ids()
            
            for device_id in device_ids:
                try:
                    # Get new reading
                    reading = await sensor_manager.get_reading(device_id)
                    
                    # Broadcast sensor update
                    await manager.broadcast({
                        "type": "sensor",
                        "payload": {
                            "device_id": reading.device_id,
                            "village_id": reading.village_id,
                            "village_name": reading.village_name,
                            "ph_level": reading.ph_level,
                            "turbidity_ntu": reading.turbidity_ntu,
                            "tds_ppm": reading.tds_ppm,
                            "water_temp_celsius": reading.water_temp_celsius,
                            "quality_status": reading.quality_status,
                            "anomaly_detected": reading.anomaly_detected,
                            "anomaly_type": reading.anomaly_type,
                            "timestamp": reading.timestamp.isoformat()
                        }
                    })
                    
                    # Check for anomalies and create alerts
                    if reading.anomaly_detected and reading.anomaly_type:
                        # Get prediction for this village
                        pred = predictor.predict(reading.village_id)
                        
                        # Create alert if risk is high enough
                        if pred["risk_score"] >= 60:
                            alert = alert_service.create_alert(
                                village_id=reading.village_id,
                                village_name=reading.village_name,
                                alert_level=pred["alert_level"],
                                risk_score=pred["risk_score"],
                                predicted_disease=pred["predicted_disease"],
                                trigger_reason=f"Sensor anomaly detected: {reading.anomaly_type}. {reading.quality_status.upper()} water quality.",
                                cases_at_risk=pred["cases_predicted_next_7_days"],
                                triggered_by_sensor=True,
                                sensor_device_id=device_id,
                                sensor_reading_summary=f"pH: {reading.ph_level}, Turbidity: {reading.turbidity_ntu} NTU, TDS: {reading.tds_ppm} ppm",
                                recommended_actions=pred["recommended_actions"],
                                resources_required=alert_service.get_alert_resources(pred["alert_level"], pred["cases_predicted_next_7_days"])
                            )
                            
                            # Broadcast alert
                            await manager.broadcast({
                                "type": "alert",
                                "payload": {
                                    "alert_id": alert.alert_id,
                                    "village_name": alert.village_name,
                                    "alert_level": alert.alert_level,
                                    "risk_score": alert.risk_score,
                                    "trigger_reason": alert.trigger_reason,
                                    "predicted_disease": alert.predicted_disease,
                                    "triggered_by_sensor": True,
                                    "sensor_device_id": device_id
                                }
                            })
                
                except Exception as e:
                    logger.error(f"Error processing device {device_id}: {e}")
            
            # Wait for next update interval
            await asyncio.sleep(settings.mock_update_interval)
        
        except Exception as e:
            logger.error(f"Error in sensor update loop: {e}")
            await asyncio.sleep(5)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 BioGuard AI starting up...")
    
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    # Seed demo alerts
    alert_service.seed_demo_alerts()
    
    # Train ML model
    try:
        predictor.train()
    except Exception as e:
        logger.warning(f"⚠️  ML training failed: {e}. Using demo predictions.")
    
    # Start background sensor update task
    sensor_task = asyncio.create_task(sensor_update_loop())
    
    logger.info("=" * 60)
    logger.info("🟢 BioGuard AI ready")
    logger.info(f"   Sensor mode: {settings.sensor_mode.upper()}")
    logger.info(f"   Pi integration: {'ACTIVE' if settings.sensor_mode == 'pi' else 'READY'}")
    logger.info(f"   Villages monitored: {len(VILLAGES)}")
    logger.info(f"   Devices configured: {len(sensor_manager.get_all_device_ids())}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    sensor_task.cancel()
    logger.info("👋 BioGuard AI shutting down...")

# Create FastAPI app
app = FastAPI(
    title="BioGuard AI",
    description="Water-borne disease outbreak early warning system for rural India",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(raspberry_pi.router)

# WebSocket endpoint
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    
    try:
        # Send initial summary on connect
        from routers.analytics import get_summary_stats
        from routers.raspberry_pi import get_all_devices
        
        summary = await get_summary_stats()
        devices = await get_all_devices()
        
        await websocket.send_json({
            "type": "init",
            "payload": {
                "summary": summary,
                "devices": devices
            }
        })
        
        # Keep connection alive
        while True:
            # Wait for messages from client (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    active_alerts = len(alert_service.get_active_alerts())
    devices_online = 0
    device_ids = sensor_manager.get_all_device_ids()
    
    for device_id in device_ids:
        try:
            status = await sensor_manager.get_device_status(device_id)
            if status.is_online:
                devices_online += 1
        except:
            pass
    
    return {
        "status": "healthy",
        "sensor_mode": settings.sensor_mode,
        "pi_integration_status": "ready — set SENSOR_MODE=pi to activate",
        "ml_model_loaded": predictor.trained,
        "active_alerts": active_alerts,
        "devices_online": devices_online,
        "devices_total": len(device_ids),
        "uptime_seconds": 0  # Would track actual uptime
    }

# Demo scenario endpoints
@app.post("/api/demo/scenario/{scenario_num}")
async def trigger_demo_scenario(scenario_num: int):
    """Trigger demo scenarios for presentation."""
    
    if scenario_num == 1:
        # SCENARIO 1: Live Outbreak Trigger
        logger.info("🚨 SCENARIO 1: Dharangaon cholera outbreak simulated")
        
        # Create critical alert
        alert = alert_service.create_alert(
            village_id="MH_DHA",
            village_name="Dharangaon",
            alert_level="critical",
            risk_score=94,
            predicted_disease="cholera",
            trigger_reason="Raspberry Pi sensor RPI5-UNIT-002 detected water contamination. Turbidity: 8.7 NTU (CRITICAL), pH: 6.1 (dangerously low). ML model classified as cholera risk with 91% confidence.",
            cases_at_risk=47,
            triggered_by_sensor=True,
            sensor_device_id="RPI5-UNIT-002",
            sensor_reading_summary="pH: 6.1, Turbidity: 8.7 NTU, TDS: 512 ppm",
            recommended_actions=[
                "🚨 IMMEDIATE: Deploy emergency medical team to village",
                "💧 URGENT: Chlorinate all water sources (2-3 ppm)",
                "📦 Distribute 500+ ORS packets door-to-door",
                "🏥 Establish temporary medical camp within 24 hours"
            ],
            resources_required=alert_service.get_alert_resources("critical", 47)
        )
        
        # Broadcast alert
        await manager.broadcast({
            "type": "alert",
            "payload": {
                "alert_id": alert.alert_id,
                "village_name": "Dharangaon",
                "alert_level": "critical",
                "risk_score": 94,
                "trigger_reason": alert.trigger_reason,
                "predicted_disease": "cholera"
            }
        })
        
        return {
            "scenario": 1,
            "title": "Live Outbreak Trigger",
            "alert": {
                "alert_id": alert.alert_id,
                "village_name": "Dharangaon",
                "alert_level": "critical",
                "risk_score": 94,
                "predicted_disease": "cholera",
                "confidence": 91
            },
            "story": "Raspberry Pi sensor RPI5-UNIT-002 detected water contamination. ML model classified as cholera risk with 91% confidence. Alert dispatched to District Health Officer within 30 seconds."
        }
    
    elif scenario_num == 2:
        # SCENARIO 2: Pi Saved the Day
        timeline = [
            {
                "day": -3,
                "event": "RPI5-UNIT-002 detected turbidity=4.2 NTU",
                "type": "sensor_warning",
                "risk_score": 44,
                "alert": "low"
            },
            {
                "day": -2,
                "event": "Turbidity rising: 5.8 NTU. AI predicts HIGH risk",
                "type": "ai_prediction",
                "risk_score": 68,
                "alert": "high"
            },
            {
                "day": -1,
                "event": "Turbidity: 7.1 NTU. CRITICAL alert sent to DHO",
                "type": "critical_alert",
                "risk_score": 88,
                "alert": "critical"
            },
            {
                "day": 0,
                "event": "First human cases reported (without Pi: this would be Day 0 detection, 3 days too late)",
                "type": "human_detection",
                "risk_score": 94
            },
            {
                "day": 1,
                "event": "Emergency chlorination deployed. 200 ORS kits distributed. Medical camp established.",
                "type": "intervention"
            },
            {
                "day": 4,
                "event": "Risk score declining: 61. Outbreak contained.",
                "type": "resolution",
                "risk_score": 61
            },
            {
                "day": 7,
                "event": "Village cleared. 47 cases prevented. ₹2.3L saved.",
                "type": "outcome",
                "cases_prevented": 47,
                "savings_inr": 230000
            }
        ]
        
        return {
            "scenario": 2,
            "title": "Pi Saved the Day - Early Detection Story",
            "timeline": timeline,
            "story": "Without Raspberry Pi IoT monitoring, this outbreak would have been detected 3 days later with 47+ more cases. Early sensor detection + AI prediction = lives saved.",
            "key_insight": "72 hours early detection enabled by IoT sensors"
        }
    
    elif scenario_num == 3:
        # SCENARIO 3: Intervention Success
        return {
            "scenario": 3,
            "title": "Intervention Success - Yawal Recovery",
            "before_intervention": {
                "risk_score": 72,
                "alert": "high",
                "water_quality": 41,
                "active_cases": 18
            },
            "interventions_deployed": [
                {
                    "action": "Emergency chlorination of main water source",
                    "date": "Day 1",
                    "cost_inr": 4500
                },
                {
                    "action": "200 ORS kits distributed door-to-door",
                    "date": "Day 1",
                    "cost_inr": 3000
                },
                {
                    "action": "Water testing kits deployed (5 units)",
                    "date": "Day 2",
                    "cost_inr": 7500
                },
                {
                    "action": "Health worker village visit + awareness session",
                    "date": "Day 2",
                    "cost_inr": 1200
                },
                {
                    "action": "Weekly monitoring protocol activated",
                    "date": "Day 3",
                    "cost_inr": 500
                }
            ],
            "recovery_timeline": [
                {"day": 0, "risk": 72},
                {"day": 1, "risk": 65},
                {"day": 2, "risk": 51},
                {"day": 3, "risk": 40},
                {"day": 5, "risk": 28},
                {"day": 7, "risk": 18}
            ],
            "outcome": {
                "cases_prevented": 47,
                "total_cost_inr": 16700,
                "cost_per_case_prevented_inr": 355,
                "estimated_hospital_cost_averted_inr": 234000,
                "roi": "14x return on intervention investment",
                "current_risk_score": 18,
                "current_alert_level": "baseline"
            }
        }
    
    else:
        return {"error": "Invalid scenario number. Use 1, 2, or 3."}

@app.get("/api/demo/reset")
async def reset_demo():
    """Reset demo scenarios."""
    logger.info("🔄 Resetting demo scenarios...")
    
    # Re-seed alerts
    alert_service.seed_demo_alerts()
    
    return {
        "status": "reset complete",
        "message": "All scenarios cleared. Demo alerts re-seeded."
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "BioGuard AI",
        "description": "Water-borne disease outbreak early warning system for rural India",
        "version": "1.0.0",
        "sensor_mode": settings.sensor_mode,
        "pi_integration": "ready",
        "docs": "/docs"
    }
