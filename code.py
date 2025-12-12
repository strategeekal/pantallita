"""
Pantallita 3.0 - Bootstrap Test
Tests CircuitPython 10 foundation before implementing features
"""

import time
import gc
import traceback
import supervisor
from adafruit_display_text import bitmap_label

import config
import state
import hardware

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level=config.LogLevel.INFO):
	"""Simple logging"""
	if level <= config.CURRENT_LOG_LEVEL:
		level_name = ["", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE"][level]
		print(f"[MAIN:{level_name}] {message}")

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
	"""Run one bootstrap test cycle"""
	state.cycle_count += 1

	log(f"=== Cycle {state.cycle_count} ===", config.LogLevel.DEBUG)

	if not hardware.is_wifi_connected():
		log("WiFi disconnected!", config.LogLevel.WARNING)
		show_message("NO WIFI", config.Colors.RED)
		time.sleep(5)

		if hardware.reconnect_wifi():
			show_message("WIFI OK", config.Colors.GREEN)
			time.sleep(2)
		else:
			log("WiFi reconnect failed - continuing without network", config.LogLevel.ERROR)
		return

	show_clock()

	sleep_time = config.Timing.CLOCK_UPDATE_INTERVAL
	end_time = time.monotonic() + sleep_time

	while time.monotonic() < end_time:
		if hardware.button_up_pressed():
			log("UP button pressed - exiting", config.LogLevel.INFO)
			raise KeyboardInterrupt
		time.sleep(0.1)

	if state.cycle_count % config.Timing.MEMORY_CHECK_INTERVAL == 0:
		free_before = state.last_memory_free
		gc.collect()
		free_after = gc.mem_free()
		state.last_memory_free = free_after

		if free_before > 0:
			delta = free_after - free_before
			delta_sign = "+" if delta >= 0 else ""
			log(f"Memory: {free_after} bytes free ({delta_sign}{delta})", config.LogLevel.INFO)
		else:
			log(f"Memory: {free_after} bytes free", config.LogLevel.INFO)

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize():
	"""Initialize all hardware and services"""
	log("=== Pantallita 3.0 Bootstrap Test ===")
	
	try:
		# Initialize display FIRST (before show_message)
		log("Initializing display...")
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
	
		# Sync time
		show_message("SYNC...", config.Colors.GREEN, 16)
		hardware.sync_time(state.rtc)
	
		# Ready!
		show_message("READY!", config.Colors.GREEN, 16)
		time.sleep(2)
	
		log("=== Initialization complete ===")
		log("Press UP button to stop test")
		log("Running bootstrap test - target: 1 hour")
	
		return True
	
	except Exception as e:
		log(f"Initialization failed: {e}", config.LogLevel.ERROR)
		traceback.print_exception(e)
		show_message("INIT ERR", config.Colors.RED, 16)
		return False
	

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
	"""Main entry point"""

	if not initialize():
		log("Cannot continue - initialization failed", config.LogLevel.ERROR)
		time.sleep(10)
		return

	try:
		gc.collect()
		state.last_memory_free = gc.mem_free()
		log(f"Baseline memory: {state.last_memory_free} bytes free")

		while True:
			run_test_cycle()

	except KeyboardInterrupt:
		log("=== Bootstrap test stopped by button press ===")
		show_message("STOPPED", config.Colors.ORANGE, 16)
		time.sleep(2)

		gc.collect()
		final_memory = gc.mem_free()
		log(f"Final memory: {final_memory} bytes free")
		log(f"Total cycles: {state.cycle_count}")

		uptime_minutes = state.cycle_count * config.Timing.CLOCK_UPDATE_INTERVAL / 60
		log(f"Uptime: {uptime_minutes:.1f} minutes")

	except Exception as e:
		log(f"Bootstrap test error: {e}", config.LogLevel.ERROR)
		traceback.print_exception(e)
		show_message("ERROR!", config.Colors.RED, 16)
		time.sleep(10)

if __name__ == "__main__":
	main()
