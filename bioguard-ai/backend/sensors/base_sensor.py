"""Abstract sensor interface for BioGuard AI water quality monitoring."""
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class SensorReading(BaseModel):
    """Water quality sensor reading from a Pi device."""
    
    timestamp: datetime
    device_id: str
    village_id: str
    village_name: str
    ph_level: float = Field(description="Safe: 6.5–8.5")
    turbidity_ntu: float = Field(description="Safe: < 4.0 NTU")
    tds_ppm: float = Field(description="Safe: < 500 ppm")
    water_temp_celsius: float = Field(description="Expected: 20–35°C")
    air_temp_celsius: float
    humidity_percent: float
    flow_rate_lpm: float
    is_live_hardware: bool = Field(description="False = mock, True = real Pi")
    anomaly_detected: bool
    anomaly_type: Optional[str] = Field(default=None, description="high_turbidity, low_ph, etc.")
    quality_status: str = Field(description="safe, marginal, unsafe, critical")


class DeviceStatus(BaseModel):
    """Raspberry Pi device status and health metrics."""
    
    device_id: str
    village_id: str
    village_name: str
    is_online: bool
    is_live_hardware: bool = Field(description="Always False in mock mode")
    cpu_temp_celsius: float = Field(description="Simulated Pi CPU temp")
    cpu_usage_percent: float
    ram_used_gb: float
    ram_total_gb: float = Field(default=16.0, description="16.0 for Raspberry Pi 5")
    uptime_hours: float
    last_reading_at: datetime
    readings_today: int
    anomalies_today: int
    network_type: str = Field(description="4G, WiFi, LoRa")
    signal_dbm: int
    battery_backup_hours: float
    solar_charging: bool
    sensor_health: dict = Field(description="{ph: 'ok', turbidity: 'ok', ...}")
    pi_ready_for_integration: bool = Field(default=True, description="Always True (code is ready)")


class CalibrationResult(BaseModel):
    """Result of sensor calibration."""
    
    device_id: str
    calibrated_at: datetime
    success: bool
    offsets: dict = Field(description="Calibration offsets per sensor")
    message: str


class SensorInterface(ABC):
    """Abstract base class for all sensor implementations (mock and real Pi)."""
    
    @abstractmethod
    async def get_reading(self, device_id: str) -> SensorReading:
        """Get current sensor reading from device."""
        pass
    
    @abstractmethod
    async def get_device_status(self, device_id: str) -> DeviceStatus:
        """Get device status and health metrics."""
        pass
    
    @abstractmethod
    async def get_history(self, device_id: str, count: int = 50) -> list[SensorReading]:
        """Get historical readings from device."""
        pass
    
    @abstractmethod
    async def calibrate(self, device_id: str) -> CalibrationResult:
        """Calibrate sensors on device."""
        pass
