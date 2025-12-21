"""
Pantallita 3.0 - Event Display Module
Renders event displays with custom images and colored text
INLINE ARCHITECTURE - everything inline, no helper functions
"""

import time
import gc
from adafruit_display_text import bitmap_label
import displayio

import config
import state
import logger


# ============================================================================
# BOTTOM-ALIGNED TEXT POSITIONING (INLINE HELPER)
# ============================================================================

def calculate_bottom_aligned_positions(font, top_text, bottom_text):
	"""
	Calculate Y positions for bottom-aligned text

	Positions text from bottom of display upward, ensuring it stays above bottom margin

	Args:
		font: Font object to use for text measurement
		top_text: Top line text string
		bottom_text: Bottom line text string

	Returns:
		tuple: (top_y, bottom_y) positions for text labels

	INLINE - all calculation inline
	"""
	# Create temporary labels to measure bounding boxes (inline)
	temp_top = bitmap_label.Label(font, text=top_text)
	temp_bottom = bitmap_label.Label(font, text=bottom_text)

	# Get bounding box heights (inline)
	top_height = temp_top.bounding_box[3]
	bottom_height = temp_bottom.bounding_box[3]

	# Calculate positions from bottom up (inline)
	# Bottom text Y = display height - bottom margin - bottom text height
	bottom_y = config.Layout.HEIGHT - config.Layout.EVENT_BOTTOM_MARGIN - bottom_height

	# Top text Y = bottom text Y - line spacing - top text height
	top_y = bottom_y - config.Layout.EVENT_LINE_SPACING - top_height

	# Clean up temp labels (inline)
	del temp_top
	del temp_bottom

	return (top_y, bottom_y)


# ============================================================================
# EVENT DISPLAY (INLINE)
# ============================================================================

def show_events(active_events, duration):
	"""
	Display events for specified duration

	Handles single or multiple events:
	- Single event: Full duration
	- Multiple events: Time split equally (minimum duration enforced)

	Layout (64×32 pixels):
	- Event image: 25×28 (top-right, x=37, y=2)
	- Top text: Left-aligned, DIMMEST_WHITE (greeting/name)
	- Bottom text: Left-aligned, custom color (occasion)
	- Bottom-aligned text positioning

	Args:
		active_events: List of event data arrays [[top, bottom, image, color, start, end], ...]
		duration: Total duration in seconds for all events

	INLINE - all rendering and timing logic inline
	"""
	if not active_events:
		logger.log("No active events to display", config.LogLevel.DEBUG, area="EVENT")
		return

	event_count = len(active_events)
	logger.log(f"Displaying {event_count} event(s) for {duration}s total", config.LogLevel.INFO, area="EVENT")

	# Calculate duration per event (inline)
	if event_count == 1:
		duration_per_event = duration
	else:
		# Split time equally, enforce minimum duration (inline)
		duration_per_event = max(
			config.Layout.EVENT_MIN_DURATION,
			duration // event_count
		)

	# Display each event in sequence (inline)
	for i, event_data in enumerate(active_events):
		# event_data = [top_line, bottom_line, image, color, start_hour, end_hour]
		top_line = event_data[0]
		bottom_line = event_data[1]
		image_file = event_data[2]
		color_name = event_data[3]

		logger.log(f"Showing event {i+1}/{event_count}: {top_line} {bottom_line} ({duration_per_event}s)", config.LogLevel.INFO, area="EVENT")

		# Show single event (inline)
		show_event(top_line, bottom_line, image_file, color_name, duration_per_event)

		# Memory cleanup between events (inline)
		gc.collect()


