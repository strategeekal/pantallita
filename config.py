"""
Pantallita 3.0 - Configuration Module (Bootstrap Version)
Minimal config for foundation testing
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

	@classmethod
	def load(cls):
		"""Load all environment variables"""
		cls.WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
		cls.WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
		cls.TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")

# ============================================================================
# PATHS
# ============================================================================

class Paths:
	"""File system paths"""
	FONT_LARGE = "/fonts/bigbit10-16.bdf"
	FONT_SMALL = "/fonts/tinybit6-16.bdf"

# ============================================================================
# LOGGING
# ============================================================================

class LogLevel:
	"""Logging levels"""
	ERROR = 1
	WARNING = 2
	INFO = 3
	DEBUG = 4
	VERBOSE = 5

# Current log level
CURRENT_LOG_LEVEL = LogLevel.INFO

# ============================================================================
# TIMING
# ============================================================================

class Timing:
	"""Timing constants in seconds"""
	CLOCK_UPDATE_INTERVAL = 10  # Update clock every 10 seconds
	MEMORY_CHECK_INTERVAL = 10  # Check memory every 10 cycles

# Load environment variables at import
Env.load()
