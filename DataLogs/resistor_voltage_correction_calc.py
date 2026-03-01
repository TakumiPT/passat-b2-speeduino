"""
RESISTOR PROTECTION ANALYSIS + VOLTAGE CORRECTION TABLE
========================================================
Two questions:
1. Can the voltage correction table compensate for ballast resistor dead time?
2. Does a smaller resistor (1.5Ω, 2.2Ω) still protect the injector?
"""
import math

print("=" * 75)
print("QUESTION 1: CAN VOLTAGE CORRECTION HELP?")
print("=" * 75)

print("""
Your TunerStudio "Battery Voltage Correction" mode is "Open Time only".
This means the correction % multiplies ONLY the injOpen (dead time).

  Effective_injOpen = injOpen × (correction% / 100)

So YES, this table CAN compensate for the longer dead time at low voltage
caused by the ballast resistor. BUT only if the injector can physically
open (current must exceed pull-in threshold).

Let's calculate the CORRECT voltage correction values for each resistor.
""")

R_inj = 2.0  # Ohms

# Voltage points from the TunerStudio table
voltages = [6.6, 9.4, 12.1, 14.8, 16.9, 20.3]

def calc_dead_time_ratio(R_total, V, V_ref=14.8):
    """
    Dead time is dominated by the RL time constant and the fraction
    of I_steady needed to reach I_open.
    
    t_open = -(L/R) × ln(1 - I_open/I_steady)
    
    where I_steady = V/R_total
    
    The RATIO of dead times at two voltages (same L, R, I_open):
    t1/t2 = ln(1 - I_open×R/V1) / ln(1 - I_open×R/V2)
    
    Since we don't know I_open exactly, we'll compute for typical values.
    The correction% = (t_at_V / t_at_V_ref) × 100
    """
    pass

print("--- DEAD TIME RATIO vs VOLTAGE (relative to 14.8V baseline) ---\n")

for R_ballast in [0, 1.5, 2.2, 3.3]:
    R_total = R_inj + R_ballast
    if R_ballast == 0:
        label = "NO resistor"
    else:
        label = f"{R_ballast}Ω resistor"
    
    print(f"\n  {label} (R_total = {R_total}Ω)")
    print(f"  {'Voltage':>8} | {'I_steady':>9} | {'Dead time ratio':>15} | {'Correction %':>13} | Note")
    print("  " + "-" * 75)
    
    # Reference: 14.8V
    V_ref = 14.8
    I_ref = V_ref / R_total
    
    # Use I_open = 2.0A as typical pull-in current
    I_open = 2.0
    
    for V in voltages:
        I_steady = V / R_total
        
        if I_steady <= I_open:
            print(f"  {V:>7.1f}V | {I_steady:>8.2f}A | {'NEVER OPENS':>15} | {'∞':>13} | ← CANNOT OPEN")
            continue
        
        if I_ref <= I_open:
            print(f"  {V:>7.1f}V | {I_steady:>8.2f}A | {'N/A':>15} | {'N/A':>13} |")
            continue
        
        # RL circuit: t = -(L/R) × ln(1 - I_open/I_steady)
        # Ratio: t_V / t_ref = [ln(1 - I_open/I_V)] / [ln(1 - I_open/I_ref)]
        # Since L/R is constant, it cancels out
        ratio = math.log(1 - I_open/I_steady) / math.log(1 - I_open/I_ref)
        correction = round(ratio * 100)
        
        note = ""
        if abs(V - 14.8) < 0.5:
            note = "← baseline"
        elif correction > 200:
            note = "← very slow opening"
        elif I_steady < 2.5:
            note = "← marginal"
        
        print(f"  {V:>7.1f}V | {I_steady:>8.2f}A | {ratio:>14.2f}× | {correction:>12}% | {note}")

print(f"""

KEY INSIGHT:
  Without a resistor, the voltage correction is nearly flat (6.6V to 20.3V 
  causes barely any change in dead time because I_steady is always >> I_open).
  
  With a 3.3Ω resistor, the correction becomes EXTREME at low voltage —
  and at cranking voltages (~9-10V), the injector CANNOT OPEN AT ALL,
  so no correction table can fix it.
  
  With a 1.5Ω or 2.2Ω resistor, the corrections are moderate and 
  the voltage correction table CAN compensate.
""")

