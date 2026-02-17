"""Mock sensor service that generates realistic sensor data for demo purposes.

This service simulates Raspberry Pi 5 sensor readings with realistic noise,
drift, time-of-day variation, and seasonal patterns. It implements the same
SensorInterface as the real Pi code, allowing instant switching between mock
and real hardware by changing SENSOR_MODE in .env.
"""
import random
import math
from datetime import datetime, timedelta
from collections import deque, defaultdict
from typing import Optional
from sensors.base_sensor import (
    SensorInterface, SensorReading, DeviceStatus, CalibrationResult
)


class MockSensorService(SensorInterface):
    """Mock sensor service generating realistic water quality data."""
    
    # Device configurations with realistic baselines
    DEVICES = {
        "RPI5-UNIT-001": {
            "village_id": "MH_SHP",
            "village_name": "Shirpur",
            "status": "healthy",
            "baseline": {
                "ph": 7.2,
                "turbidity": 1.1,
                "tds": 312,
                "water_temp": 26.5,
                "air_temp": 31.0,
                "humidity": 65,
                "flow_rate": 12.5
            }
        },
        "RPI5-UNIT-002": {
            "village_id": "MH_DHA",
            "village_name": "Dharangaon",
            "status": "warning",
            "baseline": {
                "ph": 6.8,
                "turbidity": 4.2,  # Will increase over time
                "tds": 478,
                "water_temp": 28.1,
                "air_temp": 33.2,
                "humidity": 72,
                "flow_rate": 10.8
            }
        },
        "RPI5-UNIT-003": {
            "village_id": "UP_BAH",
            "village_name": "Bahraich",
            "status": "offline",
            "baseline": {
                "ph": 7.0,
                "turbidity": 2.5,
                "tds": 390,
                "water_temp": 27.0,
                "air_temp": 32.5,
                "humidity": 68,
                "flow_rate": 11.2
            }
        }
    }
    
    def __init__(self):
        """Initialize mock sensor service with circular buffers."""
        self.readings_buffer: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.device_start_time = datetime.now()
        self.readings_count: dict[str, int] = defaultdict(int)
        self.anomalies_count: dict[str, int] = defaultdict(int)
        self.drift_state: dict[str, dict] = defaultdict(lambda: {
            "ph_drift": 0.0,
            "turbidity_drift": 0.0,
            "tds_drift": 0.0,
            "temp_drift": 0.0
        })
        self.turbidity_increase_counter = 0  # For UNIT-002 progressive deterioration
        
    def _get_seasonal_multiplier(self) -> dict:
        """Get seasonal variation multipliers based on current month."""
        month = datetime.now().month
        
        # Monsoon months (Jun-Sep): higher turbidity and contamination risk
        if 6 <= month <= 9:
            return {"turbidity": 1.8, "tds": 1.2, "temp": 0.95}
        # Summer (Mar-May): higher temperature and TDS
        elif 3 <= month <= 5:
            return {"turbidity": 1.1, "tds": 1.15, "temp": 1.1}
        # Winter (Nov-Feb): generally better quality
        elif month >= 11 or month <= 2:
            return {"turbidity": 0.9, "tds": 0.95, "temp": 0.85}
        # Post-monsoon (Oct)
        else:
            return {"turbidity": 1.0, "tds": 1.0, "temp": 1.0}
    
    def _get_time_of_day_variation(self) -> dict:
        """Get time-of-day variation based on current hour."""
        hour = datetime.now().hour
        
        # Water temp peaks at 14:00, lowest at 05:00
        temp_factor = 1.0 + 0.15 * math.sin((hour - 5) * math.pi / 12)
        
        # Turbidity slightly higher after 18:00 (evening usage)
        turbidity_factor = 1.15 if hour >= 18 else 1.0
        
        return {"temp": temp_factor, "turbidity": turbidity_factor}
    
    def _add_noise(self, value: float, noise_std: float) -> float:
        """Add Gaussian noise to a value."""
        return value + random.gauss(0, noise_std)
    
    def _update_drift(self, device_id: str):
        """Update drift values every 10 readings."""
        if self.readings_count[device_id] % 10 == 0:
            drift = self.drift_state[device_id]
            drift["ph_drift"] += random.gauss(0, 0.02)
            drift["turbidity_drift"] += random.gauss(0, 0.05)
            drift["tds_drift"] += random.gauss(0, 2)
            drift["temp_drift"] += random.gauss(0, 0.1)
            
            # Clamp drift to reasonable bounds
            drift["ph_drift"] = max(-0.3, min(0.3, drift["ph_drift"]))
            drift["turbidity_drift"] = max(-0.5, min(0.5, drift["turbidity_drift"]))
            drift["tds_drift"] = max(-20, min(20, drift["tds_drift"]))
            drift["temp_drift"] = max(-2, min(2, drift["temp_drift"]))
    
    def _check_anomaly(self, reading_data: dict) -> tuple[bool, Optional[str]]:
        """Check if reading contains anomalies."""
        if reading_data["ph"] < 6.5 or reading_data["ph"] > 8.5:
            return True, "ph_out_of_range"
        if reading_data["turbidity"] > 5.0:
            return True, "high_turbidity"
        if reading_data["tds"] > 500:
            return True, "high_tds"
        if reading_data["water_temp"] > 35:
            return True, "high_temperature"
        return False, None
    
    def _get_quality_status(self, reading_data: dict, anomaly_detected: bool) -> str:
        """Determine water quality status."""
        if anomaly_detected:
            if reading_data["turbidity"] > 8 or reading_data["ph"] < 6.0 or reading_data["ph"] > 9.0:
                return "critical"
            return "unsafe"
        
        # Check marginal conditions
        if (6.5 <= reading_data["ph"] <= 6.7 or 8.3 <= reading_data["ph"] <= 8.5 or
            3.5 <= reading_data["turbidity"] <= 5.0 or
            450 <= reading_data["tds"] <= 500):
            return "marginal"
        
        return "safe"
    
    async def get_reading(self, device_id: str) -> SensorReading:
        """Generate realistic mock sensor reading."""
        if device_id not in self.DEVICES:
            raise ValueError(f"Unknown device: {device_id}")
        
        device_config = self.DEVICES[device_id]
        baseline = device_config["baseline"]
        
        # Handle offline device
        if device_config["status"] == "offline":
            # Return last known reading if available
            if self.readings_buffer[device_id]:
                last_reading = self.readings_buffer[device_id][-1]
                # Update timestamp to show it's old
                return last_reading
        
        # Get seasonal and time-of-day variations
        seasonal = self._get_seasonal_multiplier()
        time_var = self._get_time_of_day_variation()
        
        # Update drift
        self._update_drift(device_id)
        drift = self.drift_state[device_id]
        
        # Generate reading with noise, drift, and variations
        reading_data = {
            "ph": self._add_noise(
                baseline["ph"] + drift["ph_drift"],
                0.05
            ),
            "turbidity": self._add_noise(
                baseline["turbidity"] * seasonal["turbidity"] * time_var["turbidity"] + drift["turbidity_drift"],
                0.1
            ),
            "tds": self._add_noise(
                baseline["tds"] * seasonal["tds"] + drift["tds_drift"],
                5
            ),
            "water_temp": self._add_noise(
                baseline["water_temp"] * seasonal["temp"] * time_var["temp"] + drift["temp_drift"],
                0.3
            ),
            "air_temp": self._add_noise(baseline["air_temp"] * seasonal["temp"], 0.5),
            "humidity": self._add_noise(baseline["humidity"], 2),
            "flow_rate": self._add_noise(baseline["flow_rate"], 0.3)
        }
        
        # Special handling for UNIT-002: progressive turbidity increase
        if device_id == "RPI5-UNIT-002":
            self.turbidity_increase_counter += 1
            reading_data["turbidity"] += self.turbidity_increase_counter * 0.15
        
        # Clamp values to realistic ranges
        reading_data["ph"] = max(5.0, min(10.0, reading_data["ph"]))
        reading_data["turbidity"] = max(0, reading_data["turbidity"])
        reading_data["tds"] = max(0, reading_data["tds"])
        reading_data["water_temp"] = max(15, min(40, reading_data["water_temp"]))
        reading_data["air_temp"] = max(20, min(45, reading_data["air_temp"]))
        reading_data["humidity"] = max(30, min(100, reading_data["humidity"]))
        reading_data["flow_rate"] = max(0, reading_data["flow_rate"])
        
        # Check for anomalies
        anomaly_detected, anomaly_type = self._check_anomaly(reading_data)
        quality_status = self._get_quality_status(reading_data, anomaly_detected)
        
        # Create sensor reading
        reading = SensorReading(
            timestamp=datetime.now(),
            device_id=device_id,
            village_id=device_config["village_id"],
            village_name=device_config["village_name"],
            ph_level=round(reading_data["ph"], 2),
            turbidity_ntu=round(reading_data["turbidity"], 2),
            tds_ppm=round(reading_data["tds"], 1),
            water_temp_celsius=round(reading_data["water_temp"], 1),
            air_temp_celsius=round(reading_data["air_temp"], 1),
            humidity_percent=round(reading_data["humidity"], 1),
            flow_rate_lpm=round(reading_data["flow_rate"], 1),
            is_live_hardware=False,
            anomaly_detected=anomaly_detected,
            anomaly_type=anomaly_type,
            quality_status=quality_status
        )
        
        # Store in buffer
        self.readings_buffer[device_id].append(reading)
        self.readings_count[device_id] += 1
        if anomaly_detected:
            self.anomalies_count[device_id] += 1
        
        return reading
    
    async def get_device_status(self, device_id: str) -> DeviceStatus:
        """Get mock device status."""
        if device_id not in self.DEVICES:
            raise ValueError(f"Unknown device: {device_id}")
        
        device_config = self.DEVICES[device_id]
        is_offline = device_config["status"] == "offline"
        
        # Simulate realistic Pi 5 metrics
        uptime = (datetime.now() - self.device_start_time).total_seconds() / 3600
        current_hour = datetime.now().hour
        
        # CPU temp oscillates between 48-58°C
        cpu_temp = 53 + 5 * math.sin(uptime * 0.5) + random.gauss(0, 1)
        
        # CPU usage varies 15-35%
        cpu_usage = 25 + 10 * math.sin(uptime * 0.3) + random.gauss(0, 3)
        
        # RAM usage: 1.8-2.4 GB on 16GB Pi 5
        ram_used = 2.1 + 0.3 * math.sin(uptime * 0.2) + random.gauss(0, 0.1)
        
        # Solar charging during daytime (07:00-18:00)
        solar_charging = 7 <= current_hour <= 18
        
        # Battery backup calculation
        if solar_charging:
            battery_hours = min(72, 48 + uptime * 0.5)
        else:
            battery_hours = max(24, 72 - (uptime * 0.3))
        
        # Signal strength
        signal_dbm = -71 + random.randint(-5, 5)
        
        # Sensor health
        sensor_health = {
            "ph": "ok" if not is_offline else "offline",
            "turbidity": "warning" if device_id == "RPI5-UNIT-002" else ("ok" if not is_offline else "offline"),
            "tds": "ok" if not is_offline else "offline",
            "temperature": "ok" if not is_offline else "offline",
            "humidity": "ok" if not is_offline else "offline",
            "flow_rate": "ok" if not is_offline else "offline"
        }
        
        # Last reading time
        if is_offline:
            last_reading_at = datetime.now() - timedelta(hours=3)
        else:
            last_reading_at = datetime.now() - timedelta(seconds=random.randint(1, 10))
        
        return DeviceStatus(
            device_id=device_id,
            village_id=device_config["village_id"],
            village_name=device_config["village_name"],
            is_online=not is_offline,
            is_live_hardware=False,
            cpu_temp_celsius=round(cpu_temp, 1),
            cpu_usage_percent=round(max(0, min(100, cpu_usage)), 1),
            ram_used_gb=round(ram_used, 2),
            ram_total_gb=16.0,
            uptime_hours=round(uptime, 1),
            last_reading_at=last_reading_at,
            readings_today=self.readings_count[device_id],
            anomalies_today=self.anomalies_count[device_id],
            network_type="4G" if device_id == "RPI5-UNIT-001" else "WiFi",
            signal_dbm=signal_dbm,
            battery_backup_hours=round(battery_hours, 1),
            solar_charging=solar_charging,
            sensor_health=sensor_health,
            pi_ready_for_integration=True
        )
    
    async def get_history(self, device_id: str, count: int = 50) -> list[SensorReading]:
        """Get historical readings from buffer."""
        if device_id not in self.DEVICES:
            raise ValueError(f"Unknown device: {device_id}")
        
        buffer = self.readings_buffer[device_id]
        return list(buffer)[-count:]
    
    async def calibrate(self, device_id: str) -> CalibrationResult:
        """Simulate sensor calibration."""
        if device_id not in self.DEVICES:
            raise ValueError(f"Unknown device: {device_id}")
        
        # Slightly adjust baseline values
        device_config = self.DEVICES[device_id]
        baseline = device_config["baseline"]
        
        offsets = {
            "ph_offset": round(random.gauss(0, 0.05), 3),
            "turbidity_offset": round(random.gauss(0, 0.1), 3),
            "tds_offset": round(random.gauss(0, 5), 2),
            "temp_offset": round(random.gauss(0, 0.2), 3)
        }
        
        return CalibrationResult(
            device_id=device_id,
            calibrated_at=datetime.now(),
            success=True,
            offsets=offsets,
            message=f"Mock calibration successful for {device_id}. Offsets applied."
        )