def show_event(top_text, bottom_text, image_file, color_name, duration):
	"""
	Display a single event for specified duration

	Args:
		top_text: Top line text (greeting/name)
		bottom_text: Bottom line text (occasion)
		image_file: Image filename (e.g., "cake.bmp")
		color_name: Color name for bottom text (e.g., "RED", "BUGAMBILIA")
		duration: Duration in seconds

	INLINE - all rendering inline
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	# === DRAW EVENT IMAGE (TOP-RIGHT) ===

	# Load event image with fallback (inline with LRU cache)
	event_image_path = f"{config.Paths.EVENT_IMAGES}/{image_file}"
	fallback_image_path = f"{config.Paths.EVENT_IMAGES}/blank.bmp"

	try:
		# Try loading event-specific image (inline)
		# LRU Cache check (inline)
		if event_image_path in state.image_cache:
			# Cache hit - move to end (mark as recently used)
			state.image_cache_order.remove(event_image_path)
			state.image_cache_order.append(event_image_path)
			bitmap = state.image_cache[event_image_path]
			logger.log(f"Using cached event image: {image_file}", config.LogLevel.DEBUG, area="EVENT")
		else:
			# Cache miss - load from SD card
			logger.log(f"Loading event image from SD: {image_file}", config.LogLevel.DEBUG, area="EVENT")
			bitmap = displayio.OnDiskBitmap(event_image_path)

			# Add to cache
			state.image_cache[event_image_path] = bitmap
			state.image_cache_order.append(event_image_path)

			# LRU eviction: remove oldest if cache is full
			if len(state.image_cache_order) > state.IMAGE_CACHE_MAX:
				oldest_path = state.image_cache_order.pop(0)
				del state.image_cache[oldest_path]
				logger.log(f"Evicted oldest image from cache: {oldest_path}", config.LogLevel.DEBUG, area="EVENT")

		# Create TileGrid with bitmap's pixel shader
		event_img = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
		event_img.x = config.Layout.EVENT_IMAGE_X
		event_img.y = config.Layout.EVENT_IMAGE_Y
		state.main_group.append(event_img)

	except Exception as e:
		# Fallback to blank.bmp (inline)
		logger.log(f"Event image error ({image_file}): {e}, using blank.bmp", config.LogLevel.WARNING, area="EVENT")

		try:
			# LRU Cache check for fallback (inline)
			if fallback_image_path in state.image_cache:
				state.image_cache_order.remove(fallback_image_path)
				state.image_cache_order.append(fallback_image_path)
				bitmap = state.image_cache[fallback_image_path]
			else:
				bitmap = displayio.OnDiskBitmap(fallback_image_path)
				state.image_cache[fallback_image_path] = bitmap
				state.image_cache_order.append(fallback_image_path)

				if len(state.image_cache_order) > state.IMAGE_CACHE_MAX:
					oldest_path = state.image_cache_order.pop(0)
					del state.image_cache[oldest_path]

			event_img = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
			event_img.x = config.Layout.EVENT_IMAGE_X
			event_img.y = config.Layout.EVENT_IMAGE_Y
			state.main_group.append(event_img)

		except Exception as fallback_error:
			logger.log(f"Fallback image error: {fallback_error}", config.LogLevel.ERROR, area="EVENT")
			# Continue without image

	# === DRAW BOTTOM-ALIGNED TEXT ===

	# Calculate text positions (inline)
	top_y, bottom_y = calculate_bottom_aligned_positions(state.font_small, top_text, bottom_text)

	# Get color from config.Colors (inline)
	try:
		color = getattr(config.Colors, color_name, config.Colors.WHITE)
	except AttributeError:
		logger.log(f"Unknown color: {color_name}, using WHITE", config.LogLevel.WARNING, area="EVENT")
		color = config.Colors.WHITE

	# Create top text label (DIMMEST_WHITE) (inline)
	top_label = bitmap_label.Label(
		state.font_small,
		color=config.Colors.DIMMEST_WHITE,
		text=top_text,
		x=config.Layout.EVENT_TEXT_X,
		y=top_y
	)
	state.main_group.append(top_label)

	# Create bottom text label (custom color) (inline)
	bottom_label = bitmap_label.Label(
		state.font_small,
		color=color,
		text=bottom_text,
		x=config.Layout.EVENT_TEXT_X,
		y=bottom_y
	)
	state.main_group.append(bottom_label)

	# Display for duration (inline)
	logger.log(f"Event: '{top_text}' / '{bottom_text}' (color: {color_name})", config.LogLevel.INFO, area="EVENT")
	time.sleep(duration)
