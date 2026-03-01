"""
INJECTOR DEAD TIME (injOpen) CALCULATOR
=======================================
Scientific calculation for IWM500.01 with ballast resistor.

Physics: RL circuit energization
  i(t) = (V/R) × (1 - e^(-t×R/L))

The injector opens when current reaches the pull-in threshold (I_open).
The time to reach I_open IS the electromagnetic dead time.

Known:
  V = 14V (alternator voltage while running)
  R_inj = 2Ω (measured)
  R_ballast = 3.3Ω (your resistor)
  
Unknown (must be estimated from constraints):
  L = inductance of IWM500.01 coil (mH)
  I_open = minimum current to pull the pintle open (A)

We CAN derive constraints:
  - Original Magneti Marelli ECU used ~4A peak → this is MORE than I_open
    (they over-drive for fast opening, not because 4A is the minimum)
  - Hold current = 1.0-1.5A → injector STAYS open at this current
  - So I_open is between hold current and peak: 1.5A < I_open < 4.0A
  - With 3.3Ω resistor: I_steady = 14/5.3 = 2.64A
  - If I_open > 2.64A → injector NEVER opens → need smaller resistor!
"""

import math

print("=" * 75)
print("INJECTOR DEAD TIME CALCULATOR - IWM500.01 + 3.3Ω BALLAST")
print("=" * 75)

# Known parameters
V = 14.0           # Volts (alternator running)
V_crank = 10.5     # Volts (cranking, battery under load)
R_inj = 2.0        # Ohms (measured)
R_ballast = 3.3    # Ohms (your resistor)
R_total = R_inj + R_ballast  # 5.3 Ohms

print(f"\n--- CIRCUIT PARAMETERS ---")
print(f"Supply voltage (running):  {V:.1f}V")
print(f"Supply voltage (cranking): {V_crank:.1f}V")
print(f"Injector resistance:       {R_inj:.1f}Ω")
print(f"Ballast resistance:        {R_ballast:.1f}Ω")
print(f"Total resistance:          {R_total:.1f}Ω")

I_steady_no_R = V / R_inj
I_steady_with_R = V / R_total
I_steady_crank = V_crank / R_total

print(f"\n--- STEADY-STATE CURRENTS ---")
print(f"Without resistor:          {I_steady_no_R:.2f}A")
print(f"With resistor (running):   {I_steady_with_R:.2f}A")
print(f"With resistor (cranking):  {I_steady_crank:.2f}A  ← WORST CASE")

# =====================================================================
# CRITICAL CHECK: Can the injector even open with this resistor?
# =====================================================================
print(f"\n{'=' * 75}")
print("CRITICAL CHECK: WILL THE INJECTOR OPEN?")
print(f"{'=' * 75}")
print(f"""
The injector has a PULL-IN CURRENT (I_open) — the minimum current
needed to generate enough electromagnetic force to overcome the
return spring + fuel pressure and move the pintle.

Original Magneti Marelli ECU:
  - Peak current: ~4A (for 1-2ms) → fast, forceful opening
  - Hold current: ~1.0-1.5A → keeps it open (less force needed)

The pull-in current I_open is somewhere between hold and peak.
For SPI monopoint injectors, typical I_open = 1.5 - 3.5A

YOUR steady-state currents:
  Running (14V):   {I_steady_with_R:.2f}A
  Cranking (10.5V): {I_steady_crank:.2f}A ← must exceed I_open!
""")

# For each possible I_open, check if it can open
print("Can the injector open?")
print("-" * 50)
print(f"  If I_open = 1.5A: YES  (1.98A > 1.5A at cranking)")
print(f"  If I_open = 2.0A: BARELY (1.98A ≈ 2.0A at cranking)")
print(f"  If I_open = 2.5A: NO during cranking! (1.98A < 2.5A)")
print(f"  If I_open = 3.0A: NO at any voltage!")

print(f"""
⚠️  DURING CRANKING, battery drops to ~10.5V
    I_steady = 10.5 / 5.3 = {I_steady_crank:.2f}A
    
    If this is below I_open, the injector CANNOT open during cranking.
    This would explain why it doesn't start!
""")

# =====================================================================
# DEAD TIME CALCULATION - RL circuit
# =====================================================================
print(f"{'=' * 75}")
print("DEAD TIME vs INDUCTANCE (for different I_open values)")
print(f"{'=' * 75}")

print("""
Formula: i(t) = (V/R) × (1 - e^(-t·R/L))
Solving for time to reach I_open:
  t = -(L/R) × ln(1 - I_open·R/V)
  t = -(L/R) × ln(1 - I_open/I_steady)

Condition: I_open MUST be < I_steady, otherwise NEVER opens.
""")

