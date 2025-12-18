# Pantallita 3.0

Complete rewrite of Pantallita with proper CircuitPython architecture to solve pystack exhaustion issues.

### 🔑 Key Architectural Changes in v3.0

**Problem to Solve:** v2.5.0's 6,175-line monolithic code constantly hit pystack exhaustion (25 levels in CP9, 32 in CP10)

**Solution:** Flat architecture with inline rendering
- **Stack depth:** 2 levels (main → show) vs 8+ levels in v2.5.0
- **No helper functions** in display modules (everything inline)
- **Direct module calls** from main loop (no nesting)
- **Proper socket management** (always close responses, 2-second WiFi delay)
- **Temperature fetched in correct unit** (Metric/Imperial from API, no conversion)
- **Anchor point text alignment** (handles variable-width fonts automatically)

**Features Working:**
- ✅ Weather fetching from AccuWeather (temperature in correct and controllable unit)
- ✅ Icon display (64×32 full-screen BMPs)
- ✅ Text alignment using anchor points (handles variable-width fonts)
- ✅ Feels like temperature (right-aligned when different)
- ✅ Feels shade temperature (right-aligned below feels when different)
- ✅ Clock display (centered or right-aligned based on shade visibility)
- ✅ Clock refresh (checked 10 time per second but only update clock lable once minute changes to avoid flicker)
- ✅ UV bar (white, gaps every 3 pixels, 1 pixel = 1 UV index)
- ✅ Humidity bar (white, gaps every 2 pixels, 1 pixel = 10% humidity)
- ✅ Live clock updates (refreshes every second during display)
- ✅ Timezone support with fallback
- ✅ WiFi recovery
- ✅ Button control (UP to stop)
- ✅ Centralized logging system (Phase 1.5)
- ✅ Location & timezone from AccuWeather (Phase 1.5)
- ✅ Memory tracking as % used (not bytes free)
- ✅ Human-readable cache age (e.g., "12m old")
- ✅ Cycle separators and module area prefixes
- ✅ Accurate uptime tracking
- ✅ 12-hour forecast display (Phase 2)
- ✅ Smart precipitation detection (shows when rain starts/stops)
- ✅ 3-column forecast layout with 13×13 icons
- ✅ Separate cache timers (weather: 5 min, forecast: 15 min)
- ✅ Color-coded time labels (white: consecutive, mint: jumped hours)
- ✅ Live clock in forecast column 1
- ✅ Stock/forex/crypto/commodity displays (Phase 4)
- ✅ Multi-stock display (3 stocks vertically with prices/percentages)
- ✅ Single stock chart display (intraday 78-point progressive charts)
- ✅ Market hours detection (9:30 AM - 4:00 PM ET with grace period)
- ✅ Smart stock caching (once outside hours, fresh during market)
- ✅ Configurable display frequency and market hours respect
- ✅ stocks.csv with GitHub remote loading

## Status: Phase 4 - Stock Display ✅ COMPLETE

**Completed:**
- ✅ **Phase 0: Bootstrap** - Foundation validated (2+ hour test)
  - CircuitPython 10.0.1 stable on hardware
  - Display, RTC, WiFi, buttons all working
  - Timezone handling with DST support
  - Memory stable (no leaks)
  - 740 cycles without crashes

- ✅ **Phase 1: Weather Display** - 8+ hour test successful
  - Created weather_api.py (fetch from AccuWeather)
  - Created display_weather.py (inline rendering)
  - Updated code.py (show weather instead of clock)
  - 95 cycles, zero crashes, memory stable

- ✅ **Phase 1.5: Centralized Logging & Location/Timezone** - Deployed
  - Created logger.py (centralized logging module)
  - Location & timezone from AccuWeather Location API
  - Weather and time always in sync (same API source)
  - Memory shown as % used (easier to spot leaks)
  - Cache age in human-readable format (e.g., "12m old")
  - Module area prefixes (MAIN, HW, WEATHER, DISPLAY, FORECAST)
  - Configurable timestamps and log levels
  - Accurate uptime tracking with monotonic time
  - 9.5-hour stress test successful (115 cycles, 0 errors)

- ✅ **Phase 2: Forecast Display** - Complete and stable (11+ hour test successful)
   - Created display_forecast.py with smart precipitation logic (inline, flattened)
   - Added fetch_forecast() to weather_api.py (12-hour forecast)
   - 3-column layout with 13×13 icons (v2.5 proven layout)
   - Smart column selection (shows when rain starts/stops) ✅ Validated
   - Color cascade logic (white for consecutive, mint for jumped hours)
   - Separate cache timers (weather: 5 min, forecast: 15 min)
   - Fixed smart logic bug: now checks all 12 hours for precipitation (was only 6)
   - Fixed color bug (col3 now compares to col2, not current hour)
   - Fixed positioning (v2.5 layout: x=3, 25, 48)
   - Precipitation testing complete: 3 scenarios tested, bug found & fixed
   - 11+ hour stability test: No errors, memory stable

- ✅ **Phase 3: Display Configuration** - Complete
   - Created config_manager.py (inline CSV parsing, GitHub remote config)
   - Display toggles: weather, forecast, clock (on/off control)
   - Temperature unit control: F/C switching via config
   - Remote control via GitHub-hosted config file
   - Config priority: GitHub > Local CSV > Defaults
   - Auto-refresh every ~50 minutes
   - Example files: config.csv.example, settings.toml.example