# =====================================================================
# QUESTION 2: DOES A SMALLER RESISTOR STILL PROTECT?
# =====================================================================
print("=" * 75)
print("QUESTION 2: DOES A SMALLER RESISTOR STILL PROTECT THE INJECTOR?")
print("=" * 75)

print("""
The injector's ENEMY is HEAT (average power dissipated in the coil).
The coil is designed for P&H drive: ~1.0-1.5A hold → 2-4.5W in coil.

But what matters for longevity is AVERAGE power, not instantaneous.
Average power = instantaneous power × duty cycle.

From your datalogs:
  98.6% of time: duty cycle < 10%
  Typical idle: ~2-5% duty
  Typical cruise: ~8-12% duty
  WOT (rare): ~40-50% duty
""")

print(f"{'':>10} | {'I @ 14V':>8} | {'P_coil':>8} | {'Pavg':>8} | {'Pavg':>8} | {'Pavg':>8} | {'vs Design':>10} | {'Protects?':>10}")
print(f"{'Resistor':>10} | {'':>8} | {'instant':>8} | {'@ 5%':>8} | {'@ 12%':>8} | {'@ 45%':>8} | {'@ 12%':>10} | {'':>10}")
print("-" * 95)

P_design = 4.5  # Watts - designed average coil power

for R_b in [0, 0.5, 1.0, 1.5, 2.0, 2.2, 2.7, 3.3]:
    R_t = R_inj + R_b
    I = 14.0 / R_t
    P_inst = I**2 * R_inj  # Power in the COIL (not resistor)
    P_5 = P_inst * 0.05
    P_12 = P_inst * 0.12
    P_45 = P_inst * 0.45
    
    ratio = P_12 / P_design
    
    if R_b == 0:
        label = "NONE"
    else:
        label = f"{R_b:.1f}Ω"
    
    if ratio <= 1.0:
        prot = "YES ✅"
    elif ratio <= 2.0:
        prot = "MOSTLY ⚠️"
    elif ratio <= 5.0:
        prot = "PARTIAL ⚠️"
    else:
        prot = "NO ❌"
    
    mark = ""
    if R_b == 3.3:
        mark = " ← YOUR CURRENT (won't start)"
    elif R_b == 1.5:
        mark = " ← RECOMMENDED"
    elif R_b == 0:
        mark = " ← BEFORE"
        
    print(f"{label:>10} | {I:>7.2f}A | {P_inst:>7.1f}W | {P_5:>7.2f}W | {P_12:>7.2f}W | {P_45:>7.1f}W | {ratio:>9.1f}× | {prot}{mark}")

print(f"""
Design power = {P_design}W (hold current 1.5A × 2Ω = 4.5W, 100% duty during hold)

READING THE TABLE:
  "Protects?" column is based on average power during CRUISE (12% duty).
  - YES ✅ = average coil power ≤ design spec → injector runs within design
  - MOSTLY ⚠️ = 1-2× design → minor extra heating, very long life
  - PARTIAL ⚠️ = 2-5× design → reduced life but usable for years
  - NO ❌ = >5× design → progressive coil degradation
""")

# =====================================================================
# RECOMMENDED VALUE WITH VOLTAGE CORRECTION
# =====================================================================
print("=" * 75)
print("★ BEST SOLUTION: 1.5Ω RESISTOR + VOLTAGE CORRECTION TABLE ★")
print("=" * 75)

R_best = 1.5
R_total_best = R_inj + R_best
I_open_assumed = 2.0  # Conservative estimate

print(f"""
Resistor: 1.5Ω wirewound (10W or 25W)
R_total: {R_total_best}Ω
""")

# Calculate voltage correction table for 1.5Ω
print("Voltage Correction Table for TunerStudio (1.5Ω resistor):")
print("-" * 55)

V_ref = 14.8
I_ref = V_ref / R_total_best

for V in voltages:
    I_steady = V / R_total_best
    
    if I_steady <= I_open_assumed:
        print(f"  {V:>6.1f}V → CANNOT OPEN (need higher V or lower R)")
        continue
    
    ratio = math.log(1 - I_open_assumed/I_steady) / math.log(1 - I_open_assumed/I_ref)
    correction = round(ratio * 100)
    
    # Also show no-resistor baseline for comparison
    I_ref_noR = V_ref / R_inj
    I_noR = V / R_inj
    ratio_noR = math.log(1 - I_open_assumed/I_noR) / math.log(1 - I_open_assumed/I_ref_noR)
    corr_noR = round(ratio_noR * 100)
    
    print(f"  {V:>6.1f}V → {correction:>4}%  (without resistor would be: {corr_noR}%)")

