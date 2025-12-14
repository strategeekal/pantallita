"""
Pantallita 3.0 - Forecast Display Module
Renders 12-hour forecast with smart precipitation detection
CRITICAL: ALL logic is INLINE - NO helper functions
"""

import time
import displayio
from adafruit_display_text import bitmap_label

import config
import state
import hardware
import logger

# ============================================================================
# FORECAST DISPLAY (EVERYTHING INLINE)
# ============================================================================

def show(current_data, forecast_data, duration):
	"""
	Show 3-column forecast display with smart precipitation logic.

	CRITICAL ARCHITECTURE RULE:
	This function has ZERO helper function calls (except hardware.button_up_pressed).
	All logic is inlined to minimize stack depth.

	Args:
		current_data: Current weather dict from weather_api.fetch_current()
		forecast_data: List of 12 hourly forecasts from weather_api.fetch_forecast()
		duration: How long to display (seconds)
	"""

	# Validate inputs
	if not current_data:
		logger.log("No current weather data for forecast display", config.LogLevel.WARNING, area="FORECAST")
		return

	if not forecast_data or len(forecast_data) < 2:
		logger.log(f"Insufficient forecast data (need 2, got {len(forecast_data) if forecast_data else 0})", config.LogLevel.WARNING, area="FORECAST")
		return

	# ========================================================================
	# SMART COLUMN SELECTION LOGIC (INLINE - FLATTENED)
	# ========================================================================

	# Default: show hours 0 and 1 (next 2 hours)
	col2_index = 0
	col3_index = 1

	# Extract precipitation flags for first 6 hours (inline - avoid nested access)
	current_has_precip = current_data.get('has_precipitation', False)
	precip_flags = [h.get('has_precipitation', False) for h in forecast_data[:min(6, len(forecast_data))]]

	# Precipitation logic (inline - sequential, not nested)
	if current_has_precip:
		# Currently raining - find when it stops
		stop_hour = -1
		for i in range(len(precip_flags)):
			if not precip_flags[i]:
				stop_hour = i
				break

		if stop_hour != -1:
			# Rain stops - show stop hour and next hour
			col2_index = stop_hour
			col3_index = min(stop_hour + 1, len(forecast_data) - 1)
			logger.log(f"Smart: Rain stops at hour {stop_hour+1}", config.LogLevel.DEBUG, area="FORECAST")
		else:
			# Rain doesn't stop - show hour 1 and last hour (11)
			col2_index = 1
			col3_index = 11
			logger.log(f"Smart: Rain continues, showing hour 1 and 11", config.LogLevel.DEBUG, area="FORECAST")
	else:
		# Not raining - find when it starts
		rain_start = -1
		rain_stop = -1

		for i in range(len(precip_flags)):
			if precip_flags[i] and rain_start == -1:
				rain_start = i
			elif not precip_flags[i] and rain_start != -1 and rain_stop == -1:
				rain_stop = i
				break

		if rain_start != -1:
			if rain_stop != -1:
				# Rain starts and stops - show both transitions
				col2_index = rain_start
				col3_index = rain_stop
				logger.log(f"Smart: Rain hours {rain_start+1} to {rain_stop+1}", config.LogLevel.DEBUG, area="FORECAST")
			else:
				# Rain starts but doesn't stop - show start and last hour
				col2_index = rain_start
				col3_index = 11
				logger.log(f"Smart: Rain starts at hour {rain_start+1}, doesn't stop", config.LogLevel.DEBUG, area="FORECAST")
		# else: No rain - keep default (hours 0, 1)

	# Duplicate hour check (if forecast[0] hour == current hour, skip it)
	current_hour = state.rtc.datetime.tm_hour
	first_forecast_hour = int(forecast_data[col2_index]['datetime'][11:13]) % 24

	if col2_index == 0 and first_forecast_hour == current_hour and len(forecast_data) >= 3:
		# Shift forward to avoid duplicate
		col2_index = 1
		col3_index = 2
		logger.log(f"Smart: Skipped duplicate hour {current_hour}, showing hours 1-2", config.LogLevel.DEBUG, area="FORECAST")

	# ========================================================================
	# CLEAR DISPLAY (Inline - CircuitPython safe method)
	# ========================================================================
	try:
		while True:
			state.main_group.pop()
	except IndexError:
		pass  # Group is empty

	# ========================================================================
	# CALCULATE TIME LABELS AND COLORS (INLINE)
	# ========================================================================

	# Column 1: Current time (will update live)
	col1_temp = f"{int(current_data['feels_like'])}\u00b0"
	col1_icon = current_data['icon']

	# Column 2: Selected forecast hour
	col2_temp = f"{int(forecast_data[col2_index]['feels_like'])}\u00b0"
	col2_icon = forecast_data[col2_index]['icon']
	col2_hour = int(forecast_data[col2_index]['datetime'][11:13]) % 24

	# Calculate hours ahead for column 2
	col2_hours_ahead = (col2_hour - current_hour) % 24

	# Determine color (white if consecutive, mint if jumped)
	if col2_hours_ahead <= 1:
		col2_color = config.Colors.DIMMEST_WHITE
	else:
		col2_color = config.Colors.MINT

	# Column 3: Selected forecast hour
	col3_temp = f"{int(forecast_data[col3_index]['feels_like'])}\u00b0"
	col3_icon = forecast_data[col3_index]['icon']
	col3_hour = int(forecast_data[col3_index]['datetime'][11:13]) % 24

	# Calculate gap between col3 and col2 (not from current hour!)
	col3_col2_gap = (col3_hour - col2_hour) % 24

	# Color cascade: if col2 is MINT, col3 is ALWAYS MINT
	# Otherwise, check if col3 jumped from col2
	if col2_color == config.Colors.MINT:
		col3_color = config.Colors.MINT
	elif col3_col2_gap <= 1:
		col3_color = config.Colors.DIMMEST_WHITE
	else:
		col3_color = config.Colors.MINT

	# Format time labels for columns 2 and 3 (12-hour format with A/P suffix)
	# Inline 12-hour conversion
	col2_hour_12 = col2_hour % 12
	if col2_hour_12 == 0:
		col2_hour_12 = 12
	col2_suffix = "A" if col2_hour < 12 else "P"
	col2_time = f"{col2_hour_12}{col2_suffix}"

	col3_hour_12 = col3_hour % 12
	if col3_hour_12 == 0:
		col3_hour_12 = 12
	col3_suffix = "A" if col3_hour < 12 else "P"
	col3_time = f"{col3_hour_12}{col3_suffix}"

	# Log what we're displaying
	unit_symbol = "\u00b0C" if config.Env.TEMPERATURE_UNIT == "C" else "\u00b0F"
	logger.log(f"Displaying forecast: Current {col1_temp[:-1]}{unit_symbol} \u2192 {col2_time} {col2_temp[:-1]}{unit_symbol}, {col3_time} {col3_temp[:-1]}{unit_symbol}", area="FORECAST")

	# ========================================================================
	# LOAD COLUMN ICONS WITH LRU CACHE (INLINE)
	# ========================================================================

	columns_data = [
		{"icon": col1_icon, "x": config.Layout.FORECAST_COL1_X, "temp": col1_temp},
		{"icon": col2_icon, "x": config.Layout.FORECAST_COL2_X, "temp": col2_temp},
		{"icon": col3_icon, "x": config.Layout.FORECAST_COL3_X, "temp": col3_temp}
	]

	for i, col in enumerate(columns_data):
		icon_path = f"{config.Paths.FORECAST_IMAGES}/{col['icon']}.bmp"

		try:
			# LRU Cache check (inline - no helper functions)
			if icon_path in state.image_cache:
				# Cache hit - move to end (mark as recently used)
				state.image_cache_order.remove(icon_path)
				state.image_cache_order.append(icon_path)
				bitmap = state.image_cache[icon_path]
			else:
				# Cache miss - load from SD card
				bitmap = displayio.OnDiskBitmap(icon_path)

				# Add to cache
				state.image_cache[icon_path] = bitmap
				state.image_cache_order.append(icon_path)

				# LRU eviction: remove oldest if cache is full
				if len(state.image_cache_order) > state.IMAGE_CACHE_MAX:
					oldest_path = state.image_cache_order.pop(0)  # Remove oldest
					del state.image_cache[oldest_path]  # Free memory

			# Create TileGrid
			tile_grid = displayio.TileGrid(
				bitmap,
				pixel_shader=bitmap.pixel_shader,
				x=col["x"],
				y=config.Layout.FORECAST_COLUMN_Y
			)

			state.main_group.append(tile_grid)

		except OSError as e:
			logger.log(f"Column {i+1} icon {col['icon']} not found: {e}", config.LogLevel.WARNING, area="FORECAST")
			# Continue without icon
		except Exception as e:
			logger.log(f"Column {i+1} icon loading error: {e}", config.LogLevel.ERROR, area="FORECAST")
			# Continue without icon

	# ========================================================================
	# CREATE TIME LABELS - CENTERED WITHIN COLUMNS (INLINE)
	# ========================================================================

	# Calculate column centers inline (simple arithmetic, zero stack depth)
	col1_center_x = config.Layout.FORECAST_COL1_X + config.Layout.FORECAST_COLUMN_WIDTH // 2  # 1 + 10 = 11
	col2_center_x = config.Layout.FORECAST_COL2_X + config.Layout.FORECAST_COLUMN_WIDTH // 2  # 22 + 10 = 32
	col3_center_x = config.Layout.FORECAST_COL3_X + config.Layout.FORECAST_COLUMN_WIDTH // 2  # 43 + 10 = 53

	# Column 1 time (will update live - start with placeholder)
	col1_time_label = bitmap_label.Label(
		state.font_small,
		text="00:00",  # Placeholder, will update immediately
		color=config.Colors.DIMMEST_WHITE
	)
	col1_time_label.anchor_point = (0.5, 0.0)  # Center horizontally, top vertically
	col1_time_label.anchored_position = (col1_center_x, config.Layout.FORECAST_TIME_Y)
	state.main_group.append(col1_time_label)

	# Column 2 time (static)
	col2_time_label = bitmap_label.Label(
		state.font_small,
		text=col2_time,
		color=col2_color
	)
	col2_time_label.anchor_point = (0.5, 0.0)
	col2_time_label.anchored_position = (col2_center_x, config.Layout.FORECAST_TIME_Y)
	state.main_group.append(col2_time_label)

	# Column 3 time (static)
	col3_time_label = bitmap_label.Label(
		state.font_small,
		text=col3_time,
		color=col3_color
	)
	col3_time_label.anchor_point = (0.5, 0.0)
	col3_time_label.anchored_position = (col3_center_x, config.Layout.FORECAST_TIME_Y)
	state.main_group.append(col3_time_label)

	# ========================================================================
	# CREATE TEMPERATURE LABELS - CENTERED WITHIN COLUMNS (INLINE)
	# ========================================================================

	temp_centers = [col1_center_x, col2_center_x, col3_center_x]

	for i, col in enumerate(columns_data):
		temp_label = bitmap_label.Label(
			state.font_small,
			text=col["temp"],
			color=config.Colors.DIMMEST_WHITE
		)
		temp_label.anchor_point = (0.5, 0.0)  # Center horizontally, top vertically
		temp_label.anchored_position = (temp_centers[i], config.Layout.FORECAST_TEMP_Y)
		state.main_group.append(temp_label)

	# ========================================================================
	# INTERRUPTIBLE SLEEP WITH LIVE CLOCK FOR COLUMN 1 (INLINE)
	# ========================================================================

	end_time = time.monotonic() + duration
	last_minute = -1  # Track last minute to avoid unnecessary updates

	while time.monotonic() < end_time:
		# Check button inline
		import hardware
		if hardware.button_up_pressed():
			logger.log("UP button pressed during forecast display", config.LogLevel.INFO, area="FORECAST")
			raise KeyboardInterrupt

		# Update column 1 time only when minute changes
		now = state.rtc.datetime
		current_minute = now.tm_min

		if current_minute != last_minute:
			# Minute changed - update column 1 time
			hour = now.tm_hour
			hour_12 = hour % 12
			if hour_12 == 0:
				hour_12 = 12

			new_time_text = f"{hour_12}:{current_minute:02d}"
			col1_time_label.text = new_time_text
			last_minute = current_minute

		time.sleep(0.1)

	logger.log("Forecast display complete \n", area="FORECAST")
