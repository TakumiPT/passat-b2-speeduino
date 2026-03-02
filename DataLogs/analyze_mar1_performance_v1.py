"""
Engine Performance Analysis - March 1, 2026 Test Sessions
MLG1: 2026-03-01_19.05.30 - Car STARTED (corrected voltage correction table)
MLG2: 2026-03-01_19.08.45 - Car DID NOT START

Analyzes: cranking quality, AFR during run, idle stability, enrichment behavior,
voltage correction impact vs Feb 28 baseline.
"""
import json, sys, os
from collections import defaultdict

def load_json(fname):
    with open(fname) as f:
        d = json.load(f)
    return d['records']

def afr_val(r):
    """AFR field: JSON stores raw (149 = 14.9 AFR), detect and scale"""
    v = r.get('AFR', 0)
    if v > 50:  # raw integer, divide by 10
        return v / 10.0
    return v

def stats(vals):
    if not vals:
        return {'min': 0, 'max': 0, 'avg': 0, 'n': 0, 'std': 0}
    avg = sum(vals) / len(vals)
    variance = sum((x - avg)**2 for x in vals) / len(vals) if len(vals) > 1 else 0
    return {'min': min(vals), 'max': max(vals), 'avg': avg, 'n': len(vals), 'std': variance**0.5}

def print_stats(label, vals, unit='', fmt='.1f'):
    s = stats(vals)
    if s['n'] == 0:
        print(f"    {label:20s}: NO DATA")
        return s
    print(f"    {label:20s}: min={s['min']:{fmt}}  avg={s['avg']:{fmt}}  max={s['max']:{fmt}}  std={s['std']:{fmt}}  (n={s['n']}) {unit}")
    return s

# ========================================================================
# LOAD DATA
# ========================================================================
print("=" * 80)
print("  ENGINE PERFORMANCE ANALYSIS - 2026-03-01 TEST SESSIONS")
print("  (Corrected Voltage Correction Table: 255/176/127/100/86/70)")
print("=" * 80)

files = {
    'MLG1': ('2026-03-01_19.05.30.json', 'CAR STARTED'),
    'MLG2': ('2026-03-01_19.08.45.json', 'CAR DID NOT START'),
}

all_data = {}
for key, (fname, label) in files.items():
    recs = load_json(fname)
    all_data[key] = recs
    print(f"\n  {key}: {fname} — {label} — {len(recs)} records")

# ========================================================================
# MLG1 ANALYSIS - THE CAR THAT STARTED
# ========================================================================
recs = all_data['MLG1']

# Classify phases
key_off = [r for r in recs if r['RPM'] == 0]
cranking = [r for r in recs if 0 < r['RPM'] < 500]
transition = [r for r in recs if 500 <= r['RPM'] < 700]  # catching/stumbling
running = [r for r in recs if r['RPM'] >= 700]
idle = [r for r in recs if 700 <= r['RPM'] <= 1000 and r['TPS'] == 0]

print(f"\n{'='*80}")
print(f"  MLG1 ANALYSIS — STARTED SUCCESSFULLY")
print(f"{'='*80}")
print(f"\n  Phase Classification:")
print(f"    Key off (0 RPM):      {len(key_off):>5}")
print(f"    Cranking (1-499):     {len(cranking):>5}")
print(f"    Transition (500-699): {len(transition):>5}")
print(f"    Running (>=700):      {len(running):>5}")
print(f"    Idle (700-1000, 0 TPS): {len(idle):>5}")

