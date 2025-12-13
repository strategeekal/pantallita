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
import logger

# ============================================================================
# DISPLAY INITIALIZATION
# ============================================================================

def init_display():
	"""Initialize RGB matrix display"""
	logger.log("Initializing display...", area="HW")

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
		logger.log("Large font loaded", area="HW")
	except Exception as e:
		logger.log(f"Failed to load large font: {e}", config.LogLevel.ERROR, area="HW")

	try:
		state.font_small = bitmap_font.load_font(config.Paths.FONT_SMALL)
		logger.log("Small font loaded", area="HW")
	except Exception as e:
		logger.log(f"Failed to load small font: {e}", config.LogLevel.WARNING, area="HW")

	logger.log("Display initialized successfully", area="HW")

# ============================================================================
# RTC INITIALIZATION
# ============================================================================

def init_rtc():
	"""Initialize DS3231 RTC module"""
	logger.log("Initializing RTC...", area="HW")

	try:
		i2c = busio.I2C(board.SCL, board.SDA)
		state.rtc = adafruit_ds3231.DS3231(i2c)
		logger.log(f"RTC initialized - Current time: {state.rtc.datetime}", area="HW")
		return state.rtc
	except Exception as e:
		logger.log(f"RTC initialization failed: {e}", config.LogLevel.ERROR, area="HW")
		raise

# ============================================================================
# BUTTON INITIALIZATION
# ============================================================================

def init_buttons():
	"""Initialize MatrixPortal S3 built-in buttons"""
	logger.log("Initializing buttons...", area="HW")

	try:
		# UP button (stop)
		state.button_up = digitalio.DigitalInOut(board.BUTTON_UP)
		state.button_up.switch_to_input(pull=digitalio.Pull.UP)

		# DOWN button (reserved)
		state.button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
		state.button_down.switch_to_input(pull=digitalio.Pull.UP)

		logger.log("Buttons initialized - UP=stop, DOWN=reserved", area="HW")
		return True

	except Exception as e:
		logger.log(f"Button initialization failed: {e}", config.LogLevel.WARNING, area="HW")
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
	logger.log(f"Connecting to WiFi: {config.Env.WIFI_SSID}...", area="HW")

	if not config.Env.WIFI_SSID or not config.Env.WIFI_PASSWORD:
		logger.log("WiFi credentials not found in settings.toml", config.LogLevel.ERROR, area="HW")
		raise ValueError("Missing WiFi credentials")

	try:
		# Connect to WiFi
		wifi.radio.connect(config.Env.WIFI_SSID, config.Env.WIFI_PASSWORD)
		logger.log(f"WiFi connected - IP: {wifi.radio.ipv4_address}", area="HW")

		# Create socket pool
		state.socket_pool = socketpool.SocketPool(wifi.radio)

		# Create HTTP session
		state.session = adafruit_requests.Session(
			state.socket_pool,
			ssl.create_default_context()
		)
		logger.log("HTTP session created", area="HW")

		return True

	except Exception as e:
		logger.log(f"WiFi connection failed: {e}", config.LogLevel.ERROR, area="HW")
		raise

def is_wifi_connected():
	"""Check if WiFi is connected"""
	return wifi.radio.connected

def reconnect_wifi():
	"""Attempt to reconnect WiFi"""
	logger.log("Attempting WiFi reconnect...", area="HW")
	try:
		return connect_wifi()
	except Exception as e:
		logger.log(f"WiFi reconnect failed: {e}", config.LogLevel.ERROR, area="HW")
		return False

# ============================================================================
# TIME SYNCHRONIZATION
# ============================================================================

def get_timezone_offset():
	"""Get timezone offset from worldtimeapi.org"""
	if not config.Env.TIMEZONE:
		logger.log("No TIMEZONE in settings.toml, using UTC", config.LogLevel.WARNING, area="HW")
		return 0

	url = f"http://worldtimeapi.org/api/timezone/{config.Env.TIMEZONE}"
	response = None  # Initialize

	try:
		logger.log(f"Fetching timezone data for {config.Env.TIMEZONE}...", area="HW")
		response = state.session.get(url, timeout=10)

		if response.status_code == 200:
			data = response.json()

			# Get UTC offset in seconds, convert to hours
			offset_seconds = data.get("raw_offset", 0)
			dst_offset = data.get("dst_offset", 0)
			total_offset = (offset_seconds + dst_offset) / 3600

			is_dst = data.get("dst", False)
			dst_status = "DST" if is_dst else "Standard"

			logger.log(f"Timezone: {config.Env.TIMEZONE} = UTC{total_offset:+.1f} ({dst_status})", area="HW")
			return int(total_offset)
		else:
			logger.log(f"Timezone API error: {response.status_code}", config.LogLevel.ERROR, area="HW")
			return -6  # Default to CST

	except Exception as e:
		logger.log(f"Timezone fetch failed: {e}", config.LogLevel.ERROR, area="HW")
		return -6  # Default to CST

	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass

def sync_time(rtc):
	"""Sync RTC with NTP server using correct timezone"""
	logger.log("Syncing time with NTP...", area="HW")

	if not state.session:
		logger.log("No network session available", config.LogLevel.ERROR, area="HW")
		return False

	try:
		# Give network time to settle (socket pool needs to be ready)
		import time as time_module
		time_module.sleep(2)

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

		logger.log(f"Time synced: {now.tm_mon}/{now.tm_mday} {hour_12}:{now.tm_min:02d} {ampm}", area="HW")
		return True

	except Exception as e:
		logger.log(f"NTP sync failed: {e}", config.LogLevel.WARNING, area="HW")
		logger.log("Continuing with RTC time (may be incorrect)", config.LogLevel.WARNING, area="HW")
		return False


