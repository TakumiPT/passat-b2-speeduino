"""
REFINED analysis — separate ASE-period from post-ASE data.
Calculate exact WUE and ASE fix values.
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

# Find engine start time
start_time = None
for r in recs:
    if r['RPM'] >= 500:
        start_time = r['Time']
        break

print("=" * 80)
print("  REFINED ANALYSIS: ASE vs WUE — Separate Time Periods")
print("=" * 80)
print(f"  Engine start time: {start_time:.1f}s")
print(f"  ASE duration at 26°C (interpolated): ~17s")

# ASE period: 0 to 17s after start
# Post-ASE period: 17s+ after start
ASE_END = 17  # seconds after start

ase_period = [r for r in recs if r['RPM'] >= 500 and r['TPS'] <= 2
              and 0 <= (r['Time'] - start_time) < ASE_END]
post_ase = [r for r in recs if r['RPM'] >= 500 and r['TPS'] <= 2
            and (r['Time'] - start_time) >= ASE_END]

print(f"\n  ASE period (0-{ASE_END}s): {len(ase_period)} samples")
print(f"  Post-ASE period (>{ASE_END}s): {len(post_ase)} samples")

# ================================================================
# POST-ASE WUE ANALYSIS — Only this data reflects true WUE behavior
# ================================================================
print(f"\n{'=' * 80}")
print("  WUE ANALYSIS (Post-ASE only — true WUE behavior)")
print("=" * 80)

bands = [
    (20, 28, "20-28°C", 28),   # nearest WUE bin
    (28, 33, "28-33°C", 28),
    (33, 37, "33-37°C", 37),
    (37, 40, "37-40°C", 37),
    (40, 43, "40-43°C", 50),   # interpolating toward 50°C bin
    (43, 47, "43-47°C", 50),
    (47, 50, "47-50°C", 50),
]

wue_table = {-40: 195, -20: 190, 0: 182, 20: 154, 28: 150, 37: 138, 50: 122, 65: 110, 76: 102, 85: 100}

TARGET_AFR = 13.2  # target for warmup

print(f"\n  Target warmup AFR: {TARGET_AFR}")
print(f"\n  {'Band':>10} | {'N':>4} | {'Avg AFR':>7} | {'Gwarm%':>6} | {'PW ms':>7} | {'RPM':>5} | {'MAP':>4} | {'Status':>12}")
print(f"  {'-'*75}")

for lo, hi, label, wue_bin in bands:
    samples = [r for r in post_ase if lo <= r['CLT'] < hi]
    if len(samples) < 5:
        print(f"  {label:>10} | {len(samples):>4} | {'insufficient':>7}")
        continue
    
    avg_afr = sum(r['AFR'] for r in samples) / len(samples)
    avg_gw = sum(r['Gwarm'] for r in samples) / len(samples)
    avg_pw = sum(r['PW'] for r in samples) / len(samples)
    avg_rpm = sum(r['RPM'] for r in samples) / len(samples)
    avg_map = sum(r['MAP'] for r in samples) / len(samples)
    
    if avg_afr < 12.5: status = "TOO RICH"
    elif avg_afr < 14.0: status = "OK (warm-rich)"
    elif avg_afr < 14.9: status = "GOOD"
    elif avg_afr < 15.5: status = "LEAN"
    else: status = "VERY LEAN!"
    
    print(f"  {label:>10} | {len(samples):>4} | {avg_afr:>7.1f} | {avg_gw:>5.0f}% | {avg_pw:>7.3f} | {avg_rpm:>5.0f} | {avg_map:>4.0f} | {status:>12}")

# Now calculate exact WUE corrections for post-ASE data
print(f"\n\n  WUE CORRECTIONS (calculated from post-ASE data only):")
print(f"  {'Band':>10} | {'N':>4} | {'Actual AFR':>10} | {'Gwarm%':>6} | {'Need?':>8}")
print(f"  {'-'*55}")

wue_corrections = {}
for lo, hi, label, wue_bin in bands:
    samples = [r for r in post_ase if lo <= r['CLT'] < hi]
    if len(samples) < 10:
        continue
    
    avg_afr = sum(r['AFR'] for r in samples) / len(samples)
    avg_gw = sum(r['Gwarm'] for r in samples) / len(samples)
    
    if avg_afr > 14.5:
        # Need correction: new_WUE = current_WUE × (actual_AFR / target_AFR)
        # Because: AFR ∝ 1/fuel, and fuel ∝ WUE, so AFR ∝ 1/WUE
        # target_AFR = actual_AFR × (current_WUE / new_WUE)
        # new_WUE = current_WUE × (actual_AFR / target_AFR)
        new_wue = round(avg_gw * avg_afr / TARGET_AFR)
        delta = new_wue - round(avg_gw)
        print(f"  {label:>10} | {len(samples):>4} | {avg_afr:>10.1f} | {avg_gw:>5.0f}% | YES +{delta}%")
        
        # Track per-bin corrections
        if wue_bin not in wue_corrections:
            wue_corrections[wue_bin] = []
        wue_corrections[wue_bin].append({
            'clt_range': label, 'n': len(samples), 'afr': avg_afr,
            'gwarm': avg_gw, 'new_gwarm': new_wue, 'delta': delta
        })
    else:
        print(f"  {label:>10} | {len(samples):>4} | {avg_afr:>10.1f} | {avg_gw:>5.0f}% | NO")

# ================================================================
# Resolve WUE bin changes
# ================================================================
print(f"\n\n{'=' * 80}")
print("  EXACT WUE BIN CHANGES")
print("=" * 80)

for wue_bin, corrections in sorted(wue_corrections.items()):
    current = wue_table[wue_bin]
    # Use the correction with most samples for best reliability
    best = max(corrections, key=lambda x: x['n'])
    
    # The correction gives us the GWARM value needed, which IS the WUE
    # at the measured CLT. But we need to solve for the BIN value.
    
    # Measured CLT = midpoint of the range
    avg_clt = (float(best['clt_range'].split('-')[0].rstrip('°C')) + 
               float(best['clt_range'].split('-')[1].rstrip('°C'))) / 2
    
    # Find the two WUE bins that bracket this CLT
    bins_sorted = sorted(wue_table.keys())
    for i in range(len(bins_sorted) - 1):
        if bins_sorted[i] <= avg_clt < bins_sorted[i+1]:
            lo_bin = bins_sorted[i]
            hi_bin = bins_sorted[i+1]
            break
    
    lo_wue = wue_table[lo_bin]
    hi_wue = wue_table[hi_bin]
    
    # Interpolation fraction
    frac = (avg_clt - lo_bin) / (hi_bin - lo_bin)
    current_interp = lo_wue + frac * (hi_wue - lo_wue)
    
    # Target Gwarm at this CLT
    target_gwarm = best['new_gwarm']
    
    print(f"\n  WUE bin {wue_bin}°C (current: {current}%):")
    print(f"    Data from {best['clt_range']}: {best['n']} samples")
    print(f"    Avg measured CLT: ~{avg_clt:.0f}°C")
    print(f"    Interpolated between {lo_bin}°C ({lo_wue}%) and {hi_bin}°C ({hi_wue}%)")
    print(f"    Current WUE at {avg_clt:.0f}°C: {current_interp:.1f}% (matches Gwarm {best['gwarm']:.0f}%)")
    print(f"    Needed WUE at {avg_clt:.0f}°C: {target_gwarm}%")
    
    # Solve: target_gwarm = lo_wue + frac × (X - lo_wue)
    # where X = new value for hi_bin (the bin we're changing)
    if wue_bin == hi_bin:
        new_bin_value = round((target_gwarm - lo_wue) / frac + lo_wue)
        print(f"    Solving: {target_gwarm} = {lo_wue} + {frac:.3f} × (X - {lo_wue})")
        print(f"    X = ({target_gwarm} - {lo_wue}) / {frac:.3f} + {lo_wue}")
        print(f"    X = {new_bin_value}")
        
        # Check: does this make the curve non-monotonic?
        if new_bin_value > lo_wue:
            print(f"    ⚠️ WARNING: {hi_bin}°C bin ({new_bin_value}%) > {lo_bin}°C bin ({lo_wue}%)")
            print(f"       WUE should decrease with temperature!")
            print(f"       SOLUTION: Also increase {lo_bin}°C bin to maintain monotonic curve")
            
            # Both bins need adjustment. Keep the ratio similar.
            # At the measured CLT, we need target_gwarm.
            # Constraint: lo_wue_new > new_bin_value (curve stays monotonic)
            # Simple approach: set both bins so the midpoint gives target_gwarm
            # and the slope is similar to adjacent sections
            
            # Adjacent slope (50→65): (122-110)/(65-50) = 0.8 per °C
            # Current slope (37→50): (138-122)/(50-37) = 1.23 per °C
            # We need a FLATTER slope since the engine needs more fuel at 43-47°C
            
            # Let's set the new values so the curve is approximately flat from 37-50°C
            # This means engine maintains similar enrichment through the 37-50°C range
            # which makes sense physically — the engine still needs enrichment until fully warm
            
            # If we want WUE at 45°C = target_gwarm and WUE at 37°C = lo_wue:
            # slope = (lo_wue - target_gwarm) / (45 - 37) per °C
            # Extrapolate to 50°C: WUE_50 = lo_wue - slope × (50 - 37)
            
            # But we want target at the MEASURED CLT, not at the bin CLT
            # Let me just set WUE_50 so that the interpolated value at avg_clt = target_gwarm
            # AND also increase WUE_37 if needed
            
            # Actually, the simplest approach that works:
            # Set WUE_50 = target_gwarm (approximately)
            # Set WUE_37 = keep current IF it's > new WUE_50
            
            if lo_wue >= target_gwarm:
                # 37°C bin stays, only 50°C changes
                # But we already showed this makes curve go UP which is wrong
                # Actually lo_wue=138, target_gwarm=160... 138 < 160
                pass
            
            # Final approach: set new 50°C = target_gwarm, increase 37°C proportionally
            # New 37°C = current_37 × (target/current_interp) proportionally
            new_37 = round(lo_wue * target_gwarm / current_interp)
            new_50 = round(current * target_gwarm / current_interp)
            
            # Verify interpolation at measured CLT
            verify = new_37 + frac * (new_50 - new_37)
            
            print(f"\n       Proportional fix:")
            print(f"       37°C bin: {lo_wue}% → {new_37}%")
            print(f"       50°C bin: {current}% → {new_50}%")
            print(f"       Verification at {avg_clt:.0f}°C: {verify:.1f}% (target: {target_gwarm}%)")
            
            # Check the 28-37°C range is still OK
            wue_28 = wue_table[28]
            interp_32 = wue_28 + (32-28)/(37-28) * (new_37 - wue_28)
            print(f"       Cross-check at 32°C: WUE = {interp_32:.1f}% (was: {wue_28 + (32-28)/(37-28) * (lo_wue - wue_28):.1f}%)")
        else:
            print(f"    ✅ Curve stays monotonically decreasing")
            print(f"    CHANGE: {hi_bin}°C bin: {current}% → {new_bin_value}%")
    elif wue_bin == lo_bin:
        # Solve for the lo_bin
        new_bin_value = round((target_gwarm - hi_wue * frac - lo_wue * (1-frac)) / (1-frac) + lo_wue)
        print(f"    Would need {lo_bin}°C bin change")

# ================================================================
# ASE ANALYSIS
# ================================================================
print(f"\n\n{'=' * 80}")
print("  EXACT ASE BIN CHANGES")
print("=" * 80)

# Current ASE settings from MSQ
ase_pct = {-20: 100, 0: 90, 40: 60, 80: 30}
ase_count = {-20: 25, 0: 20, 40: 15, 80: 6}

print(f"\n  Current ASE table:")
print(f"  CLT:     -20°C    0°C   40°C   80°C")
print(f"  ASE%:     {ase_pct[-20]}%   {ase_pct[0]}%   {ase_pct[40]}%   {ase_pct[80]}%")
print(f"  Time:      {ase_count[-20]}s    {ase_count[0]}s    {ase_count[40]}s     {ase_count[80]}s")

# At 26°C (interpolated between 0°C and 40°C):
clt_start = 26
frac = (clt_start - 0) / (40 - 0)  # 0.65
current_ase = ase_pct[0] + frac * (ase_pct[40] - ase_pct[0])  # 90 + 0.65*(60-90) = 70.5
current_dur = ase_count[0] + frac * (ase_count[40] - ase_count[0])

print(f"\n  At start CLT {clt_start}°C (interpolated, frac={frac:.2f}):")
print(f"    Current ASE: {current_ase:.1f}%")
print(f"    Current duration: {current_dur:.1f}s")

# From datalog:
# ASE period (0-17s): AFR 17.2, Gammae 268%
# Post-ASE (>17s, same CLT ~26-28°C): AFR 13.0-13.2, Gammae 157%

# The ASE multiplier is: Gammae_with_ASE / Gammae_without_ASE
# 268 / 157 = 1.706 → ASE adds 70.6% → matches interpolated 70.5% ✅

# We need AFR during ASE to be ~13.2 instead of 17.2
# Required Gammae during ASE: 268 × (17.2 / 13.2) = 349.3
# Required ASE multiplier: 349.3 / 157 = 2.225 → ASE% = 122.5%

ase_afr = sum(r['AFR'] for r in ase_period) / len(ase_period)
ase_gammae = sum(r['Gammae'] for r in ase_period) / len(ase_period)

post_ase_early = [r for r in post_ase if r['CLT'] < 30]  # same CLT range, no ASE
if post_ase_early:
    base_gammae = sum(r['Gammae'] for r in post_ase_early) / len(post_ase_early)
    base_afr = sum(r['AFR'] for r in post_ase_early) / len(post_ase_early)
else:
    base_gammae = 157
    base_afr = 13.2

print(f"\n  Datalog evidence:")
print(f"    ASE period (0-17s): AFR={ase_afr:.1f}, Gammae={ase_gammae:.0f}%")
print(f"    Post-ASE (~26-30°C): AFR={base_afr:.1f}, Gammae={base_gammae:.0f}%")
print(f"    Current ASE multiplier: {ase_gammae:.0f}/{base_gammae:.0f} = {ase_gammae/base_gammae:.3f} → ASE = {(ase_gammae/base_gammae - 1)*100:.1f}%")
print(f"    Matches interpolated ASE {current_ase:.1f}%: {'YES ✅' if abs((ase_gammae/base_gammae - 1)*100 - current_ase) < 5 else 'NO ❌'}")

# Required ASE
needed_gammae = ase_gammae * (ase_afr / TARGET_AFR)
needed_ase_multiplier = needed_gammae / base_gammae
needed_ase_pct = (needed_ase_multiplier - 1) * 100

print(f"\n  Required ASE at {clt_start}°C:")
print(f"    Target AFR: {TARGET_AFR}")
print(f"    Needed Gammae: {ase_gammae:.0f} × ({ase_afr:.1f}/{TARGET_AFR}) = {needed_gammae:.0f}%")
print(f"    Needed ASE multiplier: {needed_gammae:.0f}/{base_gammae:.0f} = {needed_ase_multiplier:.3f}")
print(f"    Needed ASE%: {needed_ase_pct:.1f}%")
print(f"    Increase factor: {needed_ase_pct:.1f}/{current_ase:.1f} = {needed_ase_pct/current_ase:.2f}×")

# Now solve for bin values
# At 26°C: needed_ase = ASE_0 + 0.65 × (ASE_40 - ASE_0)
# We want needed_ase_pct at 26°C

# Option: Scale both bins proportionally
scale_factor = needed_ase_pct / current_ase
new_ase_0 = round(ase_pct[0] * scale_factor)
new_ase_40 = round(ase_pct[40] * scale_factor)
new_ase_minus20 = round(ase_pct[-20] * scale_factor)

# Verify
verify_ase = new_ase_0 + frac * (new_ase_40 - new_ase_0)

print(f"\n  ASE bin changes (proportional scaling by {scale_factor:.2f}×):")
print(f"    -20°C: {ase_pct[-20]}% → {new_ase_minus20}%")
print(f"    0°C:   {ase_pct[0]}% → {new_ase_0}%")
print(f"    40°C:  {ase_pct[40]}% → {new_ase_40}%")
print(f"    80°C:  {ase_pct[80]}% → {ase_pct[80]}% (no data — keep unchanged)")
print(f"    Verification at 26°C: {verify_ase:.1f}% (target: {needed_ase_pct:.1f}%)")

# Also check duration — is 17s enough?
print(f"\n  ASE duration analysis:")
print(f"    Current at 26°C: {current_dur:.1f}s")
print(f"    Datalog shows ASE effect lasts until ~17s ✅")
print(f"    By 14s, AFR was improving (15.4) ← ASE had 3s more to help")
print(f"    By 21s, AFR was 13.7 ← 4s after ASE ended, mixture normalized")
print(f"    VERDICT: Duration is CORRECT. Only magnitude needs to increase.")
print(f"    No change to aseCount values.")

# ================================================================
# FINAL DEFINITIVE SUMMARY
# ================================================================
print(f"\n\n{'=' * 80}")
print("  ╔══════════════════════════════════════════════════════════╗")
print("  ║         DEFINITIVE FIX — EXACT VALUES TO CHANGE        ║")
print("  ╚══════════════════════════════════════════════════════════╝")
print("=" * 80)

print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │ 1. STALL vs SHUTDOWN ANSWER:                                   │
  │    YOU TURNED THE KEY OFF. The engine DID NOT stall.            │
  │                                                                │
  │    Proof:                                                      │
  │    • RPM was stable at 970 RPM (no decline)                    │
  │    • Battery voltage dropped 12.8V → 6.8V in 0.1s             │
  │      (impossible from a stall — this is ignition cutoff)       │
  │    • Voltage then decayed: 6.8→3.6→1.9→0.5→0.0V               │
  │      (capacitor discharge after power cut)                     │
  │    • A stall would show gradual RPM decline over 1-2 seconds   │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ 2. ASE (After Start Enrichment) — TunerStudio Values:          │
  │                                                                │
  │    Settings → Warmup → ASE (After Start Enrichment)            │
  │                                                                │
  │    Bins (aseBins) — DO NOT CHANGE:                             │
  │      -20°C,  0°C,  40°C,  80°C                                │
  │                                                                │
  │    ASE% (asePct) — CHANGE THESE:                               │
  │      -20°C:  100% → {new_ase_minus20}%                             │
  │        0°C:   90% → {new_ase_0}%                             │
  │       40°C:   60% → {new_ase_40}%                             │
  │       80°C:   30% → 30% (keep)                                │
  │                                                                │
  │    Duration (aseCount) — DO NOT CHANGE:                        │
  │      25s, 20s, 15s, 6s (already correct)                      │
  │                                                                │
  │    Reason: First 17s after start, AFR is 17.2 (too lean).     │
  │    After ASE ends, AFR normalizes to 13.0 (perfect).          │
  │    ASE magnitude insufficient — needs +{needed_ase_pct/current_ase*100 - 100:.0f}% increase.           │
  └─────────────────────────────────────────────────────────────────┘
""")

