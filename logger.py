"""
Pantallita 3.0 - Centralized Logging Module
Simple inline logging with configurable features
"""

import config
import state

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def log(message, level=config.LogLevel.INFO, area="MAIN"):
	"""
	Centralized logging function.

	CRITICAL: All logic is INLINE to avoid stack depth issues.
	Early return when log level too low = zero overhead.

	Args:
		message: Log message string
		level: Log level (ERROR, WARNING, INFO, DEBUG, VERBOSE)
		area: Module area (MAIN, HW, WEATHER, DISPLAY, etc.)
	"""

	# Early exit if not logging this level (no overhead)
	if level > config.CURRENT_LOG_LEVEL:
		return

	# Build log message inline (no helper functions)
	level_names = ["PROD", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE"]
	level_str = level_names[level] if level < len(level_names) else "???"

	# Optional timestamp (inline)
	timestamp = ""
	if config.Logging.USE_TIMESTAMPS and state.rtc:
		try:
			now = state.rtc.datetime
			timestamp = f"[{now.tm_mon:02d}-{now.tm_mday:02d} {now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}] "
		except:
			pass  # RTC not ready, skip timestamp

	# Print inline
	print(f"{timestamp}[{area}:{level_str}] {message}")


def log_memory(area="MAIN", level=config.LogLevel.INFO):
	"""
	Log memory usage as percentage.

	INLINE implementation - called from main loop every N cycles.
	Shows: Memory: 3.8% used (76KB) [+512]
	"""

	# Early exit if not logging this level
	if level > config.CURRENT_LOG_LEVEL:
		return

	try:
		import gc

		# Get current memory
		free_before = state.last_memory_free
		gc.collect()
		free_after = gc.mem_free()
		state.last_memory_free = free_after

		# Calculate percentage used (inline)
		used_bytes = config.Hardware.TOTAL_MEMORY - free_after
		used_percent = (used_bytes / config.Hardware.TOTAL_MEMORY) * 100
		used_kb = used_bytes // 1024

		# Calculate delta (inline)
		if free_before > 0:
			delta = free_after - free_before
			delta_sign = "+" if delta >= 0 else ""
			log(f"Memory: {used_percent:.1f}% used ({used_kb}KB) [{delta_sign}{delta}]", level, area)
		else:
			log(f"Memory: {used_percent:.1f}% used ({used_kb}KB)", level, area)

	except Exception as e:
		log(f"Memory check failed: {e}", config.LogLevel.ERROR, area)


def format_cache_age(cache_age_seconds):
	"""
	Format cache age in human-readable form.

	INLINE helper for weather/API cache logging.
	Returns: "2m", "15m", "1h 5m"

	Args:
		cache_age_seconds: Age in seconds

	Returns:
		String like "2m" or "1h 5m"
	"""

	if cache_age_seconds < 60:
		return f"{int(cache_age_seconds)}s"

	minutes = int(cache_age_seconds / 60)

	if minutes < 60:
		return f"{minutes}m"

	hours = minutes // 60
	remaining_minutes = minutes % 60

	if remaining_minutes > 0:
		return f"{hours}h {remaining_minutes}m"
	else:
		return f"{hours}h"


def format_uptime(uptime_seconds):
	"""
	Format uptime in human-readable form.

	INLINE helper for final statistics.
	Returns: "2.5 hours (150.0 minutes)"

	Args:
		uptime_seconds: Uptime in seconds

	Returns:
		String like "2.5 hours (150.0 minutes)"
	"""

	uptime_hours = uptime_seconds / 3600
	uptime_minutes = uptime_seconds / 60

	return f"{uptime_hours:.1f} hours ({uptime_minutes:.1f} minutes)"


# ============================================================================
# CYCLE SEPARATOR (for v2.5-style logs)
# ============================================================================

def log_cycle_start(cycle_number, level=config.LogLevel.INFO, area="MAIN"):
	"""Log start of a new cycle with separator"""
	if level > config.CURRENT_LOG_LEVEL:
		return

	log(f"## CYCLE {cycle_number} ##", level, area)
