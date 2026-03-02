"""
FINAL definitive analysis — Check ALL factors causing 43-48°C lean.
Includes VE table check, IAT effect, and steady-state filtering.
"""
import json

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

# Find start time
start_time = None
for r in recs:
    if r['RPM'] >= 500:
        start_time = r['Time']
        break

ASE_END = 17
post_ase = [r for r in recs if r['RPM'] >= 700 and r['TPS'] <= 2
            and (r['Time'] - start_time) >= ASE_END]

# =========================================================
# Check ALL available fields for the 37-43 vs 43-48 comparison
# =========================================================
print("=" * 80)
print("  FULL COMPARISON: 37-43°C (OK) vs 43-48°C (LEAN)")
print("=" * 80)

good = [r for r in post_ase if 37 <= r['CLT'] < 43 and 900 <= r['RPM'] <= 1050]
lean = [r for r in post_ase if 43 <= r['CLT'] < 48 and 900 <= r['RPM'] <= 1050]

print(f"\n  Filtered for steady-state idle (RPM 900-1050, TPS ≤ 2):")
print(f"  37-43°C: {len(good)} samples")
print(f"  43-48°C: {len(lean)} samples")

# Show ALL fields
all_fields = [k for k in recs[0].keys() if k not in ('type', 'timestamp')]
# Pick the interesting ones
fields_to_compare = ['RPM', 'MAP', 'AFR', 'PW', 'CLT', 'IAT', 'Battery V', 
                     'Gwarm', 'Gammae', 'TPS', 'Accel Enrich', 'Duty Cycle',
                     'Gbattery', 'Dwell']

print(f"\n  {'Field':>15} | {'37-43°C':>10} | {'43-48°C':>10} | {'Change':>8} | {'%':>7}")
print(f"  {'-'*60}")

for field in fields_to_compare:
    if field in recs[0]:
        g_avg = sum(r[field] for r in good) / len(good) if good else 0
        l_avg = sum(r[field] for r in lean) / len(lean) if lean else 0
        delta = l_avg - g_avg
        pct = (l_avg/g_avg - 1) * 100 if g_avg != 0 else 0
        print(f"  {field:>15} | {g_avg:>10.2f} | {l_avg:>10.2f} | {delta:>+8.2f} | {pct:>+6.1f}%")

# Check if Gbattery changed (injector opening time correction from voltage)
print(f"\n  KEY FINDING: Gbattery (battery voltage correction factor)")
if 'Gbattery' in recs[0]:
    g_bat = sum(r['Gbattery'] for r in good) / len(good) if good else 0
    l_bat = sum(r['Gbattery'] for r in lean) / len(lean) if lean else 0
    print(f"    37-43°C: Gbattery = {g_bat:.1f}%")
    print(f"    43-48°C: Gbattery = {l_bat:.1f}%")
    bat_effect = (l_bat/g_bat - 1) * 100 if g_bat else 0
    print(f"    Change: {bat_effect:+.1f}%")

# Now show EXACTLY what's in the fields
print(f"\n  All available datalog fields:")
for f in sorted(recs[0].keys()):
    if f not in ('type', 'timestamp'):
        print(f"    {f}: scale={scales.get(f, 1.0)}")

# =========================================================
# Check steady-state at 46°C specifically (excluding transient)
# =========================================================
print(f"\n\n{'=' * 80}")
print("  STEADY-STATE CHECK: 46-47°C ONLY (no transients)")
print("=" * 80)

# The last ~30 seconds of the run are steady-state at 46-47°C
# From the stall analysis: samples 2440-2470 are all at 46-47°C, RPM 937-996
# These are clean steady-state idle
late_lean = [r for r in post_ase if r['CLT'] >= 46 and r['CLT'] <= 47.5 
             and r['RPM'] >= 900 and r['RPM'] <= 1050
             and r['Time'] > 160]  # last few seconds, guaranteed steady

# Also get clean steady-state at 40-42°C for comparison  
# These should be 50-100 seconds into the run
clean_good = [r for r in post_ase if r['CLT'] >= 40 and r['CLT'] <= 42
              and r['RPM'] >= 900 and r['RPM'] <= 1050]

print(f"\n  Clean steady-state 40-42°C: {len(clean_good)} samples")
print(f"  Clean steady-state 46-47°C (t>160s): {len(late_lean)} samples")

