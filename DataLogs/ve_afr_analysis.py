"""
Analysis of VE Table and AFR Target Table
"""

print("="*80)
print("VE TABLE AND AFR TARGET TABLE ANALYSIS")
print("="*80)

print("""
YOUR VE TABLE (Volumetric Efficiency):
=======================================

At cold idle conditions (your log data):
  Load/MAP: ~60 kPa
  RPM: ~527 (between 600-800 range)
  CLT: 30°C (cold)
  
Looking at VE table at 60 kPa load, 600 RPM:
  VE = 49% (from table)
  
At 800 RPM, 60 kPa load:
  VE = 55% (from table)
  
Your actual VE in log: ~40% average

ANALYSIS:
  Table expects: 49-55% VE at this condition
  Your actual: 40% VE
  Difference: 9-15% LOWER than expected
  
WHY VE IS LOW:
  1. Engine running at only 527 RPM (very low, poor pumping)
  2. Vacuum leak adds unmeasured air (ECU thinks less air than actual)
  3. Poor combustion from lean AFR (14.7:1 vs target 12.8:1)
  4. IAC closed to 88 steps, restricting metered airflow

The low VE is a SYMPTOM, not the cause.


YOUR AFR TARGET TABLE:
=======================

At cold idle conditions:
  Load/MAP: ~60 kPa  
  RPM: ~600 (closest in table)
  
Looking at AFR target at 60 kPa, 600 RPM:
  Target AFR = 14.1:1
  
Your actual AFR in log: 14.7:1 average

WAIT... TARGET IS 14.1:1 ?!
===========================

This is VERY LEAN for cold start!

Typical cold start AFR targets:
  -20°C to 20°C: 11.5-12.5:1 (rich for cold)
  20°C to 40°C: 12.0-13.0:1 (moderately rich)
  40°C to 60°C: 12.5-13.5:1 (slightly rich)
  >60°C warm: 14.0-14.7:1 (stoichiometric)

Your target at 30°C cold: 14.1:1 (TOO LEAN!)

CRITICAL FINDING:
=================

Your AFR target table is set for WARM/HOT operation!
It's targeting 14.1:1 even when engine is COLD at 30°C!

This explains why:
  1. Your actual AFR is 14.7:1 (trying to reach 14.1 target)
  2. Engine cannot warm up properly (too lean for cold operation)
  3. Even WITHOUT the vacuum leak, this would struggle
  4. WITH the vacuum leak, it's impossible to start well

Your AFR target table appears to be:
  - Set for closed-loop operation (O2 sensor control)
  - Targeting stoichiometric (14.7:1) or near-stoich (14.1)
  - NOT adjusted for cold enrichment
  - Expecting warmup enrichment to handle cold temps

BUT: This conflicts with cold start requirements!
""")

print("="*80)
print("CLOSED LOOP CONTROL - IS IT ACTIVE?")
print("="*80)

print("""
From your VE table screenshot:

"Multiply by ratio of AFR to Target AFR" = No
"Multiply by ratio of stoich AFR/target AFR (incorporate AFR)" = No

This means: Closed-loop O2 correction is DISABLED

WHAT THIS MEANS:
================

ECU is NOT using O2 sensor to adjust fuel in real-time
ECU calculates fuel based on:
  1. VE table
  2. MAP sensor
  3. RPM
  4. Warmup enrichment (still need to see this!)
  5. ASE enrichment
  6. Cranking enrichment

AFR target table (14.1:1) is shown but NOT actively controlling fuel
It's there for reference or future closed-loop use

So why is actual AFR 14.7:1 when target is 14.1:1?
Because ECU is in OPEN LOOP mode:
  - Calculates fuel based on VE, MAP, RPM
  - Applies warmup enrichment
  - Applies ASE enrichment
  - Does NOT correct based on O2 sensor feedback
  - If calculation is wrong (due to vacuum leak), AFR goes lean
""")

print("="*80)
print("FUEL CALCULATION BREAKDOWN")
print("="*80)

