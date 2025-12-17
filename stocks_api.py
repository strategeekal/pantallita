"""
Pantallita 3.0 - Stocks API Module
Fetches stock/forex/crypto/commodity data from Twelve Data API
INLINE ARCHITECTURE - no helper functions
"""

import time
import config
import state
import logger

# ============================================================================
# STOCKS CSV LOADING (INLINE)
# ============================================================================

def load_stocks_csv():
	"""
	Load stocks from CSV with priority: GitHub > Local > Empty
	Returns list of stock dicts or empty list if none found
	INLINE - no helper functions
	"""
	stocks = []

	# Try GitHub first
	if config.Env.STOCKS_GITHUB_URL:
		github_stocks = load_stocks_from_github()
		if github_stocks:
			logger.log(f"Loaded {len(github_stocks)} stocks from GitHub", area="STOCKS")
			return github_stocks

	# Try local CSV
	local_stocks = load_stocks_from_local()
	if local_stocks:
		logger.log(f"Loaded {len(local_stocks)} stocks from local stocks.csv", area="STOCKS")
		return local_stocks

	logger.log("No stocks configured (no local or GitHub stocks.csv)", config.LogLevel.WARNING, area="STOCKS")
	return []


def load_stocks_from_github():
	"""
	Load stocks.csv from GitHub URL
	Returns list of stock dicts or empty list
	INLINE - all parsing inline
	"""
	response = None

	try:
		logger.log("Fetching stocks.csv from GitHub...", config.LogLevel.DEBUG, area="STOCKS")
		response = state.session.get(config.Env.STOCKS_GITHUB_URL, timeout=10)

		if response.status_code != 200:
			logger.log(f"GitHub stocks fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="STOCKS")
			return []

		# Parse CSV content (inline)
		return parse_stocks_csv_content(response.text)

	except Exception as e:
		logger.log(f"GitHub stocks fetch failed: {e}", config.LogLevel.WARNING, area="STOCKS")
		return []

	finally:
		if response:
			try:
				response.close()
			except:
				pass


def load_stocks_from_local():
	"""
	Load stocks.csv from local file
	Returns list of stock dicts or empty list
	INLINE - all parsing inline
	"""
	try:
		with open('/stocks.csv', 'r') as f:
			content = f.read()
		return parse_stocks_csv_content(content)

	except OSError:
		logger.log("Local stocks.csv not found", config.LogLevel.DEBUG, area="STOCKS")
		return []

	except Exception as e:
		logger.log(f"Error loading local stocks.csv: {e}", config.LogLevel.ERROR, area="STOCKS")
		return []


def parse_stocks_csv_content(csv_content):
	"""
	Parse stock/forex/crypto/commodity CSV content

	Format: symbol,name,type,display_name,highlight
	- symbol: Ticker (required)
	- name: Full name (required)
	- type: stock/forex/crypto/commodity (optional, default: stock)
	- display_name: Short name for display (optional, default: symbol)
	- highlight: 0 or 1 for chart mode (optional, default: 0)

	INLINE - all parsing inline, no helper functions
	"""
	stocks = []

	try:
		lines = csv_content.strip().split('\n')

		for line in lines:
			line = line.strip()

			# Skip empty lines and comments
			if not line or line.startswith('#'):
				continue

			# Parse line (inline)
			parts = [p.strip() for p in line.split(',')]

			if len(parts) >= 2:
				symbol = parts[0].upper()  # Uppercase ticker symbols
				name = parts[1]

				# Parse optional fields (inline)
				item_type = parts[2].lower() if len(parts) >= 3 and parts[2] else "stock"
				display_name = parts[3].upper() if len(parts) >= 4 and parts[3] else symbol

				# Parse highlight flag (inline)
				highlight = False
				if len(parts) >= 5 and parts[4]:
					highlight = (parts[4] == '1' or parts[4].lower() == 'true')

				stocks.append({
					"symbol": symbol,
					"name": name,
					"type": item_type,
					"display_name": display_name,
					"highlight": highlight
				})

		logger.log(f"Parsed {len(stocks)} stocks from CSV", config.LogLevel.DEBUG, area="STOCKS")
		return stocks

	except Exception as e:
		logger.log(f"Error parsing stocks CSV: {e}", config.LogLevel.ERROR, area="STOCKS")
		return []


# ============================================================================
# STOCK QUOTES FETCHING (INLINE)
# ============================================================================

def fetch_stock_quotes(symbols_to_fetch):
	"""
	Fetch current stock quotes from Twelve Data API (batch request)

	Args:
		symbols_to_fetch: List of stock symbol dicts [{"symbol": "AAPL", ...}, ...]

	Returns:
		dict: {symbol: {"price": float, "change_percent": float, "direction": str, "open_price": float}}

	INLINE - all parsing inline, no helper functions
	"""
	if not symbols_to_fetch:
		return {}

	# Check API key
	if not config.Env.TWELVE_DATA_API_KEY:
		logger.log("TWELVE_DATA_API_KEY not configured", config.LogLevel.ERROR, area="STOCKS")
		return {}

	response = None
	stock_data = {}

	try:
		# Build comma-separated symbol list (inline)
		symbols_list = [s["symbol"] for s in symbols_to_fetch]
		symbols_str = ",".join(symbols_list)

		# Twelve Data Quote API endpoint (batch)
		url = f"https://api.twelvedata.com/quote?symbol={symbols_str}&apikey={config.Env.TWELVE_DATA_API_KEY}"

		logger.log(f"Fetching quotes: {symbols_str}", config.LogLevel.DEBUG, area="STOCKS")
		response = state.session.get(url, timeout=10)

		if response.status_code != 200:
			logger.log(f"Stock API error: HTTP {response.status_code}", config.LogLevel.ERROR, area="STOCKS")
			return {}

		# Parse JSON (inline)
		data = response.json()

		# Handle Twelve Data response formats (inline)
		# Single symbol: {"symbol": "AAPL", "close": ..., "percent_change": ...}
		# Multiple symbols: {"AAPL": {"symbol": "AAPL", ...}, "MSFT": {...}}

		if "symbol" in data:
			# Single quote response
			quotes = [data]
		elif isinstance(data, dict):
			# Batch response
			quotes = list(data.values())
		else:
			logger.log(f"Unexpected API response format", config.LogLevel.ERROR, area="STOCKS")
			return {}

		# Parse each quote (inline)
		for quote in quotes:
			# Check for errors (inline)
			if "status" in quote and quote["status"] == "error":
				logger.log(f"Quote error for {quote.get('symbol', 'unknown')}: {quote.get('message', 'unknown')}", config.LogLevel.WARNING, area="STOCKS")
				continue

			symbol = quote.get("symbol")
			if not symbol:
				continue

			# Extract data (inline)
			try:
				price = float(quote.get("close", 0))
				open_price = float(quote.get("open", 0))
				change_percent = float(quote.get("percent_change", 0))
				direction = "up" if change_percent >= 0 else "down"

				stock_data[symbol] = {
					"price": price,
					"open_price": open_price,
					"change_percent": change_percent,
					"direction": direction
				}

			except (ValueError, TypeError) as e:
				logger.log(f"Error parsing {symbol}: {e}", config.LogLevel.WARNING, area="STOCKS")
				continue

		logger.log(f"Fetched {len(stock_data)}/{len(symbols_list)} quotes", area="STOCKS")
		return stock_data

	except Exception as e:
		logger.log(f"Stock quotes fetch failed: {e}", config.LogLevel.ERROR, area="STOCKS")
		return {}

	finally:
		if response:
			try:
				response.close()
			except:
				pass


# ============================================================================
# INTRADAY TIME SERIES FETCHING (INLINE)
# ============================================================================

def fetch_intraday_time_series(symbol, interval="15min", outputsize=26):
	"""
	Fetch intraday time series data from Twelve Data API

	Args:
		symbol: Stock ticker (e.g., "CRM")
		interval: Data interval ("5min", "15min", "30min", "1h")
		outputsize: Number of data points (default 26 = ~6.5 hours with 15min)

	Returns:
		List of dicts: [{datetime, open_price, close_price}, ...]
		Ordered chronologically (oldest first)
		Returns empty list on error

	INLINE - all parsing inline, no helper functions
	"""
	if not config.Env.TWELVE_DATA_API_KEY:
		logger.log("TWELVE_DATA_API_KEY not configured", config.LogLevel.ERROR, area="STOCKS")
		return []

	response = None

	try:
		# Build URL (inline)
		url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={config.Env.TWELVE_DATA_API_KEY}"

		logger.log(f"Fetching intraday for {symbol}...", config.LogLevel.DEBUG, area="STOCKS")
		response = state.session.get(url, timeout=10)

		if response.status_code != 200:
			logger.log(f"Time series API error: HTTP {response.status_code}", config.LogLevel.ERROR, area="STOCKS")
			return []

		# Parse JSON (inline)
		data = response.json()

		# Check for errors (inline)
		if "status" in data and data["status"] == "error":
			logger.log(f"Time series error for {symbol}: {data.get('message', 'unknown')}", config.LogLevel.ERROR, area="STOCKS")
			return []

		# Extract values array (inline)
		values = data.get("values", [])
		if not values:
			logger.log(f"No time series data for {symbol}", config.LogLevel.WARNING, area="STOCKS")
			return []

		# Parse time series data (inline)
		time_series = []
		for point in values:
			try:
				time_series.append({
					"datetime": point.get("datetime", ""),
					"open_price": float(point.get("open", 0)),
					"close_price": float(point.get("close", 0))
				})
			except (ValueError, TypeError) as e:
				logger.log(f"Error parsing time series point: {e}", config.LogLevel.WARNING, area="STOCKS")
				continue

		# Reverse to get chronological order (Twelve Data returns newest first)
		time_series.reverse()

		logger.log(f"Fetched {len(time_series)} data points for {symbol}", area="STOCKS")
		return time_series

	except Exception as e:
		logger.log(f"Time series fetch failed for {symbol}: {e}", config.LogLevel.ERROR, area="STOCKS")
		return []

	finally:
		if response:
			try:
				response.close()
			except:
				pass