# ---------- CRANKING PERFORMANCE ----------
if cranking:
    print(f"\n  --- CRANKING PERFORMANCE ---")
    print_stats("RPM", [r['RPM'] for r in cranking], "rpm")
    print_stats("Battery V", [r['Battery V'] for r in cranking], "V")
    print_stats("PW", [r['PW'] for r in cranking], "ms")
    print_stats("AFR", [afr_val(r) for r in cranking], "")
    print_stats("Gbattery", [r['Gbattery'] for r in cranking], "%")
    print_stats("Gwarm (WUE)", [r['Gwarm'] for r in cranking], "%")
    print_stats("Gammae (total)", [r['Gammae'] for r in cranking], "%")
    print_stats("VE Current", [r['VE _Current'] for r in cranking], "%")
    print_stats("Duty Cycle", [r['Duty Cycle'] for r in cranking], "%")
    print_stats("CLT", [r['CLT'] for r in cranking], "°C")
    print_stats("MAP", [r['MAP'] for r in cranking], "kPa")
    
    # AFR quality during cranking
    afrs = [afr_val(r) for r in cranking if afr_val(r) > 5]
    if afrs:
        target_rich = [a for a in afrs if 11.0 <= a <= 13.0]
        too_rich = [a for a in afrs if a < 11.0]
        too_lean = [a for a in afrs if a > 13.0]
        print(f"\n    Cranking AFR quality (target 11-13 for cold start):")
        print(f"      Too rich (<11):   {len(too_rich):>4} ({100*len(too_rich)/len(afrs):.1f}%)")
        print(f"      Target (11-13):   {len(target_rich):>4} ({100*len(target_rich)/len(afrs):.1f}%)")
        print(f"      Too lean (>13):   {len(too_lean):>4} ({100*len(too_lean)/len(afrs):.1f}%)")
    
    # Voltage correction impact
    print(f"\n    Voltage Correction during cranking:")
    print(f"    {'BattV':>8} | {'Gbattery':>8} | {'Expect':>8} | {'Match?':>8} | {'PW avg':>8} | {'AFR avg':>8}")
    print(f"    {'-'*60}")
    # Expected: <8.2V→255, 9.4V→176, 12.1V→127, 14.8V→100
    for lo, hi in [(7.0,8.0),(8.0,8.5),(8.5,9.0),(9.0,9.5),(9.5,10.0),(10.0,11.0),(11.0,12.0)]:
        band = [r for r in cranking if lo <= r['Battery V'] < hi]
        if band:
            avg_gb = sum(r['Gbattery'] for r in band) / len(band)
            avg_pw = sum(r['PW'] for r in band) / len(band)
            avg_afr = sum(afr_val(r) for r in band) / len(band)
            # What correction SHOULD be at midpoint voltage
            midv = (lo + hi) / 2
            if midv < 8.2:
                expected = 255
            elif midv < 10.8:
                # interpolate between 255@6.6 and 176@9.4 and 127@12.1
                expected = int(176 + (9.4 - midv) / (9.4 - 6.6) * (255 - 176))
            elif midv < 13.5:
                expected = int(127 + (12.1 - midv) / (12.1 - 9.4) * (176 - 127))
            else:
                expected = 100
            match = "YES" if abs(avg_gb - expected) < 15 else f"NO({expected})"
            print(f"    {lo:.1f}-{hi:.1f}V | {avg_gb:>7.0f}% | {expected:>7}% | {match:>8} | {avg_pw:>7.2f}ms | {avg_afr:>7.1f}")

# ---------- TRANSITION (500-700 RPM) ----------
if transition:
    print(f"\n  --- TRANSITION PHASE (500-700 RPM, catching/stumble) ---")
    print_stats("RPM", [r['RPM'] for r in transition], "rpm")
    print_stats("PW", [r['PW'] for r in transition], "ms")
    print_stats("AFR", [afr_val(r) for r in transition], "")
    print_stats("Battery V", [r['Battery V'] for r in transition], "V")
    print_stats("Duty Cycle", [r['Duty Cycle'] for r in transition], "%")
    
    # Did RPM recover or stall?
    rpms = [r['RPM'] for r in transition]
    if len(rpms) > 2:
        if rpms[-1] > rpms[0]:
            print(f"    → RPM RISING through transition ({rpms[0]:.0f} → {rpms[-1]:.0f}) — GOOD")
        else:
            print(f"    → RPM FALLING through transition ({rpms[0]:.0f} → {rpms[-1]:.0f}) — STRUGGLING")

