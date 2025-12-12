"""
Pantallita 3.0 - Hardware Module (Bootstrap Version)
Hardware initialization and management
"""

import board
import displayio
import digitalio
import framebufferio
import rgbmatrix
import busio
import wifi
import socketpool
import ssl
import adafruit_requests
import adafruit_ds3231
import adafruit_ntp
from adafruit_bitmap_font import bitmap_font
import time

import config
import state

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level=config.LogLevel.INFO):
	"""Simple logging"""
	if level <= config.CURRENT_LOG_LEVEL:
		level_name = ["", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE"][level]
		print(f"[HW:{level_name}] {message}")

# ============================================================================
# DISPLAY INITIALIZATION
# ============================================================================

def init_display():
	"""Initialize RGB matrix display"""
	log("Initializing display...")

	# Release any existing displays
	displayio.release_displays()

	# Create RGB matrix
	matrix = rgbmatrix.RGBMatrix(
		width=config.Display.WIDTH,
		height=config.Display.HEIGHT,
		bit_depth=config.Display.BIT_DEPTH,
		rgb_pins=[
			board.MTX_R1, board.MTX_G1, board.MTX_B1,
			board.MTX_R2, board.MTX_G2, board.MTX_B2
		],
		addr_pins=[
			board.MTX_ADDRA,
			board.MTX_ADDRB,
			board.MTX_ADDRC,
			board.MTX_ADDRD
		],
		clock_pin=board.MTX_CLK,
		latch_pin=board.MTX_LAT,
		output_enable_pin=board.MTX_OE
	)

	# Create framebuffer display
	state.display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

	# Create main display group
	state.main_group = displayio.Group()
	state.display.root_group = state.main_group

	# Load fonts
	try:
		state.font_large = bitmap_font.load_font(config.Paths.FONT_LARGE)
		log("Large font loaded")
	except Exception as e:
		log(f"Failed to load large font: {e}", config.LogLevel.ERROR)

	try:
		state.font_small = bitmap_font.load_font(config.Paths.FONT_SMALL)
		log("Small font loaded")
	except Exception as e:
		log(f"Failed to load small font: {e}", config.LogLevel.WARNING)

	log("Display initialized successfully")

# ============================================================================
# RTC INITIALIZATION
# ============================================================================

def init_rtc():
	"""Initialize DS3231 RTC module"""
	log("Initializing RTC...")

	try:
		i2c = busio.I2C(board.SCL, board.SDA)
		state.rtc = adafruit_ds3231.DS3231(i2c)
		log(f"RTC initialized - Current time: {state.rtc.datetime}")
		return state.rtc
	except Exception as e:
		log(f"RTC initialization failed: {e}", config.LogLevel.ERROR)
		raise

# ============================================================================
# BUTTON INITIALIZATION
# ============================================================================

def init_buttons():
	"""Initialize MatrixPortal S3 built-in buttons"""
	log("Initializing buttons...")

	try:
		# UP button (stop)
		state.button_up = digitalio.DigitalInOut(board.BUTTON_UP)
		state.button_up.switch_to_input(pull=digitalio.Pull.UP)

		# DOWN button (reserved)
		state.button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
		state.button_down.switch_to_input(pull=digitalio.Pull.UP)

		log("Buttons initialized - UP=stop, DOWN=reserved")
		return True

	except Exception as e:
		log(f"Button initialization failed: {e}", config.LogLevel.WARNING)
		state.button_up = None
		state.button_down = None
		return False

def button_up_pressed():
	"""Check if UP button is pressed (active LOW)"""
	if state.button_up:
		return not state.button_up.value
	return False

def button_down_pressed():
	"""Check if DOWN button is pressed (active LOW)"""
	if state.button_down:
		return not state.button_down.value
	return False

# ============================================================================
# WIFI INITIALIZATION
# ============================================================================

def connect_wifi():
	"""Connect to WiFi network"""
	log(f"Connecting to WiFi: {config.Env.WIFI_SSID}...")

	if not config.Env.WIFI_SSID or not config.Env.WIFI_PASSWORD:
		log("WiFi credentials not found in settings.toml", config.LogLevel.ERROR)
		raise ValueError("Missing WiFi credentials")

	try:
		# Connect to WiFi
		wifi.radio.connect(config.Env.WIFI_SSID, config.Env.WIFI_PASSWORD)
		log(f"WiFi connected - IP: {wifi.radio.ipv4_address}")

		# Create socket pool
		state.socket_pool = socketpool.SocketPool(wifi.radio)

		# Create HTTP session
		state.session = adafruit_requests.Session(
			state.socket_pool,
			ssl.create_default_context()
		)
		log("HTTP session created")

		return True

	except Exception as e:
		log(f"WiFi connection failed: {e}", config.LogLevel.ERROR)
		raise

def is_wifi_connected():
	"""Check if WiFi is connected"""
	return wifi.radio.connected

def reconnect_wifi():
	"""Attempt to reconnect WiFi"""
	log("Attempting WiFi reconnect...")
	try:
		return connect_wifi()
	except Exception as e:
		log(f"WiFi reconnect failed: {e}", config.LogLevel.ERROR)
		return False

# ============================================================================
# TIME SYNCHRONIZATION
# ============================================================================

def get_timezone_offset():
	"""Get timezone offset from worldtimeapi.org"""
	if not config.Env.TIMEZONE:
		log("No TIMEZONE in settings.toml, using UTC", config.LogLevel.WARNING)
		return 0
	
	url = f"http://worldtimeapi.org/api/timezone/{config.Env.TIMEZONE}"
	
	try:
		log(f"Fetching timezone data for {config.Env.TIMEZONE}...")
		response = state.session.get(url, timeout=10)
		
		if response.status_code == 200:
			data = response.json()
			
			# Get UTC offset in seconds, convert to hours
			offset_seconds = data.get("raw_offset", 0)
			dst_offset = data.get("dst_offset", 0)
			total_offset = (offset_seconds + dst_offset) / 3600
			
			is_dst = data.get("dst", False)
			dst_status = "DST" if is_dst else "Standard"
			
			log(f"Timezone: {config.Env.TIMEZONE} = UTC{total_offset:+.1f} ({dst_status})")
			
			response.close()
			return int(total_offset)
		else:
			log(f"Timezone API error: {response.status_code}", config.LogLevel.ERROR)
			response.close()
			return -6  # Default to CST
			
	except Exception as e:
		log(f"Timezone fetch failed: {e}", config.LogLevel.ERROR)
		return -6  # Default to CST

def sync_time(rtc):
	"""Sync RTC with NTP server using correct timezone"""
	log("Syncing time with NTP...")

	if not state.session:
		log("No network session available", config.LogLevel.ERROR)
		return False

	try:
		# Get correct timezone offset
		tz_offset = get_timezone_offset()
		
		# Get time from NTP with timezone offset
		ntp = adafruit_ntp.NTP(state.socket_pool, tz_offset=tz_offset)
		rtc.datetime = ntp.datetime

		# Format for display
		now = rtc.datetime
		hour_12 = now.tm_hour % 12
		if hour_12 == 0:
			hour_12 = 12
		ampm = "AM" if now.tm_hour < 12 else "PM"
		
		log(f"Time synced: {now.tm_mon}/{now.tm_mday} {hour_12}:{now.tm_min:02d} {ampm}")
		return True

	except Exception as e:
		log(f"NTP sync failed: {e}", config.LogLevel.WARNING)
		log("Continuing with RTC time (may be incorrect)", config.LogLevel.WARNING)
		return False

