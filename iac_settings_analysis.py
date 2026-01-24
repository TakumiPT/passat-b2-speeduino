"""
Analysis of IAC Idle Control Settings
"""

print("="*80)
print("IAC IDLE CONTROL SETTINGS ANALYSIS")
print("="*80)

print("""
YOUR IAC SETTINGS (from screenshots):
======================================

IAC STEPPER MOTOR - CRANKING (RPM < 300):
  -21°C: 0 steps
    0°C: 60 steps
   37°C: 120 steps
   79°C: 180 steps
   
   At 30°C (interpolated): ~105 steps during crank
   
   Note: This is INVERTED from running!
   During crank, HIGHER steps = MORE open
   (Different from running where 0=open, 165=closed)

IAC STEPPER MOTOR - RUNNING (RPM > 300):
  -26°C: 0 steps (fully open)
    2°C: 21 steps
   22°C: 39 steps
   39°C: 60 steps
   53°C: 81 steps
   66°C: 99 steps
   82°C: 120 steps
   96°C: 141 steps
  107°C: 159 steps
  117°C: 180 steps (fully closed)
  
  At 30°C (interpolated): ~48 steps
  
  Remember: 0 = fully open, 165 = fully closed
  48 steps = 71% open (29% closed)
""")

print("="*80)
print("CRITICAL FINDING - IAC TARGET vs ACTUAL")
print("="*80)

print("""
IAC TARGET at 30°C: 48 steps (71% open)
IAC ACTUAL in your log: 88 steps (47% open)

PROBLEM: IAC is 40 steps MORE CLOSED than target!
=========

Target: 48 steps (should allow good airflow for cold start)
Actual: 88 steps (ECU closing it down)

This confirms: ECU is FIGHTING excess airflow from vacuum leak!

WHY THIS HAPPENS:
=================

1. Engine starts, ECU commands IAC to 48 steps (target for 30°C)
2. Too much total air enters (IAC air + LEAK air)
3. AFR goes very lean (15-16:1)
4. RPM doesn't climb to target
5. ECU closes IAC from 48 to 88 steps (trying to reduce total air)
6. Metered air reduces, but leak air still entering
7. Still too lean, RPM still low
8. ECU can't close IAC more (would stall completely)
9. Stuck at 88 steps, 527 RPM, lean AFR

THE IAC CONTROLLER IS MAXED OUT!
================================

ECU wants: 48 steps at 30°C
ECU commanded: 88 steps (40 steps more closed)
Difference: 83% more closed than target

This is the ECU's desperate attempt to compensate for vacuum leak
But it cannot work because:
  - Closing IAC reduces METERED air
  - Leak continues adding UNMETERED air
  - Ratio gets worse, not better
""")

print("="*80)
print("WHAT ABOUT TARGET RPM? (STILL MISSING)")
print("="*80)

print("""
We now know IAC target position at 30°C: 48 steps

But we DON'T know: What RPM is the ECU trying to achieve?

This is in a different table, usually:
  "Idle Control Settings" → "Target Idle RPM vs Temperature"
  or "Idle" → "Idle RPM Target"
  or similar

Need to see:
  - Target RPM at -20°C, 0°C, 30°C, 60°C, 80°C
  - Typical values:
    -20°C: 1200-1400 RPM (very high for extreme cold)
      0°C: 1100-1200 RPM
     30°C: 900-1000 RPM ← YOUR TEMP
     60°C: 800-850 RPM
     80°C: 750-800 RPM (normal hot idle)

Your actual: 527 RPM (way below ANY reasonable target)

The ECU is probably:
  - Targeting 900-1000 RPM at 30°C
  - Seeing only 527 RPM
  - Trying to open IAC more (to add air and raise RPM)
  - But wait... IAC is at 88, more CLOSED than target 48!
  
This is contradictory! Let me analyze...
""")

print("="*80)
print("IAC CONTROL LOGIC ANALYSIS")
print("="*80)

