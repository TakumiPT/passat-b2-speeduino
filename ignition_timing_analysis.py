import csv

# Read the CSV file
data = []
with open('2025-11-19_11.29.51.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        data.append(row)

print("=" * 80)
print("IGNITION TIMING ANALYSIS")
print("=" * 80)

# Extract timing data
timing_values = []
rpm_values = []
map_values = []
tps_values = []

for row in data:
    advance = float(row['Advance _Current'])
    rpm = float(row['RPM'])
    map_kpa = float(row['MAP'])
    tps = float(row['TPS'])
    
    timing_values.append(advance)
    rpm_values.append(rpm)
    map_values.append(map_kpa)
    tps_values.append(tps)

# Overall statistics
print(f"\n=== OVERALL TIMING STATISTICS ===")
print(f"Minimum timing: {min(timing_values):.1f}° BTDC")
print(f"Maximum timing: {max(timing_values):.1f}° BTDC")
print(f"Average timing: {sum(timing_values)/len(timing_values):.1f}° BTDC")

# Idle timing (TPS = 0, RPM < 1100)
idle_timing = [timing_values[i] for i in range(len(data)) 
               if tps_values[i] == 0 and rpm_values[i] < 1100]

if idle_timing:
    print(f"\n=== IDLE TIMING (TPS=0%, RPM<1100) ===")
    print(f"Average: {sum(idle_timing)/len(idle_timing):.1f}° BTDC")
    print(f"Range: {min(idle_timing):.1f}° to {max(idle_timing):.1f}° BTDC")
    print(f"Samples: {len(idle_timing)}")

# WOT timing (TPS > 90%)
wot_timing = [(timing_values[i], rpm_values[i], map_values[i]) 
              for i in range(len(data)) if tps_values[i] > 90]

if wot_timing:
    print(f"\n=== WIDE OPEN THROTTLE (TPS>90%) ===")
    wot_advances = [t[0] for t in wot_timing]
    wot_rpms = [t[1] for t in wot_timing]
    print(f"Average timing: {sum(wot_advances)/len(wot_advances):.1f}° BTDC")
    print(f"Range: {min(wot_advances):.1f}° to {max(wot_advances):.1f}° BTDC")
    print(f"Average RPM: {sum(wot_rpms)/len(wot_rpms):.0f} RPM")
    print(f"Samples: {len(wot_timing)}")

# Part throttle (0 < TPS < 90%)
part_throttle = [(timing_values[i], tps_values[i], rpm_values[i]) 
                 for i in range(len(data)) if 0 < tps_values[i] < 90]

if part_throttle:
    print(f"\n=== PART THROTTLE (0%<TPS<90%) ===")
    pt_advances = [t[0] for t in part_throttle]
    print(f"Average timing: {sum(pt_advances)/len(pt_advances):.1f}° BTDC")
    print(f"Range: {min(pt_advances):.1f}° to {max(pt_advances):.1f}° BTDC")
    print(f"Samples: {len(part_throttle)}")

# Check for the fast acceleration events with timing
print(f"\n=== TIMING DURING FAST ACCELERATION EVENTS ===")
for i in range(len(data)):
    tps_dot = float(data[i]['TPS DOT'])
    if tps_dot > 500:  # Very fast acceleration
        time = float(data[i]['Time'])
        rpm = float(data[i]['RPM'])
        advance = float(data[i]['Advance _Current'])
        tps = float(data[i]['TPS'])
        afr = float(data[i]['AFR'])
        
        print(f"t={time:5.2f}s: RPM={rpm:4.0f}, TPS={tps:4.1f}%, "
              f"TPS DOT={tps_dot:6.0f}%/s, Timing={advance:4.1f}°, AFR={afr:5.2f}")

# Timing vs RPM breakdown
print(f"\n=== TIMING BY RPM RANGE (Idle conditions) ===")
rpm_ranges = [
    (800, 900, "800-900 RPM"),
    (900, 1000, "900-1000 RPM"),
    (1000, 1100, "1000-1100 RPM")
]

for rpm_min, rpm_max, label in rpm_ranges:
    range_timing = [timing_values[i] for i in range(len(data))
                   if rpm_min <= rpm_values[i] < rpm_max and tps_values[i] == 0]
    if range_timing:
        avg = sum(range_timing)/len(range_timing)
        print(f"{label}: {avg:.1f}° BTDC (n={len(range_timing)})")

# Assessment
print(f"\n=== TIMING ASSESSMENT ===")
avg_idle = sum(idle_timing)/len(idle_timing) if idle_timing else 0
print(f"Idle timing ({avg_idle:.1f}° BTDC):")
if 10 <= avg_idle <= 25:
    print("  ✓ EXCELLENT - Within optimal range (10-25° for TBI engines)")
elif avg_idle < 10:
    print("  ⚠ TOO RETARDED - Can increase for better idle stability")
else:
    print("  ⚠ TOO ADVANCED - Risk of knock, reduce slightly")

if wot_timing:
    avg_wot = sum(wot_advances)/len(wot_advances)
    print(f"\nWOT timing ({avg_wot:.1f}° BTDC):")
    if 20 <= avg_wot <= 35:
        print("  ✓ GOOD - Safe range for NA TBI engine")
    elif avg_wot < 20:
        print("  ⚠ CONSERVATIVE - Can advance for more power")
    else:
        print("  ⚠ AGGRESSIVE - Monitor for knock/detonation")

print("\n" + "=" * 80)