if clean_good and late_lean:
    for field in ['AFR', 'PW', 'MAP', 'RPM', 'CLT', 'Gwarm', 'Gammae', 'Gbattery', 'IAT', 'Battery V', 'Duty Cycle']:
        if field in recs[0]:
            g = sum(r[field] for r in clean_good) / len(clean_good)
            l = sum(r[field] for r in late_lean) / len(late_lean)
            pct = (l/g - 1) * 100 if g else 0
            print(f"    {field:>15}: {g:>8.2f} → {l:>8.2f} ({pct:>+6.1f}%)")
    
    # Calculate PW ratio vs Gammae ratio
    g_pw = sum(r['PW'] for r in clean_good) / len(clean_good)
    l_pw = sum(r['PW'] for r in late_lean) / len(late_lean)
    g_ge = sum(r['Gammae'] for r in clean_good) / len(clean_good)
    l_ge = sum(r['Gammae'] for r in late_lean) / len(late_lean)
    
    pw_ratio = l_pw / g_pw
    ge_ratio = l_ge / g_ge
    unexplained = pw_ratio / ge_ratio
    
    print(f"\n    PW ratio: {pw_ratio:.4f} (= {(pw_ratio-1)*100:+.1f}%)")
    print(f"    Gammae ratio: {ge_ratio:.4f} (= {(ge_ratio-1)*100:+.1f}%)")
    print(f"    Unexplained: {unexplained:.4f} (= {(unexplained-1)*100:+.1f}%)")
    
    if 'Gbattery' in recs[0]:
        g_gb = sum(r['Gbattery'] for r in clean_good) / len(clean_good)
        l_gb = sum(r['Gbattery'] for r in late_lean) / len(late_lean)
        gb_ratio = l_gb / g_gb if g_gb else 1
        print(f"    Gbattery ratio: {gb_ratio:.4f} (= {(gb_ratio-1)*100:+.1f}%)")
        fully_explained = pw_ratio / (ge_ratio * gb_ratio)
        print(f"    After Gbattery: {fully_explained:.4f} (= {(fully_explained-1)*100:+.1f}%)")

# =========================================================
# VE TABLE CHECK at operating point
# =========================================================
print(f"\n\n{'=' * 80}")
print("  VE TABLE VALUES AT OPERATING POINT")
print("=" * 80)

# VE table from MSQ
rpm_bins = [500, 700, 900, 1200, 1500, 1800, 2200, 2700, 3000, 3400, 3900, 4300, 4800, 5200, 5700, 6200]
map_bins = [16, 26, 30, 36, 40, 46, 50, 56, 60, 66, 70, 76, 86, 90, 96, 100]
ve = [
    [30, 30, 32, 35, 39, 43, 47, 50, 53, 56, 59, 61, 63, 65, 63, 61],  # MAP 16
    [31, 31, 33, 36, 40, 43, 45, 51, 54, 57, 60, 62, 64, 66, 64, 62],  # MAP 26
    [32, 32, 34, 36, 41, 45, 49, 52, 55, 58, 61, 63, 65, 67, 65, 63],  # MAP 30
    [34, 34, 36, 34, 43, 47, 51, 54, 57, 60, 63, 65, 67, 69, 67, 65],  # MAP 36
    [36, 36, 38, 34, 45, 49, 53, 56, 59, 62, 65, 67, 69, 71, 69, 67],  # MAP 40
    [38, 38, 40, 43, 47, 51, 55, 58, 61, 64, 67, 69, 71, 73, 71, 69],  # MAP 46
    [40, 40, 42, 45, 49, 53, 57, 60, 63, 66, 69, 71, 73, 75, 73, 71],  # MAP 50
    # ... rest not needed for idle
]

# At RPM ~970, MAP ~38
rpm = 970
map_val = 38

# RPM interpolation
rpm_lo_idx = max(i for i, r in enumerate(rpm_bins) if r <= rpm)
rpm_hi_idx = rpm_lo_idx + 1
rpm_frac = (rpm - rpm_bins[rpm_lo_idx]) / (rpm_bins[rpm_hi_idx] - rpm_bins[rpm_lo_idx])

# MAP interpolation
map_lo_idx = max(i for i, m in enumerate(map_bins) if m <= map_val)
map_hi_idx = map_lo_idx + 1
map_frac = (map_val - map_bins[map_lo_idx]) / (map_bins[map_hi_idx] - map_bins[map_lo_idx])

print(f"\n  Operating point: RPM={rpm}, MAP={map_val}")
print(f"  RPM between {rpm_bins[rpm_lo_idx]} and {rpm_bins[rpm_hi_idx]} (frac={rpm_frac:.3f})")
print(f"  MAP between {map_bins[map_lo_idx]} and {map_bins[map_hi_idx]} (frac={map_frac:.3f})")

v00 = ve[map_lo_idx][rpm_lo_idx]
v01 = ve[map_lo_idx][rpm_hi_idx]
v10 = ve[map_hi_idx][rpm_lo_idx]
v11 = ve[map_hi_idx][rpm_hi_idx]

