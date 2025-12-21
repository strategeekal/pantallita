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
- ✅ Bicolor charts (green above open price, red below open price)
- ✅ Market hours detection (9:30 AM - 4:00 PM ET with grace period)
- ✅ Smart stock caching (once outside hours, fresh during market)
- ✅ Grace period optimization (per-symbol tracking, zero redundant API calls)
- ✅ Dynamic grace period extension (ensures all stocks updated for 24/7 display)
- ✅ Configurable display frequency and market hours respect
- ✅ stocks.csv with GitHub remote loading

## Status: Phase 5 - Schedule Display ✅ COMPLETE

**Display Order:** Forecast >> Weather >> Events >> Stocks >> Schedule (highest priority)

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

- ✅ **Phase 4: Stock Display** - Complete and stable (15+ hours testing)
   - Created stocks_api.py with Twelve Data API integration (inline, flattened)
   - Created display_stocks.py for multi-stock and chart rendering (inline)
   - Two display modes: multi-stock (3 at a time) and single chart (highlighted)
   - Support for stocks, forex, crypto, and commodities
   - Market hours detection (9:30 AM - 4:00 PM ET) with grace period
   - Smart caching: fetch once outside hours, fresh data during market hours
   - Progressive chart loading: shows elapsed portion of trading day
   - 78-point intraday charts with 5-minute intervals (compressed to 64 pixels)
   - **Bicolor chart:** Green above opening price, red below (live intraday performance)
   - **Grace period smart fetching:** Per-symbol tracking prevents redundant API calls
   - **Dynamic grace period extension:** Ensures all stocks updated when respect_market_hours=false
   - Configurable display frequency and market hours respect
   - stocks.csv with GitHub remote loading support
   - Initial test: 6.6 hours, 233 cycles, zero errors, memory stable (+7.4%)
   - Extended tests: 15+ hours total across market hours, after hours, and grace period scenarios

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
- ~~**Phase 5:** Schedule display (time-based activities with progress tracking)~~ ✅ **COMPLETE**
- **Phase 6:** Events display (date-based special occasions)
- **Phase 7:** Transit displays and production deployment

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
- [x] **Bicolor chart rendering:** Green segments above open, red below (inline color logic)
- [x] Chart compression: 78 data points → 64 pixels (preserves first/last, samples middle)

### Step 4.3: API Optimization ✅ COMPLETE
- [x] **Grace period smart fetching:** Per-symbol tracking with `grace_period_fetched_symbols` set
- [x] Prevent redundant API calls during grace period (fetch each symbol once)
- [x] **Dynamic grace period extension:** When respect_market_hours=false
- [x] Auto-extends until all stocks fetched, then switches to cached data
- [x] Logging: Shows unfetched stock count and completion status

### Step 4.4: Test & Validate ✅ COMPLETE
- [x] Test during market hours (fresh data fetched correctly)
- [x] Test outside market hours (cached data reused)
- [x] Test weekend behavior (no unnecessary fetches)
- [x] Test all asset types (stock, forex, crypto, commodity - all working)
- [x] Verify chart rendering with various price ranges (validated)
- [x] Progressive chart loading (elapsed time based, blank space for future)
- [x] Test grace period optimization (zero redundant API calls confirmed)
- [x] Test bicolor chart (opening price comparison working)
- [x] Test dynamic extension (all stocks fetched before 24/7 cached display)
- [x] Initial stability test: 6.6 hours, 233 cycles, zero errors
- [x] Extended market hours test: 4.4 hours, 173 cycles, zero errors
- [x] After hours + grace period test: 4.9 hours, 57 cycles, quota handling validated
- [x] Grace period smart fetching test: 18 minutes, 13 cycles, zero redundant calls

**Success Criteria:** ✅ Stocks display works in all market conditions, optimized API usage, no stack exhaustion, memory stable

## Phase 5: Schedule Display ✅ COMPLETE

### Overview
Time-based activity reminders and routines (e.g., "Get Dressed" at 7:00 AM, "Bedtime" at 8:45 PM). Schedules take over the display during configured time windows, showing a custom image with progress tracking and weather context.

### Features
- **Time-based activation**: Displays during specific time windows (e.g., 7:00-7:15 AM)
- **Day filtering**: Can limit to specific days of week (weekdays only, weekends, specific days)
- **Progress tracking**: Visual progress bar shows elapsed time vs total duration
- **Weather integration**: Shows current weather alongside schedule (15-min cache)
- **Long schedule support**: Can run for hours with continuous updates
- **Date-specific overrides**: GitHub date-specific schedules override defaults
- **Priority display**: Schedules override normal rotation (highest priority)