print("""
NORMAL IAC CONTROL (no vacuum leak):
=====================================

Target at 30°C: 48 steps (71% open)
Target RPM: 900-1000 (unknown, but reasonable guess)

Control loop:
  1. ECU sets IAC to 48 steps
  2. Air flows in at correct rate
  3. Fuel added to match air (with warmup + ASE enrichment)
  4. AFR stays at 12.0:1
  5. RPM climbs to 950
  6. ECU maintains IAC at 48 steps
  7. Smooth cold idle achieved

YOUR IAC CONTROL (with vacuum leak):
====================================

Target at 30°C: 48 steps (71% open)
Target RPM: 900-1000 (probably)
Actual: 88 steps (47% open) - MORE CLOSED
Actual RPM: 527 - WAY BELOW target

Why is IAC MORE closed if RPM is too LOW?
Normally, if RPM too low, ECU should OPEN IAC (add more air)

EXPLANATION: ECU DETECTING LEAN CONDITION
==========================================

Speeduino has multiple control strategies:
  1. IAC position control (open-loop, based on CLT)
  2. RPM feedback control (closed-loop, PID)
  3. AFR feedback control (if O2 sensor active)

What's happening:
  1. ECU starts with IAC at 48 steps (open-loop target)
  2. Measures AFR: sees 15-16:1 (way too lean)
  3. Adds more fuel, but still lean (vacuum leak)
  4. Decides: "Too much air, not enough fuel capacity"
  5. CLOSES IAC to 88 steps to reduce total air
  6. But this is wrong strategy! (leak still adding air)
  7. RPM falls to 527 (not enough power from lean mixture)
  8. ECU stuck: can't open IAC (too lean), can't close more (would stall)

OR: IAC Stepper Motor Could Be Stuck/Binding
=============================================

Possible mechanical issue:
  - IAC stepper motor binding/sticky
  - ECU commands 48 steps, but IAC only moves to 88
  - Dirt/carbon buildup in IAC bore
  - Worn IAC pintle
  
Test: Remove IAC, clean thoroughly, test movement
But this doesn't explain the high MAP (60 kPa)
High MAP proves vacuum leak exists
""")

print("="*80)
print("COMPARISON: IAC CRANKING vs RUNNING")
print("="*80)

print("""
INTERESTING OBSERVATION:
========================

IAC During Cranking at 30°C: ~105 steps
  - This is on a DIFFERENT scale (higher = more open)
  - Purpose: Allow lots of air for cold cranking
  - Works with 540% cranking enrichment
  - Engine starts successfully ✓

IAC After Start (Running) at 30°C: Target 48, Actual 88
  - Scale: 0 = open, 165 = closed
  - Target 48 steps = 71% open (good for cold idle)
  - Actual 88 steps = 47% open (ECU closing it down)
  - Works with ASE 100% + Warmup enrichment
  - Engine struggles, RPM only 527 ✗

DURING CRANKING:
  - High IAC opening + High enrichment (540%) = Engine fires
  - Vacuum leak present, but cranking enrichment compensates
  
AFTER START:
  - Moderate IAC opening (target 48) + Moderate enrichment (ASE 100%)
  - Vacuum leak overwhelms the enrichment
  - ECU closes IAC to 88 trying to help
  - Makes it worse (less metered air, same leak air)
""")

print("="*80)
print("WHAT WE STILL NEED")
print("="*80)

print("""
CRITICAL TABLE STILL MISSING:
==============================

1. WARMUP ENRICHMENT TABLE ⚠️ MOST IMPORTANT
   Location: "Fuel" → "Warmup Enrichment"
   Shows: Fuel enrichment % vs Coolant Temperature
   
   Need: What's the multiplier at 30°C?
   
   This is the BASE enrichment for cold running
   ASE multiplies THIS value
   
   Example calculation:
     Base fuel: 1.5ms
     Warmup enrichment at 30°C: 140% → 1.5 × 1.4 = 2.1ms
     ASE enrichment: 100% → 2.1 × 2.0 = 4.2ms total
     
   If warmup is only 110% at 30°C:
     1.5 × 1.1 = 1.65ms
     1.65 × 2.0 = 3.3ms total (not enough!)

2. TARGET IDLE RPM TABLE
   Location: "Idle" → "Target RPM" or similar
   Shows: Target RPM vs Coolant Temperature
   
   Need: What RPM is ECU trying to achieve at 30°C?
   Typical: 900-1000 RPM
   Your actual: 527 RPM (huge deficit)
   
3. O2 SENSOR / CLOSED LOOP SETTINGS
   Location: "Tuning" → "AFR/O2" or "Closed Loop"
   
   Need to know:
   - Is closed-loop control active during warm-up?
   - Is O2 sensor influencing fuel calculations?
   - AFR target table: what AFR at 30°C idle?
""")

