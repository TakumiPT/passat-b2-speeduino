"""
Analysis of After-Start Enrichment (ASE) Settings vs Log Data
"""

print("="*80)
print("AFTER-START ENRICHMENT (ASE) ANALYSIS - FOUND THE PROBLEM!")
print("="*80)

print("""
YOUR ASE SETTINGS (from screenshots):
======================================

ASE ENRICHMENT AMOUNT (%):
  -20°C: 150%
    0°C: 120%
   40°C: 90%
   80°C: 60%
   
   At 30°C (interpolated): ~100% (2.0x fuel multiplier)

ASE DURATION (seconds):
  -20°C: 25 seconds
    0°C: 20 seconds
   40°C: 15 seconds
   80°C: 6 seconds
   
   At 30°C (interpolated): ~17 seconds

Transition time to disable: 1.0 second

Note: "Common values are 5% when hot to 50% when cold"
Your settings: 60% when hot, 90-150% when cold (higher than typical)
""")

print("="*80)
print("COMPARING ASE SETTINGS TO YOUR LOG DATA")
print("="*80)

print("""
FROM YOUR DATA LOG:
===================
- Engine starts at: t=10.7s (RPM jumps to 534)
- Initial PW after start: 3.17ms
- PW at t=27.5s: ~2.5ms
- PW at t=38.2s: 1.98ms
- Time to decay 38%: 27.5 seconds

ASE SHOULD PROVIDE:
===================
At 30°C:
- Enrichment: 100% extra fuel (2.0x multiplier)
- Duration: 17 seconds
- After 17 seconds: ASE should taper off over 1 second

WHAT SHOULD HAPPEN:
===================

t=0 to 10.7s: CRANKING
  - Cranking enrichment: 540% (5.4x)
  - PW: ~6.3ms during crank

t=10.7s: ENGINE FIRES (RPM > 300)
  - Cranking enrichment STOPS
  - ASE activates: 100% enrichment (2.0x)
  - Warmup enrichment: Unknown (need to see table)
  - Combined PW should be: base × warmup × ASE
  
t=10.7s to 27.7s: ASE ACTIVE (17 seconds)
  - ASE should hold 100% enrichment
  - PW should stay HIGH (~3.5-4.0ms)
  - AFR should stay at 11.5-12.5:1
  
t=27.7s to 28.7s: ASE TAPER (1 second transition)
  - ASE reduces from 100% to 0%
  - PW tapers down gradually
  - Warmup enrichment takes over
  
t=28.7s onwards: WARMUP ONLY
  - Only warmup enrichment active
  - PW determined by warmup table
  - Should still be enriched at 30°C

YOUR ACTUAL BEHAVIOR:
=====================

t=10.7s: Engine fires
  - PW: 3.17ms (reasonable with ASE)
  
t=10.7s to 27.5s: Should be ASE active period
  - PW decays from 3.17ms to 2.5ms (21% drop)
  - ASE should hold steady, but it's DECAYING!
  
t=27.5s to 38.2s: Should be post-ASE period
  - PW continues dropping to 1.98ms
  - AFR goes lean: 13.6-14.7:1
  
PROBLEM IDENTIFIED:
===================

Your ASE is configured for:
  - 17 seconds duration at 30°C
  - 100% enrichment amount
  
But in your log:
  - Fuel starts decaying IMMEDIATELY after start
  - By 17 seconds, PW already dropped 15-20%
  - By 27 seconds, PW dropped 38%
  
This means: ASE IS NOT WORKING AS CONFIGURED!
""")

print("="*80)
print("WHY ASE IS FAILING - ROOT CAUSE ANALYSIS")
print("="*80)