- ✅ **Phase 4: Stock Display** - Complete and stable (6.6+ hour test successful)
   - Created stocks_api.py with Twelve Data API integration (inline, flattened)
   - Created display_stocks.py for multi-stock and chart rendering (inline)
   - Two display modes: multi-stock (3 at a time) and single chart (highlighted)
   - Support for stocks, forex, crypto, and commodities
   - Market hours detection (9:30 AM - 4:00 PM ET) with grace period
   - Smart caching: fetch once outside hours, fresh data during market hours
   - Progressive chart loading: shows elapsed portion of trading day
   - 78-point intraday charts with 5-minute intervals
   - Configurable display frequency and market hours respect
   - stocks.csv with GitHub remote loading support
   - 6.6-hour test: 233 cycles, zero errors, memory stable (+7.4%)

---

## Phase 0 Lessons Learned

### What Worked
✅ Flat architecture - 2-level stack depth proven
✅ Module separation - Clean boundaries
✅ CircuitPython 10 - Stable, 28% more stack headroom
✅ Timezone with 2s delay - Reliable after socket pool initialization
✅ Fallback patterns - Default to CST when API fails

### Issues Encountered
⚠️ Socket timing - Need 2-second delay after WiFi for API calls - Still failing to sync at times
⚠️ Library dependencies - adafruit_ticks required by display_text in CP10
⚠️ Fast refreshes lead to slight but noticeable blinking (e.g. refresh clock per second)

### Memory Baseline
- Startup: 2,000,672 bytes free
- Stabilized: ~1,995,000 bytes free
- Usage: ~5KB for runtime state (excellent)

### 📋 Remaining Phases

- ~~**Phase 1.5:** Add Logging, Monitoring and Configuration functionality~~ ✅ **COMPLETE**
- ~~**Phase 2:** Forecast display (12-hour forecast, 3-column layout)~~ ✅ **COMPLETE**
- ~~**Phase 3:** Display configuration (toggles, temperature units, remote control)~~ ✅ **COMPLETE**
- ~~**Phase 4:** Stock display (with intraday charts)~~ ✅ **COMPLETE**
- **Phase 5:** Events, schedules, transit displays
- **Phase 6:** Production deployment and 24+ hour stability testing

---

## Why v3.0?

**Problem:** v2.5.0 (6175 lines, monolithic) hits pystack exhaustion when adding features
- Stack depth: 8-10 levels deep in display code
- Adding simple functions causes crashes
- CircuitPython 9: ~25 level limit
- Only 56% stack headroom remaining

**Solution:** Flat architecture + CircuitPython 10
- Stack depth: 2 levels max
- CircuitPython 10: ~32 level limit (+28%)
- 94% stack headroom for new features
- Inline all helper functions in display modules

---

## Architecture Principles

### 1. Flat Module Calls
```python
# GOOD - v3.0
def run_display_cycle():
	weather_data = weather_api.fetch_current()  # Level 1
	display_weather.show(weather_data, 240)     # Level 1
	# Returns to level 0

# BAD - v2.5.0
def run_display_cycle():
	_run_normal_cycle()                          # Level 1
		show_weather_display()                   # Level 2
			fetch_current_weather()              # Level 3
				fetch_weather_with_retries()     # Level 4
					_process_response()          # Level 5
```
						
### 2. Inline Everything in Display Modules

# GOOD - All logic inline

```python
def show(weather_data, duration):
	# Clear display inline
	while len(state.main_group) > 0:
		state.main_group.pop()

	# Calculate inline
	uv_length = int((weather_data['uv'] / 11) * 40)

	# Render inline
	for i in range(uv_length):
		rect = Rect(i, y, 1, 1, fill=color)
		state.main_group.append(rect)

```

### 3. Separate Data Fetching from Rendering

- API modules fetch data (called from main loop)
- Display modules render data (called from main loop)
- No nested calls between modules

---

## Module Structure

