"""
Pantallita 3.0 - Phase 2: Forecast Display
Tests CircuitPython 10 foundation before implementing features (v3.0.0)
Phase 1: Current weather display (v3.0.1)
Phase 2: 12-hour forecast with smart precipitation detection (v3.0.2)

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
			except Exception as e:
				logger.log(f"Clock display error: {e}", config.LogLevel.ERROR)
				time.sleep(10)
		return
	
	# Fetch weather and forecast data
	try:
		weather_data = weather_api.fetch_current()
		forecast_data = weather_api.fetch_forecast()

		if weather_data:
			# Display forecast first (uses current weather for column 1)
			if forecast_data:
				display_forecast.show(weather_data, forecast_data, config.Timing.FORECAST_DISPLAY_DURATION)
			else:
				logger.log("No forecast data - skipping forecast display", config.LogLevel.WARNING, area="MAIN")

			# Then display current weather
			display_weather.show(weather_data, config.Timing.WEATHER_DISPLAY_DURATION)
		else:
			logger.log("No weather data - showing clock", config.LogLevel.WARNING)
			show_clock()

	except KeyboardInterrupt:
		raise  # Button pressed, exit
	except Exception as e:
		logger.log(f"Weather cycle error: {e}", config.LogLevel.ERROR)
		# Fall back to clock
		try:
			show_clock()
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
	logger.log("==== PANTALLITA 3.0 | PHASE 1.5: WEATHER DISPLAY ====")

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
		logger.log("=== Weather test stopped by button press ===")
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
