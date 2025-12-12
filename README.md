# Pantallita 3.0

Complete rewrite of Pantallita with proper CircuitPython architecture to solve pystack exhaustion issues.

## Status: Phase 1 - Weather Display

**Current Goal:** Implement weather fetching and display

**Completed:**
- ✅ **Phase 0: Bootstrap** - Foundation validated (2+ hour test)
  - CircuitPython 10.0.1 stable on hardware
  - Display, RTC, WiFi, buttons all working
  - Timezone handling with DST support
  - Memory stable (no leaks)
  - 740 cycles without crashes

**In Progress:**
- ⏳ **Phase 1: Weather Display**
  - Create weather_api.py (fetch from AccuWeather)
  - Create display_weather.py (inline rendering)
  - Update code.py (show weather instead of clock)
  - Run 24-hour stability test

**Next Steps:**
1. Implement weather_api.py
2. Implement display_weather.py
3. Test weather display
4. 24-hour stability validation

---

## Phase 0 Lessons Learned

### What Worked
✅ Flat architecture - 2-level stack depth proven
✅ Module separation - Clean boundaries
✅ CircuitPython 10 - Stable, 28% more stack headroom
✅ Timezone with 2s delay - Reliable after socket pool initialization
✅ Fallback patterns - Default to CST when API fails

### Issues Encountered
⚠️ Socket timing - Need 2-second delay after WiFi for API calls
⚠️ Library dependencies - adafruit_ticks required by display_text in CP10

### Memory Baseline
- Startup: 2,000,672 bytes free
- Stabilized: ~1,995,000 bytes free
- Usage: ~5KB for runtime state (excellent)

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
Screeny/
├── code.py              # Main entry point (~200 lines)
│                        # - Calls modules directly, no nesting
│                        # - Hardware init, main loop only
│
├── config.py            # Constants (~400 lines) ✅ DONE
│                        # - Display, Colors, Paths, Timing
│                        # - Zero runtime cost (pure data)
│
├── state.py             # Global state (~200 lines) ✅ DONE
│                        # - Display objects, RTC, buttons
│                        # - HTTP session, caches
│
├── hardware.py          # Hardware init (~300 lines) ✅ DONE
│                        # - init_display(), init_rtc()
│                        # - connect_wifi(), init_buttons()
│                        # - Timezone handling with DST
│
├── weather_api.py       # Weather fetching (Phase 1) ⏳ NEXT
│                        # - fetch_current() - inline parsing
│                        # - Returns: {temp, uv, humidity, icon, condition}
│
├── display_weather.py   # Weather rendering (Phase 1) ⏳ NEXT
│                        # - show() - everything inline
│                        # - No helper functions
│
├── display_forecast.py  # Forecast rendering (Phase 2)
├── stocks_api.py        # Stock fetching (Phase 3)
├── display_stocks.py    # Stock rendering (Phase 3)
└── display_other.py     # Events, schedules, transit, clock

```
---

## Hardware

- **Controller:** Adafruit MatrixPortal S3 (ESP32-S3)
- **Display:** 2× RGB LED matrices (64×32 pixels)
- **RTC:** DS3231 real-time clock
- **Firmware:** CircuitPython 10.0.1
- **Memory:** 2MB SRAM (~1.6MB available)

---

## Libraries Installed

**Phase 0 (Bootstrap):**
- adafruit_bitmap_font/
- adafruit_display_text/
- adafruit_ticks.mpy (CP10 requirement)
- adafruit_ntp.mpy
- adafruit_ds3231.mpy
- adafruit_requests.mpy
- adafruit_bus_device/
- adafruit_register/
- adafruit_connection_manager.mpy

**Phase 1 (Weather) - To Install:**
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

# Future phases
TWELVE_DATA_API_KEY = "your-key"
CTA_API_KEY = "your-key"

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

## Testing Protocol

### Per-Phase Testing:
1. **Code review:** Check for stack depth violations
2. **Deploy:** Copy to MatrixPortal
3. **Monitor:** Watch serial console for errors
4. **Stability:** Run for target duration
5. **Memory:** Check for leaks every N cycles
6. **Validate:** All features work as expected

### Phase 0 Results:
- ✅ Duration: 123.3 minutes (2+ hours)
- ✅ Cycles: 740 without crashes
- ✅ Memory: 0.25% loss, stable
- ✅ WiFi: Connected entire duration
- ✅ Errors: Zero critical errors
- ⚠️ Timezone API needs 2s delay (fixed)

---

## Phase 1 Implementation Plan

### Step 1: Create weather_api.py

```python

# Fetch current weather from AccuWeather
# Returns: {temp, feels_like, uv, humidity, icon, condition}
# Inline parsing, no helper functions

```


### Step 2: Create display_weather.py

```python

# Show weather on display
# Everything inline: image load, text, bars, layout
# No helper functions

```

 

### Step 3: Update code.py

```python

# Replace clock cycle with weather cycle
# Call weather_api.fetch_current()
# Call display_weather.show()

```

 

### Step 4: Test

- Deploy to MatrixPortal
- Watch serial logs
- Run 24-hour stability test
- Validate weather data accuracy

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
   exhaustion. I've completed Phase 0 (bootstrap test). Currently starting
   Phase 1 (weather display). Here's the README: [paste this file]

   ```

2. **Current status:** Phase 1 - Implementing weather_api.py and display_weather.py

3. **Key files completed:**

   - config.py (constants)
   - state.py (global state)
   - hardware.py (init functions with timezone handling)
   - code.py (bootstrap test - shows clock)

4. **Next steps:**

   - Create weather_api.py (fetch from AccuWeather)
   - Create display_weather.py (inline rendering)
   - Update code.py (replace clock with weather)

---

**Repository:** https://github.com/strategeekal/pantallita
**Branch:** bootstrap-test (Phase 0 complete)
**Next Branch:** weather-display (Phase 1)
**Last Updated:** 2025-12-11
**CircuitPython Version:** 10.0.1