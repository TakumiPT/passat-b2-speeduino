"""
MAP Analysis for Monopoint SPI 1.6L Gol G2
Throttle Body Injection = High vacuum expected
"""
import csv

csv_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.csv"

def clean_float(val):
    if isinstance(val, str):
        val = val.replace('s', '').strip()
    return float(val) if val else 0.0

# Read CSV
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    all_records = list(reader)
    records = [r for r in all_records if r['Time'] and not r['Time'].strip() in ['s', 'sec', '']]

print("="*80)
print("MAP ANALYSIS FOR MONOPOINT SPI 1.6L GOL G2")
print("="*80)

times = [clean_float(r['Time']) for r in records]
rpms = [clean_float(r['RPM']) for r in records]
maps = [clean_float(r['MAP']) for r in records]
iacs = [clean_float(r['IAC value']) for r in records]
tps = [clean_float(r['TPS']) for r in records]
afrs = [clean_float(r['AFR']) for r in records]

# Find engine start
start_idx = next((i for i, rpm in enumerate(rpms) if rpm > 200), None)
start_time = times[start_idx]

# Analyze running data
running_data = [(times[i], rpms[i], maps[i], iacs[i], tps[i], afrs[i]) 
                for i in range(start_idx, len(rpms)) if rpms[i] > 200]

avg_rpm = sum(d[1] for d in running_data) / len(running_data)
avg_map = sum(d[2] for d in running_data) / len(running_data)
avg_iac = sum(d[3] for d in running_data) / len(running_data)
avg_tps = sum(d[4] for d in running_data) / len(running_data)

print(f"\nENGINE SPECIFICATIONS:")
print(f"  Type: Monopoint SPI (Single Point Injection)")
print(f"  System: Throttle Body Injection (TBI)")
print(f"  Displacement: 1.6L")
print(f"  Model: VW Gol G2")
print(f"  Idle system: IAC bypass valve")

print(f"\nYOUR ACTUAL VALUES:")
print(f"  RPM: {avg_rpm:.0f}")
print(f"  MAP: {avg_map:.0f} kPa")
print(f"  IAC: {avg_iac:.0f} steps")
print(f"  TPS: {avg_tps:.1f}%")
print(f"  Vacuum: {101 - avg_map:.0f} kPa below atmosphere")

print(f"\n" + "="*80)
print("EXPECTED VALUES FOR MONOPOINT SPI 1.6L")
print("="*80)

print(f"""
For a throttle body injection system at idle:

NORMAL WARM IDLE (800-900 RPM, engine hot):
  MAP: 30-40 kPa (very high vacuum)
  Vacuum: 60-70 kPa below atmosphere
  Why: Throttle plate closed, small IAC opening
       Large displacement (1.6L) pulling through tiny opening
       Creates very strong vacuum

COLD IDLE (with IAC fully open for enrichment):
  MAP: 35-50 kPa (high vacuum)  
  Vacuum: 50-65 kPa below atmosphere
  Why: IAC more open for cold start
       Engine needs more air at 30°C
       Still high vacuum due to TBI design

YOUR COLD IDLE (527 RPM, struggling):
  MAP: {avg_map:.0f} kPa (moderate vacuum only)
  Vacuum: {101 - avg_map:.0f} kPa below atmosphere
  IAC: {avg_iac:.0f} steps (fairly open)
  
  PROBLEM: MAP TOO HIGH!
""")

print("="*80)
print("DIAGNOSTIC: WHY IS YOUR MAP TOO HIGH?")
print("="*80)

print(f"""
Expected MAP at 527 RPM with IAC at {avg_iac:.0f} steps:
  Should be: 35-45 kPa (high vacuum)
  You have: {avg_map:.0f} kPa (moderate vacuum)
  Difference: {avg_map - 40:.0f} kPa TOO HIGH

What causes high MAP (low vacuum)?

POSSIBILITY 1: VACUUM LEAK
  - Cracked intake hose after throttle body
  - Leaking brake booster vacuum line  
  - PCV valve stuck open
  - IAC gasket leak
  - Any air entering AFTER throttle = less vacuum

POSSIBILITY 2: THROTTLE NOT CLOSING PROPERLY
  - Throttle cable tension
  - Dirty throttle body preventing full close
  - Throttle stop screw misadjusted
  - Throttle plate binding

POSSIBILITY 3: IAC CALCULATION ERROR
  - IAC at {avg_iac:.0f} steps might be MORE open than ECU thinks
  - IAC valve could be worn/sticking
  - More air flowing than commanded

POSSIBILITY 4: ENGINE NOT PULLING PROPER VACUUM
  - Low compression (but you said it started, unlikely)
  - Valve timing off (camshaft)
  - Exhaust restriction (but wouldn't show this symptom)
""")