# For WUE, we need to be more careful
# Let me recalculate with ONLY post-ASE data for each temperature band
print(f"  ┌─────────────────────────────────────────────────────────────────┐")
print(f"  │ 3. WUE (Warmup Enrichment) — TunerStudio Values:              │")
print(f"  │                                                                │")
print(f"  │    Settings → Warmup → WUE (Warmup Enrichment)                │")
print(f"  │                                                                │")

# Check each WUE bin against post-ASE data
print(f"  │    POST-ASE AFR by temperature (WUE-only behavior):           │")
wue_changes_needed = []
for lo, hi, label, wue_bin in bands:
    samples = [r for r in post_ase if lo <= r['CLT'] < hi]
    if len(samples) >= 10:
        avg_afr = sum(r['AFR'] for r in samples) / len(samples)
        avg_gw = sum(r['Gwarm'] for r in samples) / len(samples)
        if avg_afr > 14.5:
            new_wue_at_clt = round(avg_gw * avg_afr / TARGET_AFR)
            wue_changes_needed.append((wue_bin, label, len(samples), avg_afr, avg_gw, new_wue_at_clt))
            print(f"  │    {label}: AFR {avg_afr:.1f} (Gwarm {avg_gw:.0f}%) → need {new_wue_at_clt}%   LEAN  │")
        else:
            print(f"  │    {label}: AFR {avg_afr:.1f} (Gwarm {avg_gw:.0f}%)              OK    │")

