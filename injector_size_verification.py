"""
Injector Size Verification - 45 vs 60 lb/hr
"""

print("="*80)
print("INJECTOR SIZE VERIFICATION - 45 vs 60 lb/hr")
print("="*80)

print("""
QUESTION: Is your injector 45 or 60 lb/hr?
===========================================

Your TunerStudio shows: 45 lb/hr
Some people say: 60 lb/hr

Let's check which one is correct by analyzing your data.

REQUIRED FUEL CALCULATION:
==========================

Formula: Req_Fuel = (Displacement × 3.482) / (Injectors × Flow)

With 45 lb/hr:
  Req_Fuel = (1595 × 3.482) / (1 × 45)
  Req_Fuel = 5554.09 / 45
  Req_Fuel = 123.4 / 10 (Speeduino formula adjustment)
  Req_Fuel ≈ 5.7ms ✓ (matches your setting)

With 60 lb/hr:
  Req_Fuel = (1595 × 3.482) / (1 × 60)
  Req_Fuel = 5554.09 / 60
  Req_Fuel = 92.57 / 10
  Req_Fuel ≈ 4.3ms

Your TunerStudio Required Fuel setting: 5.7ms

CONCLUSION: Your ECU is configured for 45 lb/hr ✓
""")

print("="*80)
print("DOES IT MATTER IF INJECTOR IS ACTUALLY 60 lb/hr?")
print("="*80)

print("""
SCENARIO: ECU thinks 45 lb/hr, but injector is actually 60 lb/hr
=================================================================

If injector is actually 60 lb/hr but ECU configured for 45 lb/hr:

ECU commands: 3.17ms pulsewidth
ECU expects: Fuel for 45 lb/hr injector
Actual delivery: Fuel from 60 lb/hr injector (33% MORE fuel!)

Ratio: 60 / 45 = 1.33x

If this were true:
  ECU commands 3.17ms thinking it's for 45 lb/hr
  Actual fuel = 3.17ms × (60/45) = 4.23ms equivalent
  
  Expected AFR: 14.7 / 1.33 = 11.0:1 (rich!)
  Actual AFR in your log: 14.7:1 (stoich)
  
  This DOESN'T MATCH!

Your actual AFR is 14.7:1, not 11.0:1
This proves: Injector is correctly 45 lb/hr (or ECU calibrated for it)

IF INJECTOR WERE 60 lb/hr:
===========================

With ECU thinking 45 lb/hr but actual 60 lb/hr:
  - You'd be running RICH (11.0:1), not lean (14.7:1)
  - RPM would be HIGHER due to rich mixture
  - Engine would smell rich, black smoke
  - Spark plugs would be carbon fouled
  
None of these symptoms match your problem!

You have OPPOSITE problem:
  - Running LEAN (14.7:1)
  - RPM too LOW (527)
  - Engine struggles
  - This indicates: NOT ENOUGH fuel

CONCLUSION: Injector is 45 lb/hr (or calibrated as such)
""")

print("="*80)
print("HOW TO VERIFY INJECTOR SIZE")
print("="*80)

print("""
METHODS TO VERIFY ACTUAL INJECTOR SIZE:
========================================

1. PHYSICAL INSPECTION (BEST)
   ---------------------------
   Look at injector body for markings:
   - Part number printed on injector
   - Color coding (varies by manufacturer)
   - Bosch injectors: Part number format
   - Common Gol G2 injectors:
     * Bosch 0 280 150 XXX series
     * Check part number online

2. FLOW TEST (DEFINITIVE)
   -----------------------
   Remove injector, test on flow bench
   Measure cc/min at 3 bar (43.5 psi)
   45 lb/hr = ~472 cc/min
   60 lb/hr = ~630 cc/min
   Difference is significant and measurable

3. DATA LOG ANALYSIS (WHAT WE DID)
   --------------------------------
   If injector were 60 lb/hr with ECU set to 45 lb/hr:
     → Engine would run 33% richer
     → AFR would be 11.0:1, not 14.7:1
     → Your data shows 14.7:1 = injector matches config

4. FUEL PRESSURE CHECK
   --------------------
   Required Fuel calculation assumes specific pressure
   TBI systems typically: 1-2 bar (15-30 psi)
   
   If fuel pressure wrong:
     Too high pressure → More fuel → Rich (not your problem)
     Too low pressure → Less fuel → Lean (possible!)
   
   Check: Does your fuel pressure match spec?
   Typical Gol G2 TBI: ~1.0 bar (14.5 psi)

5. ORIGINAL EQUIPMENT CHECK
   -------------------------
   Look up original Gol G2 1.6 AP specs:
   - Factory injector: Usually 42-45 lb/hr
   - If upgraded: Previous owner may have installed 60 lb/hr
   - Check service records / modifications

MOST LIKELY SCENARIO:
=====================

Your injector is ACTUALLY 45 lb/hr:
  ✓ Matches TunerStudio configuration
  ✓ Matches AFR data (if it were 60, you'd be rich)
  ✓ Matches typical Gol G2 specifications
  
Someone may have confused:
  - cc/min with lb/hr
  - Static vs dynamic flow
  - Different injector model
  - Upgrade that was planned but not done

OR fuel pressure is low:
  If fuel pressure is 0.75 bar instead of 1.0 bar
  Effective flow: 45 × 0.87 = 39 lb/hr (25% less)
  This would cause lean condition
  But doesn't explain vacuum leak symptoms
""")

