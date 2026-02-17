"""Sensor manager that routes between mock and real Pi sensors based on configuration."""
from loguru import logger
from config import settings
from sensors.base_sensor import SensorInterface
from sensors.mock_sensor_service import MockSensorService
from sensors.pi_sensor_service import RealPiSensorService


class SensorManager:
    """Manages sensor service selection based on SENSOR_MODE configuration."""
    
    def __init__(self):
        """Initialize sensor manager and select appropriate service."""
        self.sensor_mode = settings.sensor_mode
        self.service: SensorInterface = self._initialize_service()
        
        logger.info(f"🔧 Sensor Manager initialized")
        logger.info(f"   Mode: {self.sensor_mode.upper()}")
        logger.info(f"   Service: {self.service.__class__.__name__}")
        
        if self.sensor_mode == "mock":
            logger.info("   ⚡ Mock data mode active - Pi integration ready")
            logger.info("   💡 To activate real Pi: Set SENSOR_MODE=pi in .env and restart")
        else:
            logger.info("   🔴 Real Pi mode active - using hardware sensors")
    
    def _initialize_service(self) -> SensorInterface:
        """Initialize the appropriate sensor service based on configuration."""
        if self.sensor_mode == "mock":
            return MockSensorService()
        elif self.sensor_mode == "pi":
            try:
                return RealPiSensorService()
            except NotImplementedError as e:
                logger.error(f"❌ Real Pi service not available: {e}")
                logger.warning("⚠️  Falling back to mock sensor service")
                return MockSensorService()
        else:
            logger.warning(f"⚠️  Unknown sensor mode: {self.sensor_mode}, using mock")
            return MockSensorService()
    
    async def get_reading(self, device_id: str):
        """Get sensor reading from active service."""
        return await self.service.get_reading(device_id)
    
    async def get_device_status(self, device_id: str):
        """Get device status from active service."""
        return await self.service.get_device_status(device_id)
    
    async def get_history(self, device_id: str, count: int = 50):
        """Get reading history from active service."""
        return await self.service.get_history(device_id, count)
    
    async def calibrate(self, device_id: str):
        """Calibrate sensors via active service."""
        return await self.service.calibrate(device_id)
    
    def get_all_device_ids(self) -> list[str]:
        """Get list of all configured device IDs."""
        if isinstance(self.service, MockSensorService):
            return list(MockSensorService.DEVICES.keys())
        else:
            # For real Pi, would query device registry
            return []
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.sensor_mode == "mock"


# Global sensor manager instance
sensor_manager = SensorManager()
