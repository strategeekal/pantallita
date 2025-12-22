"""
Pantallita 3.0 - Schedule Loading Module
Loads and parses schedule CSV files (GitHub date-specific > default > local)
INLINE ARCHITECTURE - all parsing inline, no helper functions
"""

import config
import state
import logger


# ============================================================================
# LOCAL SCHEDULE LOADING (INLINE)
# ============================================================================

def load_local_schedules():
	"""
	Load schedules from local schedules.csv file

	Returns:
		dict: {schedule_name: {enabled, days, start_hour, start_min, end_hour, end_min, image, progressbar}}

	INLINE - all parsing inline, no helpers
	"""
	schedules = {}

	try:
		with open("schedules.csv", "r") as f:
			content = f.read()

		return parse_schedule_csv_content(content)

	except OSError:
		logger.log("Local schedules.csv not found", config.LogLevel.DEBUG, area="SCHEDULE")
		return {}

	except Exception as e:
		logger.log(f"Error loading local schedules.csv: {e}", config.LogLevel.ERROR, area="SCHEDULE")
		return {}


# ============================================================================
# GITHUB SCHEDULE LOADING (INLINE)
# ============================================================================

def fetch_github_schedules(rtc):
	"""
	Fetch schedules from GitHub (date-specific > default > none)

	Priority:
	1. Date-specific CSV (schedules/YYYY-MM-DD.csv)
	2. Default CSV (schedules/default.csv)
	3. None (returns empty dict)

	Args:
		rtc: Real-time clock object for getting current date

	Returns:
		tuple: (schedules_dict, source_description)

	INLINE - all fetching and parsing inline
	"""
	if not config.Env.SCHEDULES_GITHUB_URL:
		logger.log("SCHEDULES_GITHUB_URL not configured", config.LogLevel.DEBUG, area="SCHEDULE")
		return {}, None

	# Get current date (YYYY-MM-DD format)
	now = rtc.datetime
	date_str = f"{now.tm_year:04d}-{now.tm_mon:02d}-{now.tm_mday:02d}"

	# Extract base URL (remove trailing filename if present)
	github_base = config.Env.SCHEDULES_GITHUB_URL
	if github_base.endswith('.csv'):
		github_base = '/'.join(github_base.split('/')[:-1])

	response = None
	schedules = {}
	source = None

	try:
		# Try date-specific CSV first
		date_url = f"{github_base}/{date_str}.csv"
		logger.log(f"Fetching date-specific schedules: {date_str}.csv", config.LogLevel.DEBUG, area="SCHEDULE")

		response = state.session.get(date_url, timeout=10)

		if response.status_code == 200:
			# Success - parse date-specific CSV
			content = response.text
			schedules = parse_schedule_csv_content(content)
			source = f"github:{date_str}.csv"
			logger.log(f"Loaded {len(schedules)} schedules from {date_str}.csv", config.LogLevel.INFO, area="SCHEDULE")

		elif response.status_code == 404:
			# Date-specific not found - try default
			logger.log(f"No date-specific schedule ({date_str}.csv), trying default", config.LogLevel.DEBUG, area="SCHEDULE")
			response.close()

			default_url = f"{github_base}/default.csv"
			response = state.session.get(default_url, timeout=10)

			if response.status_code == 200:
				# Success - parse default CSV
				content = response.text
				schedules = parse_schedule_csv_content(content)
				source = "github:default.csv"
				logger.log(f"Loaded {len(schedules)} schedules from default.csv", config.LogLevel.INFO, area="SCHEDULE")
			else:
				logger.log(f"GitHub default schedule fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="SCHEDULE")

		else:
			logger.log(f"GitHub schedule fetch failed: HTTP {response.status_code}", config.LogLevel.WARNING, area="SCHEDULE")

	except Exception as e:
		logger.log(f"GitHub schedule fetch error: {e}", config.LogLevel.ERROR, area="SCHEDULE")

	finally:
		if response:
			response.close()

	return schedules, source


# ============================================================================
# CSV PARSING (INLINE)
# ============================================================================

def parse_schedule_csv_content(csv_content):
	"""
	Parse schedule CSV content directly from string (no file I/O)

	Format: name,enabled,days,start_hour,start_min,end_hour,end_min,image,progressbar,night_mode
	Example: Get Dressed,1,0123456,7,0,7,15,get_dressed.bmp,1,0

	Args:
		csv_content: CSV string content

	Returns:
		dict: {schedule_name: {enabled, days, start_hour, start_min, end_hour, end_min, image, progressbar, night_mode}}

	INLINE - all parsing inline, no helpers
	"""
	schedules = {}

	try:
		lines = csv_content.strip().split('\n')

		for line in lines:
			line = line.strip()

			# Skip empty lines and comments
			if not line or line.startswith('#'):
				continue

			# Parse line (inline)
			parts = [p.strip() for p in line.split(',')]

			if len(parts) >= 8:
				name = parts[0]

				# Parse days string into list of integers (inline)
				days = [int(d) for d in parts[2] if d.isdigit()]

				# Parse night_mode as integer (0=normal, 1=temp only, 2=clock only)
				night_mode = 0  # default to normal
				if len(parts) > 9:
					try:
						night_mode = int(parts[9])
						# Clamp to valid range 0-2
						if night_mode < 0 or night_mode > 2:
							night_mode = 0
					except ValueError:
						night_mode = 0

				schedule = {
					"enabled": parts[1] == "1",
					"days": days,
					"start_hour": int(parts[3]),
					"start_min": int(parts[4]),
					"end_hour": int(parts[5]),
					"end_min": int(parts[6]),
					"image": parts[7],
					"progressbar": parts[8] == "1" if len(parts) > 8 else True,
					"night_mode": night_mode
				}

				schedules[name] = schedule

		logger.log(f"Parsed {len(schedules)} schedules from CSV", config.LogLevel.DEBUG, area="SCHEDULE")
		return schedules

	except Exception as e:
		logger.log(f"Error parsing schedule CSV: {e}", config.LogLevel.ERROR, area="SCHEDULE")
		return {}


# ============================================================================
# SCHEDULE ACTIVATION DETECTION (INLINE)
# ============================================================================

def is_schedule_active(rtc, schedule_name, schedule_config):
	"""
	Check if a schedule is currently active based on time and day

	Args:
		rtc: Real-time clock object
		schedule_name: Name of schedule
		schedule_config: Schedule configuration dict

	Returns:
		bool: True if schedule is active, False otherwise

	INLINE - all time comparison inline
	"""
	if not schedule_config["enabled"]:
		return False

	current = rtc.datetime

	# Check if current day is in schedule
	if current.tm_wday not in schedule_config["days"]:
		return False

	# Convert times to minutes for easier comparison (inline)
	current_mins = current.tm_hour * 60 + current.tm_min
	start_mins = schedule_config["start_hour"] * 60 + schedule_config["start_min"]
	end_mins = schedule_config["end_hour"] * 60 + schedule_config["end_min"]

	# Handle midnight crossover (e.g., 22:30-00:00)
	# If end_mins < start_mins, schedule spans midnight
	if end_mins <= start_mins:
		# Treat end_mins as next day (add 24 hours)
		# Schedule is active if: current >= start OR current < end
		return current_mins >= start_mins or current_mins < end_mins
	else:
		# Normal case: schedule doesn't cross midnight
		return start_mins <= current_mins < end_mins


def get_active_schedule(rtc, schedules):
	"""
	Check if any schedule is currently active

	Args:
		rtc: Real-time clock object
		schedules: Dict of schedules {name: config}

	Returns:
		tuple: (schedule_name, schedule_config) or (None, None)

	INLINE - iterates and checks inline
	"""
	for schedule_name, schedule_config in schedules.items():
		if is_schedule_active(rtc, schedule_name, schedule_config):
			return schedule_name, schedule_config

	return None, None


def get_remaining_schedule_time(rtc, schedule_config):
	"""
	Calculate remaining time for active schedule (in seconds)

	Args:
		rtc: Real-time clock object
		schedule_config: Schedule configuration dict

	Returns:
		int: Remaining seconds, or 0 if schedule not active

	INLINE - time calculation inline
	"""
	current = rtc.datetime
	current_mins = current.tm_hour * 60 + current.tm_min
	start_mins = schedule_config["start_hour"] * 60 + schedule_config["start_min"]
	end_mins = schedule_config["end_hour"] * 60 + schedule_config["end_min"]

	# Handle midnight crossover (e.g., 22:30-00:00)
	if end_mins <= start_mins:
		# Schedule spans midnight
		if current_mins >= start_mins:
			# Before midnight: remaining = (1440 - current) + end
			remaining_mins = (1440 - current_mins) + end_mins
		else:
			# After midnight: normal calculation
			remaining_mins = end_mins - current_mins
	else:
		# Normal case: schedule doesn't cross midnight
		remaining_mins = end_mins - current_mins

	if remaining_mins <= 0:
		return 0

	# Convert to seconds and subtract current seconds (inline)
	return (remaining_mins * 60) - current.tm_sec