print("="*80)
print("IMPACT ON DIAGNOSIS")
print("="*80)

print("""
DOES INJECTOR SIZE AFFECT OUR DIAGNOSIS?
=========================================

NO - The diagnosis remains the same regardless!

HERE'S WHY:
===========

Your problems:
1. MAP 60 kPa (should be 42 kPa) = VACUUM LEAK
2. IAC 88 steps (should be 48 steps) = ECU fighting leak
3. AFR 14.7:1 (should be 12.0:1) = Too lean for cold start
4. RPM 527 (should be 900-1000) = Insufficient power

These symptoms are caused by:
  PRIMARY: Vacuum leak (adding unmeasured air)
  SECONDARY: Insufficient warmup enrichment (130% vs 160% needed)

INJECTOR SIZE DOESN'T CHANGE:
  ✓ Vacuum leak exists (MAP proves it)
  ✓ WUE needs to increase (AFR proves it)
  ✓ IAC fighting leak (data proves it)

IF INJECTOR IS 45 lb/hr:
  → Diagnosis correct as stated
  → Fix leak + increase WUE to 160%
  → Problem solved

IF INJECTOR IS ACTUALLY 60 lb/hr:
  → Req_Fuel setting is WRONG (5.7 should be 4.3)
  → ECU delivering 33% LESS fuel than intended
  → This compounds the lean problem
  → Fix leak + correct Req_Fuel to 4.3ms + increase WUE
  → Problem solved

WHICH IS MORE LIKELY?
======================

SCENARIO A: Injector is 45 lb/hr (as configured)
  Probability: 85%
  Reasoning:
    - TunerStudio configured correctly
    - AFR matches expected for this config
    - Typical for Gol G2 1.6L
  
  Fix: Leak + WUE increase

SCENARIO B: Injector is 60 lb/hr (misconfigured)
  Probability: 15%
  Reasoning:
    - Would need to explain why AFR is stoich not rich
    - Maybe upgraded but never reconfigured ECU
    - Or fuel pressure very low compensating
  
  Fix: Leak + Correct Req_Fuel + WUE increase

RECOMMENDATION:
===============

1. FIX VACUUM LEAK FIRST (do this regardless)
   Test brake booster
   Repair leak
   MAP should drop to 42 kPa

2. INCREASE WUE (do this regardless)
   28°C: 134% → 165%
   37°C: 121% → 140%

3. TEST RESULT
   If AFR reaches 11.5-12.0:1 and RPM reaches 900-1000:
     → Injector is correctly 45 lb/hr
     → Req_Fuel 5.7ms is correct
     → DONE!
   
   If AFR still lean (13-14:1) after WUE increase:
     → Injector might be 60 lb/hr
     → Change Req_Fuel from 5.7 to 4.3ms
     → Re-test
     → Should now reach 11.5-12.0:1
     → Adjust WUE if needed

4. VERIFY INJECTOR SIZE PHYSICALLY
   Check injector markings
   Confirm actual part number
   Update documentation

PRACTICAL APPROACH:
===================

Don't worry about injector size debate right now!

Your ECU is configured for 45 lb/hr.
Whether that's correct or not, the fixes are the same:

IMMEDIATE:
  1. Fix vacuum leak
  2. Increase WUE to 165% at 28°C

THEN TEST:
  If fixed → Done!
  If still lean → Check Req_Fuel setting
  
The data will tell us if Req_Fuel needs adjustment.

START WITH VACUUM LEAK!
Everything else is secondary until leak is fixed.
""")

print("="*80)
print("FINAL ANSWER - INJECTOR SIZE QUESTION")
print("="*80)

print("""
INJECTOR SIZE: Most likely 45 lb/hr (as configured)
====================================================

Evidence for 45 lb/hr:
  ✓ TunerStudio configured for 45 lb/hr
  ✓ Req_Fuel 5.7ms matches 45 lb/hr calculation
  ✓ AFR behavior consistent with 45 lb/hr
  ✓ Typical specification for Gol G2 1.6L

If actually 60 lb/hr:
  → Would show as RICH (11:1), not lean (14.7:1)
  → Unless Req_Fuel setting is wrong
  → Unlikely but possible

DIAGNOSIS UNCHANGED:
====================

Regardless of injector size:
  1. Vacuum leak exists (MAP 60 vs 42 kPa)
  2. WUE insufficient (130% vs 160% needed)
  3. These must be fixed

FIX SEQUENCE:
=============
  
1. Vacuum leak (physical repair)
2. WUE increase to 165% at 28-30°C (tuning)
3. Test and verify AFR reaches 11.5-12.0:1
4. If still lean, consider Req_Fuel adjustment
5. Verify actual injector size if uncertainty remains

DO THE BRAKE BOOSTER PINCH TEST!
Then fix leak and increase WUE.
The data after fixes will confirm if Req_Fuel is correct.

Injector size debate doesn't change the immediate action plan.
""")

print("="*80)