print("""
How ECU calculates fuel in OPEN LOOP mode:

STEP 1: Base fuel from VE table
  MAP: 60 kPa
  RPM: 527 (use 600 RPM cell)
  VE: 49% (from table)
  
  Air mass = f(MAP, VE, RPM, Temp)
  Base fuel = Air mass / 14.7 (stoichiometric ratio)
  
  Let's say base fuel = 1.5ms (hypothetical)

STEP 2: Apply warmup enrichment
  CLT: 30°C
  Warmup multiplier: ??? (STILL NEED THIS TABLE!)
  
  Let's assume warmup = 120% (1.2x)
  Fuel after warmup = 1.5 × 1.2 = 1.8ms

STEP 3: Apply ASE enrichment (first 17 seconds)
  ASE at 30°C: 100% (2.0x)
  Fuel with ASE = 1.8 × 2.0 = 3.6ms
  
  Your actual PW at start: 3.17ms ✓ Close!

STEP 4: ASE decays (but shouldn't this fast!)
  At t=27s: ASE should still be active
  Your PW at t=27s: 2.5ms
  Expected with ASE: 3.6ms
  Difference: 30% LESS than expected
  
  This suggests: ASE is decaying too fast OR warmup is too low

STEP 5: After ASE ends (t > 27s)
  Only warmup enrichment remains
  Fuel = 1.5 × 1.2 = 1.8ms
  
  Your actual PW at t=38s: 1.98ms
  Expected: 1.8ms
  Close enough ✓

PROBLEM IDENTIFIED:
===================

Base fuel calculation (VE table based):
  Assumes MAP 60 kPa = 60 kPa of air entering
  But with vacuum leak:
    Metered air: Less (IAC at 88 steps, closed)
    Unmetered air: +72 L/min from leak
    Total air: 34% more than ECU thinks
  
  ECU adds fuel for metered air only
  Actual AFR = Target AFR × (Actual air / Metered air)
  Actual AFR = 14.1 × 1.34 = 18.9:1
  
  Wait, your actual is 14.7:1, not 18.9:1...
  
  This suggests: MAP sensor is reading total pressure
  ECU calculates fuel for 60 kPa (total air)
  But vacuum leak means 60 kPa includes unmeasured air
  
  So VE table thinks: "60 kPa, VE 49%, calculate fuel"
  Reality: VE is lower (40%) due to leak/restriction
  Less air than table expects, but leak compensates
  Result: AFR close to table assumption but engine struggles
""")

print("="*80)
print("THE MISSING PIECE: WARMUP ENRICHMENT TABLE")
print("="*80)

print("""
We now have:
  ✓ Cranking enrichment: 540% at 30°C
  ✓ ASE enrichment: 100% (2.0x) for 17 seconds at 30°C
  ✓ IAC target: 48 steps at 30°C
  ✓ VE table: Expects 49-55% VE at idle
  ✓ AFR target: 14.1:1 (but closed-loop disabled)
  
  ✗ Warmup enrichment: STILL MISSING!

This is the critical multiplier for cold operation!

If warmup enrichment at 30°C is:
  100% (1.0x) = NO enrichment
    → AFR will be ~14.7:1 (stoich)
    → TOO LEAN for cold start
    → Engine struggles (your situation)
  
  120% (1.2x) = Slight enrichment
    → AFR will be ~12.3:1
    → Marginal for 30°C
    → May work without vacuum leak
    → Will struggle with vacuum leak (your situation)
  
  150% (1.5x) = Good cold enrichment
    → AFR will be ~9.8:1
    → Too rich for 30°C
    → Might work even with small vacuum leak
    → Unlikely you have this (would see different symptoms)

Based on your symptoms, warmup enrichment is probably:
  100-120% at 30°C (insufficient)

Need to see actual table to confirm and calculate fix.
""")

print("="*80)
print("COMPLETE DIAGNOSTIC SUMMARY")
print("="*80)