print("""
HYPOTHESIS 1: VACUUM LEAK OVERWHELMS ASE
=========================================

Your ASE is set to add 100% extra fuel (2.0x)
This should be plenty for cold start at 30°C

But vacuum leak adds ~34% extra AIR (72 L/min unmetered)

Math:
  Normal air at IAC 88 steps: 210 L/min
  Leak adds: 72 L/min
  Total air: 282 L/min (+34%)
  
  ECU thinks it needs fuel for: 210 L/min
  ECU adds ASE 100%: doubles fuel
  But actual air is 282 L/min (34% more)
  
  Expected AFR with ASE: 12.0:1 (if no leak)
  Actual AFR with leak: 12.0 × 1.34 = 16:1 (way too lean!)
  
  To compensate, ECU may be:
  - Reducing ASE based on O2 sensor feedback
  - Closing IAC (88 steps) to reduce total air
  - Unable to add enough fuel for leak + cold

HYPOTHESIS 2: ASE TAPER STARTING TOO EARLY
===========================================

ASE duration: 17 seconds
But decay starts immediately

Possible causes:
  - ASE taper curve configured wrong
  - ASE tied to RPM threshold (if RPM varies, ASE varies)
  - Bug in Speeduino ASE implementation
  - ASE being overridden by closed-loop O2 control

HYPOTHESIS 3: WARMUP ENRICHMENT TOO LOW
========================================

ASE adds 100% extra
But if base warmup enrichment is too low, even 2x isn't enough

Example:
  Base fuel needed at 30°C: 3.5ms
  Warmup enrichment: 110% (1.1x)
  ASE: 100% (2.0x)
  Result: 3.5 × 1.1 × 2.0 = 7.7ms during ASE
  
  But your PW is only 3.17ms at start
  This suggests base calculation is too low
  Or warmup enrichment is way below 110%

MOST LIKELY: COMBINATION OF ALL THREE
======================================

1. Vacuum leak adds 34% extra air (proven by MAP)
2. Warmup enrichment is insufficient for 30°C
3. ASE duration/amount not enough to overcome 1+2
4. ECU closes IAC to 88 steps trying to compensate
5. Result: Lean AFR, low RPM, struggling engine
""")

print("="*80)
print("WHAT WE STILL NEED TO SEE")
print("="*80)

print("""
CRITICAL TABLE STILL MISSING:
==============================

WARMUP ENRICHMENT TABLE
  Location: "Fuel" → "Warmup Enrichment" or similar
  Shows: Fuel multiplier (%) vs Coolant Temperature
  
  Need to know: What's the multiplier at 30°C?
  
  Typical values:
    -20°C: 180-250%
      0°C: 150-180%
     30°C: 130-160%  ← YOUR TEMP, need this value!
     60°C: 110-120%
     80°C: 100-105%
     
  If your 30°C value is < 130%, it's TOO LOW
  Combined with vacuum leak, this explains everything

IDLE TARGET RPM TABLE
  Location: "Idle" → "Target RPM" or "IAC Settings"
  Shows: Target idle RPM vs Coolant Temperature
  
  Need to know: What RPM is ECU trying to achieve at 30°C?
  
  Typical for cold start:
    -20°C: 1200-1400 RPM (very high fast idle)
      0°C: 1100-1200 RPM
     30°C: 900-1000 RPM  ← Should be here
     60°C: 800-850 RPM
     80°C: 750-800 RPM (normal warm idle)
     
  If your target at 30°C is < 900, that's too low
  Current actual: 527 RPM (way below any reasonable target)
""")

print("="*80)
print("MATHEMATICAL PROOF - WHY ASE FAILS WITH VACUUM LEAK")
print("="*80)

print("""
Let's calculate what SHOULD happen vs what DOES happen:

SCENARIO A: NO VACUUM LEAK (ideal)
===================================

At 30°C cold start:
  1. Base fuel calculation: 1.5ms (example)
  2. Warmup enrichment (assume 140%): 1.5 × 1.4 = 2.1ms
  3. ASE enrichment (100%): 2.1 × 2.0 = 4.2ms
  4. Air entering: 210 L/min (IAC at ~30 steps, wide open)
  5. AFR: 12.0:1 (perfect for cold start)
  6. RPM: 950 (reaches target)
  7. After 17s, ASE ends: PW drops to 2.1ms
  8. Engine now warm enough, continues at 750 RPM on warmup only

SCENARIO B: WITH VACUUM LEAK (your situation)
==============================================

At 30°C cold start WITH 34% extra air from leak:
  1. Base fuel calculation: 1.5ms (ECU doesn't know about leak)
  2. Warmup enrichment (assume 120%): 1.5 × 1.2 = 1.8ms
  3. ASE enrichment (100%): 1.8 × 2.0 = 3.6ms
  4. Air entering: 282 L/min (210 metered + 72 from leak)
  5. ECU adds fuel for 210 L/min only
  6. Actual AFR: 12.0 × (282/210) = 16.1:1 (way too lean!)
  7. RPM: 534 (cannot reach target due to lean mixture)
  8. ECU detects RPM too low, closes IAC to 88 steps
  9. Metered air reduces to ~150 L/min
  10. Total air now: 150 + 72 = 222 L/min
  11. ECU adds fuel for 150 L/min: 1.8 × 2.0 = 3.6ms
  12. Actual AFR: 12.0 × (222/150) = 17.8:1 (even worse!)
  13. ECU may start reducing ASE due to lean condition
  14. PW decays to 3.17ms, then 2.5ms, then 1.98ms
  15. AFR stays lean at 13.6-14.7:1
  16. RPM stuck at 527

THE MATH SHOWS:
===============

Even with ASE at 100% (2.0x multiplier):
  - Vacuum leak adds too much unmeasured air
  - ECU cannot compensate (doesn't know leak exists)
  - Closing IAC makes it worse (less metered air, same leak air)
  - ASE alone cannot fix this problem
  
FIX REQUIRED:
=============

Step 1: FIX VACUUM LEAK
  - Test brake booster (pinch test)
  - Replace leaking component
  - MAP will drop from 60 to 40 kPa
  - IAC will open from 88 to 20-30 steps
  - ASE will then work as designed

Step 2: CHECK WARMUP ENRICHMENT
  - If < 130% at 30°C, increase it
  - Should be 140-160% for reliable cold start
  - This works WITH ASE, not instead of

Step 3: POSSIBLY EXTEND ASE
  - After leak is fixed, test
  - If engine still struggles, extend ASE duration
  - Change from 17s to 25s at 30°C
  - Or increase enrichment from 100% to 120%
""")