# ---------- RUNNING PERFORMANCE ----------
if running:
    print(f"\n  --- RUNNING PERFORMANCE (>=700 RPM) ---")
    print_stats("RPM", [r['RPM'] for r in running], "rpm")
    print_stats("Battery V", [r['Battery V'] for r in running], "V")
    print_stats("PW", [r['PW'] for r in running], "ms")
    print_stats("AFR", [afr_val(r) for r in running], "")
    print_stats("Gbattery", [r['Gbattery'] for r in running], "%")
    print_stats("Gwarm (WUE)", [r['Gwarm'] for r in running], "%")
    print_stats("Gammae (total)", [r['Gammae'] for r in running], "%")
    print_stats("VE Current", [r['VE _Current'] for r in running], "%")
    print_stats("Duty Cycle", [r['Duty Cycle'] for r in running], "%")
    print_stats("CLT", [r['CLT'] for r in running], "°C")
    print_stats("MAP", [r['MAP'] for r in running], "kPa")
    print_stats("TPS", [r['TPS'] for r in running], "%")
    print_stats("Accel Enrich", [r['Accel Enrich'] for r in running], "%")
    print_stats("Sync Loss #", [r['Sync Loss #'] for r in running], "")
    
    # AFR distribution while running
    afrs = [afr_val(r) for r in running if afr_val(r) > 5]
    if afrs:
        print(f"\n    AFR Distribution (running):")
        bands = [
            ("Very rich", 0, 11),
            ("Rich (cold ok)", 11, 13),
            ("Slightly rich", 13, 14),
            ("Stoich zone", 14, 15),
            ("Slightly lean", 15, 16),
            ("Lean", 16, 18),
            ("Very lean", 18, 25),
        ]
        for label, lo, hi in bands:
            count = len([a for a in afrs if lo <= a < hi])
            pct = 100 * count / len(afrs) if afrs else 0
            bar = '#' * int(pct / 2)
            print(f"      {label:20s} ({lo:>4.0f}-{hi:<4.0f}): {count:>5} ({pct:>5.1f}%) {bar}")
        
        # Time in good AFR range
        good = [a for a in afrs if 13.5 <= a <= 15.5]
        print(f"\n      Time in good range (13.5-15.5): {100*len(good)/len(afrs):.1f}%")
        print(f"      Time lean (>15.5):              {100*len([a for a in afrs if a > 15.5])/len(afrs):.1f}%")
        print(f"      Time rich (<13.5):              {100*len([a for a in afrs if a < 13.5])/len(afrs):.1f}%")

# ---------- IDLE STABILITY ----------
if idle:
    print(f"\n  --- IDLE STABILITY (700-1000 RPM, TPS=0) ---")
    rpms = [r['RPM'] for r in idle]
    s_rpm = print_stats("RPM", rpms, "rpm")
    print_stats("AFR", [afr_val(r) for r in idle], "")
    print_stats("PW", [r['PW'] for r in idle], "ms")
    print_stats("MAP", [r['MAP'] for r in idle], "kPa")
    
    # RPM stability (std dev)
    if s_rpm['std'] > 0:
        stability = "EXCELLENT" if s_rpm['std'] < 20 else "GOOD" if s_rpm['std'] < 40 else "FAIR" if s_rpm['std'] < 60 else "POOR"
        print(f"\n    Idle stability: {stability} (RPM σ = {s_rpm['std']:.1f})")
    
    # RPM trend (is it dropping/rising/stable?)
    if len(rpms) > 20:
        first_10 = sum(rpms[:10]) / 10
        last_10 = sum(rpms[-10:]) / 10
        print(f"    RPM trend: {first_10:.0f} → {last_10:.0f} (Δ = {last_10 - first_10:+.0f})")