```
pantallita/
├── code.py              # Main entry point (~250 lines) ✅ DONE
│                        # - Calls modules directly, no nesting
│                        # - Hardware init, main loop only
│
├── config.py            # Constants (~145 lines) ✅ DONE
│                        # - Display, Colors, Paths, Timing, Logging
│                        # - Zero runtime cost (pure data)
│
├── state.py             # Global state (~60 lines) ✅ DONE
│                        # - Display objects, RTC, buttons
│                        # - HTTP session, caches, tracking
│
├── logger.py            # Centralized logging (Phase 1.5) ✅ DONE
│                        # - log(), log_memory(), format helpers
│                        # - Inline implementation, zero stack overhead
│
├── hardware.py          # Hardware init (~270 lines) ✅ DONE
│                        # - init_display(), init_rtc()
│                        # - connect_wifi(), init_buttons()
│                        # - Timezone handling with DST
│
├── weather_api.py       # Weather fetching (Phase 1 + 1.5 + 2) ✅ DONE
│                        # - fetch_location_info() - location & timezone
│                        # - fetch_current() - inline parsing (current weather)
│                        # - fetch_forecast() - 12-hour forecast (Phase 2)
│                        # - Separate cache timers (weather: 5 min, forecast: 15 min)
│
├── display_weather.py   # Weather rendering (Phase 1) ✅ DONE
│                        # - show() - everything inline
│                        # - No helper functions
│
├── display_forecast.py  # Forecast rendering (Phase 2) ✅ DONE
│                        # - show() - smart precipitation logic inline
│                        # - 3-column layout with color cascade
│                        # - Live clock in column 1
│
├── config_manager.py    # Display configuration (Phase 3) ✅ DONE
│                        # - load_config() - CSV parsing inline
│                        # - Local CSV and GitHub remote config
│                        # - Display toggles and temperature unit control
│
├── stocks_api.py        # Stock fetching (Phase 4) ✅ DONE
│                        # - load_stocks_csv() - GitHub > Local priority
│                        # - fetch_stock_quotes() - batch quotes
│                        # - fetch_intraday_time_series() - 78-point charts
│
├── display_stocks.py    # Stock rendering (Phase 4) ✅ DONE
│                        # - show_multi_stock() - 3 stocks vertically
│                        # - show_single_stock_chart() - progressive charts
│
└── display_other.py     # Events, schedules, transit, clock

```
---

## Reference Files

```
├── LOGS/                # Directory with relevant logs for review
├── old_code.py          # Original 2.5 Code Stable but frail (Reference)
└── old_README.md        # 2.5V Readme for additional context
```

## Hardware

- **Controller:** Adafruit MatrixPortal S3 (ESP32-S3)
- **Display:** 2× RGB LED matrices (64×32 pixels)
- **RTC:** DS3231 real-time clock
- **Firmware:** CircuitPython 10.0.1
- **Memory:** 2MB SRAM (~1.6MB available)

---

## Libraries Installed

**Phase 0 (Bootstrap) Installed:**
- adafruit_bitmap_font/
- adafruit_display_text/
- adafruit_ticks.mpy (CP10 requirement)
- adafruit_ntp.mpy
- adafruit_ds3231.mpy
- adafruit_requests.mpy
- adafruit_bus_device/
- adafruit_register/
- adafruit_connection_manager.mpy

**Phase 1 (Weather) - Installed:**
- adafruit_imageload/ (for weather icons)
- adafruit_display_shapes/ (for UV/humidity bars)

---

## Configuration

**settings.toml** (not in git - has secrets):

```toml
CIRCUITPY_WIFI_SSID = "your-network"
CIRCUITPY_WIFI_PASSWORD = "your-password"
TIMEZONE = "America/Chicago"

# AccuWeather API (Phase 1)
ACCUWEATHER_API_KEY_TYPE1 = "your-key"
ACCUWEATHER_LOCATION_KEY = "your-location-key"

# Display Configuration (Phase 3) - Optional
# Upload config.csv to GitHub and provide the raw URL here
# Example: "https://raw.githubusercontent.com/username/repo/main/config.csv"
CONFIG_GITHUB_URL = ""

# Stock Configuration (Phase 4) - Optional
# Upload stocks.csv to GitHub and provide the raw URL here
STOCKS_GITHUB_URL = ""

# Phase 4
TWELVE_DATA_API_KEY = "your-key"

# Future phases
CTA_API_KEY = "your-key"
```

**config.csv** (Phase 3 - Display Configuration):

```csv
setting,value
display_weather,true
display_forecast,true
display_stocks,false
display_clock,false
temperature_unit,F
stocks_display_frequency,3
stocks_respect_market_hours,true
stocks_grace_period_minutes,30
```

This file controls:
- Which displays are enabled (weather, forecast, stocks, clock)
- Temperature units (F or C)
- Stock display settings (frequency, market hours, grace period)
- Can be overridden by GitHub remote config (if CONFIG_GITHUB_URL is set)
- Auto-reloads every ~50 minutes

**stocks.csv** (Phase 4 - Stock Configuration):

```csv
# symbol,name,type,display_name,highlighted
CRM,Salesforce Inc.,stock,,1
SPY,SPDR S&P 500 ETF Trust,stock,,0
USD/MXN,US Dollar / Mexican Peso,forex,MXN,0
BTC/USD,Bitcoin US Dollar,crypto,BTC,1
```

This file controls:
- Which stocks/forex/crypto/commodities to display
- Display names (optional, uses symbol if empty)
- highlighted=1 for chart mode, highlighted=0 for multi-stock mode
- Can be overridden by GitHub remote config (if STOCKS_GITHUB_URL is set)
- Priority: GitHub > Local > Empty

**Logging Configuration** (in config.py):

```python
# Log level control (Phase 1.5)
CURRENT_LOG_LEVEL = config.LogLevel.INFO  # PRODUCTION=0, ERROR=1, WARNING=2, INFO=3, DEBUG=4, VERBOSE=5

# Logging options
class Logging:
    USE_TIMESTAMPS = False  # Turn ON for debugging, OFF for production (saves RTC overhead)
    SHOW_CYCLE_SEPARATOR = True  # Show "## CYCLE N ##" markers

# Temperature unit
TEMPERATURE_UNIT = "F"  # "F" or "C"
```

**Examples:**

