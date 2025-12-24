"""
Pantallita 3.0 - Transit Display Module (v2.5 format)
Renders CTA train and bus arrival predictions using v2.5 display layout
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
import hardware


# ============================================================================
# TRANSIT DISPLAY (V2.5 FORMAT)
# ============================================================================

def show_transit(duration, current_data=None):
	"""
	Display transit arrivals for specified duration (v2.5 format)

	Layout (64×32 pixels):
	- Header: "CTA HH:MM TEMP°" or "MMM DD HH:MM" (top-left, y=1, MINT color)
	- Weekday indicator: 4×4 colored square (top-right corner)
	- 3 route rows (y=9, y=17, y=25):
		- Route indicator: 4×6 colored rectangle or text (x=1)
		- Destination label: (x=8)
		- Up to 2 arrival times: right-aligned columns (x=51, x=63)

	Updates continuously during display duration:
	- Refresh transit data every 60 seconds
	- Update clock every minute

	Args:
		duration: Total duration in seconds
		current_data: Optional weather data dict with 'feels_like' temp

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

	# === DRAW HEADER ===
	# Header: "CTA HH:MM TEMP°" or "MMM DD HH:MM" (all-in-one header, no separate clock)
	now = state.rtc.datetime
	hour_12 = now.tm_hour % 12
	if hour_12 == 0:
		hour_12 = 12
	time_str = f"{hour_12}:{now.tm_min:02d}"

	# Build dynamic header based on weather availability
	if current_data and "feels_like" in current_data:
		temp = round(current_data["feels_like"])
		header_text = f"CTA {time_str} {temp}°"
	else:
		# Month abbreviations
		months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
		month_abbr = months[now.tm_mon - 1] if 1 <= now.tm_mon <= 12 else "???"
		header_text = f"{month_abbr} {now.tm_mday:02d} {time_str}"

	header_label = bitmap_label.Label(
		state.font_small,
		color=config.Colors.MINT,
		text=header_text,
		x=1,
		y=1
	)
	state.main_group.append(header_label)

	# Weekday indicator (if enabled)
	if config_manager.should_show_weekday_indicator():
		display_weekday.add_weekday_indicator(state.rtc)

	# Route row Y positions (v2.5 layout)
	row_y_positions = [9, 17, 25]  # Y positions for 3 route rows

	# Store route elements for updates
	route_indicators = [None, None, None]  # TileGrids or Labels
	destination_labels = [None, None, None]
	time1_labels = [None, None, None]
	time2_labels = [None, None, None]

	# Pre-create labels (will be updated in loop)
	for i in range(3):
		y_pos = row_y_positions[i]

		# Destination label (x=8, white)
		dest_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.WHITE,
			text="",
			x=7,
			y=y_pos
		)
		state.main_group.append(dest_label)
		destination_labels[i] = dest_label

		# Time labels (right-aligned columns)
		# Destination has space from x=8 to ~x=40 (32 pixels for longer names)
		# Column 1: right-align at x=51 (2-digit numbers)
		# Column 2: right-align at x=63 (2-digit numbers)
		time1_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.WHITE,
			text=""
		)
		time1_label.anchor_point = (1.0, 0.0)  # Set anchor AFTER creation
		time1_label.anchored_position = (51, y_pos)  # Then set position
		state.main_group.append(time1_label)
		time1_labels[i] = time1_label

		time2_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.WHITE,
			text=""
		)
		time2_label.anchor_point = (1.0, 0.0)  # Set anchor AFTER creation
		time2_label.anchored_position = (63, y_pos)  # Then set position
		state.main_group.append(time2_label)
		time2_labels[i] = time2_label

	# === DISPLAY LOOP (CONTINUOUS UPDATES) ===

	start_time = time.monotonic()
	last_transit_fetch = 0
	last_minute = -1
	need_display_update = True  # Flag to update display only when needed

	logger.log(f"Displaying transit arrivals", config.LogLevel.INFO, area="TRANSIT")

	while time.monotonic() - start_time < duration:
		elapsed = time.monotonic() - start_time
		current_minute = state.rtc.datetime.tm_min

		# Update header time every minute
		if current_minute != last_minute:
			now = state.rtc.datetime
			hour_12 = now.tm_hour % 12
			if hour_12 == 0:
				hour_12 = 12
			time_str = f"{hour_12}:{now.tm_min:02d}"

			# Update header text with new time
			if current_data and "feels_like" in current_data:
				temp = round(current_data["feels_like"])
				header_label.text = f"CTA {time_str} {temp}°"
			else:
				months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
				month_abbr = months[now.tm_mon - 1] if 1 <= now.tm_mon <= 12 else "???"
				header_label.text = f"{month_abbr} {now.tm_mday:02d} {time_str}"

			last_minute = current_minute

		# Refresh transit data (every 60 seconds)
		if elapsed - last_transit_fetch > 60:
			logger.log(f"Transit refresh ({elapsed:.0f}s elapsed)", config.LogLevel.DEBUG, area="TRANSIT")

			try:
				new_transit_data = transit_api.fetch_transit_data()

				if new_transit_data:
					transit_data = new_transit_data
					need_display_update = True  # Mark for update
				else:
					logger.log("Transit refresh returned no data", config.LogLevel.WARNING, area="TRANSIT")

			except Exception as e:
				logger.log(f"Transit refresh error: {e}", config.LogLevel.WARNING, area="TRANSIT")

			# Cleanup after fetch (inline)
			gc.collect()
			last_transit_fetch = elapsed

		# Update display with current transit_data (only when data changes)
		if need_display_update:
			need_display_update = False  # Reset flag

			# Take up to 3 routes
			routes_to_show = transit_data[:3]

			for i, route_data in enumerate(routes_to_show):
				# route_data = {'label': str, 'color': str, 'color2': str or None, 'arrivals': [...]}
				label = route_data['label']
				color_name = route_data['color']
				color2_name = route_data.get('color2')  # Optional second color
				arrivals = route_data['arrivals']
				route_type = route_data.get('type', 'train')

				y_pos = row_y_positions[i]

				# Get color from config.Colors (inline)
				try:
					color = getattr(config.Colors, color_name, config.Colors.WHITE)
				except AttributeError:
					logger.log(f"Unknown color: {color_name}, using WHITE", config.LogLevel.WARNING, area="TRANSIT")
					color = config.Colors.WHITE

				# Get second color if specified (inline)
				color2 = None
				if color2_name:
					try:
						color2 = getattr(config.Colors, color2_name, None)
					except AttributeError:
						logger.log(f"Unknown color2: {color2_name}, ignoring", config.LogLevel.WARNING, area="TRANSIT")
						color2 = None

				# Create route indicator if not exists (inline)
				if route_indicators[i] is None:
					if route_type == 'bus':
						# Bus: Show route number as text (v2.5 style)
						route_num = route_data.get('route', '8')
						indicator = bitmap_label.Label(
							state.font_small,
							color=color,
							text=route_num,
							x=1,
							y=y_pos
						)
						state.main_group.append(indicator)
						route_indicators[i] = indicator
					else:
						# Train: Show 4×6 colored rectangle
						# If color2 specified, create split rectangle (left 2px + right 2px)
						if color2:
							# Split rectangle: 2 pixels color1 (x=0-1), 2 pixels color2 (x=2-3)
							rect_bitmap = displayio.Bitmap(4, 6, 2)
							rect_palette = displayio.Palette(2)
							rect_palette[0] = color   # Left side
							rect_palette[1] = color2  # Right side
							# Fill left half with color1
							for y in range(6):
								for x in range(2):  # x=0,1
									rect_bitmap[x, y] = 0
							# Fill right half with color2
							for y in range(6):
								for x in range(2, 4):  # x=2,3
									rect_bitmap[x, y] = 1
						else:
							# Single color rectangle
							rect_bitmap = displayio.Bitmap(4, 6, 1)
							rect_palette = displayio.Palette(1)
							rect_palette[0] = color

						rect_grid = displayio.TileGrid(rect_bitmap, pixel_shader=rect_palette, x=1, y=y_pos)
						state.main_group.append(rect_grid)
						route_indicators[i] = rect_grid

				# Update destination label (inline)
				destination_labels[i].text = label

				# Update arrival times (take first 2) (inline)
				time1_labels[i].text = str(arrivals[0]['minutes']) if len(arrivals) >= 1 else ""
				time2_labels[i].text = str(arrivals[1]['minutes']) if len(arrivals) >= 2 else ""

			# Clear unused rows (inline)
			for i in range(len(routes_to_show), 3):
				destination_labels[i].text = ""
				time1_labels[i].text = ""
				time2_labels[i].text = ""

				# Remove indicator if present
				if route_indicators[i] is None:
					try:
						state.main_group.remove(route_indicators[i])
					except ValueError:
						pass
					route_indicators[i] = None

		# Check for button press (inline)
		if hardware.button_up_pressed():
			logger.log("UP button pressed - stopping execution", config.LogLevel.INFO, area="TRANSIT")
			raise KeyboardInterrupt  # Stop code execution

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

	# Display for duration with button check (inline)
	logger.log(f"No transit data - showing message for {duration}s", config.LogLevel.INFO, area="TRANSIT")

	start_time = time.monotonic()
	while time.monotonic() - start_time < duration:
		# Check for button press (inline)
		if hardware.button_up_pressed():
			logger.log("UP button pressed - stopping execution", config.LogLevel.INFO, area="TRANSIT")
			raise KeyboardInterrupt  # Stop code execution

		time.sleep(1)
