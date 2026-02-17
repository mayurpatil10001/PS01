"""Predictions API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ml.predictor import predictor
from ml.data_generator import VILLAGES
from sensors.sensor_manager import sensor_manager

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


class SimulationRequest(BaseModel):
    """Request model for what-if simulation."""
    village_id: str
    ph_override: Optional[float] = None
    turbidity_override: Optional[float] = None
    rainfall_override: Optional[float] = None
    new_cases_inject: Optional[int] = None


@router.get("/all-villages")
async def get_all_village_predictions():
    """Get predictions for all 15 villages."""
    predictions = []
    
    for village in VILLAGES:
        village_id = village["id"]
        
        # Check if village has a sensor assigned
        sensor_reading = None
        device_ids = sensor_manager.get_all_device_ids()
        
        for device_id in device_ids:
            try:
                status = await sensor_manager.get_device_status(device_id)
                if status.village_id == village_id:
                    reading = await sensor_manager.get_reading(device_id)
                    sensor_reading = {
                        "ph_level": reading.ph_level,
                        "turbidity_ntu": reading.turbidity_ntu,
                        "tds_ppm": reading.tds_ppm
                    }
                    break
            except:
                pass
        
        # Get prediction
        prediction = predictor.predict(village_id, sensor_reading)
        
        # Add village metadata
        prediction["state"] = village["state"]
        prediction["lat"] = village["lat"]
        prediction["lon"] = village["lon"]
        prediction["population"] = village["pop"]
        
        predictions.append(prediction)
    
    # Sort by risk score descending
    predictions.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return predictions


@router.get("/{village_id}")
async def get_village_prediction(village_id: str):
    """Get detailed prediction for a specific village."""
    village_info = next((v for v in VILLAGES if v["id"] == village_id), None)
    if not village_info:
        raise HTTPException(status_code=404, detail="Village not found")
    
    # Check for sensor
    sensor_reading = None
    sensor_device_id = None
    device_ids = sensor_manager.get_all_device_ids()
    
    for device_id in device_ids:
        try:
            status = await sensor_manager.get_device_status(device_id)
            if status.village_id == village_id:
                reading = await sensor_manager.get_reading(device_id)
                sensor_reading = {
                    "ph_level": reading.ph_level,
                    "turbidity_ntu": reading.turbidity_ntu,
                    "tds_ppm": reading.tds_ppm,
                    "water_temp_celsius": reading.water_temp_celsius,
                    "quality_status": reading.quality_status
                }
                sensor_device_id = device_id
                break
        except:
            pass
    
    # Get prediction
    prediction = predictor.predict(village_id, sensor_reading)
    
    # Add sensor info
    prediction["sensor_device_id"] = sensor_device_id
    prediction["sensor_reading"] = sensor_reading
    
    # Add village metadata
    prediction["latitude"] = village_info["lat"]
    prediction["longitude"] = village_info["lon"]
    prediction["population"] = village_info["pop"]
    prediction["state"] = village_info["state"]
    
    return prediction


@router.post("/simulate")
async def simulate_prediction(request: SimulationRequest):
    """Run what-if simulation with overridden parameters."""
    village_info = next((v for v in VILLAGES if v["id"] == request.village_id), None)
    if not village_info:
        raise HTTPException(status_code=404, detail="Village not found")
    
    # Get original prediction
    original = predictor.predict(request.village_id)
    
    # Build simulated sensor reading
    simulated_reading = {}
    if request.ph_override is not None:
        simulated_reading["ph_level"] = request.ph_override
    if request.turbidity_override is not None:
        simulated_reading["turbidity_ntu"] = request.turbidity_override
    
    # Get simulated prediction
    simulated = predictor.predict(request.village_id, simulated_reading if simulated_reading else None)
    
    # Calculate changes
    risk_change = simulated["risk_score"] - original["risk_score"]
    alert_level_change = simulated["alert_level"] != original["alert_level"]
    
    return {
        "original_prediction": original,
        "simulated_prediction": simulated,
        "risk_change": round(risk_change, 1),
        "alert_level_change": alert_level_change,
        "simulation_parameters": {
            "ph_override": request.ph_override,
            "turbidity_override": request.turbidity_override,
            "rainfall_override": request.rainfall_override,
            "new_cases_inject": request.new_cases_inject
        }
    }
