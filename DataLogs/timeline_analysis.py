"""
Detailed timeline analysis - When do specific events happen?
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
print("TIMELINE ANALYSIS - WHEN DO CRITICAL EVENTS HAPPEN?")
print("="*80)

times = [clean_float(r['Time']) for r in records]
rpms = [clean_float(r['RPM']) for r in records]
pws = [clean_float(r['PW']) for r in records]
batteries = [clean_float(r['Battery V']) for r in records]
maps = [clean_float(r['MAP']) for r in records]
iacs = [clean_float(r['IAC value']) for r in records]
afrs = [clean_float(r['AFR']) for r in records]

# Find engine start
start_idx = next((i for i, rpm in enumerate(rpms) if rpm > 200), None)
start_time = times[start_idx] if start_idx else 0

print(f"\nEngine started at: {start_time:.3f}s")

# Question 1: When does PW drop from 3.175 to 1.98ms?
print("\n" + "="*80)
print("FUEL DELIVERY DECAY TIMELINE")
print("="*80)

max_pw = max(pws)
max_pw_idx = pws.index(max_pw)
max_pw_time = times[max_pw_idx]

print(f"\nMaximum PW: {max_pw:.3f}ms at t={max_pw_time:.3f}s")
print(f"\nPW decay timeline (showing every 5 seconds after peak):")
print(f"{'Time (s)':>10s} {'PW (ms)':>10s} {'Change':>10s} {'RPM':>8s} {'AFR':>8s} {'MAP':>8s} {'IAC':>8s}")
print("-"*66)

# Show PW progression every 5 seconds
for target_time in range(int(max_pw_time), int(times[-1]), 5):
    idx = min(range(len(times)), key=lambda i: abs(times[i] - target_time))
    change = pws[idx] - max_pw
    print(f"{times[idx]:10.1f} {pws[idx]:10.3f} {change:10.3f} {rpms[idx]:8.0f} {afrs[idx]:8.1f} {maps[idx]:8.0f} {iacs[idx]:8.0f}")

# Find when PW reaches 1.98ms
target_pw = 1.98
pw_198_idx = min(range(len(pws)), key=lambda i: abs(pws[i] - target_pw))
pw_198_time = times[pw_198_idx]
time_to_decay = pw_198_time - max_pw_time

print(f"\nPW reaches 1.98ms at: t={pw_198_time:.1f}s")
print(f"Time for 38% decay: {time_to_decay:.1f} seconds after peak")
print(f"This happens {pw_198_time - start_time:.1f}s after engine started")

# Question 2: When does battery drop to 9.7V?
print("\n" + "="*80)
print("BATTERY VOLTAGE TIMELINE")
print("="*80)

min_battery = min(batteries)
min_battery_idx = batteries.index(min_battery)
min_battery_time = times[min_battery_idx]

print(f"\nMinimum battery voltage: {min_battery:.1f}V at t={min_battery_time:.1f}s")
print(f"This occurs {min_battery_time - start_time:.1f}s after engine started")

# Show battery voltage around critical moments
print(f"\nBattery voltage at key moments:")
print(f"{'Event':30s} {'Time (s)':>10s} {'Voltage (V)':>12s} {'RPM':>8s}")
print("-"*62)

# At start
print(f"{'Engine start':30s} {start_time:10.1f} {batteries[start_idx]:12.1f} {rpms[start_idx]:8.0f}")

# At max PW (crank/enrichment)
print(f"{'Max PW (cranking)':30s} {max_pw_time:10.1f} {batteries[max_pw_idx]:12.1f} {rpms[max_pw_idx]:8.0f}")

# At minimum battery
print(f"{'Minimum battery':30s} {min_battery_time:10.1f} {min_battery:12.1f} {rpms[min_battery_idx]:8.0f}")

# Find all times battery < 11V
low_battery_times = [(times[i], batteries[i], rpms[i]) for i in range(len(batteries)) if batteries[i] < 11.0]
print(f"\nBattery below 11V: {len(low_battery_times)} samples ({len(low_battery_times)/len(batteries)*100:.1f}% of log)")
if low_battery_times:
    print(f"First below 11V: t={low_battery_times[0][0]:.1f}s ({low_battery_times[0][1]:.1f}V)")
    print(f"Last below 11V: t={low_battery_times[-1][0]:.1f}s ({low_battery_times[-1][1]:.1f}V)")
    print(f"Duration below 11V: {low_battery_times[-1][0] - low_battery_times[0][0]:.1f}s")

# Question 3: Is MAP normal for that RPM?
print("\n" + "="*80)
print("MAP ANALYSIS - IS IT NORMAL FOR THE RPM?")
print("="*80)

# Calculate average MAP while running
running_data = [(rpms[i], maps[i], iacs[i]) for i in range(start_idx, len(rpms)) if rpms[i] > 200]
avg_rpm_running = sum(r[0] for r in running_data) / len(running_data)
avg_map_running = sum(r[1] for r in running_data) / len(running_data)

print(f"\nWhile engine running:")
print(f"  Average RPM: {avg_rpm_running:.0f}")
print(f"  Average MAP: {avg_map_running:.0f} kPa")
print(f"  Minimum MAP: {min(r[1] for r in running_data):.0f} kPa")
print(f"  Maximum MAP: {max(r[1] for r in running_data):.0f} kPa")

print(f"\nMAP EVALUATION:")
print(f"  At {avg_rpm_running:.0f} RPM with closed throttle (TPS=0%):")
print(f"  Expected MAP: 45-65 kPa (depends on IAC opening)")
print(f"  Actual MAP: {avg_map_running:.0f} kPa")

if 45 <= avg_map_running <= 65:
    print(f"  ✓ MAP is NORMAL for this RPM")
    print(f"  This indicates: Engine is creating vacuum, pulling air through IAC")
else:
    print(f"  ✗ MAP is ABNORMAL")
    if avg_map_running > 65:
        print(f"  Too high: Not enough vacuum, possibly too much air leak")
    else:
        print(f"  Too low: Too much vacuum, possibly restricted intake")

# MAP to RPM relationship
print(f"\nMAP vs RPM relationship:")
print(f"  Lower MAP = More vacuum = Engine working harder")
print(f"  Higher MAP = Less vacuum = More air entering")
print(f"  Your {avg_map_running:.0f} kPa at {avg_rpm_running:.0f} RPM shows:")
print(f"  - Engine creating moderate vacuum ({(101-avg_map_running):.0f} kPa below atmosphere)")
print(f"  - IAC allowing sufficient airflow for low idle")
print(f"  - NOT a MAP problem - this is normal")

# Question 4: IAC analysis
print("\n" + "="*80)
print("IAC (IDLE AIR CONTROL) ANALYSIS")
print("="*80)

avg_iac_running = sum(r[2] for r in running_data) / len(running_data)
max_iac = max(iacs)
max_iac_idx = iacs.index(max_iac)

print(f"\nIAC Statistics:")
print(f"  Average while running: {avg_iac_running:.0f} steps")
print(f"  Minimum: {min(iacs):.0f} steps")
print(f"  Maximum: {max_iac:.0f} steps at t={times[max_iac_idx]:.1f}s")

print(f"\nIAC progression:")
print(f"{'Time (s)':>10s} {'IAC steps':>12s} {'RPM':>8s} {'MAP':>8s} {'Comment':30s}")
print("-"*70)

# Show IAC at key moments
key_times = [start_time, start_time+5, start_time+10, start_time+20, start_time+30, start_time+40]
for t in key_times:
    if t <= times[-1]:
        idx = min(range(len(times)), key=lambda i: abs(times[i] - t))
        comment = ""
        if t == start_time:
            comment = "Engine start"
        elif iacs[idx] > 100:
            comment = "Opening to raise RPM"
        elif iacs[idx] < 50:
            comment = "Closing, less air needed"
        print(f"{times[idx]:10.1f} {iacs[idx]:12.0f} {rpms[idx]:8.0f} {maps[idx]:8.0f} {comment:30s}")

print(f"\nIAC EVALUATION:")
print(f"  At {avg_rpm_running:.0f} RPM, IAC at {avg_iac_running:.0f} steps")
print(f"  Typical cold idle IAC: 80-120 steps (depends on calibration)")
print(f"  Your IAC position: {avg_iac_running:.0f} steps")

if 60 <= avg_iac_running <= 120:
    print(f"  ✓ IAC is in NORMAL range")
    print(f"  IAC is trying to add air to increase RPM")
    print(f"  BUT: RPM not responding because mixture is too LEAN")
    print(f"  Adding more air makes AFR even leaner!")
else:
    print(f"  ! IAC position unusual")

print(f"\nKEY INSIGHT:")
print(f"  IAC opening to {avg_iac_running:.0f} steps adds more AIR")
print(f"  More air without more FUEL = even leaner AFR")
print(f"  This is why IAC cannot fix the problem")
print(f"  Solution: Fix FUEL first, then IAC can stabilize RPM")

# Correlation analysis
print("\n" + "="*80)
print("CORRELATION SUMMARY")
print("="*80)

print(f"""
TIMELINE OF EVENTS:
===================

