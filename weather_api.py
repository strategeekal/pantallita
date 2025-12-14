"""
Pantallita 3.0 - Weather API Module
Fetches current weather from AccuWeather
INLINE PARSING - no helper functions
"""

import time

import config
import state
import logger

# ============================================================================
# LOCATION INFO (INLINE - NO HELPERS)
# ============================================================================

def fetch_location_info():
	"""
	Fetch location and timezone info from AccuWeather Location API.

	Returns dict with:
		- name: str (timezone name, e.g., "America/Chicago")
		- offset: int (UTC offset in hours, e.g., -6)
		- is_dst: bool (daylight saving time active)
		- city: str (city name, e.g., "Sheffield And Depaul")
		- state: str (state code, e.g., "IL")
		- location: str (formatted location, e.g., "Sheffield And Depaul, IL")

	Returns None if fetch fails.

	CRITICAL: All parsing is INLINE to minimize stack depth.
	"""

	# Validate configuration
	if not config.Env.ACCUWEATHER_KEY:
		logger.log("No AccuWeather API key configured", config.LogLevel.ERROR, area="WEATHER")
		return None

	if not config.Env.ACCUWEATHER_LOCATION:
		logger.log("No AccuWeather location key configured", config.LogLevel.ERROR, area="WEATHER")
		return None

	# Build URL (inline - no function)
	url = f"http://dataservice.accuweather.com/locations/v1/{config.Env.ACCUWEATHER_LOCATION}?apikey={config.Env.ACCUWEATHER_KEY}"

	response = None

	try:
		logger.log("Fetching location info from AccuWeather...", config.LogLevel.DEBUG, area="WEATHER")

		# Fetch from API
		response = state.session.get(url, timeout=10)

		# Check status
		if response.status_code != 200:
			logger.log(f"Location API error: HTTP {response.status_code}", config.LogLevel.WARNING, area="WEATHER")
			return None

		# Parse JSON (inline - no helper function)
		data = response.json()

		# Extract timezone info
		timezone_info = data.get("TimeZone", {})

		# Extract location details
		city = data.get("LocalizedName", "Unknown")
		state_code = data.get("AdministrativeArea", {}).get("ID", "")

		# Build location string
		if state_code:
			location_str = f"{city}, {state_code}"
		else:
			location_str = city

		# Build result dict (inline)
		location_data = {
			"name": timezone_info.get("Name", config.Env.TIMEZONE),
			"offset": int(timezone_info.get("GmtOffset", -6)),
			"is_dst": timezone_info.get("IsDaylightSaving", False),
			"city": city,
			"state": state_code,
			"location": location_str
		}

		logger.log(f"Location: {location_data['location']} | Timezone: {location_data['name']} (UTC{location_data['offset']:+d})", area="WEATHER")

		return location_data

	except Exception as e:
		logger.log(f"Location fetch failed: {e}", config.LogLevel.WARNING, area="WEATHER")
		return None

	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass

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
		# Use human-readable cache age
		cache_age_str = logger.format_cache_age(cache_age)
		logger.log(f"Using cached weather ({cache_age_str} old)", area="WEATHER")
		return state.last_weather_data

	# Validate configuration
	if not config.Env.ACCUWEATHER_KEY:
		logger.log("No AccuWeather API key configured", config.LogLevel.ERROR, area="WEATHER")
		return state.last_weather_data  # Return cache if available

	if not config.Env.ACCUWEATHER_LOCATION:
		logger.log("No AccuWeather location configured", config.LogLevel.ERROR, area="WEATHER")
		return state.last_weather_data
	
	# Build URL (inline - no function)
	url = (config.API.ACCUWEATHER_BASE + 
		   config.API.ACCUWEATHER_CURRENT.format(location=config.Env.ACCUWEATHER_LOCATION) +
		   f"&apikey={config.Env.ACCUWEATHER_KEY}")
	
	response = None

	try:
		logger.log(f"Fetching weather from AccuWeather...", area="WEATHER")

		# Fetch from API
		response = state.session.get(url, timeout=10)

		# Check status
		if response.status_code != 200:
			logger.log(f"API error: HTTP {response.status_code}", config.LogLevel.ERROR, area="WEATHER")
			state.weather_fetch_errors += 1
			return state.last_weather_data

		# Parse JSON (inline - no helper function)
		data = response.json()

		# AccuWeather returns a list with one item
		if not data or len(data) == 0:
			logger.log("API returned empty data", config.LogLevel.ERROR, area="WEATHER")
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
			logger.log("Missing temperature data", config.LogLevel.ERROR, area="WEATHER")
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
		logger.log(f"Weather: {weather_data['temp']}{unit_symbol}, {weather_data['condition']}, UV:{weather_data['uv']}", area="WEATHER")
		logger.log(f"Fetch #{state.weather_fetch_count}, Errors: {state.weather_fetch_errors}", area="WEATHER")

		return weather_data

	except Exception as e:
		logger.log(f"Weather fetch failed: {e}", config.LogLevel.ERROR, area="WEATHER")
		state.weather_fetch_errors += 1

		# Return cached data if available
		if state.last_weather_data:
			cache_age = time.monotonic() - state.last_weather_time
			cache_age_str = logger.format_cache_age(cache_age)
			logger.log(f"Using stale cache ({cache_age_str} old)", config.LogLevel.WARNING, area="WEATHER")
			return state.last_weather_data

		return None

	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass

