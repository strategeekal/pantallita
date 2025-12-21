"""
Pantallita 3.0 - Phase 5: Schedule Display
Tests CircuitPython 10 foundation before implementing features (v3.0.0)
Phase 1: Current weather display (v3.0.1)
Phase 2: 12-hour forecast with smart precipitation detection (v3.0.2)
Phase 3: Display toggles and temperature unit control (v3.0.3)
Phase 4: Stock/forex/crypto/commodity display with market hours (v3.0.4)
Phase 5: Schedule display with date-based GitHub override (v3.0.5)

"""

import time
import gc
import traceback
import supervisor
from adafruit_display_text import bitmap_label

import config
import state
import hardware

# Import weather modules (Phase 1)
import weather_api
import display_weather

# Import forecast module (Phase 2)
import display_forecast

# Import centralized logger (Phase 1.5)
import logger

# Import configuration manager (Phase 3)
import config_manager

# Import stocks modules (Phase 4)
import stocks_api
import display_stocks

# Import schedule modules (Phase 5)
import schedule_loader
import display_schedules

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def show_message(text, color=config.Colors.GREEN, y_pos=16):
	"""Show a simple text message on display"""
	while len(state.main_group) > 0:
		state.main_group.pop()

	label = bitmap_label.Label(
		state.font_large,
		text=text,
		color=color,
		x=2,
		y=y_pos
	)
	state.main_group.append(label)

def show_clock():
	"""Show current time from RTC"""
	while len(state.main_group) > 0:
		state.main_group.pop()
	
	now = state.rtc.datetime
	hour = now.tm_hour
	minute = now.tm_min
	# Remove: second = now.tm_sec
	
	hour_12 = hour % 12
	if hour_12 == 0:
		hour_12 = 12
	ampm = "AM" if hour < 12 else "PM"
	
	time_text = f"{hour_12}:{minute:02d}"
	time_label = bitmap_label.Label(
		state.font_large,
		text=time_text,
		color=config.Colors.WHITE,
		x=5,
		y=12
	)
	state.main_group.append(time_label)
	
	ampm_label = bitmap_label.Label(
		state.font_large,
		text=ampm,
		color=config.Colors.GREEN,
		x=5,
		y=24
	)
	state.main_group.append(ampm_label)

# ============================================================================
# MAIN LOOP
# ============================================================================