```python
# For debugging: enable timestamps and verbose logging
CURRENT_LOG_LEVEL = config.LogLevel.DEBUG
config.Logging.USE_TIMESTAMPS = True

# For production: minimal logging, no timestamps
CURRENT_LOG_LEVEL = config.LogLevel.ERROR
config.Logging.USE_TIMESTAMPS = False
```

---

## Implementation Phases

### Phase 0: Bootstrap ✅ COMPLETE
- **Goal:** Validate foundation
- **Files:** config.py, state.py, hardware.py, code.py
- **Test:** 2+ hour stability test
- **Result:** 740 cycles, no crashes, memory stable

### Phase 1: Weather Display ⏳ IN PROGRESS
- **Goal:** Add current weather from AccuWeather
- **New files:** weather_api.py, display_weather.py
- **Test:** 24-hour stability test
- **Success:** Weather displays correctly, no stack issues

### Phase 2: Forecast Display
- **Goal:** Add 12-hour forecast
- **New files:** display_forecast.py
- **Test:** 24-hour with weather + forecast rotation

### Phase 3: Stocks Display
- **Goal:** Add stock market data
- **New files:** stocks_api.py, display_stocks.py
- **Test:** 48-hour including weekend behavior
 
### Phase 4: Remaining Displays
- **Goal:** Events, schedules, transit, enhanced clock
- **New files:** display_other.py, data_loader.py, transit_api.py
- **Test:** 72-hour full rotation test

### Phase 5: Production
- **Goal:** Error handling, monitoring, deployment
- **Test:** 7-day uptime test

---

## Critical Rules (Proven in Phase 0)

### ✅ WORKS:
1. Flat module calls (no nesting)
2. 2-second delay after WiFi for API calls
3. Timezone API with fallback to default offset
4. Inline rendering in display modules
5. Global state management via state.py


### ❌ AVOID:
1. Helper functions in display modules
2. Immediate API calls after WiFi connect
3. Nested function calls more than 2 levels
4. Complex exception nesting

---

## Stack Depth Budget (CircuitPython 10)

```
Phase 0 Validation:
- Framework:          10 levels
- Main loop:           2 levels (main → run_cycle)
- Display rendering:   0 levels (inline)
-----------------------------------
Total used:           12 levels
Available:            32 levels
Reserve:              20 levels (62% headroom) ✅

```

---

## Memory Budget

```
Phase 0 Baseline:
- Framework + libs:   ~400KB
- Module imports:     ~100KB (4 modules)
- Runtime state:      ~5KB
-----------------------------------
Total usage:          ~505KB / 2MB (25%)
Free:                 ~1,995KB (75% headroom) ✅
```

---

## Refactoring Plan

## Phase 1.5: Logging and Monitoring ✅ COMPLETE

**Goal:** Centralized logging system for easier debugging and monitoring

**Implemented:**

### Centralized Logger (`logger.py`)
- **`log(message, level, area)`** - Main logging function with early exit for performance
- **`log_memory(area, level)`** - Memory as % used (not bytes free)
- **`format_cache_age(seconds)`** - Human-readable age (e.g., "2m", "15m", "1h 5m")
- **`format_uptime(seconds)`** - Formatted uptime display
- **`log_cycle_start(cycle_num)`** - Cycle separator markers

### Location & Timezone Integration (`weather_api.py`)
- **`fetch_location_info()`** - Fetches location and timezone from AccuWeather Location API
- Returns: timezone name, UTC offset, DST status, city, state, formatted location
- **Primary timezone source:** AccuWeather Location API
- **Fallback chain:** settings.toml TIMEZONE → worldtimeapi.org → continue with RTC time
- **Benefits:** Weather and time always in sync (same API source), eliminates worldtimeapi.org dependency

**Initialization flow:**
```python
# code.py initialize()
1. hardware.connect_wifi()
2. location_info = weather_api.fetch_location_info()  # AccuWeather Location API
3. hardware.sync_time(rtc, timezone_offset=location_info['offset'])  # Use AccuWeather timezone
```

**Log output:**
```
[WEATHER:INFO] Location: Sheffield And Depaul, IL | Timezone: America/Chicago (UTC-6)
[HW:INFO] Time synced: 12/13 9:53 AM
```

### Configuration Options (`config.py`)
```python
class LogLevel:
    PRODUCTION = 0  # Only critical errors
    ERROR = 1
    WARNING = 2
    INFO = 3        # Default
    DEBUG = 4
    VERBOSE = 5

class Logging:
    USE_TIMESTAMPS = False  # RTC timestamps (OFF for performance)
    SHOW_CYCLE_SEPARATOR = True  # "## CYCLE N ##" markers

class Hardware:
    TOTAL_MEMORY = 2000000  # For % calculations
```

### Example Log Output

**Without timestamps (production mode):**
```
[MAIN:INFO] ## CYCLE 1 ##
[WEATHER:INFO] Fetching weather from AccuWeather...
[WEATHER:INFO] Weather: -4°F, Mostly cloudy, UV:0
[WEATHER:INFO] Fetch #1, Errors: 0
[DISPLAY:INFO] Displaying weather: -4° Mostly cloudy
[DISPLAY:INFO] Weather display complete
[MAIN:INFO] Memory: 3.8% used (76KB) [+0]
```