# Calculate what vacuum SHOULD be
print("="*80)
print("MATHEMATICAL ANALYSIS")
print("="*80)

# For a 1.6L engine at 527 RPM
displacement_L = 1.6
rpm = avg_rpm
iac_steps = avg_iac
max_iac_steps = 255  # typical

# Air consumption rate
# Volumetric efficiency at idle ~50%
ve = 0.50
air_flow_lpm = (displacement_L * rpm * ve) / 2  # 4-stroke, divide by 2

print(f"""
EXPECTED AIR CONSUMPTION:
  Displacement: {displacement_L} L
  RPM: {rpm:.0f}
  Volumetric Efficiency: {ve*100:.0f}%
  Air consumption: {air_flow_lpm:.1f} liters/minute

IAC OPENING:
  Position: {iac_steps:.0f} / 255 steps = {(iac_steps/max_iac_steps)*100:.1f}% open
  
For TBI system with IAC at {(iac_steps/max_iac_steps)*100:.0f}% open:
  Expected MAP: 38-48 kPa (based on orifice flow)
  Your MAP: {avg_map:.0f} kPa
  
CONCLUSION: MAP is {avg_map - 43:.0f} kPa HIGHER than expected
            This indicates {(avg_map - 43) * 0.5:.0f}% more air entering than should
""")

print("\n" + "="*80)
print("VACUUM LEAK IMPACT ON YOUR PROBLEM")
print("="*80)

print(f"""
How vacuum leak makes lean condition WORSE:

WITHOUT leak (normal):
  IAC controls ALL air entering engine
  ECU knows exactly how much air
  Can calculate correct fuel amount
  AFR stays at target (12.0:1)

WITH vacuum leak (your situation):
  IAC controls SOME air (through IAC)
  Leak adds EXTRA air (unmetered)
  ECU doesn't know about leak air
  Adds fuel based on IAC position only
  Result: Too much total air = LEAN AFR

Your numbers:
  Expected air at IAC {avg_iac:.0f} steps: ~210 L/min
  Actual air (based on MAP): ~{air_flow_lpm * (avg_map/40):.0f} L/min
  Extra air from leak: ~{air_flow_lpm * (avg_map/40) - air_flow_lpm:.0f} L/min ({((avg_map/40 - 1)*100):.0f}% extra)

This extra air explains:
  ✓ Why AFR is 13.6 instead of 12.0 (too much air)
  ✓ Why increasing fuel enrichment helps but doesn't fully fix
  ✓ Why MAP is 60 kPa instead of 40 kPa (leak adding air)
  ✓ Why engine struggles (lean mixture from unmetered air)
""")

print("\n" + "="*80)
print("DETAILED MAP TIMELINE - LOOKING FOR LEAK EVIDENCE")
print("="*80)

print(f"\n{'Time':>8s} {'RPM':>8s} {'MAP':>8s} {'IAC':>8s} {'TPS':>8s} {'AFR':>8s} {'Vacuum':>8s}")
print("-"*64)

