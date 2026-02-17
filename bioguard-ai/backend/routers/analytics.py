"""Analytics API router."""
from fastapi import APIRouter
from datetime import datetime, timedelta
import random
from ml.predictor import predictor
from ml.data_generator import VILLAGES
from sensors.sensor_manager import sensor_manager
from services.alert_service import alert_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary_stats():
    """Get dashboard summary statistics."""
    
    # Get all predictions
    predictions = []
    for village in VILLAGES:
        pred = predictor.predict(village["id"])
        predictions.append(pred)
    
    # Count by alert level
    alert_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "baseline": 0}
    total_cases = 0
    wqi_values = []
    
    for pred in predictions:
        alert_level = pred["alert_level"]
        alert_counts[alert_level] = alert_counts.get(alert_level, 0) + 1
        total_cases += pred.get("cases_predicted_next_7_days", 0)
        wqi_values.append(pred.get("water_quality_index", 70))
    
    # Device status
    device_ids = sensor_manager.get_all_device_ids()
    devices_online = 0
    for device_id in device_ids:
        try:
            status = await sensor_manager.get_device_status(device_id)
            if status.is_online:
                devices_online += 1
        except:
            pass
    
    return {
        "total_villages": len(VILLAGES),
        "critical_count": alert_counts.get("critical", 0),
        "high_count": alert_counts.get("high", 0),
        "medium_count": alert_counts.get("medium", 0),
        "low_count": alert_counts.get("low", 0),
        "baseline_count": alert_counts.get("baseline", 0),
        "total_cases_active": total_cases,
        "cases_prevented_this_month": 47,
        "healthcare_cost_saved_inr": 1240000,
        "avg_water_quality_index": round(sum(wqi_values) / len(wqi_values), 1) if wqi_values else 70.0,
        "sensor_devices_online": devices_online,
        "sensor_devices_total": len(device_ids),
        "sensor_mode": "mock" if sensor_manager.is_mock_mode() else "pi",
        "pi_integration_status": "ready",
        "last_updated": datetime.now()
    }


@router.get("/disease-trend")
async def get_disease_trend():
    """Get 90-day disease trend data."""
    
    # Generate mock trend data for last 90 days
    trend_data = []
    start_date = datetime.now() - timedelta(days=90)
    
    for week in range(13):  # 13 weeks
        week_date = start_date + timedelta(weeks=week)
        
        trend_data.append({
            "week": week_date.strftime("%b %d"),
            "cholera": random.randint(2, 15),
            "typhoid": random.randint(1, 12),
            "dysentery": random.randint(3, 18),
            "hepatitis_a": random.randint(1, 8),
            "rotavirus": random.randint(2, 10)
        })
    
    return trend_data


@router.get("/risk-history/{village_id}")
async def get_risk_history(village_id: str):
    """Get 30-day risk score history for a village."""
    
    # Generate mock historical data
    history = []
    current_pred = predictor.predict(village_id)
    current_risk = current_pred["risk_score"]
    
    for day in range(30, 0, -1):
        date = datetime.now() - timedelta(days=day)
        
        # Add some variation around current risk
        variation = random.gauss(0, 8)
        risk_score = max(0, min(100, current_risk + variation))
        
        # Determine alert level
        if risk_score >= 80:
            alert_level = "critical"
        elif risk_score >= 60:
            alert_level = "high"
        elif risk_score >= 40:
            alert_level = "medium"
        elif risk_score >= 20:
            alert_level = "low"
        else:
            alert_level = "baseline"
        
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "risk_score": round(risk_score, 1),
            "alert_level": alert_level
        })
    
    return history


@router.get("/top-risk-factors")
async def get_top_risk_factors():
    """Get aggregated top risk factors across all villages."""
    
    # Aggregate SHAP values across all predictions
    all_factors = {}
    
    for village in VILLAGES:
        pred = predictor.predict(village["id"])
        for factor in pred.get("top_risk_factors", []):
            feature = factor["feature"]
            impact = factor["impact"]
            
            if feature not in all_factors:
                all_factors[feature] = {"total_impact": 0, "count": 0}
            
            all_factors[feature]["total_impact"] += impact
            all_factors[feature]["count"] += 1
    
    # Calculate average impact
    top_factors = []
    for feature, data in all_factors.items():
        avg_impact = data["total_impact"] / data["count"]
        top_factors.append({
            "feature": feature,
            "average_impact": round(avg_impact, 2),
            "villages_affected": data["count"]
        })
    
    # Sort by impact
    top_factors.sort(key=lambda x: x["average_impact"], reverse=True)
    
    return top_factors[:10]