### Display Layout (64×32 pixels)

**Left Section (x: 0-22) - Weather & Time:**
- Clock: `hh:mm` 12-hour format (top)
- Weather icon: 13×13 pixels (below clock)
- Temperature: Below icon (e.g., "72°")
- UV bar: Always visible (empty when UV=0)

**Right Section (x: 23-63) - Schedule:**
- Schedule image: 40×28 pixels (starts at x=23, y=1 in 1-based grid)
- Custom BMP image for each activity

**Bottom Section (x: 23-62, y: 28-32) - Progress Bar:**
- Span: Same width as schedule image
- Markers:
  - Long markers (3px tall): 0% (start), 50% (middle), 100% (end)
  - Short markers (2px tall): 25%, 75%
- Overlaps schedule image by 3 pixels at marker positions

### Schedule Sources (Priority Order)

**1. GitHub Date-Specific CSV** (highest priority)
- URL: `{GITHUB_BASE}/schedules/YYYY-MM-DD.csv`
- Example: `schedules/2025-12-25.csv` (Christmas schedule)
- Checked first based on current date

**2. GitHub Default CSV** (fallback)
- URL: `{GITHUB_BASE}/schedules/default.csv`
- Used when no date-specific file exists

**3. Local CSV** (final fallback)
- Path: `schedules.csv` (root directory)
- Used when GitHub fetch fails

### CSV Format
```csv
# Format: name,enabled,days,start_hour,start_min,end_hour,end_min,image,progressbar
Get Dressed,1,0123456,7,0,7,15,get_dressed.bmp,1
Breakfast,1,0123456,7,30,8,0,breakfast.bmp,1
Sleep,1,0123456,20,45,21,30,bedtime.bmp,0
```

**Fields:**
- `name`: Schedule name (string)
- `enabled`: 1=active, 0=disabled
- `days`: String of digits (0=Monday, 6=Sunday), e.g., "0123456" for all days, "01234" for weekdays
- `start_hour`: Hour (0-23) when schedule starts
- `start_min`: Minute (0-59) when schedule starts
- `end_hour`: Hour (0-23) when schedule ends
- `end_min`: Minute (0-59) when schedule ends
- `image`: BMP filename (40×28, 4-bit indexed color)
- `progressbar`: 1=show progress bar, 0=hide

### Schedule Images
- **Location**: `img/schedules/`
- **Format**: `.bmp` (4-bit indexed color)
- **Size**: 40 pixels wide × 28 pixels tall
- **Examples**: `breakfast.bmp`, `bedtime.bmp`, `get_dressed.bmp`, `homework.bmp`

### Implementation Completed ✅

**Step 5.1: Schedule Loading & Parsing** ✅ COMPLETE
- [x] Created `schedule_loader.py` (inline CSV parsing)
- [x] Implemented date-based GitHub fetch logic (GitHub > Local priority)
- [x] Date-specific override support (YYYY-MM-DD.csv > default.csv)
- [x] Parse schedule CSV content (inline, no helpers)
- [x] Schedule activation detection (time windows + day-of-week filtering)

**Step 5.2: Schedule Display Rendering** ✅ COMPLETE
- [x] Created `display_schedules.py` with inline rendering
- [x] Implemented `show_schedule()` function with single long loop
- [x] Clock updates (every minute, 12-hour format)
- [x] Progress bar updates (continuous, LILAC fill over MINT base)
- [x] Weather refresh (every 15 minutes with cleanup - **now 5 min for stress test**)
- [x] Complete layout rendering:
  - [x] Clock label (top-left, 12-hour format)
  - [x] Weather icon (13×13, dynamic positioning based on UV)
  - [x] Temperature (dynamic positioning based on UV)
  - [x] UV bar (always visible, empty when UV=0)
  - [x] Schedule image (40×28, right side, LRU image cache)
  - [x] Progress bar with markers (bottom, 1-pixel wide at fixed positions)

**Step 5.3: Progress Bar Implementation** ✅ COMPLETE
- [x] Progress bar base (MINT, 2 pixels tall, y=29-30)
- [x] Progress fill (LILAC, 2 pixels tall, grows upward above base)
- [x] Marker system (1 pixel wide, WHITE):
  - [x] Long markers (0%, 50%, 100%): 5 pixels tall (y=31 to y=27)
  - [x] Short markers (25%, 75%): 4 pixels tall (y=31 to y=28)
  - [x] Fixed positions: x=23, 32, 42, 52, 61
