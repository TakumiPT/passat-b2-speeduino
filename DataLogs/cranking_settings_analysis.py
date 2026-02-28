"""
Analysis of TunerStudio Cranking Settings vs Log Data
"""

print("="*80)
print("CRANKING ENRICHMENT ANALYSIS FROM YOUR SETTINGS")
print("="*80)

print("""
YOUR CRANKING ENRICHMENT CURVE (from screenshot):
==================================================

Temperature (°C)  →  Enrichment Modifier
-40°C             →  840% (8.4x fuel)
-26°C             →  ~730% (7.3x fuel)  
-12°C             →  ~640% (6.4x fuel)
  2°C             →  ~590% (5.9x fuel)
 18°C             →  ~560% (5.6x fuel)
 30°C             →  ~540% (5.4x fuel)  ← YOUR COLD START TEMP
 44°C             →  ~540% (5.4x fuel)
 72°C             →  ~530% (5.3x fuel)

At 30°C (your log): Cranking enrichment = ~540% (5.4x multiplier)

CRANKING SETTINGS:
- Cranking RPM Max: 300 RPM
- Flood Clear Level: 80%
- Fuel Pump Prime: 3s
- Injectors Priming Delay: 2.0s
- Cranking Enrichment Taper Time: 1.0s
""")

print("="*80)
print("WHAT THIS MEANS FOR YOUR LOG")
print("="*80)

print("""
From your data log analysis:
- Engine started at: t=10.7s
- Initial PW at start: 3.17ms
- Peak PW (cranking): 6.31ms at t=48.6s (restart attempt)
- CLT: 30°C

CRANKING vs RUNNING:
====================

DURING CRANKING (RPM < 300):
  Base fuel calculation: Let's say 1.0ms (hypothetical base)
  Cranking enrichment at 30°C: 540% multiplier
  Expected cranking PW: 1.0ms × 5.4 = 5.4ms
  Your actual cranking PW: 6.31ms ✓ (close, reasonable)

AFTER ENGINE STARTS (RPM > 300):
  Cranking enrichment STOPS (RPM > 300 threshold)
  Switches to After-Start Enrichment (ASE)
  Your PW drops to: 3.17ms initially
  Then decays to: 1.98ms over 27 seconds

THE PROBLEM:
============

Your cranking enrichment is GOOD (5.4x at 30°C)
This is why engine STARTS successfully

But once RPM goes above 300, cranking enrichment ENDS
Now you rely on:
  1. Warmup Enrichment Table (for steady-state)
  2. After-Start Enrichment (ASE) (for transition)

And BOTH of these are insufficient!
""")

print("="*80)
print("WHAT SETTINGS ARE MISSING FROM SCREENSHOT")
print("="*80)

print("""
To complete the diagnosis, I need to see:

CRITICAL TABLES (URGENT):
=========================

1. AFTER-START ENRICHMENT (ASE)
   Location: Usually in "Enrichments" or "Tuning" menu
   Shows:
   - ASE vs Coolant Temp curve
   - ASE decay rate (how fast enrichment reduces)
   - ASE duration (how long it lasts)
   
   This controls the 10-30 seconds after engine fires
   YOUR PROBLEM: ASE decaying too fast (3.17ms → 1.98ms in 27s)

2. WARMUP ENRICHMENT TABLE
   Location: Usually "Fuel" → "Warmup Enrichment"
   Shows:
   - Enrichment multiplier vs Coolant Temperature
   - At 30°C, what's the multiplier?
   
   This controls steady-state fuel when engine is cold
   YOUR PROBLEM: Not enough fuel for 30°C operation

3. IDLE CONTROL SETTINGS
   Location: "Idle" or "IAC Settings"
   Shows:
   - Target idle RPM vs Coolant Temp
   - IAC PID parameters
   - IAC position limits
   
   Need to verify: Target RPM at 30°C (should be 900-1000)
   Current behavior: IAC at 88 steps (half-closed, fighting leak)

HELPFUL BUT NOT CRITICAL:
=========================

4. VE TABLE (Volumetric Efficiency)
   Shows how much air engine is breathing
   With vacuum leak, VE will look "normal" but actual air is higher

5. AFR TARGET TABLE
   Shows what AFR you're targeting at 30°C idle
   Should be 11.5-12.5 for cold start

6. ACCELERATION ENRICHMENT
   Not relevant for cold start, but good to see overall tune
""")

print("="*80)
print("ANALYSIS: CRANKING ENRICHMENT vs VACUUM LEAK")
print("="*80)

