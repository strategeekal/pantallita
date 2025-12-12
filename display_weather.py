"""
Pantallita 3.0 - Weather Display Module
Renders current weather on RGB matrix
CRITICAL: ALL logic is INLINE - NO helper functions
"""

import time
import displayio
from adafruit_display_text import bitmap_label
from adafruit_display_shapes.rect import Rect
import adafruit_imageload

import config
import state
import hardware

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level=config.LogLevel.INFO):
	"""Simple logging"""
	if level <= config.CURRENT_LOG_LEVEL:
		level_name = ["", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE"][level]
		print(f"[DISPLAY:{level_name}] {message}")

# ============================================================================
# WEATHER DISPLAY (EVERYTHING INLINE)
# ============================================================================

def show(weather_data, duration):
	"""
	Show current weather display.
	
	CRITICAL ARCHITECTURE RULE:
	This function has ZERO helper function calls (except hardware.button_up_pressed).
	All logic is inlined to minimize stack depth.
	
	Args:
		weather_data: Dict with keys: temp, feels_like, uv, humidity, icon, condition
		duration: How long to display (seconds)
	"""
	
	if not weather_data:
		log("No weather data to display", config.LogLevel.WARNING)
		return
	
	log(f"Displaying weather: {weather_data['temp']}° {weather_data['condition']}")
	
	# ========================================================================
	# CLEAR DISPLAY (Inline - CircuitPython safe method)
	# ========================================================================
	try:
		while True:
			state.main_group.pop()
	except IndexError:
		pass  # Group is empty

	
	# ========================================================================
	# LOAD WEATHER ICON (Inline - OnDiskBitmap for full-screen images)
	# ========================================================================
	icon_num = weather_data['icon']
	icon_path = f"{config.Paths.WEATHER_IMAGES}/{icon_num}.bmp"
	
	try:
		log(f"Loading icon: {icon_path}", config.LogLevel.DEBUG)
		
		# Use OnDiskBitmap for full-screen BMPs
		bitmap = displayio.OnDiskBitmap(icon_path)
		
		# Create TileGrid with the bitmap's pixel shader
		tile_grid = displayio.TileGrid(
			bitmap,
			pixel_shader=bitmap.pixel_shader,
			x=0,
			y=0
		)
		
		state.main_group.append(tile_grid)
		log("Icon displayed successfully", config.LogLevel.DEBUG)
		
	except OSError as e:
		log(f"Weather icon {icon_num} not found: {e}", config.LogLevel.WARNING)
		# Continue without icon
	except Exception as e:
		log(f"Icon loading error: {e}", config.LogLevel.ERROR)
		import traceback
		traceback.print_exception(e)
		# Continue without icon

	log(weather_data)
	# ========================================================================
	# TEMPERATURE LABELS (v2 Logic - Correct)
	# ========================================================================
	temp = weather_data['temp']
	feels = weather_data['feels_like']
	shade = weather_data['feels_shade']
	
	# ========================================================================
	# TEMPERATURE (Always show, left aligned, Big Font)
	# ========================================================================
	temp_text = f"{temp}°"
	temp_label = bitmap_label.Label(
		state.font_large,
		text=temp_text,
		color=config.Colors.WHITE,
		x=config.Layout.WEATHER_TEMP_X,
		y=config.Layout.WEATHER_TEMP_Y
	)
	state.main_group.append(temp_label)
	
	# Show feels like if different from temp
	show_feels = (feels != temp)
	show_shade = (shade != feels)
	
	# ========================================================================
	# FEELS LIKE (Right-aligned, only show if different to temp)
	# ========================================================================
	if show_feels:
		feels_text = f"{feels}°"
	
		# Use anchor point for proper right-alignment with variable-width fonts
		feels_label = bitmap_label.Label(
			state.font_small,
			text=feels_text,
			color=config.Colors.WHITE,
			anchor_point=(1.0, 0.0),  # Right-top anchor
			anchored_position=(config.Layout.RIGHT_EDGE, config.Layout.FEELSLIKE_Y)
		)
		state.main_group.append(feels_label)
	
	# ========================================================================
	# FEELS SHADE (Right-aligned below feels, only show if different to feels)
	# ========================================================================
	if show_shade:
		shade_text = f"{shade}°"
	
		# Use anchor point for proper right-alignment
		shade_label = bitmap_label.Label(
			state.font_small,
			text=shade_text,
			color=config.Colors.WHITE,
			anchor_point=(1.0, 0.0),  # Right-top anchor
			anchored_position=(config.Layout.RIGHT_EDGE, config.Layout.FEELSLIKE_SHADE_Y)
		)
		state.main_group.append(shade_label)

	
	# ========================================================================
	# CLOCK (Centered if shade shown, else right-aligned at shade position)
	# ========================================================================
	# Get time from RTC
	now = state.rtc.datetime
	hour = now.tm_hour
	minute = now.tm_min
	
	# Convert to 12-hour format inline
	hour_12 = hour % 12
	if hour_12 == 0:
		hour_12 = 12
	
	time_text = f"{hour_12}:{minute:02d}"
	
	# Use anchor point for proper alignment with variable-width fonts
	if show_shade:
		# Centered
		time_label = bitmap_label.Label(
			state.font_small,
			text=time_text,
			color=config.Colors.WHITE,
			anchor_point=(0.5, 0.0),  # Center-top anchor
			anchored_position=(config.Display.WIDTH // 2, config.Layout.WEATHER_TIME_Y)
		)
	else:
		# Right-aligned at shade position
		time_label = bitmap_label.Label(
			state.font_small,
			text=time_text,
			color=config.Colors.WHITE,
			anchor_point=(1.0, 0.0),  # Right-top anchor
			anchored_position=(config.Layout.RIGHT_EDGE, config.Layout.WEATHER_TIME_Y)
		)
	
	state.main_group.append(time_label)

	
	# ========================================================================
	# UV INDEX BAR (Inline - no add_indicator_bar() helper)
	# ========================================================================
	uv = weather_data.get('uv', 0)
	
	# Calculate bar length inline (no calculate_uv_bar_length())
	uv_length = int((uv / 11) * config.Layout.BAR_MAX_LENGTH)
	uv_length = min(uv_length, config.Layout.BAR_MAX_LENGTH)  # Clamp
	
	# Choose color inline (no get_uv_color())
	if uv < 3:
		uv_color = config.Colors.GREEN
	elif uv < 6:
		uv_color = config.Colors.ORANGE
	elif uv < 8:
		uv_color = 0xFFA500  # Orange
	else:
		uv_color = config.Colors.RED
	
	# Draw bar inline (no loop helper)
	for i in range(uv_length):
		rect = Rect(i, config.Layout.UV_BAR_Y, 1, 1, fill=uv_color)
		state.main_group.append(rect)
	
	# ========================================================================
	# HUMIDITY BAR (Inline - same pattern as UV)
	# ========================================================================
	humidity = weather_data.get('humidity', 0)
	
	# Calculate bar length inline
	humidity_length = int((humidity / 100) * config.Layout.BAR_MAX_LENGTH)
	humidity_length = min(humidity_length, config.Layout.BAR_MAX_LENGTH)
	
	# Humidity color is always blue
	humidity_color = config.Colors.BLUE
	
	# Draw bar with gaps for readability (inline)
	for i in range(humidity_length):
		# Add gap every 10 pixels
		if i % 10 == 0 and i > 0:
			continue  # Skip this pixel to create gap
		rect = Rect(i, config.Layout.HUMIDITY_BAR_Y, 1, 1, fill=humidity_color)
		state.main_group.append(rect)
	
	# ========================================================================
	# INTERRUPTIBLE SLEEP (Inline - no sleep() helper)
	# ========================================================================
	end_time = time.monotonic() + duration
	
	while time.monotonic() < end_time:
		# Check button inline (only hardware call allowed)
		if hardware.button_up_pressed():
			raise KeyboardInterrupt  # Clean exit
		
		time.sleep(0.1)  # Small delay to prevent CPU spinning
	
	log("Weather display complete")