def run_test_cycle():
	"""Run one display cycle - now shows weather!"""
	state.cycle_count += 1

	# Log cycle separator (v2.5 style)
	if config.Logging.SHOW_CYCLE_SEPARATOR:
		logger.log_cycle_start(state.cycle_count, config.LogLevel.INFO)

	# Reload config and schedules periodically (every 10 cycles = ~50 minutes)
	if state.cycle_count % 10 == 0:
		config_manager.load_config()

		# Reload schedules (GitHub > local)
		github_schedules, source = schedule_loader.fetch_github_schedules(state.rtc)
		if github_schedules:
			state.cached_schedules = github_schedules
			logger.log(f"Reloaded {len(github_schedules)} schedules from {source}", config.LogLevel.DEBUG, area="SCHEDULE")
		else:
			local_schedules = schedule_loader.load_local_schedules()
			if local_schedules:
				state.cached_schedules = local_schedules
				logger.log(f"Reloaded {len(local_schedules)} schedules from local file", config.LogLevel.DEBUG, area="SCHEDULE")

	# Check for active schedules (Phase 5) - takes priority over normal rotation
	if config_manager.should_show_schedules() and state.cached_schedules:
		# Log current time for debugging
		now = state.rtc.datetime
		current_time_str = f"{now.tm_hour}:{now.tm_min:02d}:{now.tm_sec:02d}"
		logger.log(f"Checking schedules at {current_time_str} (day {now.tm_wday})", config.LogLevel.DEBUG, area="SCHEDULE")

		active_schedule_name, active_schedule_config = schedule_loader.get_active_schedule(state.rtc, state.cached_schedules)

		if active_schedule_name:
			# Active schedule found - display it for remaining duration
			remaining_time = schedule_loader.get_remaining_schedule_time(state.rtc, active_schedule_config)

			if remaining_time > 0:
				logger.log(f"Active schedule: {active_schedule_name} ({remaining_time/60:.1f} min remaining)", config.LogLevel.INFO, area="SCHEDULE")

				try:
					display_schedules.show_schedule(state.rtc, active_schedule_name, active_schedule_config, remaining_time)
					logger.log("### CYCLE COMPLETE (SCHEDULE) ### \n", config.LogLevel.INFO, area="MAIN")
					return  # Skip normal display rotation
				except Exception as e:
					logger.log(f"Schedule display error: {e}", config.LogLevel.ERROR, area="SCHEDULE")
					# Fall through to normal rotation on error
		else:
			logger.log(f"No active schedule at {current_time_str}", config.LogLevel.DEBUG, area="SCHEDULE")

	# Check WiFi status
	if not hardware.is_wifi_connected():
		logger.log("WiFi disconnected!", config.LogLevel.WARNING)
		show_message("NO WIFI", config.Colors.RED)
		time.sleep(5)

		# Try to reconnect
		if hardware.reconnect_wifi():
			show_message("WIFI OK", config.Colors.GREEN)
			time.sleep(2)
		else:
			logger.log("WiFi reconnect failed - showing clock", config.LogLevel.ERROR)
			# Show clock as fallback
			try:
				show_clock()
				time.sleep(config.Timing.CLOCK_UPDATE_INTERVAL)  # Sleep to avoid tight loop
			except Exception as e:
				logger.log(f"Clock display error: {e}", config.LogLevel.ERROR)
				time.sleep(10)
		return
	
	# Fetch weather, forecast and stock data
	try:
		# Check if we need to fetch weather or forecast based on config
		need_weather = config_manager.should_show_weather()
		need_forecast = config_manager.should_show_forecast()

		# Fetch data only if needed
		weather_data = None
		forecast_data = None

		if need_weather or need_forecast:
			weather_data = weather_api.fetch_current()

		if need_forecast:
			forecast_data = weather_api.fetch_forecast()

		# Track if we showed anything
		showed_display = False

		if weather_data:
			# Display forecast first (uses current weather for column 1)
			if need_forecast and forecast_data:
				display_forecast.show(weather_data, forecast_data, config.Timing.FORECAST_DISPLAY_DURATION)
				showed_display = True
			elif need_forecast:
				logger.log("No forecast data - skipping forecast display", config.LogLevel.WARNING, area="MAIN")

			# Then display current weather
			if need_weather:
				display_weather.show(weather_data, config.Timing.WEATHER_DISPLAY_DURATION)
				showed_display = True

		# Stock display (Phase 4)
		if config_manager.should_show_stocks() and state.cached_stocks:
			# Check if we should show stocks this cycle
			freq = config_manager.get_stocks_display_frequency()
			should_show_stocks_this_cycle = (state.cycle_count % freq == 0)

			if should_show_stocks_this_cycle:
				# Check market hours status (including grace period)
				now = state.rtc.datetime
				current_minutes = now.tm_hour * 60 + now.tm_min
				current_weekday = now.tm_wday  # 0=Monday, 6=Sunday

				is_weekday = current_weekday < 5  # Monday-Friday

				# Market hours: open to close
				is_market_hours = (current_minutes >= state.market_open_local_minutes and
				                  current_minutes <= state.market_close_local_minutes)

				# Grace period: close to grace end (for fetching final close price)
				is_grace_period = (current_minutes > state.market_close_local_minutes and
				                  current_minutes <= state.market_grace_end_local_minutes)

				# Dynamic grace period extension (only when respect_market_hours = false)
				# Ensures all stocks get closing prices before switching to 24/7 cached display
				respect_hours = config_manager.get_stocks_respect_market_hours()
				if not respect_hours and current_minutes > state.market_grace_end_local_minutes and is_weekday:
					# Past normal grace period, but respect_market_hours = false (24/7 display mode)
					# Check if all stocks have been fetched during grace period
					all_stock_symbols = set([s['symbol'] for s in state.cached_stocks])
					unfetched_stocks = all_stock_symbols - state.grace_period_fetched_symbols

					if len(unfetched_stocks) > 0:
						# Still have unfetched stocks - extend grace period
						is_grace_period = True
						logger.log(f"Grace period auto-extension: {len(unfetched_stocks)} stocks remaining ({', '.join(list(unfetched_stocks)[:3])}{'...' if len(unfetched_stocks) > 3 else ''})", config.LogLevel.INFO, area="STOCKS")
					else:
						# All stocks fetched - end grace period, continue with cached data
						if state.previous_grace_period_state:
							# Log once when transitioning out
							logger.log("All stocks updated - ending grace period, using cached data", config.LogLevel.INFO, area="STOCKS")

				# Allow fetching during market hours OR grace period
				state.should_fetch_stocks = is_weekday and (is_market_hours or is_grace_period)

				# Grace period optimization: detect transition into grace period and reset tracking
				if is_grace_period and not state.previous_grace_period_state:
					# Entering grace period - clear the set of fetched symbols
					state.grace_period_fetched_symbols.clear()
					logger.log("Entering grace period - resetting symbol tracking", config.LogLevel.DEBUG, area="STOCKS")
				state.previous_grace_period_state = is_grace_period

				# Respect market hours if configured (already fetched above)
				should_display_stocks = True
				if respect_hours and not state.should_fetch_stocks:
					should_display_stocks = False
					logger.log("Outside market hours + grace - skipping stocks", config.LogLevel.DEBUG, area="STOCKS")

				if should_display_stocks:
					try:
						# Get stocks list and rotation offset
						stocks_list = state.cached_stocks
						offset = state.stock_rotation_offset

						# Check if CURRENT stock at offset is highlighted (not search for next)
						current_stock = stocks_list[offset]

						if current_stock.get('highlight') == True:
							# Single stock chart mode (highlighted)
							symbol = current_stock['symbol']

							# Check if we need to fetch (rate limiting)
							now_time = time.monotonic()
							time_since_last_fetch = now_time - state.last_stock_fetch_time

							# Fetch logic:
							# - Market hours: always fetch (respecting rate limit)
							# - Grace period: fetch ONCE per symbol, then reuse
							# - Outside hours: fetch ONCE to cache, then reuse forever
							should_fetch = False
							if symbol not in state.cached_intraday_data:
								# No cache - need to fetch regardless of market hours
								should_fetch = True
							elif state.should_fetch_stocks:
								# During market hours or grace period
								if is_grace_period:
									# Grace period - only fetch if not already fetched this grace period
									if symbol not in state.grace_period_fetched_symbols:
										should_fetch = True
								else:
									# Market hours - always fetch fresh data
									should_fetch = True
							# else: Outside market hours with cache - DO NOT fetch

							# Respect rate limiting
							if should_fetch and time_since_last_fetch >= config.Timing.STOCKS_FETCH_INTERVAL:
								logger.log(f"Fetching intraday data for {symbol}", config.LogLevel.DEBUG, area="STOCKS")
								# Fetch intraday time series (78 points = full trading day at 5min intervals)
								intraday_data = stocks_api.fetch_intraday_time_series(symbol, interval="5min", outputsize=78)
								# Fetch actual quote for accurate price and percentage
								quote_data = stocks_api.fetch_stock_quotes([symbol])

								if intraday_data and quote_data and symbol in quote_data:
									state.cached_intraday_data[symbol] = {
										'data': intraday_data,
										'quote': quote_data[symbol],
										'timestamp': now_time
									}
									state.last_stock_fetch_time = now_time

									# Track symbol as fetched during grace period (optimization)
									if is_grace_period:
										state.grace_period_fetched_symbols.add(symbol)
										logger.log(f"Added {symbol} to grace period tracking", config.LogLevel.DEBUG, area="STOCKS")

							# Get cached data and display
							if symbol in state.cached_intraday_data:
								cached = state.cached_intraday_data[symbol]
								time_series = cached['data']
								quote = cached.get('quote')

								# Build stock quote with display name (inline)
								if time_series and quote:
									stock_quote = {
										'price': quote['price'],
										'change_percent': quote['change_percent'],
										'direction': quote['direction'],
										'open_price': quote.get('open_price', 0),
										'symbol': symbol,
										'display_name': current_stock.get('display_name', symbol)
									}

									display_stocks.show_single_stock_chart(
										symbol,
										stock_quote,
										time_series,
										config.Timing.STOCKS_DISPLAY_DURATION
									)
									showed_display = True

									# Advance offset by 1 for next cycle
									state.stock_rotation_offset = (offset + 1) % len(stocks_list)
								else:
									logger.log(f"No time series data for {symbol}", config.LogLevel.WARNING, area="STOCKS")
							else:
								logger.log(f"No intraday data for {symbol}", config.LogLevel.WARNING, area="STOCKS")

						else:
							# Multi-stock mode - get next 4 non-highlighted stocks (display 3, 1 buffer)
							stocks_to_show = []
							for i in range(len(stocks_list)):
								idx = (offset + i) % len(stocks_list)
								stock = stocks_list[idx]
								if stock.get('highlight') != True:
									stocks_to_show.append(stock)
								if len(stocks_to_show) >= 4:
									break

							if stocks_to_show:
								# Check if we need to fetch (rate limiting)
								now_time = time.monotonic()
								time_since_last_fetch = now_time - state.last_stock_fetch_time

								# Get symbols to fetch (fetch 4, display 3 - buffer for failures)
								# slicing [:4] is safe even if list is shorter
								symbols_to_fetch = [s['symbol'] for s in stocks_to_show[:4]]

								# Grace period optimization: filter out already-fetched symbols during grace period
								if is_grace_period:
									symbols_to_fetch = [sym for sym in symbols_to_fetch
									                   if sym not in state.grace_period_fetched_symbols]

								# Fetch logic:
								# - Market hours: always fetch (respecting rate limit)
								# - Grace period: fetch ONCE per symbol (already filtered above), then reuse
								# - Outside hours: fetch ONCE to cache, then reuse forever
								should_fetch = False
								for sym in symbols_to_fetch:
									if sym not in state.cached_stock_prices:
										# No cache - need to fetch regardless of market hours
										should_fetch = True
										break
									elif state.should_fetch_stocks:
										# Market hours OR grace period - fetch
										# (Grace period symbols already filtered to only unfetched ones)
										should_fetch = True
										break
								# else: Outside market hours with cache - DO NOT fetch

								# Respect rate limiting
								if should_fetch and time_since_last_fetch >= config.Timing.STOCKS_FETCH_INTERVAL:
									logger.log(f"Fetching quotes for {len(symbols_to_fetch)} stocks", config.LogLevel.DEBUG, area="STOCKS")
									quotes = stocks_api.fetch_stock_quotes(symbols_to_fetch)
									if quotes:
										for sym, data in quotes.items():
											# Store quote data in cache
											state.cached_stock_prices[sym] = {
												'price': data['price'],
												'change_percent': data['change_percent'],
												'direction': data['direction'],
												'timestamp': now_time
											}
										state.last_stock_fetch_time = now_time

										# Track symbols as fetched during grace period (optimization)
										if is_grace_period:
											for sym in quotes.keys():
												state.grace_period_fetched_symbols.add(sym)
											logger.log(f"Added {len(quotes)} symbols to grace period tracking", config.LogLevel.DEBUG, area="STOCKS")

								# Attach cached prices to stocks for display
								stocks_with_prices = []
								for stock in stocks_to_show[:3]:  # Display 3
									symbol = stock['symbol']
									if symbol in state.cached_stock_prices:
										stock['price'] = state.cached_stock_prices[symbol]['price']
										stock['change_percent'] = state.cached_stock_prices[symbol]['change_percent']
										stock['direction'] = state.cached_stock_prices[symbol]['direction']
										stocks_with_prices.append(stock)

								if len(stocks_with_prices) >= 2:  # Need at least 2 to show
									display_stocks.show_multi_stock(
										stocks_with_prices,
										config.Timing.STOCKS_DISPLAY_DURATION
									)
									showed_display = True

									# Advance rotation offset by 3
									state.stock_rotation_offset = (offset + 3) % len(stocks_list)
								else:
									logger.log("Not enough stock data - skipping display", config.LogLevel.WARNING, area="STOCKS")

					except Exception as e:
						logger.log(f"Stock display error: {e}", config.LogLevel.ERROR, area="STOCKS")

		# If no displays enabled or no data, show clock as fallback
		if not showed_display:
			if not need_weather and not need_forecast:
				logger.log("All displays disabled - showing clock", config.LogLevel.INFO, area="MAIN")
			else:
				logger.log("No weather data - showing clock", config.LogLevel.WARNING)
			show_clock()
			time.sleep(config.Timing.CLOCK_UPDATE_INTERVAL)  # Sleep to avoid tight loop
			
		logger.log("### CYCLE COMPLETE ### \n", config.LogLevel.INFO, area="MAIN")

	except KeyboardInterrupt:
		raise  # Button pressed, exit
	except Exception as e:
		logger.log(f"Weather cycle error: {e}", config.LogLevel.ERROR)
		# Fall back to clock
		try:
			show_clock()
			time.sleep(config.Timing.CLOCK_UPDATE_INTERVAL)  # Sleep to avoid tight loop
		except:
			time.sleep(10)

	# Memory check using centralized logger
	if state.cycle_count % config.Timing.MEMORY_CHECK_INTERVAL == 0:
		logger.log_memory("MAIN", config.LogLevel.INFO)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize():
	"""Initialize all hardware and services"""
	logger.log("==== PANTALLITA 3.0 | PHASE 5: SCHEDULE DISPLAY ====")

	try:
		# Initialize display FIRST (before show_message)
		logger.log("Initializing display...", config.LogLevel.DEBUG)
		hardware.init_display()

		# NOW we can show messages
		show_message("INIT...", config.Colors.GREEN, 16)

		# Initialize RTC
		show_message("RTC...", config.Colors.GREEN, 16)
		hardware.init_rtc()

		# Initialize buttons
		show_message("BUTTONS", config.Colors.GREEN, 16)
		hardware.init_buttons()

		# Connect to WiFi
		show_message("WIFI...", config.Colors.GREEN, 16)
		hardware.connect_wifi()

		# Fetch location info from AccuWeather (for timezone)
		show_message("LOCATION", config.Colors.GREEN, 16)
		location_info = weather_api.fetch_location_info()

		# Sync time (with timezone from AccuWeather or fallback)
		show_message("SYNC...", config.Colors.GREEN, 16)
		if location_info:
			hardware.sync_time(state.rtc, timezone_offset=location_info['offset'])
		else:
			# Fallback to worldtimeapi.org
			logger.log("Using settings.toml timezone as fallback", config.LogLevel.WARNING, area="MAIN")
			hardware.sync_time(state.rtc)

		# Load display configuration
		show_message("CONFIG...", config.Colors.GREEN, 16)
		config_manager.load_config()

		# Load stocks configuration (Phase 4)
		if config_manager.should_show_stocks():
			show_message("STOCKS...", config.Colors.GREEN, 16)
			state.cached_stocks = stocks_api.load_stocks_csv()
			logger.log(f"Loaded {len(state.cached_stocks)} stocks from CSV", area="MAIN")

			# Calculate market hours in local timezone
			# Market hours: 9:30 AM - 4:00 PM ET
			grace_period = config_manager.get_stocks_grace_period_minutes()

			if location_info:
				# Market is always ET (UTC-5 standard time)
				tz_offset_hours = location_info['offset']
				et_offset_hours = -5  # ET standard time

				# Time difference between local and ET
				hours_diff = tz_offset_hours - et_offset_hours

				# Market times in ET
				market_open_et = 570   # 9:30 AM = 9*60 + 30
				market_close_et = 960  # 4:00 PM = 16*60

				# Convert to local time
				state.market_open_local_minutes = market_open_et + (hours_diff * 60)
				state.market_close_local_minutes = market_close_et + (hours_diff * 60)
				state.market_grace_end_local_minutes = state.market_close_local_minutes + grace_period

				logger.log(f"Market hours (local): {state.market_open_local_minutes//60}:{state.market_open_local_minutes%60:02d} - {state.market_close_local_minutes//60}:{state.market_close_local_minutes%60:02d} (grace: +{grace_period}min)", area="STOCKS")
			else:
				# Default to ET times (assume we're in ET)
				state.market_open_local_minutes = 570   # 9:30 AM
				state.market_close_local_minutes = 960  # 4:00 PM
				state.market_grace_end_local_minutes = 960 + grace_period
				logger.log("No timezone info - using ET market hours", config.LogLevel.WARNING, area="STOCKS")

		# Load schedules (Phase 5)
		show_message("SCHEDULES", config.Colors.GREEN, 16)
		# Try GitHub first (date-specific > default), then fallback to local
		github_schedules, source = schedule_loader.fetch_github_schedules(state.rtc)
		if github_schedules:
			state.cached_schedules = github_schedules
			logger.log(f"Loaded {len(github_schedules)} schedules from {source}", area="SCHEDULE")
		else:
			# Fallback to local schedules.csv
			local_schedules = schedule_loader.load_local_schedules()
			if local_schedules:
				state.cached_schedules = local_schedules
				logger.log(f"Loaded {len(local_schedules)} schedules from local file", area="SCHEDULE")
			else:
				logger.log("No schedules loaded (no GitHub or local schedules.csv)", config.LogLevel.WARNING, area="SCHEDULE")

		# Ready!
		show_message("READY!", config.Colors.GREEN, 16)
		time.sleep(2)

		logger.log("Hardware ready", area="MAIN")
		logger.log("=== Initialization complete ===")
		logger.log("Press UP button to stop test")
		logger.log("=== Starting weather display cycle === \n")

		return True

	except Exception as e:
		logger.log(f"Initialization failed: {e}", config.LogLevel.ERROR)
		traceback.print_exception(e)
		show_message("INIT ERR", config.Colors.RED, 16)
		return False
	

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
	"""Main entry point"""

	start_time = time.monotonic()

	if not initialize():
		logger.log("Cannot continue - initialization failed", config.LogLevel.ERROR)
		time.sleep(10)
		return

	try:
		gc.collect()
		state.last_memory_free = gc.mem_free()

		# Log baseline memory as percentage
		used_bytes = config.Hardware.TOTAL_MEMORY - state.last_memory_free
		used_percent = (used_bytes / config.Hardware.TOTAL_MEMORY) * 100
		used_kb = used_bytes // 1024
		logger.log(f"Baseline memory: {used_percent:.1f}% used ({used_kb}KB) \n")

		# Track actual start time for accurate uptime
		state.start_time = time.monotonic()

		while True:
			run_test_cycle()

	except KeyboardInterrupt:
		logger.log("=== Test stopped by button press ===")
		show_message("STOPPED", config.Colors.ORANGE, 16)
		time.sleep(2)

		# Final statistics
		gc.collect()
		final_memory = gc.mem_free()
		used_bytes = config.Hardware.TOTAL_MEMORY - final_memory
		used_percent = (used_bytes / config.Hardware.TOTAL_MEMORY) * 100
		used_kb = used_bytes // 1024

		logger.log(f"Final memory: {used_percent:.1f}% used ({used_kb}KB)")
		logger.log(f"Total cycles: {state.cycle_count}")
		logger.log(f"Weather fetches: {state.weather_fetch_count}")
		logger.log(f"Weather errors: {state.weather_fetch_errors}")

		# Calculate actual uptime using logger helper
		uptime_seconds = time.monotonic() - state.start_time
		logger.log(f"Uptime: {logger.format_uptime(uptime_seconds)}")

	except Exception as e:
		logger.log(f"Weather test error: {e}", config.LogLevel.ERROR)
		traceback.print_exception(e)
		show_message("ERROR!", config.Colors.RED, 16)
		time.sleep(10)

if __name__ == "__main__":
	main()