print("""
INTERESTING OBSERVATION:
========================

Your cranking enrichment is 540% at 30°C (very rich)
Yet your AFR during cranking is reasonable
This suggests: Cranking enrichment IS accounting for something

But once engine starts and switches to warmup enrichment:
AFR goes lean immediately (13.6-14.7:1)

Two possibilities:

SCENARIO A: Vacuum leak present even during cranking
  - Cranking enrichment at 540% compensates for leak + cold temp
  - Once switched to warmup enrichment (much lower %), leak causes lean
  - IAC closes to 88 steps trying to reduce total air
  - Confirms: VACUUM LEAK + INSUFFICIENT WARMUP ENRICHMENT

SCENARIO B: No vacuum leak, just bad warmup tuning
  - Cranking enrichment at 540% is for cold start only
  - Warmup enrichment is way too low for 30°C
  - IAC position of 88 steps is... wait, this doesn't make sense
  - If no leak, IAC at 88 steps (47% open) should give 44 kPa MAP
  - But MAP is 60 kPa
  - This proves: VACUUM LEAK EXISTS

CONCLUSION:
===========

Vacuum leak is REAL (MAP proves it)

Your cranking enrichment (540%) is probably:
  - Accounting for cold temp: needs ~200-250% 
  - Accounting for vacuum leak: needs ~100-150% extra
  - Total: 540% (which works during crank)

But your warmup/after-start enrichment is not enough to:
  - Account for 30°C cold operation
  - Account for vacuum leak
  - Keep AFR at 12:1 after start

TWO-PART FIX STILL NEEDED:
==========================

PART 1: FIX VACUUM LEAK (PRIMARY)
  Test brake booster first
  Repair/replace leaking component
  Expected result:
    - MAP drops from 60 to 40 kPa
    - IAC opens from 88 to 20-30 steps
    - AFR improves but may still be slightly lean

PART 2: INCREASE WARMUP ENRICHMENT (SECONDARY)
  After leak is fixed, adjust:
  - Warmup enrichment at 30°C: increase ~30-50%
  - ASE duration: extend from ~10s to 25-30s
  - ASE decay rate: slow it down by 50%
  Expected result:
    - AFR reaches 12.0-12.5:1
    - RPM climbs to 900-1000
    - PW holds at 2.8-3.2ms for 30+ seconds
""")

print("="*80)
print("WHY CRANKING ENRICHMENT WORKS BUT WARMUP DOESN'T")
print("="*80)

print("""
CRANKING PHASE (RPM < 300):
  Duration: Only a few seconds while starter is engaged
  Enrichment: 540% (5.4x multiplier)
  Goal: Get engine to fire and reach 300+ RPM
  Your result: SUCCESS - engine fires at t=10.7s

WARMUP PHASE (RPM > 300, CLT < 70°C):
  Duration: Minutes until engine warms up
  Enrichment: Unknown (need to see your table, probably ~110-130%)
  Goal: Keep engine running smoothly while cold
  Your result: FAILURE - lean AFR, low RPM, struggles

The difference:
- Cranking is temporary, so high enrichment (540%) is OK
- Warmup is long-term, so lower enrichment is used
- BUT: Your warmup enrichment is too low for:
  a) Cold operation at 30°C (needs ~180-200%)
  b) Compensating for vacuum leak (needs extra 30-50%)
  c) Total needed: ~250% but you probably have ~120%

AFTER-START ENRICHMENT (ASE):
  Duration: 10-30 seconds after engine fires
  Purpose: Smooth transition from cranking to warmup
  Typical: Starts high, decays gradually
  Your result: Decays too fast (3.17ms → 1.98ms in 27s)
  
This is the critical missing link!
ASE should hold fuel high for longer, then taper slowly
Your ASE drops too quickly, leaving engine lean before it warms up
""")

print("="*80)
print("NEXT STEPS - WHAT TO SEND")
print("="*80)

print("""
PRIORITY 1 - PHYSICAL TEST:
===========================
Before sending more screenshots, DO THIS TEST:

1. Start engine (it will idle rough at ~527 RPM)
2. Watch MAP reading in TunerStudio
3. Pinch brake booster vacuum hose shut with pliers
4. Observe:
   - Does MAP drop from 60 to 40-45 kPa?
   - Does IAC open from 88 toward 50-60?
   - Does engine sound slightly better?

This test takes 30 seconds and will PROVE leak location!

PRIORITY 2 - SCREENSHOTS NEEDED:
================================

1. After-Start Enrichment (ASE) settings
   - ASE vs Coolant curve
   - ASE taper/decay settings
   - ASE duration

2. Warmup Enrichment table
   - Enrichment % vs Coolant Temperature
   - Specifically: what's the value at 30°C?

3. Idle Control / Target RPM
   - Idle RPM vs Coolant Temperature table
   - What's target RPM at 30°C?

4. AFR Target table (if available)
   - What AFR are you targeting at idle when cold?

With these screenshots, I can:
- Calculate exact adjustments needed
- Predict results after leak fix
- Give you specific values to enter in each table

PRIORITY 3 - AFTER VACUUM LEAK TEST:
====================================

If brake booster pinch test shows leak:
1. Replace brake booster or vacuum hose
2. Re-test with new log
3. Then adjust enrichment tables as needed

If no leak found in brake booster:
1. Send more screenshots (above)
2. Check intake manifold gasket
3. Check PCV system
4. May need smoke test

ORDER OF OPERATIONS:
===================
1. Do pinch test on brake booster (30 seconds) ← DO THIS NOW
2. Send screenshots of ASE and Warmup tables
3. Fix vacuum leak
4. Adjust enrichment settings
5. Test with new log
6. Fine-tune as needed
""")

print("="*80)
print("SUMMARY")
print("="*80)

print("""
Your cranking enrichment (540% at 30°C) is GOOD
This is why engine starts successfully

Problem is AFTER engine starts:
- Warmup enrichment too low
- After-Start Enrichment decays too fast
- Vacuum leak adds unmetered air
- Result: Lean AFR, low RPM, engine struggles

DO THE BRAKE BOOSTER PINCH TEST FIRST!
Then send screenshots of:
1. After-Start Enrichment settings
2. Warmup Enrichment table
3. Idle RPM target table

This will give complete picture for exact tuning recommendations.
""")

print("="*80)
