"""
Pantallita 3.0 - Transit Display Module
Renders CTA train and bus arrival predictions
INLINE ARCHITECTURE - all logic inline, no helper functions
"""

import time
import gc
from adafruit_display_text import bitmap_label
import displayio

import config
import state
import logger
import config_manager
import display_weekday
import transit_api


# ============================================================================
# TRANSIT DISPLAY (INLINE)
# ============================================================================

def show_transit(duration):
	"""
	Display transit arrivals for specified duration

	Layout (64×32 pixels):
	- Header: "CTA" label (top-left, x=1, y=1)
	- 3 route rows (y=9, y=17, y=25):
		- Route icon (13×13, left side)
		- Route label (right of icon, max 9 chars, DIMMEST_WHITE)
		- Arrival times (right side, custom color, "5,12,18")
	- Weekday indicator (top-right corner, 4×4 colored square)

	Updates continuously during display duration:
	- Refresh transit data every TRANSIT_UPDATE_INTERVAL (1 minute)

	Args:
		duration: Total duration in seconds

	INLINE - all rendering and update logic inline
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	logger.log(f"Starting transit display ({duration}s)", config.LogLevel.INFO, area="TRANSIT")

	# Fetch initial transit data (inline)
	transit_data = transit_api.fetch_transit_data()

	if not transit_data:
		logger.log("No transit data available", config.LogLevel.WARNING, area="TRANSIT")
		# Show "No CTA" message instead of blank screen
		show_no_transit_message(duration)
		return

	# === DRAW STATIC ELEMENTS (ONCE) ===

	# Header label "CTA" (top-left) - inline
	header_label = bitmap_label.Label(
		state.font_small,
		color=config.Colors.DIMMEST_WHITE,
		text="CTA",
		x=1,
		y=1
	)
	state.main_group.append(header_label)

	# Weekday indicator (if enabled) - AFTER header
	if config_manager.should_show_weekday_indicator():
		display_weekday.add_weekday_indicator(state.rtc)

	# Route row Y positions (inline)
	row_y_positions = [9, 17, 25]  # Y positions for 3 route rows

	# Icons and labels for routes (inline)
	# We'll create placeholders that get updated in the loop
	# Each row: icon (13×13) at x=1, label at x=16, arrivals at x=28
	route_icons = []   # List of TileGrid objects (or None)
	route_labels = []  # List of Label objects
	arrival_labels = []  # List of Label objects

	# Pre-create labels for 3 routes (inline)
	for i in range(3):
		y_pos = row_y_positions[i]

		# Route label (initially empty, will be updated)
		route_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.DIMMEST_WHITE,
			text="",
			x=16,
			y=y_pos
		)
		state.main_group.append(route_label)
		route_labels.append(route_label)

		# Arrival times label (initially empty, will be updated)
		arrival_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.WHITE,  # Will be updated with route color
			text="",
			x=28,
			y=y_pos
		)
		state.main_group.append(arrival_label)
		arrival_labels.append(arrival_label)

		# Icon placeholder (will be loaded per route)
		route_icons.append(None)

	# === DISPLAY LOOP (CONTINUOUS UPDATES) ===

	start_time = time.monotonic()
	last_transit_fetch = 0

	logger.log(f"Displaying transit arrivals", config.LogLevel.INFO, area="TRANSIT")

	while time.monotonic() - start_time < duration:
		elapsed = time.monotonic() - start_time

		# Refresh transit data (every TRANSIT_UPDATE_INTERVAL = 60 seconds)
		if elapsed - last_transit_fetch > config.Timing.TRANSIT_UPDATE_INTERVAL:
			logger.log(f"Transit refresh ({elapsed:.0f}s elapsed)", config.LogLevel.DEBUG, area="TRANSIT")

			try:
				new_transit_data = transit_api.fetch_transit_data()

				if new_transit_data:
					transit_data = new_transit_data
				else:
					logger.log("Transit refresh returned no data", config.LogLevel.WARNING, area="TRANSIT")

			except Exception as e:
				logger.log(f"Transit refresh error: {e}", config.LogLevel.WARNING, area="TRANSIT")

			# Cleanup after fetch (inline)
			gc.collect()
			last_transit_fetch = elapsed

		# Update display with current transit_data (inline)
		# Take up to 3 routes
		routes_to_show = transit_data[:3]

		for i, route_data in enumerate(routes_to_show):
			# route_data = {'label': str, 'color': str, 'icon': str, 'arrivals': [...]}
			label = route_data['label']
			color_name = route_data['color']
			icon_file = route_data['icon']
			arrivals = route_data['arrivals']

			y_pos = row_y_positions[i]

			# Update route label (inline)
			route_labels[i].text = label

			# Update icon if changed (inline)
			icon_path = f"{config.Paths.COLUMN_IMAGES}/{icon_file}"

			# Check if icon needs loading (inline)
			if route_icons[i] is None:
				# First time - load icon
				try:
					# LRU Cache check (inline)
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
							oldest_path = state.image_cache_order.pop(0)
							del state.image_cache[oldest_path]

					# Create TileGrid with bitmap's pixel shader
					icon_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
					icon_grid.x = 1
					icon_grid.y = y_pos
					state.main_group.append(icon_grid)
					route_icons[i] = icon_grid

				except Exception as e:
					logger.log(f"Transit icon error ({icon_file}): {e}", config.LogLevel.WARNING, area="TRANSIT")

			# Get color from config.Colors (inline)
			try:
				color = getattr(config.Colors, color_name, config.Colors.WHITE)
			except AttributeError:
				logger.log(f"Unknown color: {color_name}, using WHITE", config.LogLevel.WARNING, area="TRANSIT")
				color = config.Colors.WHITE

			# Update arrival times (inline)
			# Format: "5,12,18" (comma-separated minutes)
			# Take first 3 arrivals
			arrival_times = []
			for arrival in arrivals[:3]:
				minutes = arrival['minutes']
				arrival_times.append(str(minutes))

			arrivals_text = ",".join(arrival_times) if arrival_times else "---"

			arrival_labels[i].text = arrivals_text
			arrival_labels[i].color = color

		# Clear unused rows (inline)
		for i in range(len(routes_to_show), 3):
			route_labels[i].text = ""
			arrival_labels[i].text = ""

			# Remove icon if present
			if route_icons[i] is not None:
				try:
					state.main_group.remove(route_icons[i])
				except ValueError:
					pass
				route_icons[i] = None

		# Sleep 1 second between updates
		time.sleep(1)

	logger.log(f"Transit display complete", config.LogLevel.INFO, area="TRANSIT")


def show_no_transit_message(duration):
	"""
	Show "No CTA" message when no transit data is available

	Args:
		duration: Duration in seconds

	INLINE - simple message display
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	# Weekday indicator (if enabled)
	if config_manager.should_show_weekday_indicator():
		display_weekday.add_weekday_indicator(state.rtc)

	# "No CTA" message (centered)
	message_label = bitmap_label.Label(
		state.font_small,
		color=config.Colors.DIMMEST_WHITE,
		text="No CTA",
		x=18,
		y=14
	)
	state.main_group.append(message_label)

	# Display for duration (inline)
	logger.log(f"No transit data - showing message for {duration}s", config.LogLevel.INFO, area="TRANSIT")
	time.sleep(duration)