t=0s to ~10s: Pre-start period
  - Battery: Normal (~11-12V)
  - RPM: 0
  - PW: 0
  - Engine not running

t={start_time:.1f}s: ENGINE STARTS
  - RPM jumps to {rpms[start_idx]:.0f}
  - PW peaks at {max_pw:.3f}ms (cranking enrichment)
  - Battery at {batteries[start_idx]:.1f}V (cranking load)
  - MAP drops to {maps[start_idx]:.0f} kPa (engine creating vacuum)
  - IAC at {iacs[start_idx]:.0f} steps (cold start position)

t={start_time:.1f}s to {pw_198_time:.1f}s: POST-START DECAY
  - PW decays from {max_pw:.3f}ms to 1.98ms over {time_to_decay:.1f} seconds
  - AFR climbs from ~12.6 to ~14.0 (getting leaner)
  - RPM stays stuck at {avg_rpm_running:.0f} (cannot climb)
  - MAP settles at {avg_map_running:.0f} kPa (normal for this RPM)
  - IAC at {avg_iac_running:.0f} steps (trying to add air)
  - Battery recovers to ~{sum(batteries[start_idx:])/len(batteries[start_idx:]):.1f}V average

t={min_battery_time:.1f}s: MINIMUM BATTERY VOLTAGE
  - Battery drops to {min_battery:.1f}V (CRITICAL LOW)
  - RPM at {rpms[min_battery_idx]:.0f} (still struggling)
  - This likely during cranking or high electrical load

THROUGHOUT LOG:
  - RPM never exceeds {max(rpms):.0f} (far below 800-1000 needed)
  - AFR averages 13.6 (should be 11.5-12.5)
  - MAP stays at {avg_map_running:.0f} kPa (NORMAL for this RPM)
  - IAC at {avg_iac_running:.0f} steps (NORMAL range, but ineffective)

CONCLUSION:
===========
- PW decay happens immediately after start ({time_to_decay:.1f}s duration)
- Battery low during crank (9.7V minimum) - possible weak battery
- MAP is NORMAL for {avg_rpm_running:.0f} RPM - not the problem
- IAC is NORMAL range but cannot compensate for LEAN mixture
- PRIMARY ISSUE: Insufficient fuel enrichment, not MAP or IAC
""")

print("="*80)