**With timestamps (debugging):**
```
[12-13 14:30:45] [MAIN:INFO] ## CYCLE 1 ##
[12-13 14:30:45] [WEATHER:INFO] Using cached weather (12m old)
[12-13 14:30:46] [MAIN:INFO] Memory: 3.8% used (76KB) [+0]
```

### Code Cleanup
- Removed duplicate `log()` functions from all modules
- All modules use `logger.log(message, level, area="MODULE")`
- Zero additional stack depth (inline implementation with early return)
- Module area prefixes: MAIN, HW, WEATHER, DISPLAY

---

## Phase 2: Forecast Display ⏳ IN PROGRESS

### Step 2.1: Add Forecast Fetching ✅ COMPLETE
- [x] `weather_api.py`: Add `fetch_forecast()` function
- [x] Parse 12-hour forecast data (inline, no helpers)
- [x] Implement smart column selection logic (inline, flattened)
- [x] Cache forecast data with timestamps
- [x] Separate cache timer (15 min vs 5 min for weather)

### Step 2.2: Implement Forecast Rendering ✅ COMPLETE
- [x] Create `display_forecast.py`
- [x] Inline ALL positioning logic (no calculate_position helpers)
- [x] Inline image loading (OnDiskBitmap for 13×13 icons)
- [x] Inline text rendering (no right_align_text helper)
- [x] 3-column layout with smart precipitation detection
- [x] Color cascade logic (mint for jumped hours)
- [x] Live clock updates for column 1

### Step 2.3: Integrate with Main Loop ✅ COMPLETE
- [x] `code.py`: Add forecast to display rotation
- [x] Implement display cycle timing (5 min weather + 1 min forecast)
- [x] Add forecast cache age checking
- [x] Update config.py with forecast constants
- [x] Update state.py with forecast tracking

### Step 2.4: Test & Validate ⏳ IN PROGRESS
- [x] Test column selection logic (clear sky - consecutive hours)
- [x] Verify image loading (13×13 BMPs working)
- [x] Fix color bug (col3 comparing to col2 correctly)
- [x] Fix positioning (v2.5 layout restored)
- [x] Test precipitation scenarios (3 tests: currently raining, will rain, retest with fix)
- [x] Fix smart logic bug (now checks all 12 hours, not just 6)
- [x] Verify fix with Test 3 (shows 1PM correctly, not 2PM)
- [ ] Run extended stability test (8-12 hours) - CURRENTLY RUNNING
- [ ] Verify memory stability over time
- [ ] Compare stack depth to Phase 1

**Success Criteria:** Weather + Forecast rotation runs 24+ hours, no stack exhaustion

## Phase 3: Display Configuration & Remote Control ✅ COMPLETE

### Step 3.1: Configuration System ✅ COMPLETE
- [x] Create `config_manager.py` (inline CSV parsing)
- [x] Create `config.csv` (local configuration file)
- [x] Add GitHub config URL to `config.py` Env class
- [x] Implement local CSV loading (inline, no helpers)
- [x] Implement GitHub remote config fetching
- [x] Configuration priority: GitHub > Local CSV > Defaults
- [x] Periodic config reload (every 10 cycles = ~50 minutes)

### Step 3.2: Display Toggles ✅ COMPLETE
- [x] `display_weather` toggle (enable/disable weather display)
- [x] `display_forecast` toggle (enable/disable forecast display)
- [x] `display_clock` toggle (enable/disable clock display - fallback)
- [x] Update `code.py` to respect display toggles
- [x] Automatic fallback to clock when all displays disabled

### Step 3.3: Temperature Unit Control ✅ COMPLETE
- [x] `temperature_unit` setting (F or C)
- [x] Local CSV control for temperature unit
- [x] GitHub remote control for temperature unit
- [x] Apply unit to `config.Env.TEMPERATURE_UNIT` dynamically
- [x] AccuWeather API already fetches correct unit (no conversion needed)

### Step 3.4: Documentation & Examples ✅ COMPLETE
- [x] Create `config.csv.example` (GitHub config template)
- [x] Create `settings.toml.example` (with CONFIG_GITHUB_URL)
- [x] Document configuration priority system
- [x] Document remote control setup instructions

**Features:**
- 🎛️ Toggle displays on/off via local or remote config
- 🌡️ Switch between Fahrenheit and Celsius
- 🌐 Remote control via GitHub-hosted config file
- 🔄 Auto-refresh config every ~50 minutes
- 📝 Simple CSV format for easy editing
- 🔌 Graceful fallback (GitHub → Local → Defaults)

**Config File Format:**
```csv
setting,value
display_weather,true
display_forecast,true
display_clock,false
temperature_unit,F
```

**Remote Control Setup:**
1. Upload `config.csv` to your GitHub repo
2. Get raw URL (e.g., `https://raw.githubusercontent.com/username/repo/main/config.csv`)
3. Add to `settings.toml`: `CONFIG_GITHUB_URL = "your-raw-url"`
4. Device will fetch and apply config from GitHub
5. Edit on GitHub to remotely control your display!

**Success Criteria:** Configuration system works reliably, remote control functional

## Phase 4: Stock Market Display ✅ COMPLETE

