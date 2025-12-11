# Pantallita 3.0 - Refactored Architecture

## Current Status: Phase 0 - Bootstrap Testing

**Goal:** Validate CircuitPython 10 foundation (1-hour stability test)

## Why v3.0?

v2.5.0 hits pystack exhaustion when adding features (6175 lines, 8-10 stack depth)

v3.0 fixes this with flat architecture (2-level stack depth, 94% headroom)

## Architecture

- **Flat module calls** - No nesting
- **Inline display code** - No helper functions
- **CircuitPython 10** - 32-level stack (+28% vs CP9)

## Files

- `code.py` - Main loop
- `config.py` - Constants
- `state.py` - Global state  
- `hardware.py` - Init functions
- Bootstrap test: Shows clock for 1-hour validation

## Next Steps

1. ✅ Create bootstrap files
2. ⏳ Run 1-hour test
3. → Implement weather_api.py
4. → Implement display_weather.py

## If Chat Ends

Share this: "Working on Pantallita v3.0 Phase 0 bootstrap test. Refactoring from 6K monolith to fix pystack exhaustion. See README.md"

**Repo:** https://github.com/strategeekal/pantallita  
**Branch:** bootstrap-test
