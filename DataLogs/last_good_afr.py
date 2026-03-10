"""
Analyze the last datalogs where the O2 sensor was working properly.
Feb 28 2026 = last fully working sessions (99-100% normal AFR)
Mar 1 2026 = partially working (91% normal)
Shows: how was the engine running when we could actually see AFR?
"""
import csv
import os
import sys

def analyze_log(filepath):
    """Analyze a single CSV datalog for AFR and engine health."""
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return None
    
    rows = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)
        
        # Find column indices
        cols = {}
        for i, h in enumerate(headers):
            h_clean = h.strip().lower()
            if 'time' in h_clean and 'dwell' not in h_clean:
                cols['time'] = i
            elif h_clean in ('afr', 'afr1'):
                cols['afr'] = i
            elif h_clean == 'rpm':
                cols['rpm'] = i
            elif h_clean == 'map':
                cols['map'] = i
            elif h_clean in ('clt', 'coolant'):
                cols['clt'] = i
            elif h_clean in ('iat', 'intake'):
                cols['iat'] = i
            elif h_clean in ('pw', 'pw1', 'pulsewidth'):
                cols['pw'] = i
            elif h_clean in ('ve', 've1', 'vecurr'):
                cols['ve'] = i
            elif h_clean in ('bat', 'battery', 'batvoltage'):
                cols['bat'] = i
            elif h_clean in ('tps', 'tps(adc)'):
                cols['tps'] = i
            elif h_clean in ('gammae', 'gamma'):
                cols['gammae'] = i
        
        for row in reader:
            try:
                d = {}
                for key, idx in cols.items():
                    try:
                        d[key] = float(row[idx])
                    except (ValueError, IndexError):
                        d[key] = None
                rows.append(d)
            except Exception:
                continue
    
    if not rows:
        return None
    
    # Filter running samples (RPM > 400)
    running = [r for r in rows if r.get('rpm') and r['rpm'] > 400]
    if not running:
        print("  No running samples found")
        return None
    
    # Separate idle vs driving
    idle = [r for r in running if r.get('rpm', 0) < 1200 and r.get('map', 100) < 60]
    driving = [r for r in running if r.get('rpm', 0) >= 1200 or r.get('map', 100) >= 60]
    
    # Hot running (CLT > 70°C) vs warmup
    hot = [r for r in running if r.get('clt') and r['clt'] > 70]
    warmup = [r for r in running if r.get('clt') and r['clt'] <= 70]
    
    # AFR analysis
    afr_valid = [r['afr'] for r in running if r.get('afr') and 9.0 < r['afr'] < 19.0]
    afr_pegged = [r['afr'] for r in running if r.get('afr') and r['afr'] >= 19.0]
    
    # Hot idle AFR
    hot_idle = [r for r in idle if r.get('clt') and r['clt'] > 70 and r.get('afr') and 9.0 < r['afr'] < 19.0]
    hot_idle_afr = [r['afr'] for r in hot_idle]
    
    # Hot driving AFR
    hot_driving = [r for r in driving if r.get('clt') and r['clt'] > 70 and r.get('afr') and 9.0 < r['afr'] < 19.0]
    hot_driving_afr = [r['afr'] for r in hot_driving]
    
    # Warmup AFR  
    warmup_afr_data = [r for r in warmup if r.get('afr') and 9.0 < r['afr'] < 19.0]
    
    # Battery voltage
    bat_vals = [r['bat'] for r in running if r.get('bat') and r['bat'] > 5]
    
    # RPM stats
    rpm_vals = [r['rpm'] for r in running if r.get('rpm')]
    
    # VE stats for hot idle
    hot_idle_ve = [r['ve'] for r in hot_idle if r.get('ve')]
    
    # PW stats for hot idle
    hot_idle_pw = [r['pw'] for r in hot_idle if r.get('pw')]
    
    # CLT range
    clt_vals = [r['clt'] for r in running if r.get('clt')]
    
    # Print results
    duration = running[-1].get('time', 0) - running[0].get('time', 0) if running[0].get('time') is not None else 0
    print(f"  Duration: {duration:.0f}s ({duration/60:.1f} min)")
    print(f"  Running samples: {len(running)}")
    print(f"  CLT range: {min(clt_vals):.0f}°C → {max(clt_vals):.0f}°C" if clt_vals else "  CLT: N/A")
    
    if bat_vals:
        print(f"  Battery: {min(bat_vals):.1f}V - {max(bat_vals):.1f}V (avg {sum(bat_vals)/len(bat_vals):.1f}V)")
    
    print(f"\n  AFR Sensor Status:")
    print(f"    Valid readings (9-19): {len(afr_valid)} ({100*len(afr_valid)/len(running):.0f}%)")
    print(f"    Pegged at 19.7: {len(afr_pegged)} ({100*len(afr_pegged)/len(running):.0f}%)")
    
    if afr_valid:
        avg_afr = sum(afr_valid)/len(afr_valid)
        print(f"    Overall AFR: {avg_afr:.1f} (min {min(afr_valid):.1f}, max {max(afr_valid):.1f})")
    
    # Detailed AFR breakdown
    print(f"\n  === HOT IDLE (CLT>70°C, RPM<1200, MAP<60) ===")
    if hot_idle_afr:
        avg = sum(hot_idle_afr)/len(hot_idle_afr)
        # Count in target ranges
        stoich = sum(1 for a in hot_idle_afr if 14.2 <= a <= 15.2)
        rich = sum(1 for a in hot_idle_afr if a < 14.2)
        lean = sum(1 for a in hot_idle_afr if a > 15.2)
        print(f"    Samples: {len(hot_idle_afr)}")
        print(f"    AFR avg: {avg:.1f}")
        print(f"    Stoich (14.2-15.2): {stoich} ({100*stoich/len(hot_idle_afr):.0f}%)")
        print(f"    Rich (<14.2): {rich} ({100*rich/len(hot_idle_afr):.0f}%)")
        print(f"    Lean (>15.2): {lean} ({100*lean/len(hot_idle_afr):.0f}%)")
        if hot_idle_ve:
            print(f"    VE avg: {sum(hot_idle_ve)/len(hot_idle_ve):.0f}%")
        if hot_idle_pw:
            print(f"    PW avg: {sum(hot_idle_pw)/len(hot_idle_pw):.1f}ms")
    else:
        print(f"    No hot idle data")
    
    print(f"\n  === HOT DRIVING (CLT>70°C, RPM≥1200 or MAP≥60) ===")
    if hot_driving_afr:
        avg = sum(hot_driving_afr)/len(hot_driving_afr)
        stoich = sum(1 for a in hot_driving_afr if 13.5 <= a <= 15.0)
        rich = sum(1 for a in hot_driving_afr if a < 13.5)
        lean = sum(1 for a in hot_driving_afr if a > 15.0)
        print(f"    Samples: {len(hot_driving_afr)}")
        print(f"    AFR avg: {avg:.1f}")
        print(f"    Near stoich (13.5-15.0): {stoich} ({100*stoich/len(hot_driving_afr):.0f}%)")
        print(f"    Rich (<13.5): {rich} ({100*rich/len(hot_driving_afr):.0f}%)")
        print(f"    Lean (>15.0): {lean} ({100*lean/len(hot_driving_afr):.0f}%)")
    else:
        print(f"    No hot driving data")
    
    print(f"\n  === WARMUP (CLT≤70°C) ===")
    if warmup_afr_data:
        afrs = [r['afr'] for r in warmup_afr_data]
        avg = sum(afrs)/len(afrs)
        # Group by temperature bands
        bands = [(0, 30, "Cold (<30°C)"), (30, 50, "Warming (30-50°C)"), (50, 70, "Almost warm (50-70°C)")]
        print(f"    Samples: {len(afrs)}, AFR avg: {avg:.1f}")
        for lo, hi, label in bands:
            band_afr = [r['afr'] for r in warmup_afr_data if r.get('clt') and lo <= r['clt'] < hi]
            if band_afr:
                print(f"    {label}: AFR {sum(band_afr)/len(band_afr):.1f} ({len(band_afr)} samples)")
    else:
        print(f"    No warmup AFR data")
    
    # RPM stability at hot idle
    if hot_idle:
        rpms = [r['rpm'] for r in hot_idle if r.get('rpm')]
        if rpms:
            avg_rpm = sum(rpms)/len(rpms)
            rpm_std = (sum((r - avg_rpm)**2 for r in rpms) / len(rpms)) ** 0.5
            print(f"\n  === IDLE STABILITY ===")
            print(f"    Hot idle RPM: {avg_rpm:.0f} ±{rpm_std:.0f} RPM")
            if rpm_std < 30:
                print(f"    Rating: EXCELLENT (±{rpm_std:.0f} < ±30)")
            elif rpm_std < 60:
                print(f"    Rating: GOOD (±{rpm_std:.0f} < ±60)")
            elif rpm_std < 100:
                print(f"    Rating: FAIR (±{rpm_std:.0f} < ±100)")
            else:
                print(f"    Rating: ROUGH (±{rpm_std:.0f} ≥ ±100)")
    
    return {'valid_afr': len(afr_valid), 'total': len(running)}