### Step 4.1: Add Stock Fetching ✅ COMPLETE
- [x] Create `stocks_api.py`
- [x] Load stocks.csv (local and GitHub)
- [x] Implement `fetch_stock_quotes()` for multi-stock (batch quotes)
- [x] Implement `fetch_intraday_time_series()` for chart mode (78 points, 5min intervals)
- [x] Market hours detection (inline, ET to local timezone conversion)
- [x] Cache management (smart caching: once outside hours, fresh during market)

### Step 4.2: Implement Stock Rendering ✅ COMPLETE
- [x] Create `display_stocks.py`
- [x] Multi-stock rotation mode (3 stocks vertically, inline layout)
- [x] Single stock chart mode (progressive loading, inline chart rendering)
- [x] Triangle arrows for stocks, $ indicator for forex/crypto/commodity (inline)
- [x] Price formatting with comma separators (inline, no helpers)
- [x] Smart rotation logic (highlight=1 for chart, highlight=0 for multi)
- [x] Right-aligned prices/percentages with bounding_box calculation

### Step 4.3: Test & Validate ✅ COMPLETE
- [x] Test during market hours (fresh data fetched correctly)
- [x] Test outside market hours (cached data reused)
- [x] Test weekend behavior (no unnecessary fetches)
- [x] Test all asset types (stock, forex, crypto, commodity - all working)
- [x] Verify chart rendering with various price ranges (validated)
- [x] Progressive chart loading (elapsed time based, blank space for future)
- [x] Run stability test (6.6 hours, 233 cycles, zero errors)

**Success Criteria:** ✅ Stocks display works in all market conditions, no stack exhaustion, memory stable

## Phase 5: Remaining Displays (Week 5)

### Step 5.1: Events & Schedules
- [ ] Create `data_loader.py` for CSV parsing
- [ ] Load events.csv (local and GitHub)
- [ ] Load schedules.csv (local and GitHub)
- [ ] Create `display_other.py`
- [ ] Implement events display (inline)
- [ ] Implement schedules display (inline)
- [ ] Implement clock display (fallback)

### Step 5.2: CTA Transit
- [ ] Create `transit_api.py`
- [ ] Fetch train arrivals
- [ ] Fetch bus arrivals
- [ ] Combine and sort arrivals
- [ ] Add transit rendering to `display_other.py`

### Step 5.3: Main Loop Logic
- [ ] Schedule detection
- [ ] Display rotation logic
- [ ] Frequency controls
- [ ] Time-based filtering (commute hours, event hours)

### Step 5.4: Test & Validate
- [ ] Test full rotation cycle
- [ ] Test schedule priority
- [ ] Test transit display during commute hours
- [ ] Test event time filtering
- [ ] Run for 72 hours (full weekend test)

**Success Criteria:** All displays work, proper rotation, 72+ hour uptime

## Phase 5: Error Handling & Polish (Week 5)

### Step 5.1: Defensive Error Handling
- [ ] WiFi recovery with exponential backoff
- [ ] API retry logic (weather, stocks, transit)
- [ ] Cached data fallback
- [ ] Socket cleanup on errors
- [ ] Session recreation on failures

### Step 5.2: Monitoring & Logging
- [ ] Memory monitoring (report every 100 cycles)
- [ ] API call tracking (per service)
- [ ] Stack depth logging (at key checkpoints)
- [ ] Error state logging

### Step 5.3: Daily Restart & Maintenance
- [ ] 3am daily restart logic
- [ ] GitHub data refresh at restart
- [ ] Cache cleanup
- [ ] API counter reset

### Step 5.4: Production Deployment
- [ ] Deploy to production matrix
- [ ] Run side-by-side with v2.5.0 for comparison
- [ ] Monitor for 1 week
- [ ] Fix any issues
- [ ] Deploy to all matrices

**Success Criteria:** 7+ day uptime, no manual intervention required

## Stack Depth Budget

**CircuitPython 10 Stack Budget:** ~32 levels (increased from 25)

### Level Allocation:
- Framework overhead: 10 levels
- Main loop (code.py): 2 levels (main → run_cycle)
- Module calls: 1 level per module (fetch, render)
- Display rendering: 5 levels max (inline everything)
- **Reserve:** 14 levels (44% headroom)

### Critical Rules:
1. `code.py` calls modules directly - NO wrapper functions
2. Display modules have ZERO helper functions - inline everything
3. API modules can have 1 level of helpers (parse_response called from fetch)
4. NEVER nest try/except more than 1 level deep
5. Avoid f-strings in deep code (they add stack depth)

## Memory Budget

**ESP32-S3 SRAM:** 2MB total
**CircuitPython 10 Usage:** ~400KB (framework + libraries)
**Available:** ~1.6MB

### Module Import Costs (Estimated):
- config.py: ~50KB (constants only)
- state.py: ~100KB (data structures)
- hardware.py: ~80KB (initialization)
- network.py: ~100KB (session management)
- weather_api.py: ~80KB (fetch + parse)
- stocks_api.py: ~120KB (fetch + parse + cache)
- transit_api.py: ~60KB (fetch + parse)
- display_weather.py: ~100KB (rendering)
- display_forecast.py: ~120KB (rendering + logic)
- display_stocks.py: ~150KB (rendering + chart)
- display_other.py: ~150KB (events + schedules + transit + clock)

