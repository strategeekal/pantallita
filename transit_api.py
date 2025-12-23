"""
Pantallita 3.0 - Transit API Module
Fetches CTA train and bus arrival predictions
INLINE ARCHITECTURE - all logic inline, no helper functions
"""

import time
import config
import state
import logger


# ============================================================================
# TRANSITS.CSV LOADING (INLINE)
# ============================================================================

def load_transits_config():
	"""
	Load transit routes from transits.csv

	Returns list of route configs:
	[
		{
			'type': 'train',  # or 'bus'
			'route': 'Red',
			'label': 'RedToLoop',
			'stops': ['40900', '41380'],  # Map IDs for trains, stop IDs for buses
			'min_time': 3,
			'color': 'RED',
			'icon': 'train.bmp',
			'commute_hours': [(6, 9), (16, 19)]  # List of (start, end) tuples, empty for all day
		},
		...
	]

	INLINE - all parsing inline
	"""
	routes = []

	try:
		# Try loading from local file
		with open('/transits.csv', 'r') as f:
			lines = f.readlines()

		logger.log(f"Loaded transits.csv from local SD card", config.LogLevel.DEBUG, area="TRANSIT")

	except OSError:
		# File not found - check GitHub
		if config.Env.TRANSITS_GITHUB_URL:
			try:
				logger.log(f"Local transits.csv not found, fetching from GitHub", config.LogLevel.DEBUG, area="TRANSIT")

				response = state.session.get(config.Env.TRANSITS_GITHUB_URL, timeout=10)

				if response.status_code == 200:
					content = response.text
					lines = content.split('\n')
					logger.log(f"Loaded transits.csv from GitHub", config.LogLevel.DEBUG, area="TRANSIT")
				else:
					logger.log(f"GitHub transits.csv fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="TRANSIT")
					return []

				# Close response
				try:
					response.close()
				except:
					pass

			except Exception as e:
				logger.log(f"GitHub transits.csv fetch error: {e}", config.LogLevel.WARNING, area="TRANSIT")
				return []
		else:
			logger.log(f"No transits.csv found (local or GitHub)", config.LogLevel.WARNING, area="TRANSIT")
			return []

	except Exception as e:
		logger.log(f"Error reading transits.csv: {e}", config.LogLevel.ERROR, area="TRANSIT")
		return []

	# Parse CSV lines (inline)
	for line in lines:
		# Strip whitespace
		line = line.strip()

		# Skip empty lines and comments
		if not line or line.startswith('#'):
			continue

		# Split by comma
		parts = line.split(',')

		# Expect 8 fields: type,route,label,stops,min_time,color,icon,commute_hours
		if len(parts) != 8:
			logger.log(f"Invalid transits.csv line (expected 8 fields): {line}", config.LogLevel.WARNING, area="TRANSIT")
			continue

		# Parse fields (inline)
		transit_type = parts[0].strip().lower()
		route = parts[1].strip()
		label = parts[2].strip()
		stops_str = parts[3].strip()
		min_time_str = parts[4].strip()
		color_name = parts[5].strip()
		icon = parts[6].strip()
		commute_hours_str = parts[7].strip()

		# Validate type
		if transit_type not in ['train', 'bus']:
			logger.log(f"Invalid transit type '{transit_type}' (must be 'train' or 'bus'): {line}", config.LogLevel.WARNING, area="TRANSIT")
			continue

		# Parse stops (pipe-separated for multiple stops)
		stops = [s.strip() for s in stops_str.split('|') if s.strip()]
		if not stops:
			logger.log(f"No stops specified: {line}", config.LogLevel.WARNING, area="TRANSIT")
			continue

		# Parse min_time
		try:
			min_time = int(min_time_str)
			if min_time < 0:
				logger.log(f"Invalid min_time '{min_time_str}' (must be >= 0): {line}", config.LogLevel.WARNING, area="TRANSIT")
				continue
		except ValueError:
			logger.log(f"Invalid min_time '{min_time_str}' (must be integer): {line}", config.LogLevel.WARNING, area="TRANSIT")
			continue

		# Parse commute hours (e.g., "6-9|16-19" -> [(6, 9), (16, 19)])
		commute_hours = []
		if commute_hours_str:
			for hour_range in commute_hours_str.split('|'):
				hour_range = hour_range.strip()
				if '-' in hour_range:
					try:
						start_str, end_str = hour_range.split('-', 1)
						start_hour = int(start_str.strip())
						end_hour = int(end_str.strip())

						# Validate hours (0-23)
						if start_hour < 0 or start_hour > 23 or end_hour < 0 or end_hour > 23:
							logger.log(f"Invalid hour range '{hour_range}' (hours must be 0-23): {line}", config.LogLevel.WARNING, area="TRANSIT")
							continue

						if start_hour >= end_hour:
							logger.log(f"Invalid hour range '{hour_range}' (start must be < end): {line}", config.LogLevel.WARNING, area="TRANSIT")
							continue

						commute_hours.append((start_hour, end_hour))

					except ValueError:
						logger.log(f"Invalid hour range '{hour_range}': {line}", config.LogLevel.WARNING, area="TRANSIT")
						continue

		# Create route config
		route_config = {
			'type': transit_type,
			'route': route,
			'label': label,
			'stops': stops,
			'min_time': min_time,
			'color': color_name,
			'icon': icon,
			'commute_hours': commute_hours
		}

		routes.append(route_config)
		logger.log(f"Loaded transit route: {label} ({transit_type} {route})", config.LogLevel.DEBUG, area="TRANSIT")

	logger.log(f"Loaded {len(routes)} transit route(s) from transits.csv", config.LogLevel.INFO, area="TRANSIT")

	return routes


# ============================================================================
# COMMUTE HOURS CHECK (INLINE)
# ============================================================================

def is_within_commute_hours(commute_hours, current_hour):
	"""
	Check if current hour is within any configured commute hour range

	Args:
		commute_hours: List of (start, end) hour tuples (e.g., [(6, 9), (16, 19)])
		current_hour: Current hour (0-23)

	Returns:
		True if within any range, or if commute_hours is empty (show all day)

	INLINE - simple loop check
	"""
	# Empty commute_hours = show all day
	if not commute_hours:
		return True

	# Check each range (inline)
	for start_hour, end_hour in commute_hours:
		# Range check: start_hour <= current_hour < end_hour (end is exclusive)
		if start_hour <= current_hour < end_hour:
			return True

	return False


# ============================================================================
# CTA TRAIN TRACKER API (INLINE)
# ============================================================================

def fetch_train_arrivals(route_config):
	"""
	Fetch train arrivals from CTA Train Tracker API

	Args:
		route_config: Route configuration dict with 'route', 'stops', 'min_time'

	Returns:
		List of arrival dicts: [{'destination': str, 'minutes': int}, ...]
		Returns empty list on error

	API: http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx
	Params:
		- key: API key
		- mapid: Station map ID (can specify multiple with &mapid=xxx&mapid=yyy)
		- max: Maximum results (default 5)
		- outputType: json

	Response structure:
		{
			"ctatt": {
				"eta": [
					{
						"destNm": "Howard",
						"arrT": "2025-12-22T09:15:00",
						"isApp": "0",  # "1" if approaching (< 1 min)
						"isDly": "0",  # "1" if delayed
						...
					},
					...
				]
			}
		}

	INLINE - all API call and parsing inline
	"""
	route = route_config['route']
	stops = route_config['stops']
	min_time = route_config['min_time']

	# Check if API key is configured
	if not config.Env.CTA_API_KEY:
		logger.log("CTA_API_KEY not configured", config.LogLevel.WARNING, area="TRANSIT")
		return []

	# Build URL with comma-separated mapid parameter (v2.5 format)
	mapid_param = ",".join(stops)
	url = f"http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?key={config.Env.CTA_API_KEY}&mapid={mapid_param}&outputType=JSON"

	response = None

	try:
		logger.log(f"Fetching train arrivals for {route} line (stops: {stops})", config.LogLevel.DEBUG, area="TRANSIT")

		# Fetch from API
		response = state.session.get(url, timeout=10)

		if response.status_code != 200:
			logger.log(f"CTA Train API error: HTTP {response.status_code}", config.LogLevel.WARNING, area="TRANSIT")
			return []

		# Parse JSON
		data = response.json()

		# Check for API errors (inline)
		if 'ctatt' not in data:
			logger.log(f"CTA Train API: unexpected response format", config.LogLevel.WARNING, area="TRANSIT")
			return []

		ctatt = data['ctatt']

		# Check for error message (errCd "0" means SUCCESS, anything else is error)
		err_code = ctatt.get('errCd', '0')
		if err_code != '0':
			err_msg = ctatt.get('errNm', 'Unknown error')
			logger.log(f"CTA Train API error: [{err_code}] {err_msg} (route: {route}, stops: {stops})", config.LogLevel.WARNING, area="TRANSIT")
			return []

		# Get arrivals
		eta_list = ctatt.get('eta', [])

		if not eta_list:
			logger.log(f"No arrivals for {route} line", config.LogLevel.DEBUG, area="TRANSIT")
			return []

		# Parse arrivals (inline)
		arrivals = []

		# Get current time from CTA API response (v2.5 method)
		tmst = ctatt.get('tmst', '')

		for eta in eta_list:
			# Get route and destination
			train_route = eta.get('rt', '??')
			destination = eta.get('destNm', 'Unknown')

			# Route filtering (v2.5 logic):
			# - Red line: all trains
			# - Brown/Purple lines: only trains to Loop
			if route == 'Brn' and train_route == 'Brn' and 'Loop' not in destination:
				continue  # Skip non-Loop Brown trains
			if route == 'P' and train_route == 'P' and 'Loop' not in destination:
				continue  # Skip non-Loop Purple trains

			# Get arrival time string (ISO format: "2025-12-22T09:15:00")
			arr_time_str = eta.get('arrT', '')

			# Check if approaching (< 1 min)
			is_approaching = eta.get('isApp', '0') == '1'

			if is_approaching:
				minutes = 0
			else:
				# Calculate minutes until arrival (v2.5 method using tmst)
				try:
					# Parse times: "2025-12-22T09:15:00"
					if 'T' in arr_time_str and 'T' in tmst:
						# Get time parts only (HH:MM:SS)
						arr_time_part = arr_time_str.split('T')[1]
						cur_time_part = tmst.split('T')[1]

						# Parse hours and minutes
						arr_hms = arr_time_part.split(':')
						cur_hms = cur_time_part.split(':')

						# Convert to total minutes
						total_arr_mins = int(arr_hms[0]) * 60 + int(arr_hms[1])
						total_cur_mins = int(cur_hms[0]) * 60 + int(cur_hms[1])

						# Calculate difference
						diff_mins = total_arr_mins - total_cur_mins

						# Handle day rollover (arrival after midnight)
						if diff_mins < 0:
							diff_mins += 24 * 60

						minutes = diff_mins
					else:
						raise ValueError("Invalid time format")

				except Exception as e:
					logger.log(f"Error parsing arrival time '{arr_time_str}': {e}", config.LogLevel.WARNING, area="TRANSIT")
					# Default to "DUE" if can't parse
					minutes = 0 if is_approaching else None
					if minutes is None:
						continue

			# Filter by min_time (inline)
			if minutes < min_time:
				logger.log(f"Filtered {route} to {destination} ({minutes} min < {min_time} min threshold)", config.LogLevel.DEBUG, area="TRANSIT")
				continue

			# Add to arrivals
			arrivals.append({
				'destination': destination,
				'minutes': minutes
			})

		logger.log(f"Found {len(arrivals)} arrival(s) for {route} line", config.LogLevel.DEBUG, area="TRANSIT")

		return arrivals

	except Exception as e:
		logger.log(f"CTA Train API fetch error: {e}", config.LogLevel.WARNING, area="TRANSIT")
		return []

	finally:
		# Always close response
		if response:
			try:
				response.close()
			except:
				pass


# ============================================================================
# CTA BUS TRACKER API (INLINE)
# ============================================================================

def fetch_bus_arrivals(route_config):
	"""
	Fetch bus arrivals from CTA Bus Tracker API

	Args:
		route_config: Route configuration dict with 'route', 'stops', 'min_time'

	Returns:
		List of arrival dicts: [{'destination': str, 'minutes': int}, ...]
		Returns empty list on error

	API: http://www.ctabustracker.com/bustime/api/v2/getpredictions
	Params:
		- key: API key
		- rt: Route number (e.g., "22")
		- stpid: Stop ID (can specify multiple with &stpid=xxx&stpid=yyy)
		- format: json

	Response structure:
		{
			"bustime-response": {
				"prd": [
					{
						"des": "Howard",
						"prdctdn": "5",  # Minutes (or "DUE" if < 1 min)
						"dly": false,
						...
					},
					...
				]
			}
		}

	INLINE - all API call and parsing inline
	"""
	route = route_config['route']
	stops = route_config['stops']
	min_time = route_config['min_time']

	# Check if API key is configured
	if not config.Env.CTA_BUS_API_KEY:
		logger.log("CTA_BUS_API_KEY not configured", config.LogLevel.WARNING, area="TRANSIT")
		return []

	# Build URL with multiple stpid parameters (inline)
	url = f"http://www.ctabustracker.com/bustime/api/v2/getpredictions?key={config.Env.CTA_BUS_API_KEY}&rt={route}&format=json"

	for stop_id in stops:
		url += f"&stpid={stop_id}"

	response = None

	try:
		logger.log(f"Fetching bus arrivals for route {route} (stops: {stops})", config.LogLevel.DEBUG, area="TRANSIT")

		# Fetch from API
		response = state.session.get(url, timeout=10)

		if response.status_code != 200:
			logger.log(f"CTA Bus API error: HTTP {response.status_code}", config.LogLevel.WARNING, area="TRANSIT")
			return []

		# Parse JSON
		data = response.json()

		# Check for API response
		if 'bustime-response' not in data:
			logger.log(f"CTA Bus API: unexpected response format", config.LogLevel.WARNING, area="TRANSIT")
			return []

		bus_response = data['bustime-response']

		# Check for error
		if 'error' in bus_response:
			error_msg = bus_response['error'][0].get('msg', 'unknown') if bus_response['error'] else 'unknown'
			logger.log(f"CTA Bus API error: {error_msg} (route: {route}, stops: {stops})", config.LogLevel.WARNING, area="TRANSIT")
			return []

		# Get predictions
		prd_list = bus_response.get('prd', [])

		if not prd_list:
			logger.log(f"No arrivals for bus route {route}", config.LogLevel.DEBUG, area="TRANSIT")
			return []

		# Parse arrivals (inline)
		arrivals = []

		for prd in prd_list:
			# Get destination
			destination = prd.get('des', 'Unknown')

			# Get prediction countdown (minutes or "DUE")
			prdctdn = prd.get('prdctdn', '0')

			# Parse minutes (inline)
			if prdctdn == 'DUE':
				minutes = 0
			else:
				try:
					minutes = int(prdctdn)
				except ValueError:
					logger.log(f"Invalid prdctdn value: {prdctdn}", config.LogLevel.WARNING, area="TRANSIT")
					continue

			# Filter by min_time (inline)
			if minutes < min_time:
				logger.log(f"Filtered bus {route} to {destination} ({minutes} min < {min_time} min threshold)", config.LogLevel.DEBUG, area="TRANSIT")
				continue

			# Add to arrivals
			arrivals.append({
				'destination': destination,
				'minutes': minutes
			})

		logger.log(f"Found {len(arrivals)} arrival(s) for bus route {route}", config.LogLevel.DEBUG, area="TRANSIT")

		return arrivals

	except Exception as e:
		logger.log(f"CTA Bus API fetch error: {e}", config.LogLevel.WARNING, area="TRANSIT")
		return []

	finally:
		# Always close response
		if response:
			try:
				response.close()
			except:
				pass


# ============================================================================
# MAIN TRANSIT DATA FETCHER (INLINE)
# ============================================================================

def fetch_transit_data():
	"""
	Fetch all configured transit arrivals

	Returns list of transit display data:
	[
		{
			'label': 'RedToLoop',
			'color': 'RED',
			'icon': 'train.bmp',
			'arrivals': [
				{'destination': 'Howard', 'minutes': 5},
				{'destination': 'Howard', 'minutes': 12},
			]
		},
		...
	]

	Returns empty list if:
	- No routes configured
	- All routes filtered by commute hours
	- All API calls fail

	INLINE - all logic inline
	"""
	# Load transits configuration
	routes = load_transits_config()

	if not routes:
		logger.log("No transit routes configured", config.LogLevel.DEBUG, area="TRANSIT")
		return []

	# Get current hour for commute hours check
	current_hour = state.rtc.datetime.tm_hour

	# Check if we should respect commute hours
	import config_manager
	respect_commute_hours = config_manager.get_transit_respect_commute_hours()

	# Fetch arrivals for each route (inline)
	transit_data = []

	for route_config in routes:
		# Check commute hours (inline)
		if respect_commute_hours:
			if not is_within_commute_hours(route_config['commute_hours'], current_hour):
				logger.log(f"Route {route_config['label']} filtered by commute hours (current: {current_hour}h)", config.LogLevel.DEBUG, area="TRANSIT")
				continue

		# Fetch arrivals based on type (inline)
		if route_config['type'] == 'train':
			arrivals = fetch_train_arrivals(route_config)
		elif route_config['type'] == 'bus':
			arrivals = fetch_bus_arrivals(route_config)
		else:
			logger.log(f"Unknown transit type: {route_config['type']}", config.LogLevel.WARNING, area="TRANSIT")
			continue

		# Skip if no arrivals
		if not arrivals:
			logger.log(f"No arrivals for {route_config['label']}", config.LogLevel.DEBUG, area="TRANSIT")
			continue

		# Add to transit data
		transit_data.append({
			'label': route_config['label'],
			'color': route_config['color'],
			'icon': route_config['icon'],
			'type': route_config['type'],  # 'train' or 'bus'
			'route': route_config['route'],  # Route identifier (e.g., 'Red', '8')
			'arrivals': arrivals
		})

	logger.log(f"Fetched transit data for {len(transit_data)} route(s)", config.LogLevel.INFO, area="TRANSIT")

	return transit_data
