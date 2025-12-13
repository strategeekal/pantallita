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
		x=config.Layout.LEFT_EDGE,
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
	# UV INDEX BAR (Inline - white bar with gaps every 3 pixels)
	# ========================================================================
	uv = weather_data.get('uv', 0)
	
	# UV index is 0-11+ scale, use directly as pixel count (don't scale)
	uv_pixels = int(uv)
	uv_pixels = min(uv_pixels, 11)  # Cap at 11 (though UV can go higher)
	
	# Draw pixels with gaps inserted every 3 pixels for readability
	# Pattern: *** *** *** (gaps don't count toward UV index)
	pixels_drawn = 0
	position = 0
	
	while pixels_drawn < uv_pixels:
		# Draw pixel at current position (white)
		rect = Rect(position + config.Layout.LEFT_EDGE, config.Layout.UV_BAR_Y, 1, 1, fill=config.Colors.WHITE)
		state.main_group.append(rect)
		pixels_drawn += 1
		position += 1
		
		# Insert gap every 3 pixels drawn (but not after the last pixel)
		if pixels_drawn % 3 == 0 and pixels_drawn < uv_pixels:
			position += 1  # Skip one position to create gap

		
	# ========================================================================
	# HUMIDITY BAR (Inline - white with gaps every 2 pixels)
	# ========================================================================
	humidity = weather_data.get('humidity', 0)
	
	# Calculate: 1 pixel per 10% humidity (0-100% = 0-10 pixels)
	humidity_pixels = int(round(humidity / 10))
	humidity_pixels = min(humidity_pixels, 10)
	
	# Draw pixels with gaps inserted for readability
	# Pattern: ** ** ** ** * (gaps don't count toward humidity)
	pixels_drawn = 0
	position = 0
	
	while pixels_drawn < humidity_pixels:
		# Draw pixel at current position
		rect = Rect(position + config.Layout.LEFT_EDGE, config.Layout.HUMIDITY_BAR_Y, 1, 1, fill=config.Colors.WHITE)
		state.main_group.append(rect)
		pixels_drawn += 1
		position += 1
		
		# Insert gap every 2 pixels drawn (but not after the last pixel)
		if pixels_drawn % 2 == 0 and pixels_drawn < humidity_pixels:
			position += 1  # Skip one position to create gap
	
	# ========================================================================
	# INTERRUPTIBLE SLEEP WITH LIVE CLOCK (Inline)
	# ========================================================================
	
	end_time = time.monotonic() + duration
	last_minute = -1  # Track last minute to avoid unnecessary updates
	
	while time.monotonic() < end_time:
		# Check button inline (import hardware only when needed to avoid circular imports)
		import hardware
		if hardware.button_up_pressed():
			log("UP button pressed during weather display", config.LogLevel.INFO)
			raise KeyboardInterrupt
	
		# Update clock only when minute changes (prevents blinking)
		now = state.rtc.datetime
		current_minute = now.tm_min
	
		if current_minute != last_minute:
			# Minute changed - update display
			hour = now.tm_hour
			hour_12 = hour % 12
			if hour_12 == 0:
				hour_12 = 12
	
			new_time_text = f"{hour_12}:{current_minute:02d}"
			time_label.text = new_time_text
			last_minute = current_minute
	
		time.sleep(0.1)

	
	log("Weather display complete")