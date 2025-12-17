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
			log_parts.append(f"{name} ${s['price']:,.2f}")
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
			# Format with comma separator for thousands
			if price >= 1000:
				value_text = f"{price:,.0f}"  # e.g., "2,843"
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
		value_label = bitmap_label.Label(
			state.font_small,
			color=color,
			text=value_text,
			anchor_point=(1.0, 0.0),  # Right-aligned
			anchored_position=(config.Layout.WIDTH - 1, y_pos)  # Right edge minus 1px margin
		)
		state.main_group.append(value_label)

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

	# Determine color based on direction (inline)
	if change_percent >= 0:
		chart_color = config.Colors.GREEN
		pct_color = config.Colors.GREEN
	else:
		chart_color = config.Colors.RED
		pct_color = config.Colors.RED

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

	# Right-align using anchor point (inline)
	pct_label = bitmap_label.Label(
		state.font_small,
		text=pct_text,
		color=pct_color,
		anchor_point=(1.0, 0.0),  # Right-aligned
		anchored_position=(config.Layout.WIDTH - 1, 1)  # Right edge minus 1px margin
	)
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

	# Right-align using anchor point (inline)
	price_label = bitmap_label.Label(
		state.font_small,
		text=price_text,
		color=config.Colors.WHITE,
		anchor_point=(1.0, 0.0),  # Right-aligned
		anchored_position=(config.Layout.WIDTH - 1, 9)  # Right edge minus 1px margin
	)
	state.main_group.append(price_label)

	# Chart area: y=17 to y=31 (15 pixels tall) (inline)
	CHART_HEIGHT = 15
	CHART_Y_START = 17
	CHART_WIDTH = 64

	if time_series and len(time_series) > 0:
		# Progressive loading: only show elapsed portion of trading day
		# 78 points = 6.5 hours trading day at 5min intervals
		# Show only points that have occurred so far
		num_total_points = 78  # Full trading day
		num_available_points = len(time_series)  # What we have

		# Use only available points (inline)
		points_to_show = time_series[:num_available_points]

		# Find min and max prices for scaling (inline)
		prices = [point["close_price"] for point in points_to_show]
		min_price = min(prices)
		max_price = max(prices)
		price_range = max_price - min_price

		# Handle flat line (inline)
		if price_range == 0:
			price_range = 1

		# Compress points to fit 64 pixels, preserving first and last (inline)
		data_points = []
		num_points = len(points_to_show)

		if num_points <= CHART_WIDTH:
			# No compression needed - direct mapping
			for i, point in enumerate(points_to_show):
				x = int((i / (num_points - 1)) * (CHART_WIDTH - 1)) if num_points > 1 else 0
				price_scaled = (point["close_price"] - min_price) / price_range
				y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
				data_points.append((x, y))
		else:
			# Compression needed: preserve first and last, compress middle
			# Always show first point (open)
			first_point = points_to_show[0]
			price_scaled = (first_point["close_price"] - min_price) / price_range
			y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
			data_points.append((0, y))

			# Compress middle points (inline)
			middle_pixels = CHART_WIDTH - 2  # Exclude first and last
			middle_points = num_points - 2  # Exclude first and last

			for pixel_x in range(1, CHART_WIDTH - 1):
				# Map pixel to data point index (inline)
				point_idx = 1 + int((pixel_x - 1) * middle_points / middle_pixels)
				point = points_to_show[point_idx]
				price_scaled = (point["close_price"] - min_price) / price_range
				y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
				data_points.append((pixel_x, y))

			# Always show last point (current price)
			last_point = points_to_show[-1]
			price_scaled = (last_point["close_price"] - min_price) / price_range
			y = CHART_Y_START + CHART_HEIGHT - 1 - int(price_scaled * (CHART_HEIGHT - 1))
			data_points.append((CHART_WIDTH - 1, y))

		# Draw lines connecting data points (inline)
		for i in range(len(data_points) - 1):
			x1, y1 = data_points[i]
			x2, y2 = data_points[i + 1]
			line = Line(x1, y1, x2, y2, color=chart_color)
			state.main_group.append(line)

	# Display for duration (inline)
	time.sleep(duration)
	logger.log("Stock chart display complete", config.LogLevel.INFO, area="STOCKS")
