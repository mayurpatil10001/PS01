"""Raspberry Pi devices API router."""
from fastapi import APIRouter, HTTPException
from sensors.sensor_manager import sensor_manager

router = APIRouter(prefix="/api/pi", tags=["raspberry-pi"])


@router.get("/devices")
async def get_all_devices():
    """Get all Raspberry Pi devices with status."""
    device_ids = sensor_manager.get_all_device_ids()
    devices = []
    
    for device_id in device_ids:
        try:
            status = await sensor_manager.get_device_status(device_id)
            devices.append({
                "device_id": status.device_id,
                "village_id": status.village_id,
                "village_name": status.village_name,
                "is_online": status.is_online,
                "is_live_hardware": status.is_live_hardware,
                "cpu_temp_celsius": status.cpu_temp_celsius,
                "cpu_usage_percent": status.cpu_usage_percent,
                "ram_used_gb": status.ram_used_gb,
                "ram_total_gb": status.ram_total_gb,
                "uptime_hours": status.uptime_hours,
                "last_reading_at": status.last_reading_at,
                "readings_today": status.readings_today,
                "anomalies_today": status.anomalies_today,
                "network_type": status.network_type,
                "signal_dbm": status.signal_dbm,
                "battery_backup_hours": status.battery_backup_hours,
                "solar_charging": status.solar_charging,
                "sensor_health": status.sensor_health,
                "pi_ready_for_integration": status.pi_ready_for_integration,
                "mode": "mock_data",
                "pi_integration_note": "Real GPIO code ready in sensors/pi_sensor_service.py. Set SENSOR_MODE=pi in .env to activate when hardware is connected."
            })
        except Exception as e:
            continue
    
    return devices


@router.get("/devices/{device_id}/readings")
async def get_device_readings(device_id: str, count: int = 50):
    """Get recent readings from a device."""
    try:
        readings = await sensor_manager.get_history(device_id, count)
        
        return [
            {
                "timestamp": r.timestamp,
                "device_id": r.device_id,
                "village_id": r.village_id,
                "village_name": r.village_name,
                "ph_level": r.ph_level,
                "turbidity_ntu": r.turbidity_ntu,
                "tds_ppm": r.tds_ppm,
                "water_temp_celsius": r.water_temp_celsius,
                "air_temp_celsius": r.air_temp_celsius,
                "humidity_percent": r.humidity_percent,
                "flow_rate_lpm": r.flow_rate_lpm,
                "is_live_hardware": r.is_live_hardware,
                "anomaly_detected": r.anomaly_detected,
                "anomaly_type": r.anomaly_type,
                "quality_status": r.quality_status
            }
            for r in readings
        ]
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/devices/{device_id}/status")
async def get_device_status(device_id: str):
    """Get detailed status for a single device."""
    try:
        status = await sensor_manager.get_device_status(device_id)
        
        return {
            "device_id": status.device_id,
            "village_id": status.village_id,
            "village_name": status.village_name,
            "is_online": status.is_online,
            "is_live_hardware": status.is_live_hardware,
            "cpu_temp_celsius": status.cpu_temp_celsius,
            "cpu_usage_percent": status.cpu_usage_percent,
            "ram_used_gb": status.ram_used_gb,
            "ram_total_gb": status.ram_total_gb,
            "uptime_hours": status.uptime_hours,
            "last_reading_at": status.last_reading_at,
            "readings_today": status.readings_today,
            "anomalies_today": status.anomalies_today,
            "network_type": status.network_type,
            "signal_dbm": status.signal_dbm,
            "battery_backup_hours": status.battery_backup_hours,
            "solar_charging": status.solar_charging,
            "sensor_health": status.sensor_health,
            "pi_ready_for_integration": status.pi_ready_for_integration
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/devices/{device_id}/calibrate")
async def calibrate_device(device_id: str):
    """Calibrate sensors on a device."""
    try:
        result = await sensor_manager.calibrate(device_id)
        
        return {
            "device_id": result.device_id,
            "calibrated_at": result.calibrated_at,
            "success": result.success,
            "offsets": result.offsets,
            "message": result.message
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/integration-guide")
async def get_integration_guide():
    """Get Raspberry Pi integration guide."""
    return {
        "step_1": "Install Raspbian OS on Raspberry Pi 5 (16GB RAM)",
        "step_2": "Install required libraries: pip install RPi.GPIO spidev adafruit-circuitpython-dht",
        "step_3": "Wire sensors per GPIO pin map in pi_sensor_service.py",
        "step_4": "Set SENSOR_MODE=pi in .env file",
        "step_5": "Restart backend: uvicorn main:app --reload",
        "step_6": "System automatically switches to real sensors",
        "gpio_pin_map": {
            "DS18B20_water_temp": "GPIO 4 (1-Wire protocol)",
            "turbidity_sensor": "MCP3008 CH0 → SPI0 CE0",
            "ph_sensor": "MCP3008 CH1 → SPI0 CE1",
            "DHT22_air_temp_humidity": "GPIO 17",
            "flow_sensor_YF_S201": "GPIO 27 (interrupt-based)",
            "TDS_meter": "SPI1"
        },
        "estimated_setup_time": "2-3 hours",
        "code_changes_needed": "Zero — just change SENSOR_MODE environment variable",
        "hardware_required": [
            "Raspberry Pi 5 (16GB RAM)",
            "DS18B20 waterproof temperature probe",
            "Gravity: Analog Turbidity Sensor",
            "Gravity: Analog pH Sensor Kit",
            "DHT22 Temperature + Humidity Sensor",
            "MCP3008 SPI ADC (for analog sensors)",
            "YF-S201 Hall-Effect Water Flow Sensor",
            "TDS meter (analog)"
        ]
    }