- [x] Continuous progress updates in display loop

**Step 5.4: Main Loop Integration** ✅ COMPLETE
- [x] Schedule check with priority (overrides all displays)
- [x] Config toggle: `display_schedules` (on/off control)
- [x] Button interrupt support (UP button raises KeyboardInterrupt)
- [x] Schedule reload every 10 cycles (~50 minutes)

**Step 5.5: Testing & Validation** ✅ COMPLETE
- [x] Initial test: 5 schedules, 1h 35min continuous, perfect transitions
- [x] Extended stress test: 10 schedules, 4h 20min, starting at 9:25 PM
- [x] Weather refresh validated (working correctly every 5 min - stress test mode)
- [x] Clock updates validated (every minute)
- [x] Progress bar rendering validated (markers, fill, colors)
- [x] Memory stability: 5.3% → 15.0% over 3.6 hours
- [x] Zero errors, seamless schedule transitions

### Pending To-Do Items

**Night Mode Minimal Display Toggle**
- [ ] Add `night_mode_minimal_display` setting to config.csv and config_manager.py
- [ ] Detect night mode schedules (by name pattern or CSV flag)
- [ ] Conditionally hide weather icon when:
  - `night_mode_minimal_display = true` AND
  - Current schedule is a night mode schedule (e.g., "Sleep", "Night Mode")
- [ ] Purpose: Reduce screen clutter during sleep schedules for minimal distraction

### Technical Details

**Display Loop Approach:**
```python
def show_schedule(schedule, duration):
    # Draw static elements once
    draw_clock()
    draw_weather_icon()
    draw_temperature()
    draw_uv_bar()
    draw_schedule_image()
    draw_progress_bar()

    # Long display loop
    start_time = time.monotonic()
    last_weather_fetch = 0
    last_minute = -1

    while time.monotonic() - start_time < duration:
        elapsed = time.monotonic() - start_time
        current_minute = rtc.datetime.tm_min

        # Update clock (every minute)
        if current_minute != last_minute:
            update_clock_label()
            last_minute = current_minute

        # Update progress bar (continuous)
        update_progress_bar(elapsed, duration)

        # Refresh weather + cleanup (every 15 min)
        if elapsed - last_weather_fetch > 900:
            update_weather_display()
            gc.collect()  # Cleanup after fetch
            last_weather_fetch = elapsed

        time.sleep(1)  # Check every second
```

**Key Design Decisions:**
- **Single loop** (not segmented): Simpler code, no screen flicker
- **Cleanup checkpoints**: After each weather fetch (every 15 min)
- **UV bar always visible**: Simpler layout, no conditional positioning
- **Progress bar overlap**: 3-pixel overlap with schedule image at markers
- **12-hour clock format**: More user-friendly (e.g., "7:15" vs "07:15")

**Success Criteria:**
- [ ] Schedules activate at correct times
- [ ] Display shows all elements correctly
- [ ] Progress bar animates smoothly
- [ ] Clock updates every minute
- [ ] Weather refreshes every 15 minutes
- [ ] Long schedules (4+ hours) work without socket exhaustion
- [ ] Date-specific GitHub overrides work
- [ ] Fallback to local CSV works
- [ ] Memory remains stable
- [ ] No stack exhaustion

---

## Phase 6: Events Display ⏳ NEXT

### Overview
Date-based special calendar events (birthdays, anniversaries, holidays) with custom images and colored text. Events are displayed based on calendar dates and can have optional time windows for when they should appear during the day.

