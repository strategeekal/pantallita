"""
Pantallita 3.0 - Configuration Manager
Loads display settings from local CSV and GitHub remote config
INLINE ARCHITECTURE - no helper functions
"""

import time
import config
import state
import logger

# ============================================================================
# CONFIGURATION STATE
# ============================================================================

class ConfigState:
	"""Global configuration state"""
	# Display toggles
	display_weather = True
	display_forecast = True
	display_clock = False

	# Temperature unit (F or C)
	temperature_unit = "F"

	# Last config load time
	last_load_time = 0
	load_count = 0

	# Config source tracking
	last_source = "default"  # "default", "local", "github"


# ============================================================================
# CSV PARSING (INLINE)
# ============================================================================

def parse_csv_line(line):
	"""
	Parse a CSV line into setting and value.
	Returns (setting, value) tuple or None if invalid.
	INLINE - no helper functions.
	"""
	# Strip whitespace
	line = line.strip()

	# Skip empty lines and comments
	if not line or line.startswith('#'):
		return None

	# Skip header line
	if line.startswith('setting,'):
		return None

	# Split on comma
	parts = line.split(',', 1)  # Split on first comma only
	if len(parts) != 2:
		return None

	setting = parts[0].strip()
	value = parts[1].strip()

	return (setting, value)


def apply_setting(setting, value):
	"""
	Apply a setting value to ConfigState.
	Returns True if setting was applied, False if invalid.
	INLINE - no helper functions.
	"""
	# Boolean settings
	if setting in ['display_weather', 'display_forecast', 'display_clock']:
		# Parse boolean value
		if value.lower() in ['true', '1', 'yes', 'on']:
			bool_value = True
		elif value.lower() in ['false', '0', 'no', 'off']:
			bool_value = False
		else:
			logger.log(f"Invalid boolean value for {setting}: {value}", config.LogLevel.WARNING, area="CONFIG")
			return False

		# Apply to ConfigState
		if setting == 'display_weather':
			ConfigState.display_weather = bool_value
		elif setting == 'display_forecast':
			ConfigState.display_forecast = bool_value
		elif setting == 'display_clock':
			ConfigState.display_clock = bool_value

		return True

	# Temperature unit
	elif setting == 'temperature_unit':
		# Validate unit
		if value.upper() not in ['F', 'C']:
			logger.log(f"Invalid temperature unit: {value} (must be F or C)", config.LogLevel.WARNING, area="CONFIG")
			return False

		ConfigState.temperature_unit = value.upper()
		return True

	else:
		logger.log(f"Unknown setting: {setting}", config.LogLevel.WARNING, area="CONFIG")
		return False


# ============================================================================
# LOCAL CSV LOADING (INLINE)
# ============================================================================

def load_local_config():
	"""
	Load configuration from local config.csv file.
	Returns True if loaded successfully, False otherwise.
	INLINE - no helper functions.
	"""
	try:
		# Open config file
		with open('/config.csv', 'r') as f:
			lines = f.readlines()

		# Parse each line (inline)
		settings_applied = 0
		for line in lines:
			result = parse_csv_line(line)
			if result:
				setting, value = result
				if apply_setting(setting, value):
					settings_applied += 1

		if settings_applied > 0:
			logger.log(f"Loaded {settings_applied} settings from local config.csv", area="CONFIG")
			ConfigState.last_source = "local"
			return True
		else:
			logger.log("No valid settings found in local config.csv", config.LogLevel.WARNING, area="CONFIG")
			return False

	except OSError as e:
		logger.log(f"Local config.csv not found - using defaults", config.LogLevel.INFO, area="CONFIG")
		return False

	except Exception as e:
		logger.log(f"Error loading local config: {e}", config.LogLevel.ERROR, area="CONFIG")
		return False


# ============================================================================
# GITHUB CONFIG LOADING (INLINE)
# ============================================================================

def load_github_config():
	"""
	Load configuration from GitHub remote config.
	Returns True if loaded successfully, False otherwise.
	INLINE - no helper functions.
	"""
	# Check if GitHub URL is configured
	if not config.Env.CONFIG_GITHUB_URL:
		logger.log("No GitHub config URL configured - skipping remote config", config.LogLevel.DEBUG, area="CONFIG")
		return False

	response = None

	try:
		logger.log(f"Fetching config from GitHub...", config.LogLevel.DEBUG, area="CONFIG")

		# Fetch from GitHub
		response = state.session.get(config.Env.CONFIG_GITHUB_URL, timeout=10)

		# Check status
		if response.status_code != 200:
			logger.log(f"GitHub config fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="CONFIG")
			return False

		# Get text content
		content = response.text

		# Parse lines (inline)
		lines = content.split('\n')
		settings_applied = 0

		for line in lines:
			result = parse_csv_line(line)
			if result:
				setting, value = result
				if apply_setting(setting, value):
					settings_applied += 1

		if settings_applied > 0:
			logger.log(f"Loaded {settings_applied} settings from GitHub config", area="CONFIG")
			ConfigState.last_source = "github"
			return True
		else:
			logger.log("No valid settings found in GitHub config", config.LogLevel.WARNING, area="CONFIG")
			return False

	except Exception as e:
		logger.log(f"GitHub config fetch failed: {e}", config.LogLevel.WARNING, area="CONFIG")
		return False

	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass


# ============================================================================
# MAIN CONFIG LOADER (INLINE)
# ============================================================================

def load_config():
	"""
	Load configuration with priority: GitHub > Local > Defaults
	Call this at startup and periodically to refresh config.
	INLINE - no helper functions.
	"""
	logger.log("Loading configuration...", config.LogLevel.DEBUG, area="CONFIG")

	# Start with defaults (already set in ConfigState class)
	ConfigState.last_source = "default"

	# Try local config first (baseline)
	local_loaded = load_local_config()

	# Try GitHub config (overrides local)
	github_loaded = load_github_config()

	# Update load tracking
	ConfigState.last_load_time = time.monotonic()
	ConfigState.load_count += 1

	# Apply temperature unit to global config
	config.Env.TEMPERATURE_UNIT = ConfigState.temperature_unit

	# Log final configuration
	logger.log(f"Config loaded (source: {ConfigState.last_source})", area="CONFIG")
	logger.log(f"  Weather: {ConfigState.display_weather}, Forecast: {ConfigState.display_forecast}, Clock: {ConfigState.display_clock}", area="CONFIG")
	logger.log(f"  Temperature unit: {ConfigState.temperature_unit}", area="CONFIG")

	return True


# ============================================================================
# HELPER GETTERS (INLINE)
# ============================================================================

def should_show_weather():
	"""Check if weather display is enabled"""
	return ConfigState.display_weather

def should_show_forecast():
	"""Check if forecast display is enabled"""
	return ConfigState.display_forecast

def should_show_clock():
	"""Check if clock display is enabled"""
	return ConfigState.display_clock

def get_temperature_unit():
	"""Get current temperature unit (F or C)"""
	return ConfigState.temperature_unit