# Analyze the key datalogs
base = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("LAST GOOD O2 SENSOR DATA — How was the engine running?")
print("=" * 70)

logs = [
    ("2026-02-28_17.53.41.csv", "Feb 28 — Session 1 (SENSOR WORKING ✅)"),
    ("2026-02-28_18.10.43.csv", "Feb 28 — Session 2 (SENSOR WORKING ✅)"),
    ("2026-03-01_19.05.30.csv", "Mar 1 — Cold start, no resistor (91% working)"),
    ("2026-03-01_19.08.45.csv", "Mar 1 — With 3.3Ω resistor (FAILED TO START)"),
    ("2026-03-07_11.37.31.csv", "Mar 7 — Today (SENSOR DEAD ❌)"),
]

for filename, label in logs:
    filepath = os.path.join(base, filename)
    print(f"\n{'─'*70}")
    print(f"  {label}")
    print(f"  File: {filename}")
    print(f"{'─'*70}")
    analyze_log(filepath)

print(f"\n{'='*70}")
print("SUMMARY — What this tells us:")
print("="*70)
print("""
The Feb 28 data is your BASELINE — that's how the engine runs with
correct AFR readings. Compare those numbers to today's RPM, MAP, PW
to judge if the engine is still running the same (it almost certainly is).

Three separate problems, three separate fixes:
1. O2 SENSOR: Rewire GND + 12V to screw terminals (wiring issue, not sensor)
2. ALTERNATOR: Not charging (12.8V max) — check belt tension, brushes, regulator
3. IAC: Check DRV8825 wiring, measure voltage on stepper coil pins A1/A2/B1/B2
""")