print(f"\n  VE corner values:")
print(f"    VE(RPM {rpm_bins[rpm_lo_idx]}, MAP {map_bins[map_lo_idx]}): {v00}")
print(f"    VE(RPM {rpm_bins[rpm_hi_idx]}, MAP {map_bins[map_lo_idx]}): {v01} {'← Feb28 corrected!' if v01 != v00 else ''}")
print(f"    VE(RPM {rpm_bins[rpm_lo_idx]}, MAP {map_bins[map_hi_idx]}): {v10}")
print(f"    VE(RPM {rpm_bins[rpm_hi_idx]}, MAP {map_bins[map_hi_idx]}): {v11} {'← Feb28 corrected!' if v11 != v10 else ''}")

# Bilinear interpolation
ve_interp = (1-rpm_frac)*(1-map_frac)*v00 + rpm_frac*(1-map_frac)*v01 + \
            (1-rpm_frac)*map_frac*v10 + rpm_frac*map_frac*v11
print(f"\n  Interpolated VE at ({rpm}, {map_val}): {ve_interp:.1f}%")

# Show the Feb 28 corrected values that create a valley
print(f"\n  VE values at RPM 1200 (col 4) showing the corrected valley:")
for i, m in enumerate(map_bins[:7]):
    print(f"    MAP {m:>3}: VE = {ve[i][3]} {'← corrected (was higher)' if m in [30, 36, 40] else ''}")

print(f"\n  VE values at RPM 900 (col 3) for comparison:")
for i, m in enumerate(map_bins[:7]):
    print(f"    MAP {m:>3}: VE = {ve[i][2]}")

print(f"\n  FINDING: At RPM 1200, VE drops from 36→34→34 at MAP 30→36→40")
print(f"  This is the Feb 28 hot-idle correction creating a local minimum.")
print(f"  At RPM 970, this is partially masked by RPM 900 values (which are normal).")

# =========================================================
# NOW calculate the FINAL WUE correction with all factors accounted
# =========================================================
print(f"\n\n{'=' * 80}")
print("  DEFINITIVE WUE CORRECTION")
print("=" * 80)