# ============================================================================
# FORECAST FETCHING (INLINE - NO HELPERS)
# ============================================================================

def fetch_forecast():
	"""
	Fetch 12-hour forecast from AccuWeather API.

	Returns list of 12 dicts, each with:
		- temp: int (temperature in user's unit)
		- feels_like: int (feels like temp in user's unit)
		- feels_shade: int (feels like in shade in user's unit)
		- icon: int (AccuWeather icon number 1-44)
		- condition: str (weather text)
		- datetime: str (ISO format timestamp)
		- has_precipitation: bool (True if rain/snow expected)

	Returns None if fetch fails.

	CRITICAL: All parsing is INLINE to minimize stack depth.
	"""

	# Check if cache is still fresh
	cache_age = time.monotonic() - state.last_forecast_time
	if state.last_forecast_data and cache_age < config.Timing.FORECAST_CACHE_MAX_AGE:
		# Use human-readable cache age
		cache_age_str = logger.format_cache_age(cache_age)
		logger.log(f"Using cached forecast ({cache_age_str} old)", area="WEATHER")
		return state.last_forecast_data

	# Validate configuration
	if not config.Env.ACCUWEATHER_KEY:
		logger.log("No AccuWeather API key configured", config.LogLevel.ERROR, area="WEATHER")
		return state.last_forecast_data  # Return cache if available

	if not config.Env.ACCUWEATHER_LOCATION:
		logger.log("No AccuWeather location configured", config.LogLevel.ERROR, area="WEATHER")
		return state.last_forecast_data

	# Determine metric parameter based on temperature unit
	metric_param = "true" if config.Env.TEMPERATURE_UNIT == "C" else "false"

	# Build URL (inline - no function)
	url = (config.API.ACCUWEATHER_BASE +
		   config.API.ACCUWEATHER_FORECAST.format(location=config.Env.ACCUWEATHER_LOCATION) +
		   f"&metric={metric_param}&apikey={config.Env.ACCUWEATHER_KEY}")

	response = None

	try:
		logger.log(f"Fetching 12-hour forecast from AccuWeather...", area="WEATHER")

		# Fetch from API
		response = state.session.get(url, timeout=10)

		# Check status
		if response.status_code != 200:
			logger.log(f"Forecast API error: HTTP {response.status_code}", config.LogLevel.ERROR, area="WEATHER")
			state.forecast_fetch_errors += 1
			return state.last_forecast_data

		# Parse JSON (inline - no helper function)
		data = response.json()

		# AccuWeather returns a list of hourly forecasts
		if not data or len(data) < 12:
			logger.log(f"Insufficient forecast data (got {len(data) if data else 0}/12 hours)", config.LogLevel.ERROR, area="WEATHER")
			state.forecast_fetch_errors += 1
			return state.last_forecast_data

		# Build forecast list (inline - process all 12 hours)
		forecast_list = []

		for hour_data in data[:12]:  # Take first 12 hours
			# Extract temperature data (inline)
			temp = hour_data.get("Temperature", {}).get("Value", 0)
			feels_like = hour_data.get("RealFeelTemperature", {}).get("Value")
			feels_shade = hour_data.get("RealFeelTemperatureShade", {}).get("Value")

			# Fallbacks (inline)
			if feels_like is None:
				feels_like = temp
			if feels_shade is None:
				feels_shade = feels_like

			# Build hour dict (inline)
			hour_dict = {
				"temp": int(temp),
				"feels_like": int(feels_like),
				"feels_shade": int(feels_shade),
				"icon": hour_data.get("WeatherIcon", 1),
				"condition": hour_data.get("IconPhrase", "Unknown"),
				"datetime": hour_data.get("DateTime", ""),
				"has_precipitation": hour_data.get("HasPrecipitation", False)
			}

			forecast_list.append(hour_dict)

		# Update cache
		state.last_forecast_data = forecast_list
		state.last_forecast_time = time.monotonic()
		state.forecast_fetch_count += 1

		# Use correct temperature unit symbol
		unit_symbol = "°C" if config.Env.TEMPERATURE_UNIT == "C" else "°F"
		logger.log(f"Forecast: 12 hours fetched, next hour: {forecast_list[0]['feels_like']}{unit_symbol} {forecast_list[0]['condition']}", area="WEATHER")
		logger.log(f"Forecast fetch #{state.forecast_fetch_count}, Errors: {state.forecast_fetch_errors}", area="WEATHER")

		return forecast_list

	except Exception as e:
		logger.log(f"Forecast fetch failed: {e}", config.LogLevel.ERROR, area="WEATHER")
		state.forecast_fetch_errors += 1

		# Return cached data if available
		if state.last_forecast_data:
			cache_age = time.monotonic() - state.last_forecast_time
			cache_age_str = logger.format_cache_age(cache_age)
			logger.log(f"Using stale forecast cache ({cache_age_str} old)", config.LogLevel.WARNING, area="WEATHER")
			return state.last_forecast_data

		return None

	finally:
		# Always close response to prevent socket leak
		if response:
			try:
				response.close()
			except:
				pass
