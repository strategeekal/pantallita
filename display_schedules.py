"""
Pantallita 3.0 - Schedule Display Module
Renders schedule displays with weather, clock, and progress bar
INLINE ARCHITECTURE - everything inline, no helper functions
"""

import time
import gc
from adafruit_display_text import bitmap_label
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
import displayio

import config
import config_manager
import state
import logger
import weather_api
import hardware
import display_weekday


# ============================================================================
# SCHEDULE DISPLAY (INLINE)
# ============================================================================

def show_schedule(rtc, schedule_name, schedule_config, duration):
	"""
	Display schedule for specified duration with continuous updates

	Layout (64×32 pixels):
	- Left (x:0-22): Clock, weather icon, temperature, UV bar
	- Right (x:23-63): Schedule image (40×28)
	- Bottom (x:23-62, y:28-32): Progress bar with markers

	Single long display loop (no segmentation):
	- Clock updates every minute
	- Progress bar updates continuously
	- Weather refreshes every 15 minutes (with cleanup)

	Args:
		rtc: Real-time clock object
		schedule_name: Name of schedule (e.g., "Get Dressed")
		schedule_config: Schedule configuration dict
		duration: Total duration in seconds

	INLINE - all rendering and update logic inline
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	logger.log(f"Starting schedule: {schedule_name} ({duration/60:.1f} min)", config.LogLevel.INFO, area="SCHEDULE")

	# Get night_mode level from schedule config (0=normal, 1=temp only, 2=clock only)
	night_mode = schedule_config.get("night_mode", 0)

	# Determine what to fetch and show based on night_mode
	# Level 0: Show icon, temp, UV (fetch weather)
	# Level 1: Show temp only, no icon/UV (fetch weather)
	# Level 2: Clock only, no weather (skip fetch)
	should_fetch_weather = (night_mode <= 1)  # Fetch for levels 0 and 1
	show_weather_icon = (night_mode == 0)     # Show icon only for level 0
	show_temperature = (night_mode <= 1)      # Show temp for levels 0 and 1
	show_uv_bar = (night_mode == 0)           # Show UV only for level 0

	if night_mode == 1:
		logger.log("Night mode 1: Temperature only (no icon/UV)", config.LogLevel.DEBUG, area="SCHEDULE")
	elif night_mode == 2:
		logger.log("Night mode 2: Clock only (no weather fetch)", config.LogLevel.DEBUG, area="SCHEDULE")

	# Fetch initial weather data (inline) - skip for night_mode 2
	weather_data = None
	if should_fetch_weather:
		try:
			weather_data = weather_api.fetch_current()
			if weather_data:
				uv_index = weather_data.get('uv', 0)
				logger.log(f"Weather: {weather_data['feels_like']}°, UV:{uv_index}", config.LogLevel.DEBUG, area="SCHEDULE")
		except Exception as e:
			logger.log(f"Schedule weather fetch error: {e}", config.LogLevel.WARNING, area="SCHEDULE")

	# === DRAW STATIC ELEMENTS (ONCE) ===

	# Schedule image (40×28, right side) - no cache (loaded once per schedule)
	try:
		schedule_image_path = f"{config.Paths.SCHEDULE_IMAGES}/{schedule_config['image']}"

		# Load directly without caching (schedules only run once per day)
		logger.log(f"Loading schedule image: {schedule_image_path}", config.LogLevel.DEBUG, area="SCHEDULE")
		bitmap = displayio.OnDiskBitmap(schedule_image_path)

		# Create TileGrid with bitmap's pixel shader
		schedule_img = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
		schedule_img.x = config.Layout.SCHEDULE_IMAGE_X
		schedule_img.y = config.Layout.SCHEDULE_IMAGE_Y
		state.main_group.append(schedule_img)

	except Exception as e:
		logger.log(f"Schedule image error: {e}", config.LogLevel.ERROR, area="SCHEDULE")
		return  # Skip schedule if image fails

	# Dynamic positioning based on UV presence (inline)
	uv_index = weather_data.get('uv', 0) if weather_data else 0
	if uv_index > 0:
		# UV bar shown - move weather icon up to reduce cramping
		weather_icon_y = config.Layout.SCHEDULE_WEATHER_ICON_Y - 1
		temp_y = config.Layout.SCHEDULE_TEMP_Y
	else:
		# No UV bar - keep icon position, move temp down for spacing
		weather_icon_y = config.Layout.SCHEDULE_WEATHER_ICON_Y
		temp_y = config.Layout.SCHEDULE_TEMP_Y + 1

	# Weather icon (13×13, left side below clock) - inline with LRU cache
	if weather_data and show_weather_icon:
		try:
			weather_icon = f"{weather_data['icon']}.bmp"
			weather_icon_path = f"{config.Paths.COLUMN_IMAGES}/{weather_icon}"

			# LRU Cache check (inline)
			if weather_icon_path in state.image_cache:
				# Cache hit - move to end (mark as recently used)
				state.image_cache_order.remove(weather_icon_path)
				state.image_cache_order.append(weather_icon_path)
				bitmap = state.image_cache[weather_icon_path]
			else:
				# Cache miss - load from SD card
				bitmap = displayio.OnDiskBitmap(weather_icon_path)

				# Add to cache
				state.image_cache[weather_icon_path] = bitmap
				state.image_cache_order.append(weather_icon_path)

				# LRU eviction: remove oldest if cache is full
				if len(state.image_cache_order) > state.IMAGE_CACHE_MAX:
					oldest_path = state.image_cache_order.pop(0)
					del state.image_cache[oldest_path]

			# Create TileGrid with bitmap's pixel shader
			weather_img = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
			weather_img.x = config.Layout.SCHEDULE_WEATHER_ICON_X
			weather_img.y = weather_icon_y  # Dynamic position
			state.main_group.append(weather_img)

		except Exception as e:
			logger.log(f"Weather icon error: {e}", config.LogLevel.WARNING, area="SCHEDULE")

	# Temperature label (below weather icon) - inline
	if weather_data and show_temperature:
		temp_text = f"{round(weather_data['feels_like'])}°"
		temp_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.DIMMEST_WHITE,
			text=temp_text,
			x=config.Layout.SCHEDULE_TEMP_X,
			y=temp_y  # Dynamic position
		)
		state.main_group.append(temp_label)

	# UV bar (only shown in night_mode 0) - inline
	if weather_data and show_uv_bar:
		uv_index = weather_data.get('uv', 0)
		if uv_index > 0:
			# Calculate UV bar length (inline)
			uv_length = min(int((uv_index / 11.0) * 40), 40)

			# Draw UV bar with gaps (inline)
			for i in range(uv_length):
				# Skip gap pixels every 3 pixels (inline)
				if i % 3 != 2:
					uv_pixel = Line(
						config.Layout.SCHEDULE_UV_X + i,
						config.Layout.SCHEDULE_UV_Y,
						config.Layout.SCHEDULE_UV_X + i,
						config.Layout.SCHEDULE_UV_Y,
						config.Colors.DIMMEST_WHITE
					)
					state.main_group.append(uv_pixel)

	# Clock label (top-left, 12-hour format) - inline
	clock_label = bitmap_label.Label(
		state.font_small,
		color=config.Colors.DIMMEST_WHITE,
		text="",  # Will update in loop
		x=config.Layout.SCHEDULE_CLOCK_X,
		y=config.Layout.SCHEDULE_CLOCK_Y
	)
	state.main_group.append(clock_label)

	# Progress bar (if enabled) - inline
	show_progress_bar = schedule_config.get("progressbar", True)
	progress_pixels = []  # Track progress pixels for updates

	if show_progress_bar:
		# Draw progress bar base (horizontal line, 2 pixels tall, MINT color) - inline
		for x in range(config.Layout.PROGRESS_BAR_X, config.Layout.PROGRESS_BAR_X + config.Layout.PROGRESS_BAR_WIDTH):
			# First pixel of base (at y=30)
			pixel_1 = Line(x, config.Layout.PROGRESS_BAR_Y, x, config.Layout.PROGRESS_BAR_Y, config.Colors.MINT)
			state.main_group.append(pixel_1)
			# Second pixel of base (at y=31)
			pixel_2 = Line(x, config.Layout.PROGRESS_BAR_Y + 1, x, config.Layout.PROGRESS_BAR_Y + 1, config.Colors.MINT)
			state.main_group.append(pixel_2)

		# Draw markers (inline)
		# Long markers: 0%, 50%, 100% (5 pixels tall, y=31 to y=27)
		# Short markers: 25%, 75% (4 pixels tall, y=31 to y=28)
		# Fixed positions: x=23, 32, 42, 52, 61 (segments: 9, 10, 10, 9 pixels)
		marker_positions = [
			(23, 5),    # 0% - long (5 pixels)
			(32, 4),    # 25% - short (4 pixels)
			(42, 5),    # 50% - long (5 pixels)
			(52, 4),    # 75% - short (4 pixels)
			(62, 5)     # 100% - long (5 pixels)
		]

		for marker_x, height in marker_positions:
			# Draw marker extending upward from y=31 (inline)
			# Each marker is 1 pixel wide
			for y_offset in range(height):
				marker_pixel = Line(
					marker_x,
					31 - y_offset,  # Start at y=31, extend upward
					marker_x,
					31 - y_offset,
					config.Colors.WHITE
				)
				state.main_group.append(marker_pixel)

	# Weekday indicator (if enabled and in normal mode only) - AFTER all static elements
	# Hide during night modes (1=temp only, 2=clock only)
	night_mode = schedule_config.get("night_mode", 0)
	if config_manager.should_show_weekday_indicator() and night_mode == 0:
		display_weekday.add_weekday_indicator(state.rtc)

	# === DISPLAY LOOP (CONTINUOUS UPDATES) ===

	start_time = time.monotonic()
	last_weather_fetch = 0
	last_minute = -1
	last_progress_column = -1

	logger.log(f"Displaying schedule: {schedule_name}", config.LogLevel.INFO, area="SCHEDULE")

	while time.monotonic() - start_time < duration:
		elapsed = time.monotonic() - start_time
		current_minute = rtc.datetime.tm_min
		current_hour = rtc.datetime.tm_hour

		# Update clock (every minute) - inline
		if current_minute != last_minute:
			# Convert to 12-hour format (inline)
			display_hour = current_hour % 12
			if display_hour == 0:
				display_hour = 12

			clock_text = f"{display_hour}:{current_minute:02d}"
			clock_label.text = clock_text
			last_minute = current_minute

			logger.log(f"Schedule: {schedule_name} - {clock_text} ({elapsed/60:.1f}/{duration/60:.1f} min)", config.LogLevel.DEBUG, area="SCHEDULE")

		# Update progress bar (continuous) - inline
		if show_progress_bar:
			progress = elapsed / duration
			current_column = int(progress * config.Layout.PROGRESS_BAR_WIDTH)

			# Add new progress pixels (inline)
			if current_column != last_progress_column and current_column < config.Layout.PROGRESS_BAR_WIDTH:
				# Fill from last position to current (inline)
				for col in range(last_progress_column + 1, current_column + 1):
					if col >= 0 and col < config.Layout.PROGRESS_BAR_WIDTH:
						# Draw filled pixels (2 pixels tall ABOVE base line, LILAC color)
						progress_x = config.Layout.PROGRESS_BAR_X + col
						# First pixel
						progress_pixel_1 = Line(
							progress_x,
							config.Layout.PROGRESS_BAR_Y,
							progress_x,
							config.Layout.PROGRESS_BAR_Y,
							config.Colors.LILAC
						)
						state.main_group.append(progress_pixel_1)
						progress_pixels.append(progress_pixel_1)
						# Second pixel
						progress_pixel_2 = Line(
							progress_x,
							config.Layout.PROGRESS_BAR_Y + 1,
							progress_x,
							config.Layout.PROGRESS_BAR_Y + 1,
							config.Colors.LILAC
						)
						state.main_group.append(progress_pixel_2)
						progress_pixels.append(progress_pixel_2)

				last_progress_column = current_column

		# Refresh weather + cleanup (every 5 minutes for stress test) - inline
		# Skip weather fetch for night_mode 2 (clock only)
		if should_fetch_weather and elapsed - last_weather_fetch > 300:  # 5 minutes (stress test)
			logger.log(f"Schedule weather refresh ({elapsed/60:.1f} min elapsed)", config.LogLevel.DEBUG, area="SCHEDULE")

			try:
				new_weather_data = weather_api.fetch_current()

				if new_weather_data and show_temperature:
					# Update temperature label (inline)
					temp_text = f"{round(new_weather_data['feels_like'])}°"
					temp_label.text = temp_text

					# Update weather icon if changed (inline) - only for night_mode 0
					if show_weather_icon and new_weather_data['icon'] != weather_data.get('icon'):
						# Load new weather icon with LRU cache (inline)
						weather_icon = f"{new_weather_data['icon']}.bmp"
						weather_icon_path = f"{config.Paths.COLUMN_IMAGES}/{weather_icon}"

						# LRU Cache check (inline)
						if weather_icon_path in state.image_cache:
							# Cache hit - move to end (mark as recently used)
							state.image_cache_order.remove(weather_icon_path)
							state.image_cache_order.append(weather_icon_path)
							bitmap = state.image_cache[weather_icon_path]
						else:
							# Cache miss - load from SD card
							bitmap = displayio.OnDiskBitmap(weather_icon_path)

							# Add to cache
							state.image_cache[weather_icon_path] = bitmap
							state.image_cache_order.append(weather_icon_path)

							# LRU eviction: remove oldest if cache is full
							if len(state.image_cache_order) > state.IMAGE_CACHE_MAX:
								oldest_path = state.image_cache_order.pop(0)
								del state.image_cache[oldest_path]

						# Find and update weather icon tile grid (inline)
						for item in state.main_group:
							if isinstance(item, displayio.TileGrid) and item.x == config.Layout.SCHEDULE_WEATHER_ICON_X:
								item.bitmap = bitmap
								item.pixel_shader = bitmap.pixel_shader
								break

					weather_data = new_weather_data

			except Exception as e:
				logger.log(f"Schedule weather refresh error: {e}", config.LogLevel.WARNING, area="SCHEDULE")

			# Cleanup after fetch (inline)
			gc.collect()
			last_weather_fetch = elapsed

		# Check for button press (inline)
		if hardware.button_up_pressed():
			logger.log("UP button pressed - stopping execution", config.LogLevel.INFO, area="SCHEDULE")
			raise KeyboardInterrupt  # Stop code execution

		# Sleep 1 second between updates
		time.sleep(1)

	logger.log(f"Schedule complete: {schedule_name}", config.LogLevel.INFO, area="SCHEDULE")