# ---------- RPM TIMELINE ----------
print(f"\n  --- RPM + AFR TIMELINE (every 10th sample) ---")
print(f"    {'#':>5} | {'Time':>8} | {'RPM':>6} | {'AFR':>6} | {'PW':>7} | {'BatV':>6} | {'Gbat':>5} | {'Gwrm':>5} | {'Gmae':>5} | {'Duty':>6} | {'MAP':>4}")
print(f"    {'-'*90}")
for i in range(0, min(len(recs), 500), 10):
    r = recs[i]
    if r['RPM'] > 0 or (i > 0 and recs[max(0,i-10)]['RPM'] > 0):
        print(f"    {i:>5} | {r['Time']:>8.1f} | {r['RPM']:>6.0f} | {afr_val(r):>6.1f} | {r['PW']:>7.3f} | {r['Battery V']:>6.1f} | {r['Gbattery']:>5.0f} | {r['Gwarm']:>5.0f} | {r['Gammae']:>5.0f} | {r['Duty Cycle']:>5.1f}% | {r['MAP']:>4.0f}")

# Look at the full duration
if running:
    last_running = [r for r in recs if r['RPM'] >= 500]
    if last_running:
        first_time = last_running[0]['Time']
        last_time = last_running[-1]['Time']
        duration = last_time - first_time
        print(f"\n    Total running time: {duration:.1f} seconds")
        
        # Did it stall?
        last_30 = recs[-30:]
        stall_check = [r for r in last_30 if r['RPM'] == 0]
        if len(stall_check) > 20:
            print(f"    → Engine STALLED at end (last 30 samples mostly 0 RPM)")
        else:
            print(f"    → Engine still running at end of log")

# ========================================================================
# MLG2 ANALYSIS - THE CAR THAT DID NOT START
# ========================================================================
recs2 = all_data['MLG2']

print(f"\n\n{'='*80}")
print(f"  MLG2 ANALYSIS — DID NOT START")
print(f"{'='*80}")

key_off2 = [r for r in recs2 if r['RPM'] == 0]
cranking2 = [r for r in recs2 if 0 < r['RPM'] < 500]
transition2 = [r for r in recs2 if 500 <= r['RPM'] < 700]
running2 = [r for r in recs2 if r['RPM'] >= 700]

print(f"\n  Phase Classification:")
print(f"    Key off (0 RPM):      {len(key_off2):>5}")
print(f"    Cranking (1-499):     {len(cranking2):>5}")
print(f"    Transition (500-699): {len(transition2):>5}")
print(f"    Running (>=700):      {len(running2):>5}")

if cranking2:
    print(f"\n  --- CRANKING DATA ---")
    print_stats("RPM", [r['RPM'] for r in cranking2], "rpm")
    print_stats("Battery V", [r['Battery V'] for r in cranking2], "V")
    print_stats("PW", [r['PW'] for r in cranking2], "ms")
    print_stats("AFR", [afr_val(r) for r in cranking2], "")
    print_stats("Gbattery", [r['Gbattery'] for r in cranking2], "%")
    print_stats("Gwarm (WUE)", [r['Gwarm'] for r in cranking2], "%")
    print_stats("Gammae (total)", [r['Gammae'] for r in cranking2], "%")
    print_stats("VE Current", [r['VE _Current'] for r in cranking2], "%")
    print_stats("Duty Cycle", [r['Duty Cycle'] for r in cranking2], "%")
    print_stats("CLT", [r['CLT'] for r in cranking2], "°C")
    print_stats("MAP", [r['MAP'] for r in cranking2], "kPa")
    print_stats("Sync Loss #", [r['Sync Loss #'] for r in cranking2], "")
    
    afrs2 = [afr_val(r) for r in cranking2 if afr_val(r) > 5]
    if afrs2:
        print(f"\n    Cranking AFR quality:")
        print(f"      Too rich (<11):   {len([a for a in afrs2 if a < 11]):>4}")
        print(f"      Target (11-13):   {len([a for a in afrs2 if 11 <= a <= 13]):>4}")
        print(f"      Too lean (>13):   {len([a for a in afrs2 if a > 13]):>4}")

# Check if there were ANY moments RPM went above 400
peak_rpm2 = max(r['RPM'] for r in recs2) if recs2 else 0
print(f"\n    Peak RPM reached: {peak_rpm2}")
if peak_rpm2 < 100:
    print(f"    → NO cranking detected — starter not engaged or no trigger signal")