**Total Module Cost:** ~1.11MB
**Runtime Caches:** ~100KB (images, text widths, API data)
**Total Usage:** ~1.6MB / 2MB = 80%
**Reserve:** ~400KB (20% headroom)

## Testing Protocol

### Per-Phase Testing:
1. **Unit test:** Test module in isolation (if possible)
2. **Integration test:** Test with previous phases
3. **24-hour stability test:** Run on test matrix
4. **Stack depth check:** Log max depth during test
5. **Memory check:** Monitor for leaks
6. **Error injection:** Disconnect WiFi, kill API, etc.

### Final Validation:
1. **7-day production test:** One matrix, full feature set
2. **Multi-matrix test:** Deploy to 3 matrices, verify consistency
3. **Holiday/weekend test:** Verify market hours, transit hours, event filtering
4. **Friend deployment:** Gift matrices, monitor remotely for 2 weeks

## Testing Results

### Phase 0 Results:
- ✅ Duration: 123.3 minutes (2+ hours)
- ✅ Cycles: 740 without crashes
- ✅ Memory: 0.25% loss, stable
- ✅ WiFi: Connected entire duration
- ✅ Errors: Zero critical errors
- ⚠️ Timezone API needs 2s delay (fixed)

---

### Phase 1 Results:
- ✅ Duration: (8+ hours)
- ✅ Cycles: 95 without crashes
- ✅ Memory: Stable at 1,932,384 bytes free
- ✅ WiFi: Connected entire duration
- ✅ Errors: Zero critical errors

---

## Functionality Details for Phase 2

**Display Layout**
- **3-Column Grid:**
  - Column 1: X=3, Current weather
  - Column 2: X=25, +1 hour weather or smart selection << make sure column 2 hours is always +1 hour from column 1 hour if not show next hour
  - Column 3: X=48, +2 hour weather or smart selection
- **Each Column:**
  - Time label (top): "NOW" or "3P" or "2A" (centered, small font)
  - Icon (middle): 13×13 BMP (centered)
  - Temp label (bottom): "25°" (centered, small font)