print("="*80)
print("IMMEDIATE ACTION PLAN")
print("="*80)

print("""
DO THIS IN ORDER:
=================

1. VACUUM LEAK TEST (5 minutes)
   --------------------------------
   a) Start engine (will idle rough at 527 RPM)
   b) Connect laptop, open TunerStudio
   c) Watch MAP gauge (currently showing ~60 kPa)
   d) Pinch brake booster vacuum hose shut with pliers
   e) Observe MAP:
      - If drops to 40-45 kPa → LEAK FOUND in brake booster
      - If stays at 60 kPa → leak is elsewhere
   f) If leak found, order replacement brake booster/hose
   
2. SEND WARMUP ENRICHMENT TABLE (2 minutes)
   ------------------------------------------
   a) In TunerStudio, find "Warmup Enrichment" table
   b) Take screenshot showing % vs Coolant Temp
   c) Send screenshot
   d) I'll calculate exact adjustment needed
   
3. SEND IDLE TARGET RPM TABLE (2 minutes)
   ----------------------------------------
   a) Find "Idle Control" or "Target RPM" settings
   b) Screenshot showing target RPM vs Coolant Temp
   c) Send screenshot
   d) Verify target at 30°C is 900-1000 RPM

4. FIX VACUUM LEAK (1-2 hours)
   ----------------------------
   a) Replace brake booster or leaking component
   b) Start engine
   c) Verify MAP now reads 40-45 kPa
   d) Verify IAC opens to 20-40 steps
   e) Take new data log (same test, cold start at 30°C)
   
5. ANALYZE NEW LOG (10 minutes)
   -----------------------------
   a) Send new MLG file
   b) I'll analyze if AFR improved
   c) Check if RPM now reaches 700-800
   d) Determine if warmup enrichment adjustment needed

6. TUNE WARMUP ENRICHMENT IF NEEDED (30 minutes)
   -----------------------------------------------
   a) After leak fixed, if AFR still 13-14:1
   b) Increase warmup enrichment at 30°C
   c) Add 20-30% more fuel
   d) Test again
   e) Fine-tune until AFR = 12.0-12.5:1

EXPECTED RESULTS AFTER LEAK FIX:
=================================

MAP: 60 kPa → 40-45 kPa (vacuum restored)
IAC: 88 steps → 20-30 steps (opens for cold air)
AFR: 14.7:1 → 12.5-13.5:1 (better, may need warmup tune)
RPM: 527 → 700-850 (significant improvement)
PW: Should hold 3.0-3.5ms for full 17 seconds of ASE

After warmup enrichment adjustment (if needed):
AFR: → 11.5-12.5:1 (perfect for cold start)
RPM: → 900-1000 (reaches target fast idle)
Engine: Smooth, stable, no struggling
""")

print("="*80)
print("SUMMARY - ASE SETTINGS ARE OK, BUT VACUUM LEAK DEFEATS THEM")
print("="*80)

print("""
YOUR ASE CONFIGURATION:
=======================
Enrichment at 30°C: 100% (2.0x multiplier) ✓ GOOD
Duration at 30°C: 17 seconds ✓ REASONABLE
Transition time: 1.0 second ✓ OK

These settings should work for normal cold start.

THE PROBLEM:
============
Vacuum leak adds 72 L/min (34%) unmeasured air
Even with ASE doubling fuel, total air is still 34% more than fuel
Result: AFR goes lean despite ASE
ECU fights back by closing IAC, making it worse

THE SOLUTION:
=============
1. Fix vacuum leak FIRST (test brake booster)
2. Then check warmup enrichment table
3. Adjust warmup if needed after leak is fixed
4. ASE settings can stay as-is (they're fine)

Your ASE is not broken - it's just overwhelmed by the vacuum leak.
Fix the leak, and ASE will work as designed.

DO THE BRAKE BOOSTER PINCH TEST NOW!
Then send warmup enrichment and idle target tables.
""")

print("="*80)