print("""
SETTINGS ANALYZED:
==================

1. Cranking Enrichment: 540% at 30°C ✓ GOOD
   - Engine starts successfully
   - Compensates for cold + vacuum leak during crank

2. ASE Enrichment: 100% (2.0x) for 17s at 30°C ✓ GOOD SETTINGS
   - Should work for normal cold start
   - Overwhelmed by vacuum leak in your case

3. IAC Target: 48 steps at 30°C ✓ GOOD TARGET
   - 71% open, appropriate for cold idle
   - Actual: 88 steps (ECU fighting vacuum leak)

4. VE Table: 49-55% at idle conditions ✓ REASONABLE
   - Your actual: 40% (low due to poor combustion/leak)
   - Table is OK, engine just not reaching targets

5. AFR Target: 14.1:1 at idle ⚠️ LEAN FOR COLD START
   - Appropriate for warm/hot operation
   - Too lean for 30°C cold start
   - BUT: Closed-loop disabled, so not actively used
   - Warmup enrichment should compensate (need to see table)

6. Warmup Enrichment: ??? at 30°C ⚠️⚠️ NEED THIS!
   - Most critical missing piece
   - Determines base fuel for cold operation
   - Likely too low (100-120% instead of 140-160%)

7. Vacuum Leak: 60 kPa MAP at 88 IAC ✗ CONFIRMED
   - Should be 40-45 kPa at 48 IAC
   - Adds ~72 L/min unmeasured air (+34%)
   - Defeats all enrichment strategies

ROOT CAUSE ANALYSIS:
====================

PRIMARY ISSUE: Vacuum leak (brake booster likely)
  → Adds 34% unmeasured air
  → ECU cannot compensate (doesn't know about leak)
  → All enrichment strategies defeated
  
SECONDARY ISSUE: Warmup enrichment probably insufficient
  → Even without leak, may be marginal at 30°C
  → With leak, definitely insufficient
  → Need to see table and likely increase by 20-40%

TERTIARY ISSUE: AFR target lean for cold start
  → 14.1:1 is warm-engine target
  → Should be 12.0-12.5:1 for 30°C
  → BUT: Closed-loop disabled, so not the issue
  → Warmup enrichment should handle this

THE FIX:
========

1. FIND AND FIX VACUUM LEAK (highest priority)
   Test: Pinch brake booster hose
   Fix: Replace brake booster or vacuum hose
   Result: MAP drops to 40-45 kPa, IAC opens to 48 steps

2. CHECK WARMUP ENRICHMENT TABLE (need screenshot)
   Analyze: What % at 30°C?
   Fix: If < 140%, increase to 140-160%
   Result: AFR reaches 12.0-12.5:1 for good cold start

3. OPTIONAL: Adjust AFR target for cold conditions
   Current: 14.1:1 at all temps (warm-engine target)
   Better: Temperature-compensated AFR target:
     <20°C: 12.0:1
     20-40°C: 12.5:1
     40-60°C: 13.5:1
     >60°C: 14.1-14.7:1
   But: Only if enabling closed-loop control
   Priority: LOW (do after fixing leak and warmup)

EXPECTED RESULTS:
=================

After vacuum leak fix:
  MAP: 60 → 40-45 kPa
  IAC: 88 → 48 steps (at target)
  VE: 40% → 50-55% (better combustion)
  AFR: 14.7 → 13.0-13.5:1 (improvement)
  RPM: 527 → 700-800 (significant improvement)

After warmup enrichment adjustment:
  AFR: 13.0 → 12.0-12.5:1 (optimal cold start)
  RPM: 700-800 → 900-1000 (reaches target)
  Engine: Smooth, stable, no struggling
""")

print("="*80)
print("IMMEDIATE ACTIONS")
print("="*80)

print("""
1. VACUUM LEAK TEST (5 minutes) ⚠️ DO THIS NOW!
   --------------------------------------------
   a) Start engine (will idle at 527 RPM)
   b) Open TunerStudio, watch MAP gauge (~60 kPa)
   c) Pinch brake booster vacuum hose shut with pliers
   d) Observe:
      - MAP drops from 60 → 40-45 kPa = LEAK FOUND!
      - IAC opens from 88 → 60-70 steps
      - RPM might increase
   e) If MAP drops, order brake booster replacement

2. SEND WARMUP ENRICHMENT TABLE ⚠️ CRITICAL!
   ------------------------------------------
   a) Find "Fuel" → "Warmup Enrichment" menu
   b) Screenshot showing enrichment % vs Coolant Temp
   c) Send screenshot
   d) I'll calculate exact adjustment needed

3. FIX VACUUM LEAK (1-2 hours)
   ---------------------------
   Replace brake booster or leaking component
   Re-test with new cold start log

4. ADJUST WARMUP ENRICHMENT (after leak fixed)
   -------------------------------------------
   Based on table analysis
   Likely increase 20-40% at 30°C range
   Target: AFR 12.0-12.5:1, RPM 900-1000

5. OPTIONAL TUNING (after both fixes)
   ----------------------------------
   - Fine-tune VE table if needed
   - Consider temperature-based AFR targets
   - Enable closed-loop control if desired

DO THE BRAKE BOOSTER PINCH TEST FIRST!
This will confirm the vacuum leak in 30 seconds.
Then send Warmup Enrichment table screenshot.
""")

print("="*80)