- **Smart Column Selection (Inline Algorithm):**
  1. Get next 12 hours of forecast
  2. Find precipitation hours (precipitation = true)
  3. Select 3 hours with priority:
    - Column 1: current weather (always)
      - if current weather precipitation = false and next 12 hours every hour precipitation = false
        - Column 2: +1 hour from current
        - Column 3: +2 hours from current
      - elif current weather precipitation = false and precipitation = true in the next 12 hours
        - Column 2: show time and expected weather of when precipitation starts (First instance of precipitation = true in 12 hour data)
        - Column 3: shows next time from Column 2 hour where precipitation turns back to false (precipitation stop). if precipitation continues past 12 hour forecast show data for last available hour
      elif current weather precipitation = true  
        - Column 2: show +1 hour from current data
        - Column 3: shows next time from Column 2 hour where precipitation turns back to false (precipitation stop). if precipitation continues past 12 hour forecast show data for last available hour
  4. Color code non-consecutive hours (MINT). show in mint time stamp of column 2 and 3 when they are happening in the future in a non consecutive way (e.g. 1p | 2p | 3p = all white /// 1p | 3p | 6p = col 1 white col 2 and 3 mint [when col 2 is mint col 3 is always mint] /// 1p | 2p | 7p col 1 and 2 white col 3 mint)
- **Features**
  - ✅ 12-hour forecast data from AccuWeather
  - ✅ 3-column layout with 13×13 icons
  - ✅ Smart column selection (prioritizes precipitation)
  - ✅ NOW indicator for current hour
  - ✅ Color coding (MINT vs WHITE)
  - ✅ Temperature in correct unit
  - ✅ Anchor point text centering
  - ✅ 15-minute cache
- **Success Criteria**
  - Forecast fetches correctly - 12 hours of data
  - Column selection works - Shows relevant hours
  - Precipitation prioritized - Rainy hours shown first
  - Icons display - 13×13 BMPs load correctly
  - Text centered - Time and temp use anchor points
  - Temperature unit correct - C or F from settings.toml
  - Cache working - Reduces API calls
  - Memory stable - No leaks over 24 hours
  - No stack exhaustion - Stays at 2 levels
  - Integrates with Phase 1 - Weather + Forecast rotation works

#### config.py additions:

```python

class Layout:
    # Forecast display
    FORECAST_COL1_X = 3
    FORECAST_COL2_X = 25
    FORECAST_COL3_X = 48
    FORECAST_TIME_Y = 1
    FORECAST_ICON_Y = 9
    FORECAST_TEMP_Y = 25
    FORECAST_COLUMN_WIDTH = 13

class Paths:
    FORECAST_IMAGES = "/img/weather/columns"

class Timing:
    FORECAST_DISPLAY_DURATION = 60
    FORECAST_UPDATE_INTERVAL = 900  # 15 minutes
    FORECAST_CACHE_MAX_AGE = 1800   # 30 minutes

```

#### state.py additions:

```python

# Forecast cache
last_forecast_data = None
last_forecast_time = 0
forecast_fetch_count = 0
forecast_fetch_errors = 0

```

#### Estimated Complexity
  - Lines of code: ~300 total (forecast_api.py: ~150, display_forecast.py: ~150)
  - New files: 2
  - Modified files: 3 (code_v3.py, config.py, state.py)
  - Testing time: 24 hours minimum
  - Stack depth: 2 levels (no change from Phase 1)
  
#### Risks & Mitigations
  - Column selection complexity → Keep algorithm inline, well-commented
  - 13×13 icons not loading → Use OnDiskBitmap (proven in Phase 1)
  - Text centering issues → Use anchor_point=(0.5, 0.0) (proven in Phase 1)
  - Memory issues with more data → Cache management, gc.collect()
  - API rate limits → 15-minute cache reduces calls

#### Dependencies
  - ✅ Phase 1 complete (weather display working)
  - ✅ 13×13 forecast icons available
  - ✅ AccuWeather API key with forecast access
  - ✅ CircuitPython 10.0.1 installed

---
Status: Ready to implement after Phase 1 testing and logging/config foundations complete
---

## Troubleshooting

### Common Issues (Phase 0)
✅ **Socket failures** - Fixed with 2-second delay after WiFi
✅ **Missing adafruit_ticks** - Required by display_text in CP10
✅ **Timezone API errors** - Fallback to CST (-6) works


### If Issues in Phase 1
- Check AccuWeather API key in settings.toml
- Verify location key is correct
- Check API call quota (50/day free tier)
- Monitor serial logs for errors

---

## Related Documentation
**In v2 repo** (~/Documents/Adafruit/Screeny_V2.0):
- `REFACTOR_PLAN.md` - Complete 5-phase implementation plan
- `ARCHITECTURE_COMPARISON.md` - Deep dive on stack depth issues
- `BOOTSTRAP_GUIDE.md` - Step-by-step CP10 upgrade

**This repo:**
- `README.md` - This file (overview and status)

---

## Git Workflow

```bash

# Development branches
bootstrap-test     # Phase 0 ✅ COMPLETE
weather-display    # Phase 1 ⏳ CURRENT (to be created)
forecast-display   # Phase 2
stocks-display     # Phase 3

# Workflow
git checkout -b weather-display

# ... implement weather_api.py and display_weather.py ...
git add .
git commit -m "Implement Phase 1: Weather Display"
git push -u origin weather-display

```

---


## Success Metrics

### Phase 0 (Complete) ✅
- [x] 1+ hour uptime without crashes
- [x] WiFi stays connected
- [x] Memory stable (no leaks)
- [x] Button stops cleanly
- [x] Timezone handling works
- [x] Time displays correctly

### Phase 1 (In Progress) ⏳
- [ ] Weather fetches from AccuWeather
- [ ] Display shows temp, UV, humidity, icon
- [ ] 24-hour stability test passes
- [ ] No stack exhaustion errors
- [ ] Memory remains stable

### Final (Phase 5)
- [ ] 7+ day uptime
- [ ] All displays functional
- [ ] Zero pystack errors
- [ ] Zero socket errors
- [ ] Can add new features without crashes

---

## Contact & Context
**Original coder:** Diego Celayeta, Hobbyist learning CircuitPython
**V2 status:** 6175 lines, working but at capacity limits
**Learning goals:** Proper embedded systems architecture, stack management
**Deployment:** Personal use + gifts to 3-5 friends

---

## If This Chat Ends
**To continue in a new chat:**
1. **Share context:**

   ```

   I'm working on Pantallita v3.0, a CircuitPython refactor to fix pystack
   exhaustion. I've completed Phase 0 (bootstrap), Phase 1 (weather display),
   Phase 1.5 (centralized logging), Phase 2 (12-hour forecast with smart
   precipitation), Phase 3 (display configuration), and Phase 4 (stock/forex/
   crypto/commodity display with progressive charts). Currently ready for
   Phase 5 (events, schedules, transit). Here's the README: [paste this file]

   ```

2. **Current status:** Phase 4 complete - Stock display fully functional with progressive charts

3. **Key files completed:**

   - config.py (constants + logging + forecast + stocks layout)
   - state.py (global state + weather/forecast/stocks caches)
   - hardware.py (init functions with timezone handling)
   - logger.py (centralized logging system)
   - weather_api.py (current weather + 12-hour forecast)
   - display_weather.py (inline rendering, live clock)
   - display_forecast.py (3-column forecast with smart precipitation logic)
   - config_manager.py (display configuration with GitHub remote)
   - stocks_api.py (Twelve Data API integration, market hours detection)
   - display_stocks.py (multi-stock and progressive chart rendering)
   - code.py (main loop with weather + forecast + stocks rotation)

4. **Next steps:**

   - Begin Phase 5: Events, schedules, and transit displays
   - Implement data_loader.py for CSV parsing
   - Create display_other.py for remaining displays
   - Add transit_api.py for CTA integration

---

**Repository:** https://github.com/strategeekal/pantallita
**Branch:** claude/refactor-rgb-matrix-01LCK6gcPJ9dAaYc9Ft476Nb (Phase 4 complete)
**Last Updated:** 2025-12-18
**CircuitPython Version:** 10.0.1