### Purpose
- Display special occasions and reminders
- Birthday celebrations with custom messages
- Holiday greetings (New Year, Valentine's Day, etc.)
- Anniversary reminders
- Flexible time-windowed events (e.g., show only during waking hours)

### Display Priority
**Normal Cycle Order:** Forecast (60s) >> Weather (240s) >> Events (remaining time) >> Stocks (60s)

**Note:** Schedules override all displays when active (highest priority)

### Display Layout (64×32 pixels)

```
┌────────────────────────────────────┐
│ Top Text (left)    [IMAGE] (right)│  ← Top line: DIMMEST_WHITE
│                    [25×28]         │
│                    [IMAGE]         │
│ Bottom Text (left)                 │  ← Bottom line: Custom color
│                                    │
└────────────────────────────────────┘
```

**Layout Constants:**
- Event Image: x=37, y=2 (top-right corner)
- Image Size: 25×28 pixels (BMP, 4-bit indexed color)
- Text: Left-aligned with margin (x=1 or configurable)
- Text Positioning: **Bottom-aligned** (calculated dynamically)
  - Top line: DIMMEST_WHITE color (name/greeting)
  - Bottom line: Custom color per event (occasion type)
- No weather integration (unlike schedules)
- No progress bar (unlike schedules)
- No day indicator (removed from scope)

### Event Sources (Priority Order)

**1. GitHub Ephemeral Events** (highest priority, date-specific)
- URL: Configured via `GITHUB_EVENTS_URL` in settings.toml
- Format: `YYYY-MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]`
- Example: `2025-12-25,Merry,Christmas,blank.bmp,GREEN`
- **Auto-skips past dates** (if event date < current date, exclude from loading)
- Fetched once at startup (ephemeral, temporary events)

**2. Local Permanent Events** (recurring yearly)
- File: `events.csv` (root directory)
- Format: `MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]`
- Example: `12-25,Merry,Christmas,blank.bmp,GREEN`
- **Recurring:** Events repeat every year on same date
- Always loaded from local file

**3. Merged Events Dictionary**
- Combined: Permanent + Ephemeral events
- Key: MMDD format (e.g., "1225" for December 25)
- Value: Array of event data for that date
- If multiple events for same date, both are included

### CSV Format

**Local Events (events.csv) - Recurring Yearly:**
```csv
# Format: MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]
01-01,Happy,New Year,new_year.bmp,BUGAMBILIA
02-14,Dia,Didiculo,heart.bmp,RED,8,20
12-25,Merry,Christmas,blank.bmp,GREEN
```

**GitHub Ephemeral Events - Specific Dates:**
```csv
# Format: YYYY-MM-DD,TopLine,BottomLine,ImageFile,Color[,StartHour,EndHour]
2025-01-15,Puchis,Cumple,cake.bmp,BUGAMBILIA,8,20
2025-02-14,Happy,Valentine,heart.bmp,RED
```

**Fields:**
- `date`: MM-DD (local) or YYYY-MM-DD (GitHub)
- `TopLine`: Text shown at top (e.g., "Happy", "Puchis")
- `BottomLine`: Text shown at bottom (e.g., "Birthday", "Cumple")
- `ImageFile`: Filename in `/img/events/` (25×28 BMP)
- `Color`: Color name for bottom text (e.g., RED, BUGAMBILIA, GREEN, MINT)
- `StartHour`: Optional (0-23) - hour event becomes active (default: 0)
- `EndHour`: Optional (0-23) - hour event stops being active (default: 24)

### Event Data Structure

**Event Array:** `[top_line, bottom_line, image, color, start_hour, end_hour]`

**Example:**
```python
["Puchis", "Cumple", "cake.bmp", "BUGAMBILIA", 8, 20]
# Shows "Puchis" (top, DIMMEST_WHITE)
# Shows "Cumple" (bottom, BUGAMBILIA color)
# Image: cake.bmp (25×28)
# Active: 8:00 AM - 8:00 PM only
```

### Key Features

**1. Time Window Filtering**
- Events can specify active hours (start_hour to end_hour)
- Example: Birthday shows only 8 AM - 8 PM
- All-day events: Omit time fields (active 0:00-23:59)
- Inactive events: Logged but not displayed
  - "Event inactive: 1 event(s) today, next active at 8:00"
  - "Event inactive: 1 event(s) today, time window passed"

**2. Multiple Events Per Day**
- If multiple events for same date, **time is split equally**
- Example: 2 events + 60s available = 30s each
- Minimum duration: `MIN_EVENT_DURATION` (configurable)
- Events rotate in order loaded

**3. Special Birthday Handling**
- If `top_line == "Birthday"`: Uses special birthday cake image
- Different positioning/layout for birthdays (from old code)
- **Note:** May simplify in new implementation

**4. Image Fallback Chain**
- Primary: Event-specific image from CSV (`cake.bmp`, `heart.bmp`, etc.)
- Fallback: `blank.bmp` if primary fails to load
- Uses LRU image cache (same as schedules/weather)

**5. Bottom-Aligned Text Positioning**
- Text positions calculated dynamically using helper function
- Ensures text stays above bottom margin
- Accounts for variable font heights
- **Function:** `calculate_bottom_aligned_positions(font, top_text, bottom_text, display_height, bottom_margin, line_spacing)`

**6. Color Support**
- Colors defined in `config.Colors` class
- Examples: RED, GREEN, MINT, BUGAMBILIA, LILAC, ORANGE, WHITE, DIMMEST_WHITE
- Bottom text uses custom color, top text always DIMMEST_WHITE

### Display Logic Flow

```
1. Get today's date (MMDD format from RTC)
2. Check merged events dictionary for today's date
3. Filter events by current time window
   - Get current hour
   - Keep only events where: start_hour <= current_hour < end_hour
4. If no active events:
   - Check if events exist but are inactive (outside time window)
   - Log next activation time or "time window passed"
   - Return False (skip events display)
5. If 1 active event:
   - Display for full allocated duration
6. If multiple active events:
   - Calculate duration per event (total / count)
   - Ensure minimum duration per event
   - Display each event in sequence
7. For each event:
   - Clear display
   - Load event image (with fallback to blank.bmp)
   - Position image at top-right (x=37, y=2)
   - Calculate bottom-aligned text positions
   - Create top text label (DIMMEST_WHITE)
   - Create bottom text label (custom color)
   - Display for duration
   - Memory cleanup between events
```

### Event Images

**Location:** `/img/events/`
**Format:** BMP (4-bit indexed color)
**Size:** 25 pixels wide × 28 pixels tall

**Example Images:**
- `cake.bmp` - Birthday celebrations
- `heart.bmp` - Valentine's Day, anniversaries
- `new_year.bmp` - New Year celebrations
- `blank.bmp` - Fallback/generic events

**Note:** Events and schedules use different image sizes:
- Events: 25×28 (smaller, top-right positioning)
- Schedules: 40×28 (larger, occupies right half)

### Integration with Main Loop

**Priority Logic:**
1. **Schedules** (highest) - Override all displays when active
2. **Normal Rotation:**
   - Forecast: 60 seconds
   - Weather: 240 seconds
   - **Events: Remaining time** (if any events today and active)
   - Stocks: 60 seconds

**Typical Cycle (360s total):**
```
Forecast: 60s
Weather: 240s
Events: 0-60s (if events exist and active, uses remaining time)
Stocks: 60s
```

**Event Display Duration:**
- Allocated from remaining cycle time
- If no events: Cycle ends after weather
- If 1 event: Gets full remaining time
- If multiple events: Time split equally (min duration enforced)

### Configuration

**settings.toml:**
```toml
# GitHub Events (optional - ephemeral, date-specific events)
GITHUB_EVENTS_URL = "https://raw.githubusercontent.com/user/repo/main/ephemeral_events.csv"
```

**config.csv:**
```csv
setting,value
display_events,true
```

**New Setting:**
- `display_events` - Toggle events display on/off (true/false)

### Implementation Plan

**Step 6.1: Event Loading & Parsing** ⏳ NEXT
- [ ] Create `event_loader.py` (inline CSV parsing)
- [ ] Implement local events loading
  - [ ] Parse MM-DD format dates
  - [ ] Convert to MMDD key (e.g., "01-15" → "0115")
  - [ ] Parse event data: [top, bottom, image, color, start_hour, end_hour]
  - [ ] Store in dictionary: {"0115": [event1, event2, ...]}
- [ ] Implement GitHub ephemeral events loading
  - [ ] Parse YYYY-MM-DD format dates
  - [ ] Skip past events (date < current date)
  - [ ] Convert to MMDD key for merging
  - [ ] Fetch once at startup only
- [ ] Merge events dictionaries (permanent + ephemeral)
- [ ] Event activation detection
  - [ ] Check if today has any events
  - [ ] Filter by current hour (time window)
  - [ ] Return active events list

**Step 6.2: Event Display Rendering** ⏳ NEXT
- [ ] Create `display_events.py`
- [ ] Implement `show_event()` function (inline rendering)
  - [ ] Clear display
  - [ ] Load event image (25×28, LRU cache)
  - [ ] Image fallback to blank.bmp
  - [ ] Position image at top-right (x=37, y=2)
  - [ ] Calculate bottom-aligned text positions (inline helper)
  - [ ] Create text labels (top: DIMMEST_WHITE, bottom: custom color)
  - [ ] Sleep for duration
- [ ] Handle multiple events
  - [ ] Split time equally between events
  - [ ] Enforce minimum duration per event
  - [ ] Rotate through events in sequence
- [ ] Special birthday handling (optional, may simplify)

**Step 6.3: Bottom-Aligned Text Helper**
- [ ] Create inline helper function for text positioning
- [ ] Calculate positions based on:
  - [ ] Font bounding box heights
  - [ ] Display height (32 pixels)
  - [ ] Bottom margin (configurable)
  - [ ] Line spacing between top and bottom text
- [ ] Return (top_y, bottom_y) positions

**Step 6.4: Config Integration**
- [ ] Add `display_events` toggle to config.csv
- [ ] Add to ConfigState in config_manager.py
- [ ] Create `should_show_events()` getter function
- [ ] Add to config logging output

**Step 6.5: Main Loop Integration**
- [ ] Add event check to main cycle
- [ ] Load events at startup (permanent + ephemeral)
- [ ] Check for active events after weather display
- [ ] If events active:
  - [ ] Calculate remaining cycle time
  - [ ] Call `show_event()` with duration
  - [ ] Handle multiple events (time splitting)
- [ ] If no events or inactive:
  - [ ] Skip events, continue to stocks

**Step 6.6: Testing & Validation**
- [ ] Create test events.csv with various dates
- [ ] Test local recurring events (MM-DD format)
- [ ] Test GitHub ephemeral events (YYYY-MM-DD format)
- [ ] Test time window filtering (start_hour/end_hour)
- [ ] Test multiple events per day (time splitting)
- [ ] Test image loading and fallback
- [ ] Test color rendering (various colors)
- [ ] Test bottom-aligned text positioning
- [ ] Verify events skip when inactive (outside time window)
- [ ] Verify past events auto-skipped from GitHub
- [ ] Memory stability check
- [ ] Integration with forecast/weather/stocks cycle

### Technical Details

**Display Function Structure:**
```python
def show_events(rtc, duration):
    # Get active events for today
    active_events = get_active_events(rtc)

    if not active_events:
        return False  # No events to show

    # Split duration between events
    event_duration = max(duration // len(active_events), MIN_EVENT_DURATION)

    for event_data in active_events:
        # Clear display
        clear_display()

        # Load image (LRU cache)
        image_path = f"{Paths.EVENT_IMAGES}/{event_data[2]}"
        bitmap = load_image_with_fallback(image_path, Paths.BLANK_EVENT)

        # Position image (top-right)
        image_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        image_grid.x = 37
        image_grid.y = 2
        state.main_group.append(image_grid)

        # Calculate text positions (inline)
        top_y, bottom_y = calculate_bottom_aligned_positions(
            font, event_data[0], event_data[1],
            display_height=32, bottom_margin=2, line_spacing=2
        )

        # Create text labels
        top_label = Label(font, text=event_data[0], color=Colors.DIMMEST_WHITE, x=1, y=top_y)
        bottom_label = Label(font, text=event_data[1], color=get_color(event_data[3]), x=1, y=bottom_y)

        state.main_group.append(top_label)
        state.main_group.append(bottom_label)

        # Display for duration
        time.sleep(event_duration)
```

**Key Design Decisions:**
- **No weather integration** (simpler than schedules)
- **No progress bar** (not time-based like schedules)
- **Bottom-aligned text** (always stays above bottom margin)
- **LRU image cache** (reuse cache from schedules/weather)
- **Inline text calculation** (keep stack depth low)
- **Time window filtering** (show events only during active hours)

**Success Criteria:**
- [ ] Events display at correct dates
- [ ] Time window filtering works (inactive events skipped)
- [ ] Multiple events per day rotate correctly
- [ ] Images load with proper fallback
- [ ] Text aligns at bottom correctly
- [ ] Colors render properly
- [ ] GitHub ephemeral events load (past dates skipped)
- [ ] Local recurring events load
- [ ] Integration with cycle rotation works
- [ ] Memory remains stable
- [ ] No stack exhaustion

---

## Phase 7: Transit & Production (Future)

### Step 7.1: CTA Transit Display
- [ ] Create `transit_api.py`
- [ ] Fetch train/bus arrivals from CTA APIs
- [ ] Transit display rendering
- [ ] Time-based activation (commute hours)

### Step 7.2: Enhanced Clock Display
- [ ] Fallback clock display (when all displays disabled)
- [ ] Large centered time display
- [ ] Optional date display

### Step 7.3: Production Deployment
- [ ] 72-hour stability test (full weekend)
- [ ] Test all display priority logic
- [ ] Test transit during commute hours
- [ ] Monitor for any errors or crashes
- [ ] Deploy to production matrix
- [ ] 7-day validation test

**Success Criteria:** All displays work, proper rotation and priority, 7+ day uptime

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