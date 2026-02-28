"""
Detailed Analysis of Cold Start Sequence from MegaLogViewer Graph
Analyzing the TRENDS and TRANSITIONS, not just endpoints
"""

print("="*80)
print("COLD START SEQUENCE ANALYSIS - FULL TIMELINE")
print("="*80)

print("""
Time Range: -7.667s to 18.403s (26 second total capture)

================================================================================
PHASE 1: PRE-CRANK (-7.667s to ~0s)
================================================================================
RPM:     0 rpm (engine off)
MAP:     ~98 kPa (atmospheric - engine not running)
TPS:     0% (closed throttle)
AFR:     19.7 (reading atmospheric oxygen - meaningless)
CLT:     30°C (cold engine)
MAT:     11°C (very cold intake air - 52°F)
PW:      0 ms (no injection)
VE:      0% (no calculation yet)
IAC:     High values initially (preparing for start)

STATUS: Engine cold, ready to crank

================================================================================
PHASE 2: CRANK & FIRE (~0s to ~2s) - THE CRITICAL MOMENT
================================================================================

What the LINES show:

1. RPM (White line - Top panel):
   - SPIKE from 0 to 603 rpm VERY QUICKLY
   - Sharp vertical climb = engine fired immediately
   - Peak at 603 rpm around 1-2 seconds
   → ENGINE CAUGHT AND FIRED!

2. MAP (Red line - Top panel):
   - DROPS from 98 kPa (atmo) to ~52 kPa minimum
   - This drop = engine creating vacuum = IT'S RUNNING
   - Then settles around 58 kPa during idle attempt
   → Confirms engine is running, creating vacuum

3. TPS (Green line - Top panel):
   - Stays at 0.0% throughout
   - Multiple brief spikes visible (green vertical lines)
   - These are likely TPS noise or very brief throttle inputs
   → Throttle essentially closed

4. AFR (White line - Middle panel):
   - Starts at 19.7 (atmospheric O2)
   - DROPS SHARPLY when engine fires
   - Goes down to approximately 12.6 (rich, good for cold start!)
   - This is the white line steep descent
   → Initial mixture was GOOD and RICH

5. CLT (Red line - Lower panel):
   - Flat at 30°C (doesn't change much in 26 seconds)
   - Confirms COLD start condition

6. MAT (Red line - Lower panel):
   - Flat at 11°C 
   - Very cold intake air

7. PW (White line - Bottom panel):
   - SPIKES from 0 to 3.175 ms (MAX)
   - This spike = CRANKING ENRICHMENT + PRIMING active
   - Shows large fuel pulse during crank
   → Cranking fuel delivery was GOOD

8. VE1 (Green line - Bottom panel):
   - Jumps from 0 to ~44% initially
   - Shows engine began pulling air
   → VE calculation started

ANALYSIS OF PHASE 2:
✓ Engine fired SUCCESSFULLY
✓ Initial enrichment was GOOD (AFR went rich to ~12.6)
✓ Cranking fuel (3.175ms PW) was adequate
✓ MAP vacuum created = engine running
✓ RPM peaked at 603 - marginal but it caught

================================================================================
PHASE 3: POST-START DECLINE (~2s to ~10s) - WHERE IT GOES WRONG
================================================================================

What the LINES show:

1. RPM (White line):
   - After peak of 603, STAYS FLAT around 540-560 rpm
   - NO RECOVERY - doesn't climb to normal idle
   - Struggles to maintain even this low speed
   → Engine can't build RPM, stuck at cranking speed

2. MAP (Red line):
   - After initial drop to 52 kPa, rises to ~58 kPa
   - Slightly higher = less vacuum = weaker running
   → Engine not pulling hard, weak combustion

3. AFR (White line - CRITICAL):
   - After rich spike (~12.6), begins CLIMBING
   - Gradually increases from 12.6 → 13.0 → 13.3
   - White line ascending = getting LEANER over time
   → ENRICHMENT IS TAPERING OFF TOO FAST!

4. PW (White line - Bottom):
   - After 3.175ms spike, DROPS to ~2.4ms
   - Then continues gradual DECLINE to 2.329ms
   - Pulse width reducing = less fuel
   → ASE (After-Start Enrichment) DECAYING

5. VE (Green line - Bottom):
   - Drops from 44% to 39%
   - Lower VE = less efficient air consumption
   - At low RPM, VE calculation struggles
   → Engine not breathing well at 540 RPM

6. IAC (Green value):
   - Shows 84 steps at end
   - IAC trying to open to add air and raise RPM
   - But RPM not responding
   → IAC can't compensate for lean condition

THE PROBLEM REVEALED:
========================
After initial successful fire with rich mixture (AFR ~12.6):
- ASE enrichment TAPERS OFF too quickly (PW: 3.175 → 2.329 ms)
- AFR climbs from 12.6 to 13.3 (TOO LEAN for cold engine at 30°C)
- RPM can't climb from 540-600 to normal idle (800-1000)
- Engine stuck in "barely running" state

================================================================================
PHASE 4: STRUGGLING IDLE (~10s to 18.403s) - CURRENT STATE
================================================================================

Final steady state:
- RPM: 541 (far too low)
- AFR: 13.3 (too lean for 30°C cold engine)
- PW: 2.329 ms (insufficient fuel)
- VE: 39% (low efficiency)
- MAP: 58 kPa (weak vacuum)
- IAC: 84 steps (trying to help but can't fix lean mixture)

Engine is running but CANNOT SUSTAIN PROPER IDLE because:
1. Not enough fuel (AFR 13.3 vs needed 11.5-12.0)
2. RPM too low to generate proper airflow
3. Cold engine needs MORE enrichment, not less

================================================================================
ROOT CAUSE ANALYSIS
================================================================================

INITIAL START: SUCCESSFUL ✓
- Cranking enrichment worked (3.175ms PW)
- Engine fired immediately (603 RPM spike)
- Initial AFR was rich enough (~12.6)

FAILURE POINT: ASE TAPER TOO AGGRESSIVE ✗
- After-Start Enrichment decays too fast
- PW drops from 3.175 → 2.329 ms in ~5-10 seconds
- AFR climbs from 12.6 → 13.3 (getting leaner)
- At 30°C, engine STILL NEEDS rich mixture (11.5-12.0 AFR)

SECONDARY ISSUE: IDLE RPM TARGET TOO LOW ✗
- Engine stuck at 540-600 RPM
- Normal idle should be 900-1000 RPM
- At 540 RPM, combustion is inefficient
- VE is only 39% - not enough airflow/power

TERTIARY ISSUE: WARMUP ENRICHMENT INSUFFICIENT ✗
- At 30°C CLT, needs ongoing enrichment
- Current warmup table not providing enough
- Should maintain AFR 11.5-12.0 until warmer

================================================================================
SOLUTIONS - SPECIFIC TUNERSTUDIO ADJUSTMENTS
================================================================================

PRIORITY 1: EXTEND ASE (AFTER-START ENRICHMENT)
Location: Tuning → Acceleration Enrichment → After-Start Enrichment (ASE)

Current behavior: ASE tapers from 100% to 0% too quickly
Change:
  - Increase ASE duration from current (likely 3-5s) to 10-15 seconds
  - Increase ASE amount at 30°C by 20-30%
  - Slower decay rate
  
Target: Keep PW around 2.8-3.0ms for first 10-15 seconds
Result: AFR stays at 11.5-12.0 instead of climbing to 13.3

PRIORITY 2: INCREASE WARMUP ENRICHMENT TABLE
Location: Tuning → Warmup Enrichment (or Fuel → Enrichments → Warmup)

Current: Insufficient at 30°C CLT
Change:
  - At 30°C: increase from current value by +20-25%
  - At 20-40°C range: add +15-20% across the board
  
Target: Maintain AFR 11.5-12.5 while engine is below 60°C
Result: Engine has enough fuel to sustain combustion

PRIORITY 3: RAISE IDLE TARGET RPM FOR COLD ENGINE
Location: Idle → Idle RPM Target vs CLT (or similar)

Current: Target appears to be 550-600 RPM at 30°C (too low)
Change:
  - At 30°C CLT: set target to 950-1000 RPM
  - At 0-40°C range: set targets to 900-1000 RPM
  - Above 60°C: can lower to normal 800 RPM
  
Target: Engine runs at 950 RPM when cold, providing better airflow
Result: VE improves, combustion more stable, easier to maintain

PRIORITY 4: TUNE IAC FOR COLD START
Location: Idle → IAC Settings / IAC vs CLT

Current: IAC at 84 steps but RPM not responding
Change:
  - Increase IAC cold start position (0-40°C) by 10-20 steps
  - Increase IAC P-gain for faster response
  - Ensure IAC can open more when cold
  
Target: IAC opens more aggressively when cold to hit RPM target
Result: More airflow, helps reach 900+ RPM target

PRIORITY 5: VERIFY/ADJUST VE TABLE AT LOW RPM
Location: Tuning → VE Table

Current: VE showing 39% at 540 RPM / 58 kPa
Change:
  - Check VE table cells at 500-800 RPM, 50-70 kPa range
  - May need +5-10% in these cells
  - Low RPM/low load area often needs adjustment
  
Target: Better VE calculation at low idle speeds
Result: More accurate fuel delivery calculation

================================================================================
TESTING SEQUENCE
================================================================================

TEST 1: Quick Fix (Do this first)
1. Increase Warmup Enrichment at 30°C by +25%
2. Increase Idle Target RPM at 30°C to 950
3. Increase ASE duration to 10 seconds
4. Start engine and log

Expected result:
- RPM should climb to 800-900 instead of 540
- AFR should stay 11.5-12.5 instead of 13.3
- Engine should idle smoothly instead of struggling

TEST 2: Fine Tuning (After Test 1 works)
1. Adjust IAC settings if RPM still doesn't hit target
2. Fine-tune VE table at low RPM if AFR still drifts
3. Adjust ASE taper rate for smoothest transition

================================================================================
WHAT YOUR GRAPH TELLS ME
================================================================================

YOUR TUNE IS CLOSE! The engine:
✓ Fires immediately (good crank enrichment)
✓ Initially runs rich enough (~12.6 AFR)
✓ Creates proper vacuum (52-58 kPa MAP)

But it FAILS because:
✗ Enrichment tapers too fast (AFR 12.6 → 13.3)
✗ Idle target too low (540 vs needed 900 RPM)  
✗ Not enough ongoing warmup fuel at 30°C

This is a TUNING issue, not a mechanical issue. The engine CAN run (it did for
26 seconds!), it just needs more fuel and higher idle when cold.

Make these changes and you should see RPM climb to 900+ and AFR stay rich
around 12.0, giving you a smooth cold start and stable idle.

================================================================================
""")

print("\nAnalysis complete. Would you like me to help locate these specific")
print("tables/settings in your TunerStudio configuration?")