elif peak_rpm2 < 400:
    print(f"    → Cranking only, never caught")
elif peak_rpm2 < 700:
    print(f"    → Almost caught but stalled")
else:
    print(f"    → Briefly ran but died")

# Timeline of MLG2
print(f"\n  --- MLG2 TIMELINE (every 5th sample with RPM>0) ---")
print(f"    {'#':>5} | {'Time':>8} | {'RPM':>6} | {'AFR':>6} | {'PW':>7} | {'BatV':>6} | {'Gbat':>5} | {'Gwrm':>5} | {'Gmae':>5} | {'CLT':>4} | {'MAP':>4}")
print(f"    {'-'*85}")
count = 0
for i, r in enumerate(recs2):
    if r['RPM'] > 0:
        if count % 5 == 0:
            print(f"    {i:>5} | {r['Time']:>8.1f} | {r['RPM']:>6.0f} | {afr_val(r):>6.1f} | {r['PW']:>7.3f} | {r['Battery V']:>6.1f} | {r['Gbattery']:>5.0f} | {r['Gwarm']:>5.0f} | {r['Gammae']:>5.0f} | {r['CLT']:>4.0f} | {r['MAP']:>4.0f}")
        count += 1

# ========================================================================
# COMPARISON: MLG1 vs MLG2
# ========================================================================
print(f"\n\n{'='*80}")
print(f"  COMPARISON: MLG1 (STARTED) vs MLG2 (DID NOT START)")
print(f"{'='*80}")

c1 = [r for r in all_data['MLG1'] if 0 < r['RPM'] < 500]
c2 = [r for r in all_data['MLG2'] if 0 < r['RPM'] < 500]

if c1 and c2:
    metrics = [
        ("Avg cranking RPM", lambda rs: sum(r['RPM'] for r in rs)/len(rs), ".0f"),
        ("Avg Battery V", lambda rs: sum(r['Battery V'] for r in rs)/len(rs), ".1f"),
        ("Avg PW", lambda rs: sum(r['PW'] for r in rs)/len(rs), ".3f"),
        ("Avg AFR", lambda rs: sum(afr_val(r) for r in rs)/len(rs), ".1f"),
        ("Avg Gbattery", lambda rs: sum(r['Gbattery'] for r in rs)/len(rs), ".0f"),
        ("Avg Gwarm", lambda rs: sum(r['Gwarm'] for r in rs)/len(rs), ".0f"),
        ("Avg Gammae", lambda rs: sum(r['Gammae'] for r in rs)/len(rs), ".0f"),
        ("Avg VE", lambda rs: sum(r['VE _Current'] for r in rs)/len(rs), ".0f"),
        ("Avg Duty%", lambda rs: sum(r['Duty Cycle'] for r in rs)/len(rs), ".1f"),
        ("CLT", lambda rs: sum(r['CLT'] for r in rs)/len(rs), ".0f"),
        ("Samples", lambda rs: len(rs), "d"),
    ]
    
    print(f"\n    {'Metric':25s} | {'MLG1 (started)':>15} | {'MLG2 (no start)':>15} | {'Delta':>10}")
    print(f"    {'-'*75}")
    for name, fn, fmt in metrics:
        v1 = fn(c1)
        v2 = fn(c2)
        delta = v2 - v1
        print(f"    {name:25s} | {v1:>15{fmt}} | {v2:>15{fmt}} | {delta:>+10{fmt}}")

# ========================================================================
# COMPARISON vs FEB 28 BASELINE
# ========================================================================
print(f"\n\n{'='*80}")
print(f"  COMPARISON vs FEB 28 BASELINE (OLD voltage correction)")
print(f"{'='*80}")
print(f"""
    Feb 28 cranking (from previous analysis):
      Battery V: 8.0-9.9V (avg 9.0V)
      PW: 4.3-9.9ms  
      AFR: 15.5-19.7 (LEAN!)
      Gbattery: 100 (ALWAYS — old flat table doing nothing)
      Gammae: ~340-360

    Mar 1 MLG1 cranking (new corrected table):""")