# Use the cleanest steady-state comparison
if clean_good and late_lean:
    g_afr_ss = sum(r['AFR'] for r in clean_good) / len(clean_good)
    l_afr_ss = sum(r['AFR'] for r in late_lean) / len(late_lean)
    g_gw = sum(r['Gwarm'] for r in clean_good) / len(clean_good)
    l_gw = sum(r['Gwarm'] for r in late_lean) / len(late_lean)
    g_pw_ss = sum(r['PW'] for r in clean_good) / len(clean_good)
    l_pw_ss = sum(r['PW'] for r in late_lean) / len(late_lean)
    
    TARGET = 13.2
    
    print(f"\n  Clean steady-state data:")
    print(f"    40-42°C: AFR {g_afr_ss:.1f}, Gwarm {g_gw:.0f}%, PW {g_pw_ss:.3f}ms")
    print(f"    46-47°C: AFR {l_afr_ss:.1f}, Gwarm {l_gw:.0f}%, PW {l_pw_ss:.3f}ms")
    
    # Method: use the PW ratio needed, not just the Gwarm ratio
    # Because other factors (Gbattery, etc.) also change
    # PW_needed = current_PW × (current_AFR / target_AFR)
    pw_needed = l_pw_ss * (l_afr_ss / TARGET)
    pw_increase_pct = (pw_needed / l_pw_ss - 1) * 100
    
    print(f"\n  At 46-47°C:")
    print(f"    Current PW: {l_pw_ss:.3f}ms → Needed PW: {pw_needed:.3f}ms (+{pw_increase_pct:.0f}%)")
    
    # The needed PW increase must come from WUE (since VE, battery, etc. are what they are)
    # new_WUE = old_WUE × (needed_PW / current_PW) = old_WUE × (current_AFR / target_AFR)
    new_gwarm_needed = round(l_gw * l_afr_ss / TARGET)
    print(f"    Current Gwarm: {l_gw:.0f}% → Needed: {new_gwarm_needed}%")
    
    # Now solve for WUE bins
    # At 46.5°C (midpoint of 46-47 range):
    # WUE = WUE_37 + (46.5-37)/(50-37) × (WUE_50 - WUE_37)
    clt_target = 46.5
    frac = (clt_target - 37) / (50 - 37)  # = 0.731
    
    wue_37_current = 138
    wue_50_current = 122
    
    print(f"\n  Interpolation at {clt_target}°C: frac = {frac:.3f} (between 37°C and 50°C bins)")
    print(f"  Current: {wue_37_current} + {frac:.3f} × ({wue_50_current} - {wue_37_current}) = {wue_37_current + frac*(wue_50_current - wue_37_current):.1f}%")
    
    # Strategy: increase both 37°C and 50°C to maintain monotonic AND hit target
    # Constraint 1: new_37 ≥ new_50 + 2 (monotonic with margin)
    # Constraint 2: new_37 + frac × (new_50 - new_37) ≈ new_gwarm_needed at 46.5°C
    # Constraint 3: Don't make 40-42°C too rich (currently AFR 13.0)
    
    # Try various combinations
    print(f"\n  Candidate WUE changes (37°C, 50°C) → WUE at 46.5°C → predicted AFR at 46.5°C → AFR at 40°C:")
    print(f"  {'37°C→':>8} | {'50°C→':>8} | {'WUE@46.5':>9} | {'AFR@46.5':>8} | {'WUE@40':>8} | {'AFR@40':>7} | {'OK?':>6}")
    print(f"  {'-'*72}")
    
    best = None
    for new_37 in range(138, 170, 2):
        for new_50 in range(122, new_37, 2):  # monotonic: new_50 < new_37
            wue_at_46 = new_37 + frac * (new_50 - new_37)
            pred_afr_46 = l_afr_ss * (l_gw / wue_at_46)
            
            # AFR at 40°C
            frac_40 = (40 - 37) / (50 - 37)  # = 0.231
            wue_at_40 = new_37 + frac_40 * (new_50 - new_37)
            pred_afr_40 = g_afr_ss * (g_gw / wue_at_40) if g_gw else 0
            
            # Check constraints
            ok_46 = 12.5 <= pred_afr_46 <= 14.0
            ok_40 = 11.5 <= pred_afr_40 <= 14.0
            
            if ok_46 and ok_40:
                label = "✅"
                if best is None or (abs(pred_afr_46 - 13.2) < abs(best['afr46'] - 13.2)):
                    best = {'new_37': new_37, 'new_50': new_50, 
                           'wue46': wue_at_46, 'afr46': pred_afr_46,
                           'wue40': wue_at_40, 'afr40': pred_afr_40}
            elif ok_46:
                label = "⚠️ 40°C"
            elif ok_40:
                label = "⚠️ 46°C"
            else:
                label = "❌"
                continue
            
            # Only print OK or close ones
            if ok_46 and ok_40:
                print(f"  {new_37:>5}   | {new_50:>5}   | {wue_at_46:>8.1f}% | {pred_afr_46:>7.1f}  | {wue_at_40:>7.1f}% | {pred_afr_40:>6.1f}  | {label}")
    
    if best:
        print(f"\n  ★ BEST FIT:")
        print(f"    37°C bin: {wue_37_current}% → {best['new_37']}% (Δ = +{best['new_37']-wue_37_current})")
        print(f"    50°C bin: {wue_50_current}% → {best['new_50']}% (Δ = +{best['new_50']-wue_50_current})")
        print(f"    Predicted AFR at 46.5°C: {best['afr46']:.1f} (target: 13.2)")
        print(f"    Predicted AFR at 40°C: {best['afr40']:.1f} (currently: {g_afr_ss:.1f})")
        
        # Cross-checks
        # At 32°C (between 28°C=150 and 37°C=new_37):
        frac_32 = (32 - 28) / (37 - 28)
        wue_32_new = 150 + frac_32 * (best['new_37'] - 150)
        wue_32_old = 150 + frac_32 * (138 - 150)
        print(f"    Cross-check at 32°C: WUE {wue_32_old:.0f}% → {wue_32_new:.0f}% (AFR ~{12.6*(148/wue_32_new):.1f})")
        
        # At 55°C (between 50°C=new_50 and 65°C=110):
        frac_55 = (55 - 50) / (65 - 50)
        wue_55_new = best['new_50'] + frac_55 * (110 - best['new_50'])
        wue_55_old = 122 + frac_55 * (110 - 122)
        print(f"    Cross-check at 55°C: WUE {wue_55_old:.0f}% → {wue_55_new:.0f}% (no data to verify)")
        
        # At 43°C
        frac_43 = (43 - 37) / (50 - 37)
        wue_43_new = best['new_37'] + frac_43 * (best['new_50'] - best['new_37'])
        wue_43_old = 138 + frac_43 * (122 - 138)
        pred_afr_43 = 13.0 * (135 / wue_43_new)  # using 40-43 data
        print(f"    Cross-check at 43°C: WUE {wue_43_old:.0f}% → {wue_43_new:.0f}% (AFR ~{pred_afr_43:.1f})")

print()
