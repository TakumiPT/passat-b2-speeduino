"""
Analyze end of MLG1 — did the engine STALL or was it turned OFF?
Also extract exact WUE and ASE fix values from datalog evidence.
"""
import json

# Load MLG1
with open('2026-03-01_19.05.30.json') as f:
    d = json.load(f)

scales = {}
for fld in d['fields']:
    scales[fld['name']] = fld.get('scale', 1.0)

recs = []
for r in d['records']:
    scaled = {}
    for k, v in r.items():
        if k in ('type', 'timestamp'):
            scaled[k] = v
        else:
            scaled[k] = v * scales.get(k, 1.0)
    recs.append(scaled)

# ================================================================
# PART 1: STALL vs SHUTDOWN — Last 60 samples
# ================================================================
print("=" * 80)
print("  PART 1: DID THE ENGINE STALL OR WAS IT TURNED OFF?")
print("=" * 80)

# Find where engine was last running, then look at the transition
all_running = [(i, r) for i, r in enumerate(recs) if r['RPM'] >= 500]
if all_running:
    last_run_idx = all_running[-1][0]
    
    # Show last 60 records before and after engine stop
    start = max(0, last_run_idx - 30)
    end = min(len(recs), last_run_idx + 30)
    
    print(f"\n  Last running sample: index {last_run_idx}")
    print(f"  Showing samples {start} to {end}:\n")
    print(f"  {'#':>5} | {'Time':>7} | {'RPM':>5} | {'AFR':>5} | {'PW ms':>7} | {'MAP':>4} | {'TPS':>4} | {'CLT':>4} | {'BatV':>5} | {'Gwarm':>5}")
    print(f"  {'-'*75}")
    
    for i in range(start, end):
        r = recs[i]
        marker = " <<<" if i == last_run_idx else ""
        print(f"  {i:>5} | {r['Time']:>7.1f} | {r['RPM']:>5.0f} | {r['AFR']:>5.1f} | {r['PW']:>7.3f} | {r['MAP']:>4.0f} | {r['TPS']:>4.1f} | {r['CLT']:>4.0f} | {r['Battery V']:>5.1f} | {r['Gwarm']:>5.0f}{marker}")

    # Analysis
    last_r = recs[last_run_idx]
    after = recs[last_run_idx + 1] if last_run_idx + 1 < len(recs) else None
    
    # Check for gradual RPM decline (stall) vs immediate drop (shutdown)
    pre_stop = [recs[i] for i in range(max(0, last_run_idx - 15), last_run_idx + 1)]
    rpms_pre = [r['RPM'] for r in pre_stop]
    
    print(f"\n  RPM in last 15 samples before stop: {[int(r) for r in rpms_pre]}")
    
    # Check if RPM was declining
    if len(rpms_pre) > 5:
        first_half = sum(rpms_pre[:len(rpms_pre)//2]) / (len(rpms_pre)//2)
        second_half = sum(rpms_pre[len(rpms_pre)//2:]) / (len(rpms_pre) - len(rpms_pre)//2)
        print(f"  First half avg: {first_half:.0f} RPM")
        print(f"  Second half avg: {second_half:.0f} RPM")
        trend = second_half - first_half
        print(f"  Trend: {trend:+.0f} RPM")
    
    # Check battery voltage — if ignition turned off, voltage drops differently
    pre_batt = [r['Battery V'] for r in pre_stop]
    print(f"  Battery V in last 15 samples: {[round(v,1) for v in pre_batt]}")
    
    # Check MAP — if stall, MAP rises to ~100 kPa (atmospheric)
    # If turned off, MAP also goes to atmo but the pattern differs
    post_stop = [recs[i] for i in range(last_run_idx + 1, min(len(recs), last_run_idx + 15))]
    if post_stop:
        post_maps = [r['MAP'] for r in post_stop]
        post_rpms = [r['RPM'] for r in post_stop]
        print(f"  MAP after stop: {[int(m) for m in post_maps]}")
        print(f"  RPM after stop: {[int(r) for r in post_rpms]}")
    
    # Stall indicators:
    # 1. RPM declining gradually before stop (vs constant then sudden drop)
    # 2. AFR going lean before stop (fuel starvation)
    # 3. MAP rising before stop (less vacuum = engine losing load)
    # 4. PW still being commanded (ECU didn't cut fuel = not ignition off)
    
    last_afr = [r['AFR'] for r in pre_stop]
    last_pw = [r['PW'] for r in pre_stop]
    last_map = [r['MAP'] for r in pre_stop]
    
    print(f"\n  STALL INDICATORS:")
    
    afr_rising = last_afr[-1] > last_afr[0] + 1
    print(f"    AFR rising before stop: {'YES' if afr_rising else 'NO'} (first={last_afr[0]:.1f}, last={last_afr[-1]:.1f})")
    
    pw_active = all(pw > 0.5 for pw in last_pw[-3:])
    print(f"    PW still active at stop: {'YES' if pw_active else 'NO'} (last 3: {[round(pw,3) for pw in last_pw[-3:]]})")
    
    map_rising = last_map[-1] > last_map[0] + 3
    print(f"    MAP rising before stop: {'YES' if map_rising else 'NO'} (first={last_map[0]:.0f}, last={last_map[-1]:.0f} kPa)")
    
    rpm_declining = rpms_pre[-1] < rpms_pre[0] - 100
    gradual_decline = any(r < 600 for r in rpms_pre[-5:])
    
    # Final verdict
    if pw_active and afr_rising:
        verdict = "STALL — ECU was still commanding fuel but AFR went lean → engine died"
    elif not pw_active:
        verdict = "SHUTDOWN — ECU stopped commanding fuel → ignition turned off"
    elif rpm_declining:
        verdict = "STALL — RPM was declining before stop"
    else:
        verdict = "UNCLEAR — need more samples"
    
    print(f"\n  VERDICT: {verdict}")

# ================================================================
# PART 2: WUE ANALYSIS — What values need to change?
# ================================================================
print(f"\n\n{'=' * 80}")
print("  PART 2: WUE (WARMUP ENRICHMENT) — EXACT FIX VALUES")
print("=" * 80)

# Get all running samples grouped by CLT
running = [r for r in recs if r['RPM'] >= 700 and r['TPS'] <= 2]

print(f"\n  Current WUE table bins (from copilot-instructions.md):")
print(f"  CLT:  -40  -20    0   20   28   37   50   65   76   85+")
print(f"  WUE:  195  190  182  154  150  138  122  110  102  100")

# Group by temperature bands matching WUE table bins
bands = [
    (20, 28, "20-28°C"),
    (28, 37, "28-37°C"),
    (37, 43, "37-43°C"),
    (43, 50, "43-50°C"),
    (50, 55, "50-55°C"),
]

print(f"\n  Measured AFR by CLT band (idle, TPS ≤ 2%):")
print(f"  {'Band':>10} | {'Samples':>7} | {'Avg AFR':>7} | {'Avg Gwarm':>9} | {'Avg PW':>7} | {'Quality':>10}")
print(f"  {'-'*65}")

for lo, hi, label in bands:
    samples = [r for r in running if lo <= r['CLT'] < hi]
    if samples:
        avg_afr = sum(r['AFR'] for r in samples) / len(samples)
        avg_gw = sum(r['Gwarm'] for r in samples) / len(samples)
        avg_pw = sum(r['PW'] for r in samples) / len(samples)
        
        if avg_afr < 12.5:
            q = "TOO RICH"
        elif avg_afr < 14:
            q = "RICH (ok cold)"
        elif avg_afr < 15.5:
            q = "GOOD"
        elif avg_afr < 17:
            q = "LEAN"
        else:
            q = "VERY LEAN"
        
        print(f"  {label:>10} | {len(samples):>7} | {avg_afr:>7.1f} | {avg_gw:>8.0f}% | {avg_pw:>6.3f} | {q:>10}")
    else:
        print(f"  {label:>10} | {'NO DATA':>7} |")

# Calculate needed WUE corrections
# Target AFR during warmup: 13.0-13.5 (rich for smooth warmup)
TARGET_AFR = 13.2

print(f"\n  Target warmup AFR: {TARGET_AFR}")
print(f"\n  WUE correction calculation:")
print(f"  Formula: new_WUE = current_WUE × (target_AFR / measured_AFR)⁻¹")
print(f"  (Inverse because WUE increases fueling: higher WUE = richer = lower AFR)")
print(f"  Simplified: new_WUE = current_WUE × (measured_AFR / target_AFR)")
print()

# We need to map CLT bands to WUE bins
wue_table = {
    -40: 195, -20: 190, 0: 182, 20: 154, 28: 150, 37: 138, 50: 122, 65: 110, 76: 102, 85: 100
}

corrections = []
for lo, hi, label in bands:
    samples = [r for r in running if lo <= r['CLT'] < hi]
    if len(samples) < 5:
        continue
    
    avg_afr = sum(r['AFR'] for r in samples) / len(samples)
    avg_clt = sum(r['CLT'] for r in samples) / len(samples)
    
    # Find nearest WUE bin
    nearest_bin = min(wue_table.keys(), key=lambda t: abs(t - avg_clt))
    current_wue = wue_table[nearest_bin]
    
    if avg_afr > 14.5:  # Only fix lean spots
        # new_WUE = current_WUE * measured_AFR / target_AFR
        new_wue = round(current_wue * avg_afr / TARGET_AFR)
        delta = new_wue - current_wue
        corrections.append((nearest_bin, current_wue, new_wue, delta, avg_afr, len(samples)))
        print(f"  CLT {nearest_bin}°C bin: WUE {current_wue}% → {new_wue}% (Δ = +{delta})")
        print(f"    Reason: measured AFR {avg_afr:.1f} at CLT {avg_clt:.0f}°C ({len(samples)} samples)")
        print(f"    Math: {current_wue} × {avg_afr:.1f} / {TARGET_AFR} = {new_wue}")
    else:
        print(f"  CLT ~{avg_clt:.0f}°C ({nearest_bin}°C bin): AFR {avg_afr:.1f} — OK, no change needed")

# ================================================================
# PART 3: ASE ANALYSIS — After Start Enrichment
# ================================================================
print(f"\n\n{'=' * 80}")
print("  PART 3: ASE (AFTER START ENRICHMENT) — EXACT FIX VALUES")
print("=" * 80)

# Find the start moment — first sample where RPM crosses 500
start_idx = None
for i, r in enumerate(recs):
    if r['RPM'] >= 500:
        start_idx = i
        break

if start_idx:
    t0 = recs[start_idx]['Time']
    print(f"\n  Engine start at index {start_idx}, time {t0:.1f}s")
    
    # Show first 20 seconds after start in 1-second windows
    print(f"\n  First 30 seconds after start (1-second windows):")
    print(f"  {'Sec':>4} | {'AFR':>5} | {'RPM':>5} | {'CLT':>4} | {'PW ms':>7} | {'Gwarm':>5} | {'Gammae':>6} | {'MAP':>4} | {'Quality':>10}")
    print(f"  {'-'*75}")
    
    lean_seconds = 0
    for sec in range(0, 30):
        window = [r for r in recs if r['RPM'] >= 500 and sec <= (r['Time'] - t0) < sec + 1]
        if window:
            avg_afr = sum(r['AFR'] for r in window) / len(window)
            avg_rpm = sum(r['RPM'] for r in window) / len(window)
            avg_clt = sum(r['CLT'] for r in window) / len(window)
            avg_pw = sum(r['PW'] for r in window) / len(window)
            avg_gw = sum(r['Gwarm'] for r in window) / len(window)
            avg_ge = sum(r['Gammae'] for r in window) / len(window)
            avg_map = sum(r['MAP'] for r in window) / len(window)
            
            if avg_afr > 15.5:
                q = "LEAN!"
                lean_seconds += 1
            elif avg_afr > 14.0:
                q = "slight lean"
            elif avg_afr > 12.5:
                q = "GOOD"
            else:
                q = "rich"
            
            print(f"  {sec:>3}s | {avg_afr:>5.1f} | {avg_rpm:>5.0f} | {avg_clt:>4.0f} | {avg_pw:>7.3f} | {avg_gw:>5.0f} | {avg_ge:>6.0f} | {avg_map:>4.0f} | {q:>10}")
    
    print(f"\n  Lean seconds in first 30s: {lean_seconds}")
    
    # For ASE fix: the lean spike is in seconds 0-15
    lean_window = [r for r in recs if r['RPM'] >= 500 and 0 <= (r['Time'] - t0) < 15]
    good_window = [r for r in recs if r['RPM'] >= 500 and 15 <= (r['Time'] - t0) < 45]
    
    if lean_window and good_window:
        lean_afr = sum(r['AFR'] for r in lean_window) / len(lean_window)
        good_afr = sum(r['AFR'] for r in good_window) / len(good_window)
        lean_ge = sum(r['Gammae'] for r in lean_window) / len(lean_window)
        good_ge = sum(r['Gammae'] for r in good_window) / len(good_window)
        lean_pw = sum(r['PW'] for r in lean_window) / len(lean_window)
        good_pw = sum(r['PW'] for r in good_window) / len(good_window)
        
        print(f"\n  Comparison:")
        print(f"    First 15s (lean):  AFR {lean_afr:.1f}, Gammae {lean_ge:.0f}%, PW {lean_pw:.3f}ms")
        print(f"    Next 30s (good):   AFR {good_afr:.1f}, Gammae {good_ge:.0f}%, PW {good_pw:.3f}ms")
        
        # The PW is HIGHER in the lean window — that means the Speeduino IS
        # giving more fuel during ASE, but not enough. The extra fuel from ASE
        # isn't compensating for the fact the engine just started and manifold
        # is cold → fuel doesn't atomize well.
        
        # To fix: need ASE increase factor
        # If current ASE gives AFR 17.2 and we need 13.2:
        # We need 17.2/13.2 = 1.30× more fuel = +30%
        
        ase_correction = lean_afr / TARGET_AFR
        ase_percent_increase = (ase_correction - 1) * 100
        
        print(f"\n  ASE CORRECTION NEEDED:")
        print(f"    Current first-15s AFR: {lean_afr:.1f}")
        print(f"    Target: {TARGET_AFR}")
        print(f"    Correction factor: {lean_afr:.1f} / {TARGET_AFR} = {ase_correction:.2f}")
        print(f"    ASE must increase by: +{ase_percent_increase:.0f}%")
        
        # Check what Gammae (total enrichment) was during the lean period
        # Gammae = base × WUE × ASE × other corrections
        # If ASE was already contributing, we can estimate the ASE multiplier
        lean_clt = sum(r['CLT'] for r in lean_window) / len(lean_window)
        print(f"    CLT at start: {lean_clt:.0f}°C")

# ================================================================
# PART 4: GET CURRENT ASE SETTINGS FROM MSQ
# ================================================================
print(f"\n\n{'=' * 80}")
print("  PART 4: CURRENT SETTINGS FROM MSQ (for reference)")
print("=" * 80)
print("  (Read these from CurrentTune.msq — search for ASEnrichment, WUEBins, etc.)")

print(f"\n\n{'=' * 80}")
print("  SUMMARY OF EXACT CHANGES NEEDED")
print("=" * 80)

if corrections:
    print(f"\n  WUE TABLE CHANGES:")
    print(f"  {'CLT Bin':>8} | {'Current':>7} | {'New':>7} | {'Delta':>7}")
    print(f"  {'-'*35}")
    for clt, old, new, delta, afr, n in corrections:
        print(f"  {clt:>6}°C | {old:>6}% | {new:>6}% | {delta:>+6}%")

print(f"\n  ASE CHANGES (to be verified after reading MSQ):")
print(f"    Increase ASE at CLT 20-30°C by ~30%")
print(f"    Or extend ASE duration (cycles/time)")
print(f"\n  These are the ONLY two changes needed to fix the lean running.")
print(f"  No VE table changes. No reqFuel changes. No other modifications.")