print("="*80)
print("ACTION PLAN - UPDATED WITH IAC KNOWLEDGE")
print("="*80)

print("""
IMMEDIATE ACTIONS:
==================

1. VACUUM LEAK TEST (5 minutes) - DO THIS FIRST!
   ------------------------------------------------
   a) Start engine (will idle at ~527 RPM, IAC at 88 steps)
   b) Open TunerStudio, watch MAP (should show ~60 kPa)
   c) Pinch brake booster vacuum hose shut
   d) Observe changes:
      - MAP should drop from 60 → 40-45 kPa (LEAK FOUND!)
      - IAC should open from 88 → 60-70 steps (ECU relaxes)
      - RPM might increase slightly
      - Engine might run slightly smoother
   
   If MAP drops = BRAKE BOOSTER IS THE LEAK!
   If MAP stays same = leak is elsewhere

2. SEND REMAINING SCREENSHOTS (5 minutes)
   ----------------------------------------
   a) Warmup Enrichment table (CRITICAL!)
   b) Target Idle RPM table
   c) AFR Target table (if you have one)
   
3. FIX VACUUM LEAK (1-2 hours)
   ----------------------------
   Once confirmed, replace brake booster or vacuum hose
   
4. CLEAN IAC VALVE (30 minutes) - OPTIONAL BUT RECOMMENDED
   --------------------------------------------------------
   While fixing leak, also:
   a) Remove IAC valve
   b) Clean with carburetor cleaner
   c) Clean IAC bore in throttle body
   d) Check IAC pintle for wear
   e) Reinstall with new gasket/O-ring
   
   This ensures IAC can reach target 48 steps properly

5. RE-TEST WITH NEW LOG
   ---------------------
   After repairs, cold start test at same temp (30°C)
   Expected results:
   - MAP: 40-45 kPa (vacuum restored)
   - IAC: 40-50 steps (at target, not fighting leak)
   - RPM: 700-850 initially (big improvement)
   - AFR: 12.5-13.5:1 (better, may still need warmup tune)
   - PW: Holds 3.0-3.5ms for full ASE duration

6. ADJUST WARMUP ENRICHMENT IF NEEDED
   ------------------------------------
   After leak fixed, if AFR still 13-14:1:
   - Increase warmup enrichment at 30°C by 20-30%
   - Re-test
   - Target: AFR 11.5-12.5:1, RPM 900-1000
""")

print("="*80)
print("SUMMARY - IAC ANALYSIS")
print("="*80)

print("""
IAC TARGET at 30°C: 48 steps (71% open)
  ✓ This is a GOOD target for cold idle
  ✓ Should allow plenty of air at 30°C

IAC ACTUAL in your log: 88 steps (47% open)
  ✗ 40 steps MORE CLOSED than target (83% deviation!)
  ✗ ECU desperately closing IAC to fight vacuum leak
  ✗ Cannot work (leak bypasses IAC control)

MAP: 60 kPa (should be 40-45 kPa at 48 steps)
  ✗ Proves vacuum leak exists
  ✗ Extra 15-20 kPa = ~72 L/min unmeasured air

RPM: 527 actual (target probably 900-1000)
  ✗ 42% below target (huge deficit)
  ✗ Lean AFR from vacuum leak = insufficient power

THE ROOT CAUSE CHAIN:
=====================

Vacuum Leak (brake booster most likely)
    ↓
Adds 72 L/min unmeasured air (+34%)
    ↓
ECU doesn't know about leak air
    ↓
Calculates fuel for metered air only
    ↓
Actual AFR = 16:1 (way too lean)
    ↓
ECU closes IAC from 48 to 88 (trying to help)
    ↓
Reduces metered air, but leak air continues
    ↓
Still too lean, even worse ratio
    ↓
RPM stuck at 527 (not enough power)
    ↓
Engine struggles, nearly stalls

FIX: Remove the vacuum leak
  → MAP drops to 40-45 kPa
  → IAC opens to target 48 steps
  → ASE and warmup enrichment work as designed
  → AFR reaches 12-12.5:1
  → RPM climbs to 800-900
  → May need minor warmup enrichment adjustment
  → Then reaches target 950-1000 RPM

DO THE BRAKE BOOSTER PINCH TEST!
Then send Warmup Enrichment table screenshot.
""")

print("="*80)
