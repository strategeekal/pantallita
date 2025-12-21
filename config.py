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

	# Forecast display (Phase 2) - v2.5 proven layout
	# Layout: 1px margin | 13px icon1 | 10px gap | 13px icon2 | 10px gap | 13px icon3 | 3px margin = 64px
	FORECAST_COL1_X = 1      # Column 1 starts at x=1 (0-based) = x=2 (1-based)
	FORECAST_COL2_X = 22     # Column 2 starts at x=22 (0-based) = x=23 (1-based)
	FORECAST_COL3_X = 43     # Column 3 starts at x=43 (0-based) = x=44 (1-based)
	FORECAST_COLUMN_WIDTH = 20  # Column width in pixels (all columns are 20px wide)

	# Icon positions (13x13 icons, fixed placement per reference layout)
	FORECAST_ICON1_X = 4     # Column 1 icon: x=4,y=9 (0-based) = x=5,y=10 (1-based)
	FORECAST_ICON2_X = 26    # Column 2 icon: x=26,y=9 (0-based) = x=27,y=10 (1-based)
	FORECAST_ICON3_X = 47    # Column 3 icon: x=47,y=9 (0-based) = x=48,y=10 (1-based)
	FORECAST_ICON_Y = 9      # Icon Y position (all columns)

	FORECAST_TIME_Y = 1      # Time label Y position (0-based) = y=2 (1-based)
	FORECAST_TEMP_Y = 25     # Temperature label Y position

	# Schedule display (Phase 5)
	# Layout: Left section (x:0-22) = clock, weather, temp, UV | Right section (x:23-63) = schedule image
	SCHEDULE_CLOCK_X = 1
	SCHEDULE_CLOCK_Y = 1
	SCHEDULE_WEATHER_ICON_X = 4      # 13×13 weather icon
	SCHEDULE_WEATHER_ICON_Y = 9
	SCHEDULE_TEMP_X = 5              # Temperature label (below weather icon)
	SCHEDULE_TEMP_Y = 23
	SCHEDULE_UV_X = 1               # UV bar (horizontal, left to right)
	SCHEDULE_UV_Y = 30
	SCHEDULE_IMAGE_X = 23            # Schedule image (40×28, right side)
	SCHEDULE_IMAGE_Y = 0

	# Progress bar (bottom of schedule display)
	PROGRESS_BAR_X = 23              # Starts at x=23
	PROGRESS_BAR_Y = 29              # Base line at y=30
	PROGRESS_BAR_WIDTH = 40          # 40 pixels wide (x23-62)

# ============================================================================
# COLORS
# ============================================================================

class Colors:
	"""Color palette for 4-bit display (from old_code.py)"""
	BLACK = 0x000000
	DIMMEST_WHITE = 0x606060  # (96, 96, 96)
	MINT = 0x288C3C  # (40, 140, 60) - For forecast time labels (jumped hours)
	BUGAMBILIA = 0x400040  # (64, 0, 64)
	LILAC = 0x402040  # (64, 32, 64)
	RED = 0xCC0000  # (204, 0, 0)
	GREEN = 0x004400  # (0, 68, 0)
	LIME = 0x00CC00  # (0, 204, 0)
	BLUE = 0x003366  # (0, 51, 102)
	ORANGE = 0xCC5000  # (204, 80, 0)
	YELLOW = 0xCC8C00  # (204, 140, 0)
	CYAN = 0x00CCCC  # (0, 204, 204)
	PURPLE = 0x6600CC  # (102, 0, 204)
	PINK = 0xCC4078  # (204, 64, 120)
	LIGHT_PINK = 0xCC66AA  # (204, 102, 170)
	AQUA = 0x006666  # (0, 102, 102)
	WHITE = 0xCCCCCC  # (204, 204, 204)
	GRAY = 0x666666  # (102, 102, 102)
	DARK_GRAY = 0x202020  # (32, 32, 32)
	BEIGE = 0x885522  # (136, 85, 34)
	BROWN = 0x331100  # (51, 17, 0)

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

	# Temperature unit (will be overridden by config_manager)
	TEMPERATURE_UNIT = "C"

	# Display configuration (Phase 3)
	CONFIG_GITHUB_URL = None

	# Stocks API (Phase 4)
	TWELVE_DATA_API_KEY = None
	STOCKS_GITHUB_URL = None

	# Schedules (Phase 5)
	SCHEDULES_GITHUB_URL = None

	@classmethod
	def load(cls):
		"""Load all environment variables"""
		cls.WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
		cls.WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
		cls.TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")

		# AccuWeather (Phase 1)
		cls.ACCUWEATHER_KEY = os.getenv("ACCUWEATHER_API_KEY_TYPE1")
		cls.ACCUWEATHER_LOCATION = os.getenv("ACCUWEATHER_LOCATION_KEY")

		# Display configuration (Phase 3)
		cls.CONFIG_GITHUB_URL = os.getenv("CONFIG_GITHUB_URL")

		# Stocks API (Phase 4)
		cls.TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
		cls.STOCKS_GITHUB_URL = os.getenv("STOCKS_GITHUB_URL")

		# Schedules (Phase 5)
		cls.SCHEDULES_GITHUB_URL = os.getenv("SCHEDULES_GITHUB_URL")

# ============================================================================
# API ENDPOINTS
# ============================================================================

class API:
	"""API endpoints and configuration"""
	# AccuWeather
	ACCUWEATHER_BASE = "http://dataservice.accuweather.com"
	ACCUWEATHER_CURRENT = "/currentconditions/v1/{location}?details=true"
	ACCUWEATHER_FORECAST = "/forecasts/v1/hourly/12hour/{location}?details=true"

# ============================================================================
# PATHS
# ============================================================================

class Paths:
	"""File system paths"""
	FONT_LARGE = "/fonts/bigbit10-16.bdf"
	FONT_SMALL = "/fonts/tinybit6-16.bdf"

	# Images (Phase 1)
	WEATHER_IMAGES = "/img/weather"

	# Forecast column images (Phase 2)
	FORECAST_IMAGES = "/img/weather/columns"

	# Column images (used in schedule displays for weather icons)
	COLUMN_IMAGES = "/img/weather/columns"

	# Schedule images (Phase 5)
	SCHEDULE_IMAGES = "/img/schedules"

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
	WEATHER_DISPLAY_DURATION = 240  # 4 minutes
	WEATHER_UPDATE_INTERVAL = 300   # 5 minutes
	WEATHER_CACHE_MAX_AGE = 300     # 5 minutes

	# Forecast display (Phase 2)
	FORECAST_DISPLAY_DURATION = 60   # 1 minute
	FORECAST_UPDATE_INTERVAL = 900   # 15 minutes
	FORECAST_CACHE_MAX_AGE = 900     # 15 minutes

	# Stock display (Phase 4)
	STOCKS_DISPLAY_DURATION = 30    # 30 seconds
	STOCKS_FETCH_INTERVAL = 65      # 65 seconds (rate limit: 8 calls/minute)
	STOCKS_CACHE_MAX_AGE = 900      # 15 minutes
	INTRADAY_CACHE_MAX_AGE = 900    # 15 minutes

# Load environment variables at import
Env.load()