# Inductance range for low-Z SPI injectors
L_values_mH = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
I_open_values = [1.5, 2.0, 2.5]

# Table: dead time WITH resistor at 14V
print(f"\n--- Dead time WITH 3.3Ω resistor @ 14V (I_steady = {I_steady_with_R:.2f}A) ---")
print(f"{'L (mH)':>8} | ", end="")
for I_op in I_open_values:
    print(f"I_open={I_op:.1f}A | ", end="")
print()
print("-" * 55)

for L_mH in L_values_mH:
    L = L_mH / 1000.0  # Convert to Henries
    print(f"{L_mH:>7.1f}  | ", end="")
    for I_op in I_open_values:
        if I_op >= I_steady_with_R:
            print(f"  NEVER    | ", end="")
        else:
            t = -(L / R_total) * math.log(1 - I_op / I_steady_with_R)
            print(f"  {t*1000:.2f} ms  | ", end="")
    print()

# Table: dead time WITH resistor at 10.5V (cranking)
print(f"\n--- Dead time WITH 3.3Ω resistor @ 10.5V CRANKING (I_steady = {I_steady_crank:.2f}A) ---")
print(f"{'L (mH)':>8} | ", end="")
for I_op in I_open_values:
    print(f"I_open={I_op:.1f}A | ", end="")
print()
print("-" * 55)

for L_mH in L_values_mH:
    L = L_mH / 1000.0
    print(f"{L_mH:>7.1f}  | ", end="")
    for I_op in I_open_values:
        if I_op >= I_steady_crank:
            print(f"  NEVER    | ", end="")
        else:
            t = -(L / R_total) * math.log(1 - I_op / I_steady_crank)
            print(f"  {t*1000:.2f} ms  | ", end="")
    print()

# Table: dead time WITHOUT resistor at 14V (baseline comparison)
I_steady_no_R_val = V / R_inj
print(f"\n--- Dead time WITHOUT resistor @ 14V (I_steady = {I_steady_no_R_val:.2f}A) --- BASELINE ---")
print(f"{'L (mH)':>8} | ", end="")
for I_op in I_open_values:
    print(f"I_open={I_op:.1f}A | ", end="")
print()
print("-" * 55)

for L_mH in L_values_mH:
    L = L_mH / 1000.0
    print(f"{L_mH:>7.1f}  | ", end="")
    for I_op in I_open_values:
        t = -(L / R_inj) * math.log(1 - I_op / I_steady_no_R_val)
        print(f"  {t*1000:.2f} ms  | ", end="")
    print()

# =====================================================================
# THE REAL PROBLEM — CRANKING VOLTAGE
# =====================================================================
print(f"\n{'=' * 75}")
print("★ THE REAL PROBLEM: CRANKING VOLTAGE ★")
print(f"{'=' * 75}")
print(f"""
During cranking, battery voltage drops to ~10-11V.

With 3.3Ω resistor at 10.5V:
  I_steady = 10.5 / 5.3 = {10.5/5.3:.2f}A

This is VERY close to (or below) the pull-in current threshold.

Without resistor at 10.5V (cranking):
  I_steady = 10.5 / 2 = {10.5/2:.2f}A  ← plenty of margin

THIS is likely why it doesn't start:
  Not enough current to open the injector during cranking!
  Once the engine is running and alternator brings voltage to 14V,
  it might work — but you can't GET there without cranking.
""")

# =====================================================================
# WHAT RESISTOR VALUE WOULD WORK?
# =====================================================================
print(f"{'=' * 75}")
print("RESISTOR SIZING ANALYSIS")
print(f"{'=' * 75}")
print(f"""
For the injector to reliably open during cranking (V = 10.5V),
the maximum resistance must keep I_steady above I_open with margin.

Rule of thumb: I_steady should be at least 1.5× I_open for reliable
opening (fast enough to not cause massive dead time).
""")

print(f"{'Resistor':>10} | {'R_total':>8} | {'I @ 14V':>8} | {'I @ 10.5V':>9} | {'I @ 9V':>7} | Opens @ cranking?")
print("-" * 78)