if c1:
    print(f"      Battery V: {min(r['Battery V'] for r in c1):.1f}-{max(r['Battery V'] for r in c1):.1f}V (avg {sum(r['Battery V'] for r in c1)/len(c1):.1f}V)")
    print(f"      PW: {min(r['PW'] for r in c1):.1f}-{max(r['PW'] for r in c1):.1f}ms")
    print(f"      AFR: {min(afr_val(r) for r in c1):.1f}-{max(afr_val(r) for r in c1):.1f}")
    print(f"      Gbattery: {min(r['Gbattery'] for r in c1):.0f}-{max(r['Gbattery'] for r in c1):.0f}")
    print(f"      Gammae: {min(r['Gammae'] for r in c1):.0f}-{max(r['Gammae'] for r in c1):.0f}")

# ========================================================================
# DIAGNOSIS
# ========================================================================
print(f"\n\n{'='*80}")
print(f"  DIAGNOSIS & RECOMMENDATIONS")
print(f"{'='*80}")

if running:
    afrs_run = [afr_val(r) for r in running if afr_val(r) > 5]
    avg_afr_run = sum(afrs_run)/len(afrs_run) if afrs_run else 0
    lean_pct = 100 * len([a for a in afrs_run if a > 16]) / len(afrs_run) if afrs_run else 0
    
    print(f"\n  MLG1 Running Quality:")
    if avg_afr_run > 18:
        print(f"    ⚠ VERY LEAN running (avg AFR {avg_afr_run:.1f}) — VE table needs increase")
    elif avg_afr_run > 16:
        print(f"    ⚠ LEAN running (avg AFR {avg_afr_run:.1f}) — VE table needs ~10-15% increase")
    elif avg_afr_run > 15:
        print(f"    → SLIGHTLY LEAN (avg AFR {avg_afr_run:.1f}) — VE table needs ~5% increase")
    elif 14.0 <= avg_afr_run <= 15.0:
        print(f"    ✓ GOOD AFR (avg {avg_afr_run:.1f}) — near stoichiometric")
    elif avg_afr_run < 12.5:
        print(f"    ⚠ RICH running (avg AFR {avg_afr_run:.1f}) — VE table may need reduction")
    else:
        print(f"    → AFR avg {avg_afr_run:.1f} — acceptable for warmup")
    
    print(f"    → {lean_pct:.0f}% of running time above AFR 16 (target: <5%)")

if c2:
    print(f"\n  MLG2 No-Start Diagnosis:")
    avg_pw2 = sum(r['PW'] for r in c2)/len(c2)
    avg_afr2 = sum(afr_val(r) for r in c2)/len(c2)
    avg_batt2 = sum(r['Battery V'] for r in c2)/len(c2)
    avg_rpm2 = sum(r['RPM'] for r in c2)/len(c2)
    
    if avg_batt2 < 8.0:
        print(f"    → LOW BATTERY ({avg_batt2:.1f}V) — starter not cranking fast enough")
    if avg_rpm2 < 150:
        print(f"    → LOW CRANK SPEED ({avg_rpm2:.0f} RPM) — weak battery or starter")
    if avg_afr2 < 10:
        print(f"    → FLOODED (AFR {avg_afr2:.1f}) — too much fuel from previous attempt")
    elif avg_afr2 > 16:
        print(f"    → TOO LEAN (AFR {avg_afr2:.1f}) — not enough fuel")
    if avg_pw2 < 2:
        print(f"    → LOW PULSE WIDTH ({avg_pw2:.2f}ms) — insufficient fueling")
    elif avg_pw2 > 15:
        print(f"    → VERY HIGH PW ({avg_pw2:.2f}ms) — possible flooding")
    
    sync_losses = [r['Sync Loss #'] for r in c2]
    if max(sync_losses) > 0:
        print(f"    → SYNC LOSSES detected (max={max(sync_losses)}) — trigger signal issues")

print(f"\n{'='*80}")
print(f"  END OF ANALYSIS")
print(f"{'='*80}")
