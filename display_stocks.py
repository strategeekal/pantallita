"""
Pantallita 3.0 - Stock Display Module
Renders multi-stock and single stock chart displays
INLINE ARCHITECTURE - no helper functions, everything inline
"""

import time
from adafruit_display_text import bitmap_label
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.line import Line

import config
import state
import logger

# ============================================================================
# MULTI-STOCK DISPLAY (INLINE)
# ============================================================================

def show_multi_stock(stocks_to_show, duration):
	"""
	Display 3 stocks/forex/crypto/commodities vertically

	Display format by type:
	- Stock: Triangle arrows (▲▼) + ticker + percentage change (colored)
	- Forex: $ indicator + ticker + price (colored, with K/M suffix)
	- Crypto: $ indicator + ticker + price (colored, with K/M suffix)
	- Commodity: $ indicator + ticker + price (colored, with K/M suffix)

	Args:
		stocks_to_show: List of up to 3 stock dicts with price/change data
		duration: Display duration in seconds

	INLINE - all rendering inline, no helper functions
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	# Log start with prices (inline)
	log_parts = []
	for s in stocks_to_show:
		name = s.get("display_name", s["symbol"])
		if s.get("type") == "stock":
			log_parts.append(f"{name} {s['change_percent']:+.1f}%")
		else:
			# Format price with manual commas for logging
			price = s['price']
			if price >= 1000:
				price_int = int(price)
				price_str = str(price_int)
				if len(price_str) > 3:
					parts = []
					for i in range(len(price_str), 0, -3):
						start = max(0, i - 3)
						parts.insert(0, price_str[start:i])
					price_formatted = ",".join(parts)
				else:
					price_formatted = price_str
				log_parts.append(f"{name} ${price_formatted}")
			else:
				log_parts.append(f"{name} ${price:.2f}")
	logger.log(f"Displaying multi-stock: {', '.join(log_parts)}", config.LogLevel.INFO, area="STOCKS")

	# Row positions (divide 32px height into 3 sections) - inline
	row_positions = [2, 13, 24]

	# Render each stock (inline)
	for i, stock in enumerate(stocks_to_show):
		if i >= 3:  # Max 3 items
			break

		y_pos = row_positions[i]
		item_type = stock.get("type", "stock")

		# Determine color based on direction (inline)
		if stock["direction"] == "up":
			color = config.Colors.GREEN
		else:
			color = config.Colors.RED

		# Format value based on type (inline)
		if item_type == "stock":
			# Stock: Show percentage change (e.g., "+2.3%")
			pct = stock["change_percent"]
			value_text = f"{pct:+.1f}%"
		else:
			# Forex/Crypto/Commodity: Show full price with comma separator
			price = stock['price']
			# Format with comma separator for thousands (manual approach for CircuitPython)
			if price >= 1000:
				# Convert to int and add commas manually
				price_int = int(price)
				price_str = str(price_int)
				# Insert commas (inline)
				if len(price_str) > 3:
					# e.g., "1234" -> "1,234", "12345" -> "12,345"
					parts = []
					for i in range(len(price_str), 0, -3):
						start = max(0, i - 3)
						parts.insert(0, price_str[start:i])
					value_text = ",".join(parts)
				else:
					value_text = price_str
			else:
				value_text = f"{price:.2f}"  # e.g., "18.49"

		# Create indicator (inline)
		if item_type in ["forex", "crypto", "commodity"]:
			# Forex/Crypto/Commodity: Dollar sign indicator
			indicator_label = bitmap_label.Label(
				state.font_small,
				color=color,
				text="$",
				x=1,
				y=y_pos
			)
			state.main_group.append(indicator_label)
		else:
			# Stock: Triangle arrow indicator (inline)
			if stock["direction"] == "up":
				# Up triangle: ▲
				arrow_triangle = Triangle(
					1, y_pos + 4,   # Bottom left
					3, y_pos + 1,   # Top peak
					5, y_pos + 4,   # Bottom right
					fill=color
				)
			else:
				# Down triangle: ▼
				arrow_triangle = Triangle(
					1, y_pos + 1,   # Top left
					3, y_pos + 4,   # Bottom peak
					5, y_pos + 1,   # Top right
					fill=color
				)
			state.main_group.append(arrow_triangle)

		# Ticker symbol (use display_name)
		display_text = stock.get("display_name", stock["symbol"])
		ticker_label = bitmap_label.Label(
			state.font_small,
			color=config.Colors.DIMMEST_WHITE,
			text=display_text,
			x=8,
			y=y_pos
		)
		state.main_group.append(ticker_label)

		# Value (percentage or price, right-aligned with 1px margin)
		# Use manual x calculation to avoid anchor point baseline issues
		value_label = bitmap_label.Label(
			state.font_small,
			color=color,
			text=value_text,
			x=0,  # Temporary, will adjust
			y=y_pos
		)
		# Calculate right-aligned position (inline)
		# bounding_box[2] gives width; subtract from WIDTH for 1px margin
		value_label.x = config.Layout.WIDTH - value_label.bounding_box[2]
		state.main_group.append(value_label)

	# Add cache indicator when displaying stocks outside market hours (inline)
	# Market hours: 9:30 AM - 4:00 PM ET on weekdays (8:30 AM - 3:00 PM local Chicago)
	now = state.rtc.datetime
	current_minutes = now.tm_hour * 60 + now.tm_min
	current_weekday = now.tm_wday  # 0=Monday, 6=Sunday
	is_weekday = current_weekday < 5
	is_market_hours = (current_minutes >= state.market_open_local_minutes and
	                  current_minutes < state.market_close_local_minutes)
	show_cache_indicator = not (is_weekday and is_market_hours)

	if show_cache_indicator:
		# Draw 4-pixel LILAC indicator at top center (y=0, x=30-33)
		for x in range(30, 34):
			pixel = Line(x, 0, x, 0, color=config.Colors.LILAC)
			state.main_group.append(pixel)

	# Display for duration (inline)
	time.sleep(duration)
	logger.log("Multi-stock display complete", config.LogLevel.INFO, area="STOCKS")


# ============================================================================
# SINGLE STOCK CHART DISPLAY (INLINE)
# ============================================================================

def show_single_stock_chart(stock_symbol, stock_quote, time_series, duration):
	"""
	Display single stock with intraday price chart

	Layout:
	- Row 1 (y=1): Ticker symbol + percentage change
	- Row 2 (y=9): Current price (right-aligned)
	- Chart area (y=17-31): Intraday price movement (15 pixels tall)

	Args:
		stock_symbol: Stock symbol (e.g., "CRM")
		stock_quote: Quote dict with price/change data
		time_series: List of price points [{datetime, open_price, close_price}, ...]
		duration: Display duration in seconds

	INLINE - all rendering inline, no helper functions
	"""
	# Clear display (inline)
	while len(state.main_group) > 0:
		state.main_group.pop()

	# Get display name (inline)
	display_name = stock_quote.get("display_name", stock_symbol)

	# Log start with price and percentage (inline)
	logger.log(f"Displaying stock chart: {display_name} ${stock_quote['price']:.2f} {stock_quote['change_percent']:+.2f}%", config.LogLevel.INFO, area="STOCKS")

	# Extract quote data (inline)
	current_price = stock_quote["price"]
	change_percent = stock_quote["change_percent"]
	direction = stock_quote["direction"]

	# Determine percentage color based on direction (inline)
	if change_percent >= 0:
		pct_color = config.Colors.GREEN
	else:
		pct_color = config.Colors.RED

	# Get opening price for bicolor chart (from quote, fallback to time series)
	opening_price = stock_quote.get("open_price")
	if opening_price is None or opening_price == 0:
		# Fallback to first point in time series if quote doesn't have it
		if time_series and len(time_series) > 0:
			opening_price = time_series[0].get("open_price")
			if opening_price is None:
				opening_price = time_series[0].get("close_price")

	# Debug log for bicolor chart
	logger.log(f"Bicolor chart: {display_name} open=${opening_price:.2f}, current=${current_price:.2f}, change={change_percent:+.2f}%", config.LogLevel.DEBUG, area="STOCKS")

	# Row 1 (y=1): Ticker + percentage (inline)
	ticker_label = bitmap_label.Label(
		state.font_small,
		text=display_name,
		color=config.Colors.DIMMEST_WHITE,
		x=1,
		y=1
	)
	state.main_group.append(ticker_label)

	# Format percentage with + sign (inline)
	pct_text = f"{change_percent:+.2f}%"

	# Right-align using manual calculation (avoid anchor point baseline issues)
	pct_label = bitmap_label.Label(
		state.font_small,
		text=pct_text,
		color=pct_color,
		x=0,  # Temporary, will adjust
		y=1
	)
	pct_label.x = config.Layout.WIDTH - pct_label.bounding_box[2]
	state.main_group.append(pct_label)

	# Row 2 (y=9): Current price (inline)
	# Format price with $ and commas if needed (inline)
	if current_price >= 1000:
		# Format with commas, no cents
		price_text = f"${int(current_price):,}"
	elif current_price >= 1:
		# Show 2 decimals
		price_text = f"${current_price:.2f}"
	else:
		# Small prices, show more precision
		price_text = f"${current_price:.4f}"

	# Right-align using manual calculation (avoid anchor point baseline issues)
	price_label = bitmap_label.Label(
		state.font_small,
		text=price_text,
		color=config.Colors.WHITE,
		x=0,  # Temporary, will adjust
		y=9
	)
	price_label.x = config.Layout.WIDTH - price_label.bounding_box[2]
	state.main_group.append(price_label)

	# Chart area: y=17 to y=31 (15 pixels tall) (inline)
	CHART_HEIGHT = 15
	CHART_Y_START = 17
	CHART_WIDTH = 64

	if time_series and len(time_series) > 0:
		# Progressive loading: calculate expected points based on elapsed time
		# Trading day: 6.5 hours = 390 minutes = 78 points at 5min intervals
		# Calculate elapsed time to determine how many points to show
		trading_minutes = 390  # 9:30 AM - 4:00 PM
		num_total_points = 78  # Full trading day at 5min intervals

		# Use available points (inline)
		points_to_show = time_series  # All available points (chronological)

		# Find min and max prices for scaling (inline)
		prices = [point["close_price"] for point in points_to_show]
		min_price = min(prices)
		max_price = max(prices)
		price_range = max_price - min_price

		# Handle flat line (inline)
		if price_range == 0:
			price_range = 1

		# Progressive display: show points proportionally on left, blank space on right
		data_points = []
		num_points = len(points_to_show)

		# Calculate display width based on ACTUAL elapsed time, not number of points
		# Get current time in minutes since midnight (local) from DS3231 RTC
		now = state.rtc.datetime
		current_minutes = now.tm_hour * 60 + now.tm_min
		current_weekday = now.tm_wday  # 0=Monday, 6=Sunday

		# Check if we're actually in market hours (weekday + within market times)
		is_weekday = current_weekday < 5  # Monday-Friday
		is_within_market_hours = (current_minutes >= state.market_open_local_minutes and
		                         current_minutes <= state.market_close_local_minutes)

		# Debug logging to diagnose timezone issues
		logger.log(f"Chart timing: now={now.tm_hour}:{now.tm_min:02d} ({current_minutes}min), weekday={current_weekday}, market={state.market_open_local_minutes}-{state.market_close_local_minutes}, is_weekday={is_weekday}, is_within_hours={is_within_market_hours}", config.LogLevel.DEBUG, area="STOCKS")

		# Calculate elapsed minutes since market open
		if state.market_open_local_minutes > 0 and is_weekday and is_within_market_hours:
			# We're during actual market hours - show progressive chart
			elapsed_minutes = current_minutes - state.market_open_local_minutes
			progress_ratio = elapsed_minutes / trading_minutes
			logger.log(f"Progressive chart: elapsed={elapsed_minutes}min, ratio={progress_ratio:.2f} ({int(progress_ratio*100)}% of day)", config.LogLevel.DEBUG, area="STOCKS")
		else:
			# Outside market hours (weekend, before open, after close) - show full chart
			progress_ratio = 1.0
			logger.log(f"Full chart: outside market hours (market_open={state.market_open_local_minutes}, weekday={is_weekday}, within_hours={is_within_market_hours})", config.LogLevel.DEBUG, area="STOCKS")

		display_width = max(int(progress_ratio * CHART_WIDTH), 2)  # Minimum 2 pixels

		# Compress points to fit display_width, preserving first and last
		# Store (x, y, price) for bicolor chart support
		if num_points == 1:
			# Single point - show at x=0
			point = points_to_show[0]
			price_scaled = (point["close_price"] - min_price) / price_range
			y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
			data_points.append((0, y, point["close_price"]))
		elif num_points <= display_width:
			# No compression needed - direct mapping within display_width
			for i, point in enumerate(points_to_show):
				x = int((i / (num_points - 1)) * (display_width - 1)) if num_points > 1 else 0
				price_scaled = (point["close_price"] - min_price) / price_range
				y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
				data_points.append((x, y, point["close_price"]))
		else:
			# Compression needed: preserve first and last within display_width
			# Always show first point (open)
			first_point = points_to_show[0]
			price_scaled = (first_point["close_price"] - min_price) / price_range
			y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
			data_points.append((0, y, first_point["close_price"]))

			# Compress middle points within display_width
			middle_pixels = display_width - 2  # Exclude first and last
			middle_points = num_points - 2  # Exclude first and last

			if middle_pixels > 0 and middle_points > 0:
				for pixel_x in range(1, display_width - 1):
					# Map pixel to data point index (inline)
					point_idx = 1 + int((pixel_x - 1) * middle_points / middle_pixels)
					point = points_to_show[point_idx]
					price_scaled = (point["close_price"] - min_price) / price_range
					y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
					data_points.append((pixel_x, y, point["close_price"]))

			# Always show last point (current price)
			last_point = points_to_show[-1]
			price_scaled = (last_point["close_price"] - min_price) / price_range
			y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
			data_points.append((display_width - 1, y, last_point["close_price"]))

		# Draw lines connecting data points with bicolor (inline)
		# Color each segment based on whether ending point is above/below opening price
		for i in range(len(data_points) - 1):
			x1, y1, price1 = data_points[i]
			x2, y2, price2 = data_points[i + 1]

			# Determine color based on ending point vs opening price (bicolor chart)
			if opening_price is not None:
				if price2 >= opening_price:
					line_color = config.Colors.GREEN
				else:
					line_color = config.Colors.RED
			else:
				# Fallback: use overall direction color if opening price unavailable
				line_color = pct_color

			line = Line(x1, y1, x2, y2, color=line_color)
			state.main_group.append(line)

	# Add cache indicator when displaying stocks outside market hours (inline)
	# Market hours: 9:30 AM - 4:00 PM ET on weekdays (8:30 AM - 3:00 PM local Chicago)
	now = state.rtc.datetime
	current_minutes = now.tm_hour * 60 + now.tm_min
	current_weekday = now.tm_wday  # 0=Monday, 6=Sunday
	is_weekday = current_weekday < 5
	is_market_hours = (current_minutes >= state.market_open_local_minutes and
	                  current_minutes < state.market_close_local_minutes)
	show_cache_indicator = not (is_weekday and is_market_hours)

	if show_cache_indicator:
		# Draw 4-pixel LILAC indicator at top center (y=0, x=30-33)
		for x in range(30, 34):
			pixel = Line(x, 0, x, 0, color=config.Colors.LILAC)
			state.main_group.append(pixel)

	# Display for duration (inline)
	time.sleep(duration)
	logger.log("Stock chart display complete", config.LogLevel.INFO, area="STOCKS")
