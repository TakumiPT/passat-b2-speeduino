"""
March 7, 2026 Datalog Analysis
Focus: TinyWB wideband sensor issue, voltage, belt fix verification
"""
import csv

FILE = '2026-03-07_11.37.31.csv'

with open(FILE, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    headers = reader.fieldnames
    rows = list(reader)

print(f"Total rows: {len(rows)}")
print(f"Columns: {len(headers)}")

# Parse key columns
def g(row, col):
    for h in headers:
        if col.lower() in h.lower():
            try:
                return float(row[h])
            except:
                return None
    return None

# Get exact column names
print("\nAll columns:")
for i, h in enumerate(headers):
    print(f"  [{i}] {h}")

# Parse all data
data = []
for row in rows:
    try:
        d = {
            'time': float(row[headers[0]]),
            'rpm': float(row['RPM']),
            'map': float(row['MAP']),
            'tps': float(row['TPS']),
            'afr': float(row['AFR']),
            'iat': float(row['IAT']),
            'clt': float(row['CLT']),
            'pw': float(row['PW']),
            've': float(row['VE1']),
            'gwarm': float(row['Gwarm']),
            'gammae': float(row['Gammae']),
            'duty': float(row['Duty Cycle']),
        }
        # Try to get battery voltage
        for h in headers:
            if 'bat' in h.lower() or 'volt' in h.lower():
                try:
                    d['bat'] = float(row[h])
                except:
                    pass
        # Try to get IAC
        for h in headers:
            if 'iac' in h.lower() or 'idle' in h.lower() or 'stepper' in h.lower():
                try:
                    d['iac'] = float(row[h])
                except:
                    pass
        # AFR target
        try:
            d['afr_target'] = float(row['AFR Target'])
        except:
            d['afr_target'] = 14.7

        data.append(d)
    except Exception as e:
        pass

print(f"\nParsed {len(data)} valid rows")

# ===== OVERVIEW =====
print("\n" + "=" * 70)
print("OVERVIEW")
print("=" * 70)

duration = data[-1]['time'] - data[0]['time']
print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
print(f"Start CLT: {data[0]['clt']:.1f}°C, End CLT: {data[-1]['clt']:.1f}°C")
print(f"RPM range: {min(d['rpm'] for d in data):.0f} - {max(d['rpm'] for d in data):.0f}")

if 'bat' in data[0]:
    bat_values = [d['bat'] for d in data if 'bat' in d and d['bat'] > 0]
    if bat_values:
        print(f"Battery: min={min(bat_values):.1f}V, avg={sum(bat_values)/len(bat_values):.1f}V, max={max(bat_values):.1f}V")
else:
    print("Battery voltage column NOT FOUND")

# ===== VOLTAGE ANALYSIS (Belt Fix Check) =====
print("\n" + "=" * 70)
print("VOLTAGE ANALYSIS - BELT FIX VERIFICATION")
print("=" * 70)

if 'bat' in data[0]:
    # Time-based voltage profile
    for t_start, t_end, label in [(0,30,'First 30s'), (30,120,'30-120s'), (120,300,'2-5min'), (300,600,'5-10min'), (600,99999,'10min+')]:
        segment = [d for d in data if t_start <= d['time'] < t_end]
        if segment:
            bats = [d['bat'] for d in segment if d['bat'] > 0]
            rpms = [d['rpm'] for d in segment]
            if bats:
                print(f"  {label:>12}: V={sum(bats)/len(bats):.1f}V (min {min(bats):.1f}, max {max(bats):.1f}), RPM={sum(rpms)/len(rpms):.0f}")

    # Voltage at idle vs revving
    idle_v = [d['bat'] for d in data if d['rpm'] > 600 and d['rpm'] < 1200 and d['bat'] > 0]
    rev_v = [d['bat'] for d in data if d['rpm'] > 2000 and d['bat'] > 0]
    if idle_v:
        print(f"\n  Idle voltage: {sum(idle_v)/len(idle_v):.2f}V avg (n={len(idle_v)})")
    if rev_v:
        print(f"  Rev (>2000) voltage: {sum(rev_v)/len(rev_v):.2f}V avg (n={len(rev_v)})")
    
    # Is alternator charging?
    if idle_v and sum(idle_v)/len(idle_v) > 13.5:
        print("\n  ✅ ALTERNATOR CHARGING — belt fix confirmed!")
    elif idle_v and sum(idle_v)/len(idle_v) > 12.5:
        print("\n  ⚠️  Marginal charging — alternator engaging intermittently")
    else:
        print("\n  ❌ STILL NOT CHARGING — belt still slipping or alternator issue")
else:
    print("  No battery voltage column found!")

# ===== AFR ANALYSIS =====
print("\n" + "=" * 70)
print("AFR ANALYSIS - TinyWB SENSOR CHECK")
print("=" * 70)

# Check for pegged values (sensor not working)
afr_values = [d['afr'] for d in data if d['rpm'] > 400]
afr_pegged_high = sum(1 for a in afr_values if a >= 19.5)
afr_pegged_low = sum(1 for a in afr_values if a <= 10.0)
afr_zero = sum(1 for a in afr_values if a == 0)
afr_normal = sum(1 for a in afr_values if 10.0 < a < 19.5)

print(f"\n  Total AFR samples (engine running): {len(afr_values)}")
print(f"  Pegged HIGH (>=19.5): {afr_pegged_high} ({afr_pegged_high/len(afr_values)*100:.1f}%)")
print(f"  Pegged LOW (<=10.0): {afr_pegged_low} ({afr_pegged_low/len(afr_values)*100:.1f}%)")
print(f"  Zero readings: {afr_zero} ({afr_zero/len(afr_values)*100:.1f}%)")
print(f"  Normal range: {afr_normal} ({afr_normal/len(afr_values)*100:.1f}%)")

# AFR distribution
print(f"\n  AFR Distribution:")
for lo, hi in [(9,10),(10,11),(11,12),(12,13),(13,14),(14,15),(15,16),(16,17),(17,18),(18,19),(19,20)]:
    count = sum(1 for a in afr_values if lo <= a < hi)
    bar = '#' * int(count/len(afr_values)*200)
    print(f"    {lo:>2}-{hi:<2}: {count:>5} ({count/len(afr_values)*100:>5.1f}%) {bar}")

# AFR by temperature bucket
print(f"\n  AFR by CLT (idle 600-1200 RPM):")
for tmin, tmax, label in [(0,20,'Cold 0-20°C'), (20,40,'20-40°C'), (40,60,'40-60°C'), (60,80,'60-80°C'), (80,100,'Hot 80-100°C')]:
    bucket = [d for d in data if tmin <= d['clt'] < tmax and 600 <= d['rpm'] <= 1200]
    if bucket:
        afrs = [d['afr'] for d in bucket]
        avg_afr = sum(afrs)/len(afrs)
        avg_rpm = sum(d['rpm'] for d in bucket)/len(bucket)
        avg_map = sum(d['map'] for d in bucket)/len(bucket)
        print(f"    {label:>15}: AFR={avg_afr:.1f}, RPM={avg_rpm:.0f}, MAP={avg_map:.1f} kPa (n={len(bucket)})")

# ===== TinyWB Specific Checks =====
print("\n" + "=" * 70)
print("TinyWB SENSOR DIAGNOSTICS")
print("=" * 70)

# TinyWB calibration: 1.0V = AFR 9.7, 4.0V = AFR 18.7 (linear)
# If sensor is not heated: reads ~4.5-5.0V = lean, or 0V = disconnected
# If sensor GND issue: erratic readings

# Check first 30 seconds (sensor heating time)
first_30 = [d for d in data if d['time'] <= data[0]['time'] + 30]
if first_30:
    afrs_30 = [d['afr'] for d in first_30 if d['rpm'] > 0]
    if afrs_30:
        print(f"\n  First 30s AFR (sensor warmup): avg={sum(afrs_30)/len(afrs_30):.1f}, min={min(afrs_30):.1f}, max={max(afrs_30):.1f}")

# Check for erratic swings (indicates GND/power issue)
afr_diffs = []
running = [d for d in data if d['rpm'] > 600]
for i in range(1, len(running)):
    dt = running[i]['time'] - running[i-1]['time']
    if dt > 0 and dt < 0.2:  # consecutive samples
        diff = abs(running[i]['afr'] - running[i-1]['afr'])
        afr_diffs.append(diff)

if afr_diffs:
    avg_diff = sum(afr_diffs)/len(afr_diffs)
    large_jumps = sum(1 for d in afr_diffs if d > 2.0)
    print(f"\n  AFR stability (sample-to-sample):")
    print(f"    Average change: {avg_diff:.2f} AFR/sample")
    print(f"    Large jumps (>2.0 AFR): {large_jumps} ({large_jumps/len(afr_diffs)*100:.1f}%)")
    
    if avg_diff > 1.0:
        print("    ❌ VERY ERRATIC - likely power/GND issue on TinyWB")
    elif avg_diff > 0.5:
        print("    ⚠️  Somewhat noisy - check wiring")
    else:
        print("    ✅ Normal stability")

# Check if AFR correlates with RPM changes (working sensor responds to throttle)
print(f"\n  AFR response to throttle:")
throttle_events = []
for i in range(10, len(running)-10):
    rpm_before = sum(d['rpm'] for d in running[i-5:i]) / 5
    rpm_after = sum(d['rpm'] for d in running[i:i+5]) / 5
    if rpm_after - rpm_before > 500:  # throttle blip
        afr_before = sum(d['afr'] for d in running[i-5:i]) / 5
        afr_after = sum(d['afr'] for d in running[i+3:i+8]) / 5
        throttle_events.append((rpm_before, rpm_after, afr_before, afr_after))

if throttle_events:
    for j, (rb, ra, ab, aa) in enumerate(throttle_events[:5]):
        direction = "RICH ✅" if aa < ab else "LEAN ❌" if aa > ab + 0.5 else "FLAT ⚠️"
        print(f"    Event {j+1}: RPM {rb:.0f}→{ra:.0f}, AFR {ab:.1f}→{aa:.1f} ({direction})")
else:
    print("    No throttle events detected")

# ===== ENGINE HEALTH =====
print("\n" + "=" * 70)
print("ENGINE HEALTH")
print("=" * 70)

# Check for stalls
stalls = 0
was_running = False
for d in data:
    if d['rpm'] > 400:
        was_running = True
    elif d['rpm'] < 100 and was_running:
        stalls += 1
        was_running = False

print(f"  Stalls detected: {stalls}")

# Hot idle stats
hot_idle = [d for d in data if d['clt'] >= 80 and 600 <= d['rpm'] <= 1200]
if hot_idle:
    print(f"\n  Hot idle (CLT≥80°C, 600-1200 RPM): {len(hot_idle)} samples")
    print(f"    RPM: {sum(d['rpm'] for d in hot_idle)/len(hot_idle):.0f} avg")
    print(f"    MAP: {sum(d['map'] for d in hot_idle)/len(hot_idle):.1f} kPa avg") 
    print(f"    PW: {sum(d['pw'] for d in hot_idle)/len(hot_idle):.2f} ms avg")
    print(f"    VE: {sum(d['ve'] for d in hot_idle)/len(hot_idle):.1f}% avg")
    print(f"    AFR: {sum(d['afr'] for d in hot_idle)/len(hot_idle):.1f} avg")
    print(f"    Duty: {sum(d['duty'] for d in hot_idle)/len(hot_idle):.1f}% avg")

# ===== IAC Column Check =====
print("\n" + "=" * 70)
print("IAC STATUS IN DATALOG")
print("=" * 70)

iac_cols = [h for h in headers if 'iac' in h.lower() or 'idle' in h.lower() or 'stepper' in h.lower()]
if iac_cols:
    print(f"  IAC columns found: {iac_cols}")
    for col in iac_cols:
        vals = [float(row[col]) for row in rows if row[col].strip()]
        if vals:
            print(f"    {col}: min={min(vals):.0f}, avg={sum(vals)/len(vals):.1f}, max={max(vals):.0f}")
else:
    print("  No IAC-specific column found in datalog")
    # Check for likely step columns
    step_cols = [h for h in headers if 'step' in h.lower()]
    if step_cols:
        print(f"  Step columns: {step_cols}")

# ===== COMPLETE TIME PROFILE =====
print("\n" + "=" * 70) 
print("TIME PROFILE (30-second windows)")
print("=" * 70)

t_start = data[0]['time']
t_end = data[-1]['time']
window = 30
t = t_start

print(f"{'Time':>8} {'RPM':>6} {'MAP':>5} {'CLT':>5} {'AFR':>5} {'PW':>5} {'VE':>4} {'Bat':>5}")
print("-" * 50)

while t < t_end:
    window_data = [d for d in data if t <= d['time'] < t + window]
    if window_data:
        avg_rpm = sum(d['rpm'] for d in window_data)/len(window_data)
        avg_map = sum(d['map'] for d in window_data)/len(window_data)
        avg_clt = sum(d['clt'] for d in window_data)/len(window_data)
        avg_afr = sum(d['afr'] for d in window_data)/len(window_data)
        avg_pw = sum(d['pw'] for d in window_data)/len(window_data)
        avg_ve = sum(d['ve'] for d in window_data)/len(window_data)
        bat_str = ""
        if 'bat' in window_data[0]:
            avg_bat = sum(d['bat'] for d in window_data)/len(window_data)
            bat_str = f"{avg_bat:.1f}V"
        
        elapsed = t - t_start
        print(f"  {elapsed:>5.0f}s {avg_rpm:>6.0f} {avg_map:>5.1f} {avg_clt:>5.1f} {avg_afr:>5.1f} {avg_pw:>5.2f} {avg_ve:>4.0f} {bat_str:>5}")
    t += window
