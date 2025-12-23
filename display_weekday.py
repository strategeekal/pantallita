"""
Pantallita 3.0 - Weekday Indicator Module
Displays 4×4 colored square in top-right corner indicating day of week
INLINE ARCHITECTURE - all logic inline, no helper functions
"""

import displayio
import config
import state
import logger


# ============================================================================
# WEEKDAY INDICATOR (INLINE)
# ============================================================================

def add_weekday_indicator(rtc):
	"""
	Add 4×4 colored day-of-week indicator to top-right corner with 1px black margin

	Position: x=59, y=0 (top-right corner)
	Size: 5×5 bitmap (4×4 colored square + 1px black margin on left/bottom)
	Colors: Monday=RED, Tuesday=ORANGE, Wednesday=YELLOW, Thursday=GREEN,
	        Friday=AQUA, Saturday=PURPLE, Sunday=PINK

	Uses displayio.Bitmap for memory efficiency (1 object vs 25 Line objects)

	Args:
		rtc: Real-time clock object for getting current day

	INLINE - all color mapping and bitmap creation inline
	"""
	# Get current day of week (0=Monday, 6=Sunday)
	weekday = rtc.datetime.tm_wday

	# Map day to color (inline - no helper function)
	if weekday == 0:
		day_color = config.Colors.RED      # Monday
	elif weekday == 1:
		day_color = config.Colors.ORANGE   # Tuesday
	elif weekday == 2:
		day_color = config.Colors.YELLOW   # Wednesday
	elif weekday == 3:
		day_color = config.Colors.GREEN    # Thursday
	elif weekday == 4:
		day_color = config.Colors.AQUA     # Friday
	elif weekday == 5:
		day_color = config.Colors.PURPLE   # Saturday
	elif weekday == 6:
		day_color = config.Colors.PINK     # Sunday
	else:
		day_color = config.Colors.WHITE    # Fallback (should never happen)

	# Create 5×5 bitmap (4×4 square + 1px margin on left/bottom) - inline
	bitmap = displayio.Bitmap(5, 5, 2)  # 2 colors: black, day color
	palette = displayio.Palette(2)
	palette[0] = config.Colors.BLACK    # Margin color
	palette[1] = day_color              # Day color

	# Fill entire bitmap with black (margin) - inline
	for y in range(5):
		for x in range(5):
			bitmap[x, y] = 0

	# Fill 4×4 colored square (offset by 1 to leave left margin, y=0-3 for top alignment) - inline
	for y in range(0, 4):  # y = 0, 1, 2, 3 (top 4 rows)
		for x in range(1, 5):  # x = 1, 2, 3, 4 (skip x=0 for left margin)
			bitmap[x, y] = 1  # Use day color

	# Create TileGrid at top-right corner (x=59 to account for left margin)
	day_grid = displayio.TileGrid(
		bitmap,
		pixel_shader=palette,
		x=59,  # 64 - 5 = 59 (left margin at x=59, colored square at x=60-63)
		y=0    # Top edge
	)

	state.main_group.append(day_grid)

	logger.log(f"Weekday indicator added: day={weekday}", config.LogLevel.DEBUG, area="WEEKDAY")
