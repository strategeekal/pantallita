"""
Pantallita 3.0 - Event Loading Module
Loads and parses event CSV files (GitHub ephemeral > local recurring)
INLINE ARCHITECTURE - all parsing inline, no helper functions
"""

import config
import state
import logger


# ============================================================================
# LOCAL EVENT LOADING (INLINE)
# ============================================================================

def load_local_events():
	"""
	Load recurring events from local events.csv file

	Returns:
		dict: {MMDD: [[top, bottom, image, color, start_hour, end_hour], ...]}

	Format: MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]
	Example: 12-25,Merry,Christmas,blank.bmp,GREEN,8,20

	INLINE - all parsing inline, no helpers
	"""
	events = {}

	try:
		with open("events.csv", "r") as f:
			content = f.read()

		return parse_event_csv_content(content, is_ephemeral=False)

	except OSError:
		logger.log("Local events.csv not found", config.LogLevel.DEBUG, area="EVENT")
		return {}

	except Exception as e:
		logger.log(f"Error loading local events.csv: {e}", config.LogLevel.ERROR, area="EVENT")
		return {}


# ============================================================================
# GITHUB EVENT LOADING (INLINE)
# ============================================================================

def fetch_github_events(rtc):
	"""
	Fetch ephemeral events from GitHub (date-specific, auto-skip past dates)
	Falls back to local ephemeral_events.csv if GitHub fails or not configured

	Args:
		rtc: Real-time clock object for getting current date

	Returns:
		dict: {MMDD: [[top, bottom, image, color, start_hour, end_hour], ...]}

	Format: YYYY-MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]
	Example: 2025-12-25,Special,Christmas,blank.bmp,GREEN

	INLINE - all fetching and parsing inline
	"""
	response = None

	# Try GitHub first (if configured)
	if config.Env.GITHUB_EVENTS_URL:
		try:
			logger.log(f"Fetching ephemeral events from GitHub...", config.LogLevel.DEBUG, area="EVENT")

			# Fetch from GitHub
			response = state.session.get(config.Env.GITHUB_EVENTS_URL, timeout=10)

			# Check status
			if response.status_code == 200:
				# Get text content
				content = response.text

				# Parse content (inline)
				events = parse_event_csv_content(content, is_ephemeral=True, rtc=rtc)

				if events:
					total_events = sum(len(event_list) for event_list in events.values())
					logger.log(f"Loaded {total_events} ephemeral events from GitHub", config.LogLevel.INFO, area="EVENT")
					return events
				else:
					logger.log("No valid events found in GitHub CSV", config.LogLevel.DEBUG, area="EVENT")

			else:
				logger.log(f"GitHub ephemeral events fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="EVENT")

		except Exception as e:
			logger.log(f"GitHub ephemeral events fetch error: {e}", config.LogLevel.WARNING, area="EVENT")

		finally:
			if response:
				response.close()

	# Fallback to local ephemeral_events.csv
	try:
		logger.log("Trying local ephemeral_events.csv...", config.LogLevel.DEBUG, area="EVENT")

		with open("ephemeral_events.csv", "r") as f:
			content = f.read()

		events = parse_event_csv_content(content, is_ephemeral=True, rtc=rtc)

		if events:
			total_events = sum(len(event_list) for event_list in events.values())
			logger.log(f"Loaded {total_events} ephemeral events from local file", config.LogLevel.INFO, area="EVENT")
			return events
		else:
			logger.log("No valid events found in local ephemeral_events.csv", config.LogLevel.DEBUG, area="EVENT")

	except OSError:
		logger.log("Local ephemeral_events.csv not found", config.LogLevel.DEBUG, area="EVENT")

	except Exception as e:
		logger.log(f"Error loading local ephemeral_events.csv: {e}", config.LogLevel.WARNING, area="EVENT")

	# No ephemeral events available
	return {}


# ============================================================================
# CSV PARSING (INLINE)
# ============================================================================

def parse_event_csv_content(csv_content, is_ephemeral=False, rtc=None):
	"""
	Parse event CSV content directly from string (no file I/O)

	Args:
		csv_content: CSV string content
		is_ephemeral: True for GitHub (YYYY-MM-DD), False for local (MM-DD)
		rtc: Real-time clock (required for ephemeral to skip past dates)

	Returns:
		dict: {MMDD: [[top, bottom, image, color, start_hour, end_hour], ...]}

	Local format: MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]
	GitHub format: YYYY-MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]

	INLINE - all parsing inline, no helpers
	"""
	events = {}

	# Get current date for ephemeral filtering (inline)
	current_date = None
	if is_ephemeral and rtc:
		now = rtc.datetime
		current_date = (now.tm_year, now.tm_mon, now.tm_mday)

	try:
		lines = csv_content.strip().split('\n')

		for line in lines:
			line = line.strip()

			# Skip empty lines and comments
			if not line or line.startswith('#'):
				continue

			# Parse line (inline)
			parts = [p.strip() for p in line.split(',')]

			if len(parts) >= 5:  # Minimum: date,top,bottom,image,color
				date_str = parts[0]
				top_line = parts[1]
				bottom_line = parts[2]
				image = parts[3]
				color = parts[4]

				# Parse optional time window (inline)
				start_hour = int(parts[5]) if len(parts) > 5 and parts[5] else 0
				end_hour = int(parts[6]) if len(parts) > 6 and parts[6] else 24

				# Validate time window (inline)
				if start_hour < 0 or start_hour > 23:
					start_hour = 0
				if end_hour < 1 or end_hour > 24:
					end_hour = 24
				if start_hour >= end_hour:
					logger.log(f"Invalid time window for event {date_str}: {start_hour}-{end_hour}", config.LogLevel.WARNING, area="EVENT")
					continue

				# Parse date and convert to MMDD key (inline)
				try:
					if is_ephemeral:
						# Parse YYYY-MM-DD format
						date_parts = date_str.split('-')
						if len(date_parts) != 3:
							logger.log(f"Invalid ephemeral date format: {date_str}", config.LogLevel.WARNING, area="EVENT")
							continue

						year = int(date_parts[0])
						month = int(date_parts[1])
						day = int(date_parts[2])

						# Skip past events (inline)
						if current_date:
							event_date = (year, month, day)
							if event_date < current_date:
								logger.log(f"Skipping past event: {date_str}", config.LogLevel.DEBUG, area="EVENT")
								continue

						# Convert to MMDD key
						mmdd_key = f"{month:02d}{day:02d}"

					else:
						# Parse MM-DD format (recurring yearly)
						date_parts = date_str.split('-')
						if len(date_parts) != 2:
							logger.log(f"Invalid local date format: {date_str}", config.LogLevel.WARNING, area="EVENT")
							continue

						month = int(date_parts[0])
						day = int(date_parts[1])

						# Convert to MMDD key
						mmdd_key = f"{month:02d}{day:02d}"

					# Validate month and day (inline)
					if month < 1 or month > 12:
						logger.log(f"Invalid month in date: {date_str}", config.LogLevel.WARNING, area="EVENT")
						continue
					if day < 1 or day > 31:
						logger.log(f"Invalid day in date: {date_str}", config.LogLevel.WARNING, area="EVENT")
						continue

					# Create event data array
					event_data = [top_line, bottom_line, image, color, start_hour, end_hour]

					# Add to events dictionary (inline)
					if mmdd_key not in events:
						events[mmdd_key] = []
					events[mmdd_key].append(event_data)

				except ValueError as e:
					logger.log(f"Error parsing date {date_str}: {e}", config.LogLevel.WARNING, area="EVENT")
					continue

		total_events = sum(len(event_list) for event_list in events.values())
		source = "GitHub" if is_ephemeral else "local"
		logger.log(f"Parsed {total_events} events from {source} CSV ({len(events)} unique dates)", config.LogLevel.DEBUG, area="EVENT")
		return events

	except Exception as e:
		logger.log(f"Error parsing event CSV: {e}", config.LogLevel.ERROR, area="EVENT")
		return {}


# ============================================================================
# EVENT MERGING (INLINE)
# ============================================================================

def merge_events(local_events, github_events):
	"""
	Merge local and GitHub events dictionaries

	Priority: Both are included (GitHub doesn't override local)
	If same date has events from both sources, both are included

	Args:
		local_events: Dict from local events.csv
		github_events: Dict from GitHub ephemeral events

	Returns:
		dict: Merged events {MMDD: [event1, event2, ...]}

	INLINE - simple dict merging
	"""
	merged = {}

	# Add all local events (inline)
	for mmdd_key, event_list in local_events.items():
		merged[mmdd_key] = event_list.copy()

	# Add GitHub events (inline)
	for mmdd_key, event_list in github_events.items():
		if mmdd_key in merged:
			# Both sources have events for this date - combine them
			merged[mmdd_key].extend(event_list)
		else:
			# Only GitHub has events for this date
			merged[mmdd_key] = event_list.copy()

	total_events = sum(len(event_list) for event_list in merged.values())
	logger.log(f"Merged events: {total_events} total events across {len(merged)} dates", config.LogLevel.INFO, area="EVENT")

	return merged


# ============================================================================
# EVENT ACTIVATION DETECTION (INLINE)
# ============================================================================

def get_active_events(rtc, all_events):
	"""
	Get events active right now (today's date + current time window)

	Args:
		rtc: Real-time clock object
		all_events: Merged events dictionary

	Returns:
		list: Active event data arrays [[top, bottom, image, color, start, end], ...]
		      Empty list if no active events

	INLINE - all filtering inline
	"""
	# Get current date and time (inline)
	now = rtc.datetime
	mmdd_key = f"{now.tm_mon:02d}{now.tm_mday:02d}"
	current_hour = now.tm_hour

	# Check if today has any events (inline)
	if mmdd_key not in all_events:
		return []

	today_events = all_events[mmdd_key]

	# Filter by time window (inline)
	active_events = []
	inactive_count = 0
	next_activation = None

	for event_data in today_events:
		# event_data = [top, bottom, image, color, start_hour, end_hour]
		start_hour = event_data[4]
		end_hour = event_data[5]

		# Check if event is currently active (inline)
		if start_hour <= current_hour < end_hour:
			active_events.append(event_data)
		else:
			inactive_count += 1
			# Track next activation time (inline)
			if current_hour < start_hour:
				if next_activation is None or start_hour < next_activation:
					next_activation = start_hour

	# Log inactive events (inline)
	if inactive_count > 0:
		if next_activation is not None:
			logger.log(f"Event inactive: {inactive_count} event(s) today, next active at {next_activation}:00", config.LogLevel.DEBUG, area="EVENT")
		else:
			logger.log(f"Event inactive: {inactive_count} event(s) today, time window passed", config.LogLevel.DEBUG, area="EVENT")

	# Log active events (inline)
	if active_events:
		logger.log(f"Active events: {len(active_events)} event(s) for today ({mmdd_key})", config.LogLevel.DEBUG, area="EVENT")

	return active_events