for R_b in [0, 1.0, 1.5, 2.0, 2.2, 2.7, 3.0, 3.3, 4.7, 5.6, 6.8, 10.0]:
    R_t = R_inj + R_b
    I_14 = V / R_t
    I_10 = V_crank / R_t
    I_9 = 9.0 / R_t
    
    if R_b == 0:
        label = "NONE"
    else:
        label = f"{R_b:.1f}Ω"
    
    # Estimate: if I_crank > 2.5A → YES, > 2.0A → MAYBE, < 2.0 → RISKY
    if I_10 > 3.0:
        status = "YES - reliable"
    elif I_10 > 2.5:
        status = "YES - probably"
    elif I_10 > 2.0:
        status = "MARGINAL"
    else:
        status = "NO - too little current"
    
    print(f"{label:>10} | {R_t:>7.1f}Ω | {I_14:>7.2f}A | {I_10:>8.2f}A | {I_9:>6.2f}A | {status}")

# =====================================================================
# POWER DISSIPATION IN RESISTOR
# =====================================================================
print(f"\n{'=' * 75}")
print("RESISTOR POWER DISSIPATION (must not exceed wattage rating)")
print(f"{'=' * 75}")

print(f"\n{'Resistor':>10} | {'I @ 14V':>8} | {'P_inst':>8} | {'P @ 5%':>8} | {'P @ 15%':>8} | {'P @ 45%':>8} | Min Watts")
print("-" * 85)

for R_b in [1.0, 1.5, 2.0, 2.2, 2.7, 3.0, 3.3, 4.7]:
    R_t = R_inj + R_b
    I = V / R_t
    P_inst = I**2 * R_b
    P_5 = P_inst * 0.05
    P_15 = P_inst * 0.15
    P_45 = P_inst * 0.45
    # Resistor should be rated at least 2× average max
    min_watts = max(P_45 * 2, 5)
    
    print(f"{R_b:>9.1f}Ω | {I:>7.2f}A | {P_inst:>7.1f}W | {P_5:>7.2f}W | {P_15:>7.2f}W | {P_45:>7.2f}W | {min_watts:>7.0f}W")

# =====================================================================
# RECOMMENDATION
# =====================================================================
print(f"\n{'=' * 75}")
print("★ SCIENTIFIC RECOMMENDATION ★")
print(f"{'=' * 75}")
print(f"""
The 3.3Ω resistor may be TOO LARGE for reliable cranking.

During cranking:
  Battery voltage: ~10.5V (can drop to 9V on weak battery)
  With 3.3Ω:  I = 10.5/5.3 = 1.98A  ← marginal/insufficient
  With 3.3Ω:  I = 9.0/5.3  = 1.70A  ← almost certainly won't open

The IWM500.01 was designed for 4A peak to open fast.
The pull-in threshold is unknown but estimated 2.0-3.0A.

BETTER RESISTOR CHOICES:
  1.5Ω 10W wirewound → I_crank = 10.5/3.5 = 3.0A ✓ reliable
  2.0Ω 10W wirewound → I_crank = 10.5/4.0 = 2.6A ✓ probably OK  
  2.2Ω 10W wirewound → I_crank = 10.5/4.2 = 2.5A ✓ borderline

  Current @ 14V with 2.2Ω: 14/4.2 = 3.33A
  Injector power with 2.2Ω: 3.33² × 2 = 22W instantaneous
  Much better than 98W (no resistor) and enough to open during cranking.

TO VERIFY: Measure your battery voltage while cranking.
  If > 11V → 2.2Ω will work
  If > 10V → 1.5Ω is safer
  If < 10V → fix your battery first

THE DEFINITIVE TEST:
  1. Remove the resistor temporarily
  2. Measure battery voltage while cranking (multimeter on battery terminals)
  3. This gives you V_crank
  4. Choose resistor so that V_crank / (2 + R_ballast) > 2.5A
  5. Solve: R_ballast < (V_crank / 2.5) - 2.0
     If V_crank = 10.5V: R_ballast < 2.2Ω
     If V_crank = 11.0V: R_ballast < 2.4Ω
     If V_crank = 12.0V: R_ballast < 2.8Ω
""")

# =====================================================================
# UNKNOWN: INDUCTANCE
# =====================================================================
print(f"{'=' * 75}")
print("NOTE ON UNKNOWN INDUCTANCE")
print(f"{'=' * 75}")
print(f"""
The exact dead time (injOpen) depends on the coil inductance L,
which is NOT in any IWM500.01 datasheet we could find.

Typical range for 2Ω SPI injectors: L = 2-6 mH
Time constant τ = L/R:
  Without resistor: τ = L/2 = 1-3 ms
  With 3.3Ω:        τ = L/5.3 = 0.4-1.1 ms

You can MEASURE L with a cheap LCR meter (~$15 on Amazon).
Or estimate it from the working injOpen once the engine runs.

But the FIRST problem to solve is: enough current to open
the injector during cranking. Without that, injOpen is irrelevant.
""")