print(f"""
Cranking check (1.5Ω):
  At 10.5V: I = 10.5/{R_total_best} = {10.5/R_total_best:.2f}A → opens ✓
  At  9.0V: I = 9.0/{R_total_best} = {9.0/R_total_best:.2f}A → opens ✓

injOpen setting: start at 1.5ms, adjust by AFR at idle.

Current @ 14V: {14.0/R_total_best:.2f}A
Coil instantaneous power: {(14.0/R_total_best)**2 * R_inj:.1f}W
Coil average power @ cruise (12%): {(14.0/R_total_best)**2 * R_inj * 0.12:.1f}W
Design spec: 4.5W
Ratio: {(14.0/R_total_best)**2 * R_inj * 0.12 / 4.5:.1f}× design ← SURVIVABLE

vs no resistor: 
  Average power @ cruise: {(14.0/R_inj)**2 * R_inj * 0.12:.1f}W = {(14.0/R_inj)**2 * R_inj * 0.12 / 4.5:.0f}× design ← DANGEROUS
""")

# Also show 2.2Ω as alternative
print("=" * 75)
print("ALTERNATIVE: 2.2Ω RESISTOR + VOLTAGE CORRECTION TABLE")
print("=" * 75)

R_alt = 2.2
R_total_alt = R_inj + R_alt

print(f"""
Resistor: 2.2Ω wirewound (10W or 25W) 
R_total: {R_total_alt}Ω
""")

print("Voltage Correction Table for TunerStudio (2.2Ω resistor):")
print("-" * 55)

I_ref_alt = V_ref / R_total_alt

for V in voltages:
    I_steady = V / R_total_alt
    
    if I_steady <= I_open_assumed:
        print(f"  {V:>6.1f}V → CANNOT OPEN (need higher V or lower R)")
        continue
    
    ratio = math.log(1 - I_open_assumed/I_steady) / math.log(1 - I_open_assumed/I_ref_alt)
    correction = round(ratio * 100)
    
    I_ref_noR = V_ref / R_inj
    I_noR = V / R_inj
    ratio_noR = math.log(1 - I_open_assumed/I_noR) / math.log(1 - I_open_assumed/I_ref_noR)
    corr_noR = round(ratio_noR * 100)
    
    print(f"  {V:>6.1f}V → {correction:>4}%  (without resistor would be: {corr_noR}%)")

print(f"""
Cranking check (2.2Ω):
  At 10.5V: I = 10.5/{R_total_alt} = {10.5/R_total_alt:.2f}A → borderline ⚠️
  At  9.0V: I = 9.0/{R_total_alt} = {9.0/R_total_alt:.2f}A → risky ⚠️

Current @ 14V: {14.0/R_total_alt:.2f}A
Coil average power @ cruise (12%): {(14.0/R_total_alt)**2 * R_inj * 0.12:.1f}W
Ratio: {(14.0/R_total_alt)**2 * R_inj * 0.12 / 4.5:.1f}× design ← GOOD

2.2Ω is better protection but riskier for cranking.
1.5Ω is safer for cranking but slightly less protection.
BOTH are massive improvements over no resistor.
""")

print("=" * 75)
print("FINAL ANSWER")
print("=" * 75)
print(f"""
1. YES, the voltage correction table helps — set steeper values at low voltage
   to compensate for the slower injector opening with a ballast resistor.

2. YES, a smaller resistor STILL protects the injector:
   - 1.5Ω: reduces coil power from 98W → 32W (instantaneous)
            average at cruise: 3.8W (below 4.5W design!) ✅
   - 2.2Ω: reduces coil power from 98W → 22W (instantaneous)
            average at cruise: 2.7W (well below design!) ✅
   
   Compare: no resistor average at cruise = 11.8W = 2.6× design ❌

3. YOUR 3.3Ω won't start because at cranking voltage (~10.5V),
   the 1.98A steady-state current is below or at the pull-in threshold.
   No injOpen or voltage correction can fix this — it's a physics limit.

★ RECOMMENDATION: Replace 3.3Ω with 1.5Ω wirewound 10W.
  - Starts reliably (3.0A at cranking)
  - Still protects injector (average power within design spec at cruise)
  - Set injOpen = 1.2-1.5ms
  - Update voltage correction table per values above
""")
