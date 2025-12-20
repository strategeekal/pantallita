"""
Pantallita 3.0 - Global State Module
Global variables shared across modules
"""

# ============================================================================
# DISPLAY STATE
# ============================================================================

# Display objects (initialized by hardware.init_display)
display = None
main_group = None
font_large = None
font_small = None

# ============================================================================
# HARDWARE STATE
# ============================================================================

# RTC object (initialized by hardware.init_rtc)
rtc = None

# Button objects (initialized by hardware.init_buttons)
button_up = None
button_down = None

# ============================================================================
# NETWORK STATE
# ============================================================================

# HTTP session (initialized by hardware.connect_wifi)
session = None
socket_pool = None

# ============================================================================
# RUNTIME STATE
# ============================================================================

# Cycle counter
cycle_count = 0

# Start time (monotonic)
start_time = 0

# Last memory check
last_memory_free = 0

# ============================================================================
# WEATHER CACHE (Phase 1)
# ============================================================================

# Cached weather data
last_weather_data = None
last_weather_time = 0  # monotonic time of last fetch

# Weather fetch tracking
weather_fetch_count = 0
weather_fetch_errors = 0

# ============================================================================
# FORECAST CACHE (Phase 2)
# ============================================================================

# Cached forecast data (list of 12 hourly forecasts)
last_forecast_data = None
last_forecast_time = 0  # monotonic time of last fetch

# Forecast fetch tracking
forecast_fetch_count = 0
forecast_fetch_errors = 0

# ============================================================================
# IMAGE CACHE (Phase 2)
# ============================================================================

# Shared LRU image cache for all displays (weather, forecast, schedules, events)
# - Stores OnDiskBitmap objects by file path
# - LRU eviction: removes oldest when cache exceeds IMAGE_CACHE_MAX
# - Reduces SD card reads and memory churn
image_cache = {}  # {path: OnDiskBitmap}
image_cache_order = []  # LRU tracking list (oldest first, newest last)
IMAGE_CACHE_MAX = 12  # Max images to cache (like v2.5)

# ============================================================================
# STOCKS CACHE (Phase 4)
# ============================================================================

# Stocks list from stocks.csv (loaded at startup, refreshed with config)
cached_stocks = []  # List of stock dicts from CSV

# Stock price cache (for multi-stock display)
cached_stock_prices = {}  # {symbol: {"price": float, "change_percent": float, "direction": str, "timestamp": float}}

# Intraday chart cache (for single stock charts)
cached_intraday_data = {}  # {symbol: {"data": [...], "quote": {...}, "timestamp": float}}

# Stock rotation tracking
stock_rotation_offset = 0  # Current position in stocks list

# Stock fetch tracking
last_stock_fetch_time = 0  # monotonic time of last fetch (for rate limiting)

# Market hours tracking
should_fetch_stocks = False  # True if within market hours, False if outside
market_open_local_minutes = 0  # Market open time in minutes since midnight (local time)
market_close_local_minutes = 0  # Market close time in minutes since midnight (local time)
market_grace_end_local_minutes = 0  # Grace period end time in minutes since midnight (local time)

# Grace period optimization - track which symbols already fetched during current grace period
grace_period_fetched_symbols = set()  # Set of symbols fetched during current grace period
previous_grace_period_state = False  # Track previous cycle to detect transition into grace period

# ============================================================================
# SCHEDULES CACHE (Phase 5)
# ============================================================================

# Schedules from GitHub or local schedules.csv (loaded at startup, reloaded every 10 cycles)
cached_schedules = {}  # {schedule_name: {enabled, days, start_hour, start_min, end_hour, end_min, image, progressbar}}