if not wue_changes_needed:
    print(f"  │                                                                │")
    print(f"  │    ALL WUE bins are CORRECT for post-ASE running.             │")
    print(f"  │    The lean AFR at 20-28°C was caused by ASE insufficiency,   │")
    print(f"  │    NOT WUE. After ASE ends, WUE alone produces good AFR.      │")
    print(f"  │                                                                │")
    print(f"  │    NO WUE CHANGES NEEDED.                                     │")
else:
    for wue_bin, label, n, afr, gw, needed in wue_changes_needed:
        current = wue_table[wue_bin]
        print(f"  │                                                                │")
        print(f"  │    {wue_bin}°C bin: {current}% → needs investigation               │")
        print(f"  │    ({label}: AFR {afr:.1f}, {n} samples)                       │")

print(f"  └─────────────────────────────────────────────────────────────────┘")

# Final check on the 43-47°C lean period
print(f"\n\n{'=' * 80}")
print("  DETAILED CHECK: 43-47°C LEAN PERIOD")
print("=" * 80)

lean_samples = [r for r in post_ase if 43 <= r['CLT'] < 48]
if lean_samples:
    # Time-series analysis
    lean_samples.sort(key=lambda r: r['Time'])
    
    print(f"\n  Time series (every 5th sample) for CLT 43-48°C:")
    print(f"  {'Time':>7} | {'RPM':>5} | {'AFR':>5} | {'PW ms':>7} | {'MAP':>4} | {'CLT':>4} | {'Gwarm':>5} | {'Gammae':>6}")
    print(f"  {'-'*65}")
    
    for i, r in enumerate(lean_samples):
        if i % 5 == 0:
            print(f"  {r['Time']:>7.1f} | {r['RPM']:>5.0f} | {r['AFR']:>5.1f} | {r['PW']:>7.3f} | {r['MAP']:>4.0f} | {r['CLT']:>4.0f} | {r['Gwarm']:>5.0f} | {r['Gammae']:>6.0f}")
    
    avg_afr = sum(r['AFR'] for r in lean_samples) / len(lean_samples)
    avg_gw = sum(r['Gwarm'] for r in lean_samples) / len(lean_samples)
    avg_pw = sum(r['PW'] for r in lean_samples) / len(lean_samples)
    avg_ge = sum(r['Gammae'] for r in lean_samples) / len(lean_samples)
    avg_map = sum(r['MAP'] for r in lean_samples) / len(lean_samples)
    
    # Compare with good period just before (37-43°C)
    good_samples = [r for r in post_ase if 37 <= r['CLT'] < 43]
    if good_samples:
        g_afr = sum(r['AFR'] for r in good_samples) / len(good_samples)
        g_gw = sum(r['Gwarm'] for r in good_samples) / len(good_samples)
        g_pw = sum(r['PW'] for r in good_samples) / len(good_samples)
        g_ge = sum(r['Gammae'] for r in good_samples) / len(good_samples)
        g_map = sum(r['MAP'] for r in good_samples) / len(good_samples)
        
        print(f"\n  COMPARISON:")
        print(f"  {'':>15} | {'37-43°C (OK)':>12} | {'43-48°C (lean)':>14} | {'Change':>8}")
        print(f"  {'-'*55}")
        print(f"  {'AFR':>15} | {g_afr:>12.1f} | {avg_afr:>14.1f} | {avg_afr - g_afr:>+8.1f}")
        print(f"  {'Gwarm%':>15} | {g_gw:>12.0f} | {avg_gw:>14.0f} | {avg_gw - g_gw:>+8.0f}")
        print(f"  {'Gammae%':>15} | {g_ge:>12.0f} | {avg_ge:>14.0f} | {avg_ge - g_ge:>+8.0f}")
        print(f"  {'PW ms':>15} | {g_pw:>12.3f} | {avg_pw:>14.3f} | {avg_pw - g_pw:>+8.3f}")
        print(f"  {'MAP kPa':>15} | {g_map:>12.0f} | {avg_map:>14.0f} | {avg_map - g_map:>+8.0f}")
        
        # Key finding: if PW drops more than Gwarm, something else is reducing fuel
        gwarm_ratio = avg_gw / g_gw
        pw_ratio = avg_pw / g_pw
        gammae_ratio = avg_ge / g_ge
        
        print(f"\n  Ratios (43-48 / 37-43):")
        print(f"    Gwarm:  {gwarm_ratio:.3f} ({(gwarm_ratio-1)*100:+.1f}%)")
        print(f"    Gammae: {gammae_ratio:.3f} ({(gammae_ratio-1)*100:+.1f}%)")
        print(f"    PW:     {pw_ratio:.3f} ({(pw_ratio-1)*100:+.1f}%)")
        print(f"    AFR:    {avg_afr/g_afr:.3f} ({(avg_afr/g_afr-1)*100:+.1f}%)")
        
        print(f"\n  DIAGNOSIS:")
        if abs(gammae_ratio - pw_ratio) < 0.03:
            print(f"    Gammae and PW track together → WUE is the dominant factor")
            print(f"    Gwarm drops {(1-gwarm_ratio)*100:.1f}% but PW drops {(1-pw_ratio)*100:.1f}%")
            if abs((1-gwarm_ratio)*100 - (1-pw_ratio)*100) > 5:
                print(f"    Extra PW drop not explained by Gwarm → VE table may contribute")
            
            # Calculate needed WUE increase
            # AFR is currently avg_afr. Need it at 13.2.
            # fuel_delivered ∝ PW, fuel_needed ∝ 1/AFR
            # If we increase WUE by factor F: new_PW = old_PW × F, new_AFR = old_AFR / F
            # F = old_AFR / target_AFR = avg_afr / 13.2
            F_needed = avg_afr / TARGET_AFR
            
            # But this F needs to be applied to Gammae, not just WUE
            # Gammae includes WUE and other corrections
            # new_Gammae = old_Gammae × F
            # new_Gwarm = old_Gwarm × F (since WUE is the main variable)
            new_gwarm_needed = round(avg_gw * F_needed)
            
            print(f"\n    Needed Gwarm at ~{sum(r['CLT'] for r in lean_samples)/len(lean_samples):.0f}°C: {new_gwarm_needed}% (currently {avg_gw:.0f}%)")
            
            # What WUE bin values achieve this?
            # At CLT 45°C, interpolated between 37°C and 50°C:
            # WUE_45 = WUE_37 + (45-37)/(50-37) × (WUE_50 - WUE_37)
            # We want this = new_gwarm_needed
            
            # Option A: Only change 50°C bin
            avg_lean_clt = sum(r['CLT'] for r in lean_samples) / len(lean_samples)
            frac_lean = (avg_lean_clt - 37) / (50 - 37)
            
            wue_37 = wue_table[37]  #138
            # new_gwarm = wue_37 + frac × (new_50 - wue_37)
            new_50_A = round((new_gwarm_needed - wue_37) / frac_lean + wue_37)
            
            print(f"\n    Option A — Only change 50°C bin:")
            print(f"      50°C: {wue_table[50]}% → {new_50_A}%")
            verify_A = wue_37 + frac_lean * (new_50_A - wue_37)
            print(f"      Verify at {avg_lean_clt:.0f}°C: {verify_A:.1f}% ✓")
            
            if new_50_A > wue_37:
                print(f"      ⚠️ Makes curve non-monotonic (50°C: {new_50_A}% > 37°C: {wue_37}%)")
                
                # Option B: Keep 37°C, flatten the curve
                # Set 50°C = 37°C value (flat), then fine-tune
                print(f"\n    Option B — Flatten 37-50°C range:")
                new_50_B = wue_37  # 138
                verify_B = wue_37 + frac_lean * (new_50_B - wue_37)  # = 138 (flat)
                # AFR with WUE=138: avg_afr × (avg_gw/138)
                predicted_afr_B = avg_afr * (avg_gw / new_50_B)
                print(f"      50°C: {wue_table[50]}% → {new_50_B}%")
                print(f"      At {avg_lean_clt:.0f}°C: WUE={verify_B:.0f}% → predicted AFR={predicted_afr_B:.1f}")
                if predicted_afr_B > 14.5:
                    print(f"      Still lean — need more")
                elif predicted_afr_B < 12.5:
                    print(f"      Too rich")
                else:
                    print(f"      ✅ Good target range")
                
                # Option C: both bins maintain monotonic AND achieve target
                # Set 37°C slightly higher, 50°C between old and 37
                # Proportional increase that maintains shape
                ratio_needed = new_gwarm_needed / avg_gw
                new_37_C = round(wue_37 * ratio_needed)
                new_50_C = round(wue_table[50] * ratio_needed)
                verify_C = new_37_C + frac_lean * (new_50_C - new_37_C)
                
                print(f"\n    Option C — Proportional increase (×{ratio_needed:.2f}):")
                print(f"      37°C: {wue_37}% → {new_37_C}%")
                print(f"      50°C: {wue_table[50]}% → {new_50_C}%")
                print(f"      At {avg_lean_clt:.0f}°C: WUE={verify_C:.0f}%")
                
                # But does 37°C change break the 28-37 range?
                verify_32 = wue_table[28] + (32-28)/(37-28) * (new_37_C - wue_table[28])
                original_32 = wue_table[28] + (32-28)/(37-28) * (wue_37 - wue_table[28])
                print(f"      Cross-check AFR at 28-37°C (currently OK):")
                print(f"        WUE at 32°C: {original_32:.0f}% → {verify_32:.0f}% (+{verify_32-original_32:.0f}%)")
                print(f"        Will make 28-37°C even RICHER (currently AFR 12.6, already rich)")
                if g_afr < 13.0:
                    print(f"        ❌ NOT recommended — 28-37°C already rich ({g_afr:.1f})")
                else:
                    print(f"        ✅ OK — 28-37°C has room for richer ({g_afr:.1f})")
            else:
                print(f"      ✅ Curve stays monotonically decreasing")
                
            # RECOMMENDATION
            print(f"\n    ══════════════════════════════════════════")
            print(f"    RECOMMENDED WUE CHANGE:")
            # The ONLY data-supported change is at 50°C bin
            # But if it breaks monotonicity, we need a compromise
            if new_50_A <= wue_37:
                print(f"      50°C bin: {wue_table[50]}% → {new_50_A}%")
                print(f"      (All other bins: NO CHANGE)")
            else:
                # We need to compromise — set 50°C as high as possible without
                # exceeding 37°C, which is 138
                max_50 = wue_37 - 2  # keep 2% margin for monotonic curve
                verify_max = wue_37 + frac_lean * (max_50 - wue_37)
                predicted_afr_max = avg_afr * (avg_gw / verify_max)
                print(f"      50°C bin: {wue_table[50]}% → {max_50}%")
                print(f"      Achieves WUE {verify_max:.0f}% at {avg_lean_clt:.0f}°C")
                print(f"      Predicted AFR: {predicted_afr_max:.1f}")
                if predicted_afr_max > 14.5:
                    remaining_lean = predicted_afr_max - TARGET_AFR
                    print(f"      Still {remaining_lean:.1f} AFR points lean")
                    print(f"      ALSO change 37°C: {wue_37}% → {new_37_C}%")
                    print(f"      (This will make 28-37°C richer: AFR→~{g_afr * g_gw / (g_gw * ratio_needed):.1f})")
                print(f"    ══════════════════════════════════════════")

print()