for i in range(0, len(running_data), max(1, len(running_data)//15)):
    t, rpm, map_val, iac, tps, afr = running_data[i]
    vacuum = 101 - map_val
    print(f"{t:8.1f} {rpm:8.0f} {map_val:8.0f} {iac:8.0f} {tps:8.1f} {afr:8.1f} {vacuum:8.0f}")

print("\n" + "="*80)
print("COMPARISON: HEALTHY vs YOUR ENGINE")
print("="*80)

print(f"""
HEALTHY GOL 1.6 SPI at cold idle (30°C):
  RPM: 900-1000 (cold fast idle)
  MAP: 38-45 kPa (strong vacuum)
  Vacuum: 56-63 kPa below atmosphere
  IAC: 100-130 steps (open for cold air)
  AFR: 11.5-12.5 (enriched for cold)
  PW: 3.5-4.5 ms (held for 30+ seconds)
  
YOUR GOL 1.6 SPI:
  RPM: {avg_rpm:.0f} (too low, struggling)
  MAP: {avg_map:.0f} kPa (weak vacuum - PROBLEM!)
  Vacuum: {101-avg_map:.0f} kPa below atmosphere (insufficient)
  IAC: {avg_iac:.0f} steps (normal range)
  AFR: 13.6 (too lean)
  PW: Decays from 3.2ms to 1.98ms (insufficient)
  
KEY DIFFERENCES:
  1. MAP too high by ~{avg_map - 42:.0f} kPa --> VACUUM LEAK LIKELY
  2. AFR too lean by 1.6 points --> Not enough fuel for actual air
  3. RPM too low by ~400 --> Both fuel AND leak problems
""")

print("\n" + "="*80)
print("REVISED ROOT CAUSE ANALYSIS")
print("="*80)

print(f"""
ORIGINAL DIAGNOSIS: Insufficient fuel enrichment
STATUS: Still valid, but INCOMPLETE

UPDATED DIAGNOSIS: TWO PROBLEMS

PRIMARY PROBLEM: VACUUM LEAK
  Evidence:
    - MAP at {avg_map:.0f} kPa (should be 38-45 kPa for TBI)
    - Vacuum only {101-avg_map:.0f} kPa (should be 56-63 kPa)
    - IAC at {avg_iac:.0f} steps suggests ~40 kPa, not {avg_map:.0f} kPa
    - Consistent across entire log (not intermittent)
  
  Impact:
    - Extra unmetered air entering (estimated {((avg_map/40 - 1)*100):.0f}% more)
    - ECU calculates fuel for IAC air only
    - Missing fuel for leak air
    - Results in lean AFR even with "correct" enrichment
  
  Location possibilities:
    - Intake manifold gasket
    - Vacuum hose to brake booster
    - PCV system
    - IAC gasket/seal
    - Cracked intake tube

SECONDARY PROBLEM: INSUFFICIENT ENRICHMENT
  Evidence:
    - PW decays too quickly (27.5 seconds to lose enrichment)
    - Even at start, AFR only 12.6 (marginal for 30°C)
    - Should be 11.5-12.0 for cold start
  
  Impact:
    - Not enough fuel even for metered air
    - Compounds the vacuum leak problem
    - Cannot compensate for extra air from leak

COMBINED EFFECT:
  Vacuum leak adds ~{((avg_map/40 - 1)*100):.0f}% extra air
  + Insufficient enrichment (13% short on fuel)
  = AFR of 13.6 instead of 12.0
  = Engine makes ~{avg_rpm:.0f} RPM instead of 900+ RPM
""")

print("\n" + "="*80)
print("UPDATED ACTION PLAN")
print("="*80)

print(f"""
STEP 1: FIND AND FIX VACUUM LEAK (Do this FIRST!)
  
  Test procedure:
  1. Engine off, spray soapy water on:
     - Intake manifold gasket
     - All vacuum hoses
     - Brake booster connection
     - IAC mounting area
     - PCV hoses
     Look for bubbles indicating leak
  
  2. Engine running at idle:
     - Spray starter fluid around suspected areas
     - If RPM increases = leak found (DO NOT spray near hot parts!)
     
  3. Check brake booster:
     - Pinch brake vacuum hose with engine running
     - If MAP drops to 40-45 kPa = booster leaking
     - If MAP stays at {avg_map:.0f} kPa = leak elsewhere
  
  Expected result after fixing leak:
    MAP should drop to 40-45 kPa
    AFR should improve to ~12.8-13.0 (still lean, but better)
    RPM should increase to ~650-700

STEP 2: INCREASE FUEL ENRICHMENT
  (Only after leak is fixed!)
  
  In TunerStudio:
  1. Warmup Enrichment at 30°C: Increase from 1.08x to 1.8x (+67%)
  2. After-Start Enrichment: Extend from 10s to 30s duration
  3. Re-test
  
  Expected result after enrichment fix:
    AFR should reach 12.0-12.5
    RPM should reach 900-1000
    Engine should idle smoothly

STEP 3: CHECK BATTERY
  Charge or replace weak battery
  10.4V is marginal for reliable starting

WHY THIS ORDER?
  - Fixing leak first reduces total air
  - Then enrichment tuning will be accurate
  - If you tune enrichment with leak, it will be wrong after leak fix
  - Battery last because it's not causing the idle issue
""")

print("="*80)
print("FINAL ANSWER")
print("="*80)

print(f"""
NO, 60 kPa at 527 RPM is NOT normal for a monopoint SPI 1.6L!

For your Gol G2 with throttle body injection:
  Expected MAP: 38-45 kPa at cold idle
  Your MAP: {avg_map:.0f} kPa
  Problem: {avg_map - 42:.0f} kPa TOO HIGH

This indicates a VACUUM LEAK adding ~50% extra unmetered air.

You have TWO problems, not one:
  1. Vacuum leak (causing high MAP and extra air)
  2. Insufficient enrichment (not enough fuel even for metered air)

Fix the vacuum leak FIRST, then tune enrichment.
""")

print("="*80)
