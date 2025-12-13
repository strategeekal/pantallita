"""
Pantallita 3.0 - Weather API Module
Fetches current weather from AccuWeather
INLINE PARSING - no helper functions
"""

import time

import config
import state

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level=config.LogLevel.INFO):
	"""Simple logging"""
	if level <= config.CURRENT_LOG_LEVEL:
		level_name = ["", "ERROR", "WARN", "INFO", "DEBUG", "VERBOSE"][level]
		print(f"[WEATHER:{level_name}] {message}")

# ============================================================================
# WEATHER FETCHING (INLINE - NO HELPERS)
# ============================================================================

def fetch_current():
	"""
	Fetch current weather from AccuWeather API.
	
	Returns dict with:
		- temp: int (temperature in F)
		- feels_like: int (feels like temp in F)
		- uv: int (UV index 0-11)
		- humidity: int (humidity 0-100)
		- icon: int (AccuWeather icon number 1-44)
		- condition: str (weather text)
	
	Returns None if fetch fails.
	
	CRITICAL: All parsing is INLINE to minimize stack depth.
	"""
	
	# Check if cache is still fresh
	cache_age = time.monotonic() - state.last_weather_time
	if state.last_weather_data and cache_age < config.Timing.WEATHER_CACHE_MAX_AGE:
		log(f"Using cached weather (age: {int(cache_age)}s)")
		return state.last_weather_data
	
	# Validate configuration
	if not config.Env.ACCUWEATHER_KEY:
		log("No AccuWeather API key configured", config.LogLevel.ERROR)
		return state.last_weather_data  # Return cache if available
	
	if not config.Env.ACCUWEATHER_LOCATION:
		log("No AccuWeather location configured", config.LogLevel.ERROR)
		return state.last_weather_data
	
	# Build URL (inline - no function)
	url = (config.API.ACCUWEATHER_BASE + 
		   config.API.ACCUWEATHER_CURRENT.format(location=config.Env.ACCUWEATHER_LOCATION) +
		   f"&apikey={config.Env.ACCUWEATHER_KEY}")
	
	response = None
	
	try:
		log(f"Fetching weather from AccuWeather...")
		
		# Fetch from API
		response = state.session.get(url, timeout=10)
		
		# Check status
		if response.status_code != 200:
			log(f"API error: HTTP {response.status_code}", config.LogLevel.ERROR)
			state.weather_fetch_errors += 1
			return state.last_weather_data
		
		# Parse JSON (inline - no helper function)
		data = response.json()
		
		# AccuWeather returns a list with one item
		if not data or len(data) == 0:
			log("API returned empty data", config.LogLevel.ERROR)
			state.weather_fetch_errors += 1
			return state.last_weather_data
		
		weather = data[0]  # Get first item
		
		# Extract data (inline - no parsing function)
		# Determine which unit to fetch
		if config.Env.TEMPERATURE_UNIT == "C":
			temp_unit = "Metric"
		else:
			temp_unit = "Imperial"
		
		# Temperature (fetch in desired unit directly)
		temp = weather.get("Temperature", {}).get(temp_unit, {}).get("Value")
		if temp is None:
			log("Missing temperature data", config.LogLevel.ERROR)
			state.weather_fetch_errors += 1
			return state.last_weather_data
		
		# RealFeel (feels like)
		feels_like = weather.get("RealFeelTemperature", {}).get(temp_unit, {}).get("Value")
		if feels_like is None:
			feels_like = temp  # Fallback to actual temp
		
		# RealFeel Shade (feels like in shade)
		feels_shade = weather.get("RealFeelTemperatureShade", {}).get(temp_unit, {}).get("Value")
		if feels_shade is None:
			feels_shade = feels_like  # Fallback to feels like
		
		# Convert to int (already in correct unit, no conversion needed!)
		temp = int(temp)
		feels_like = int(feels_like)
		feels_shade = int(feels_shade)
		
		# UV Index
		uv_index = weather.get("UVIndex", 0)
		
		# Humidity
		humidity = weather.get("RelativeHumidity", 0)
		
		# Weather icon (1-44)
		icon = weather.get("WeatherIcon", 1)
		
		# Weather text
		condition = weather.get("WeatherText", "Unknown")
		
		# Build result dict (inline)
		weather_data = {
			"temp": int(temp),
			"feels_like": int(feels_like),
			"feels_shade": int(feels_shade),
			"uv": int(uv_index),
			"humidity": int(humidity),
			"icon": int(icon),
			"condition": str(condition)
		}
		
		# Update cache
		state.last_weather_data = weather_data
		state.last_weather_time = time.monotonic()
		state.weather_fetch_count += 1

		# Use correct temperature unit symbol
		unit_symbol = "°C" if config.Env.TEMPERATURE_UNIT == "C" else "°F"
		log(f"Weather: {weather_data['temp']}{unit_symbol}, {weather_data['condition']}, UV:{weather_data['uv']}")
		log(f"Fetch #{state.weather_fetch_count}, Errors: {state.weather_fetch_errors}")

		return weather_data
		
	except Exception as e:
		log(f"Weather fetch failed: {e}", config.LogLevel.ERROR)
		state.weather_fetch_errors += 1
		
		# Return cached data if available
		if state.last_weather_data:
			cache_age = time.monotonic() - state.last_weather_time
			log(f"Using stale cache (age: {int(cache_age)}s)", config.LogLevel.WARNING)
			return state.last_weather_data
		
		return None
		
	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass
