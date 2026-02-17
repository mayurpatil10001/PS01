# How to Connect Real Raspberry Pi 5

## Overview
BioGuard AI is designed with a clean separation between mock data (for demos) and real hardware integration. The entire system can switch from mock sensors to real Raspberry Pi sensors by changing a single environment variable.

## Hardware Required
- **Raspberry Pi 5 (16GB RAM)** ✓
- **DS18B20** - Waterproof temperature probe (water temperature)
- **Gravity: Analog Turbidity Sensor** - DFRobot SEN0189
- **Gravity: Analog pH Sensor Kit** - DFRobot SEN0161
- **DHT22** - Temperature + Humidity Sensor (air conditions)
- **MCP3008** - 8-Channel 10-Bit ADC with SPI Interface
- **YF-S201** - Hall-Effect Water Flow Sensor
- **TDS Meter** - Analog TDS sensor

## GPIO Wiring Diagram

```
Raspberry Pi 5 GPIO Pinout:
┌─────────────────────────────────────┐
│                                     │
│  DS18B20 (Water Temp)               │
│    → GPIO 4 (1-Wire protocol)       │
│                                     │
│  MCP3008 ADC (for analog sensors)   │
│    → MOSI: GPIO 10 (SPI0 MOSI)      │
│    → MISO: GPIO 9 (SPI0 MISO)       │
│    → CLK: GPIO 11 (SPI0 SCLK)       │
│    → CS: GPIO 8 (SPI0 CE0)          │
│                                     │
│  MCP3008 Channel Assignments:       │
│    → CH0: Turbidity Sensor          │
│    → CH1: pH Sensor                 │
│    → CH2: TDS Sensor                │
│                                     │
│  DHT22 (Air Temp + Humidity)        │
│    → GPIO 17                        │
│                                     │
│  YF-S201 (Flow Sensor)              │
│    → GPIO 27 (interrupt-based)      │
│                                     │
└─────────────────────────────────────┘
```

## Software Setup (on the Raspberry Pi)

### 1. Install Raspbian OS
```bash
# Use Raspberry Pi Imager to install Raspberry Pi OS (64-bit)
# Enable SSH and configure WiFi during setup
```

### 2. Install Python Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev

# Install required Python libraries
pip3 install RPi.GPIO spidev adafruit-circuitpython-dht
```

### 3. Enable SPI and 1-Wire
```bash
# Enable SPI
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable

# Enable 1-Wire
sudo raspi-config
# Navigate to: Interface Options → 1-Wire → Enable

# Reboot
sudo reboot
```

### 4. Test Sensor Connections

#### Test DS18B20 (Water Temperature)
```bash
# Check if sensor is detected
ls /sys/bus/w1/devices/
# Should show: 28-xxxxxxxxxxxx

# Read temperature
cat /sys/bus/w1/devices/28-*/w1_slave
```

#### Test MCP3008 (Analog Sensors)
```python
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

# Test turbidity on CH0
print(f"Turbidity raw: {read_adc(0)}")

# Test pH on CH1
print(f"pH raw: {read_adc(1)}")
```

#### Test DHT22 (Air Temp/Humidity)
```python
import adafruit_dht
import board

dht_device = adafruit_dht.DHT22(board.D17)
print(f"Temp: {dht_device.temperature}°C")
print(f"Humidity: {dht_device.humidity}%")
```

## Activation (Zero Code Changes Required)

### Step 1: Update Environment Variable
```bash
cd /path/to/bioguard-ai/backend
nano .env
```

Change this line:
```
SENSOR_MODE=mock
```

To:
```
SENSOR_MODE=pi
```

### Step 2: Restart Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify
Check the startup logs:
```
🟢 BioGuard AI ready
   Sensor mode: PI
   Pi integration: ACTIVE
   Devices configured: 3
```

That's it! The system is now reading from real sensors.

## Why It Works

Both `MockSensorService` and `RealPiSensorService` implement the same `SensorInterface` abstract class. The `SensorManager` simply routes calls to whichever implementation is active based on `SENSOR_MODE`.

```python
# In sensor_manager.py
if self.sensor_mode == "mock":
    return MockSensorService()
elif self.sensor_mode == "pi":
    return RealPiSensorService()
```

No changes needed in:
- ✅ Frontend code
- ✅ API endpoints
- ✅ Database models
- ✅ ML predictor
- ✅ Alert service
- ✅ WebSocket streaming

## Calibration

### pH Sensor Calibration
```bash
# Use standard buffer solutions
curl -X POST http://localhost:8000/api/pi/devices/RPI5-UNIT-001/calibrate

# Follow on-screen prompts:
# 1. Place sensor in pH 7.0 buffer
# 2. Place sensor in pH 4.0 buffer
# 3. System calculates offset and slope
```

### Turbidity Sensor Calibration
```bash
# Use formazin standards (0 NTU, 100 NTU, 800 NTU)
# Calibration offsets stored in device config
```

## Troubleshooting

### Sensor Not Detected
```bash
# Check wiring
# Verify GPIO pins match the pin map above
# Check power supply (sensors need 3.3V or 5V depending on model)
```

### SPI Not Working
```bash
# Verify SPI is enabled
ls /dev/spi*
# Should show: /dev/spidev0.0 /dev/spidev0.1

# Check permissions
sudo usermod -a -G spi,gpio $USER
```

### 1-Wire Not Working
```bash
# Check if module is loaded
lsmod | grep w1
# Should show: w1_gpio, w1_therm

# Manually load if needed
sudo modprobe w1-gpio
sudo modprobe w1-therm
```

## Production Deployment

### Run as System Service
```bash
sudo nano /etc/systemd/system/bioguard-ai.service
```

```ini
[Unit]
Description=BioGuard AI Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bioguard-ai/backend
Environment="PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bioguard-ai
sudo systemctl start bioguard-ai
sudo systemctl status bioguard-ai
```

## Estimated Setup Time
**2-3 hours** for complete hardware integration (including sensor wiring and calibration)

## Support
For issues with Pi integration, check:
1. `sensors/pi_sensor_service.py` - Implementation stub with detailed comments
2. This README - Complete wiring and setup guide
3. Backend logs - Detailed error messages if sensors fail

---

**Remember**: The mock data system is production-ready code. It's not a placeholder — it's a fully functional demo mode that can run indefinitely while you prepare the hardware.
