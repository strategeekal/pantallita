"""
Pantallita 3.0 - Configuration Module
"""

import os

# ============================================================================
# DISPLAY HARDWARE
# ============================================================================

class Display:
	"""RGB matrix display specifications"""
	WIDTH = 64
	HEIGHT = 32
	BIT_DEPTH = 4

class Hardware:
	"""Hardware specifications"""
	TOTAL_MEMORY = 2000000  # ESP32-S3 SRAM in bytes (~2MB)

# ============================================================================
# LAYOUT & POSITIONING
# ============================================================================

class Layout:
	"""Display positioning constants"""
	# Display dimensions
	WIDTH = 64
	HEIGHT = 32
	RIGHT_EDGE = 63
	BOTTOM_EDGE = 31
	LEFT_EDGE = 1
	
	# Weather display
	WEATHER_TEMP_Y = 20
	WEATHER_TIME_Y = 18
	FEELSLIKE_Y = 10
	FEELSLIKE_SHADE_Y = 18  # ADD THIS LINE
	UV_BAR_Y = 27
	HUMIDITY_BAR_Y = 29

# ============================================================================
# COLORS
# ============================================================================

class Colors:
	"""Color palette for 4-bit display"""
	BLACK = 0x000000
	WHITE = 0xF5F5DC
	GREEN = 0x00FF00
	RED = 0xFF0000
	BLUE = 0x0000FF
	ORANGE = 0xFFA500
	DIMMEST_WHITE = 0x4A4A3C

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

class Env:
	"""Environment variables from settings.toml"""

	@staticmethod
	def get(key, default=None):
		"""Get environment variable with fallback"""
		try:
			return os.getenv(key, default)
		except:
			return default

	# WiFi
	WIFI_SSID = None
	WIFI_PASSWORD = None

	# Timezone
	TIMEZONE = None
	
	# AccuWeather API (Phase 1)
	ACCUWEATHER_KEY = None
	ACCUWEATHER_LOCATION = None
	
	# Temperature unit
	TEMPERATURE_UNIT = "C"

	@classmethod
	def load(cls):
		"""Load all environment variables"""
		cls.WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
		cls.WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
		cls.TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
		
		# AccuWeather (Phase 1) - ADD THIS
		cls.ACCUWEATHER_KEY = os.getenv("ACCUWEATHER_API_KEY_TYPE1")
		cls.ACCUWEATHER_LOCATION = os.getenv("ACCUWEATHER_LOCATION_KEY")

# ============================================================================
# API ENDPOINTS
# ============================================================================

class API:
	"""API endpoints and configuration"""
	# AccuWeather
	ACCUWEATHER_BASE = "http://dataservice.accuweather.com"
	ACCUWEATHER_CURRENT = "/currentconditions/v1/{location}?details=true"

# ============================================================================
# PATHS
# ============================================================================

class Paths:
	"""File system paths"""
	FONT_LARGE = "/fonts/bigbit10-16.bdf"
	FONT_SMALL = "/fonts/tinybit6-16.bdf"
	
	# Images (Phase 1)
	WEATHER_IMAGES = "/img/weather"

# ============================================================================
# LOGGING
# ============================================================================

class LogLevel:
	"""Logging levels"""
	PRODUCTION = 0  # Only critical errors
	ERROR = 1
	WARNING = 2
	INFO = 3
	DEBUG = 4
	VERBOSE = 5

class Logging:
	"""Logging configuration"""
	USE_TIMESTAMPS = True  # OFF by default (turn ON for debugging)
	SHOW_CYCLE_SEPARATOR = True  # Show "## CYCLE N ##" markers

# Current log level
CURRENT_LOG_LEVEL = LogLevel.INFO

# ============================================================================
# TIMING
# ============================================================================

class Timing:
	"""Timing constants in seconds"""
	CLOCK_UPDATE_INTERVAL = 10  # Update clock every 10 seconds << CLOCK DISPLAY
	MEMORY_CHECK_INTERVAL = 5  # Check memory every 10 cycles
	
	# Weather display (Phase 1)
	WEATHER_DISPLAY_DURATION = 300  # 4 minutes
	WEATHER_UPDATE_INTERVAL = 300   # 5 minutes
	WEATHER_CACHE_MAX_AGE = 300     # 15 minutes

# Load environment variables at import
Env.load()
