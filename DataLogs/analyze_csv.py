"""
Proper MLG Analysis using the correctly converted CSV
"""
import csv

csv_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.csv"

print("="*80)
print("ACCURATE MLG DATA ANALYSIS FROM CONVERTED CSV")
print("="*80)

# Read the CSV
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    all_records = list(reader)
    # Skip the units row (second row after header)
    records = [r for r in all_records if r['Time'] and not r['Time'].strip() in ['s', 'sec', '']]

print(f"\nTotal records: {len(records)}")
print(f"Time range: {records[0]['Time']} to {records[-1]['Time']}")

# Clean time values (remove 's' suffix if present)
def clean_float(val):
    if isinstance(val, str):
        val = val.replace('s', '').strip()
    return float(val)

start_time = clean_float(records[0]['Time'])
end_time = clean_float(records[-1]['Time'])
print(f"Duration: {end_time - start_time:.3f} seconds")

# Find RPM at 24.272s if it exists
target_time = 24.272
print(f"\n{'='*80}")
print(f"LOOKING FOR DATA AT {target_time}s")
print(f"{'='*80}")

closest_record = None
min_diff = float('inf')

for rec in records:
    time = clean_float(rec['Time'])
    diff = abs(time - target_time)
    if diff < min_diff:
        min_diff = diff
        closest_record = rec

if closest_record:
    time = clean_float(closest_record['Time'])
    print(f"\nClosest record at time: {time:.3f}s (diff: {min_diff:.3f}s")
    print(f"RPM: {closest_record['RPM']}")
    print(f"MAP: {closest_record['MAP']}")
    print(f"TPS: {closest_record['TPS']}")
    print(f"AFR: {closest_record['AFR']}")
    print(f"PW: {closest_record['PW']}")
    print(f"VE1: {closest_record['VE1']}")
    print(f"CLT: {closest_record['CLT']}")
    print(f"Battery V: {closest_record['Battery V']}")
else:
    print(f"\nNo data found near {target_time}s")

# Show first 20 records
print(f"\n{'='*80}")
print("FIRST 20 SAMPLES:")
print(f"{'='*80}")
print(f"{'Time':>8s} {'RPM':>6s} {'MAP':>5s} {'TPS':>5s} {'AFR':>6s} {'PW':>6s} {'VE1':>5s} {'CLT':>5s}")
print("-"*52)

for i, rec in enumerate(records[:20]):
    try:
        print(f"{clean_float(rec['Time']):8.3f} {clean_float(rec['RPM']):6.0f} {clean_float(rec['MAP']):5.0f} "
              f"{clean_float(rec['TPS']):5.1f} {clean_float(rec['AFR']):6.1f} {clean_float(rec['PW']):6.2f} "
              f"{clean_float(rec['VE1']):5.0f} {clean_float(rec['CLT']):5.0f}")
    except:
        pass

# Statistics
print(f"\n{'='*80}")
print("STATISTICS:")
print(f"{'='*80}")

rpm_values = [clean_float(r['RPM']) for r in records]
afr_values = [clean_float(r['AFR']) for r in records]
pw_values = [clean_float(r['PW']) for r in records]
ve_values = [clean_float(r['VE1']) for r in records]
map_values = [clean_float(r['MAP']) for r in records]

print(f"\nRPM:")
print(f"  Min: {min(rpm_values):.0f}")
print(f"  Max: {max(rpm_values):.0f}")
print(f"  Avg: {sum(rpm_values)/len(rpm_values):.0f}")

print(f"\nAFR:")
print(f"  Min: {min(afr_values):.1f}")
print(f"  Max: {max(afr_values):.1f}")
print(f"  Avg: {sum(afr_values)/len(afr_values):.1f}")

print(f"\nPulse Width (ms):")
print(f"  Min: {min(pw_values):.3f}")
print(f"  Max: {max(pw_values):.3f}")
print(f"  Avg: {sum(pw_values)/len(pw_values):.3f}")

print(f"\nVE1 (%):")
print(f"  Min: {min(ve_values):.0f}")
print(f"  Max: {max(ve_values):.0f}")
print(f"  Avg: {sum(ve_values)/len(ve_values):.1f}")

print(f"\nMAP (kPa):")
print(f"  Min: {min(map_values):.0f}")
print(f"  Max: {max(map_values):.0f}")
print(f"  Avg: {sum(map_values)/len(map_values):.1f}")

# Key moments
print(f"\n{'='*80}")
print("KEY MOMENTS:")
print(f"{'='*80}")

# Find when RPM first exceeds 200 (engine fires)
for i, rec in enumerate(records):
    if clean_float(rec['RPM']) > 200:
        print(f"\nEngine fired at t={clean_float(rec['Time']):.3f}s:")
        print(f"  RPM: {rec['RPM']}")
        print(f"  AFR: {rec['AFR']}")
        print(f"  PW: {rec['PW']}")
        print(f"  VE1: {rec['VE1']}")
        break

# Find peak RPM
max_rpm_rec = max(records, key=lambda r: clean_float(r['RPM']))
print(f"\nPeak RPM at t={clean_float(max_rpm_rec['Time']):.3f}s:")
print(f"  RPM: {max_rpm_rec['RPM']}")
print(f"  AFR: {max_rpm_rec['AFR']}")
print(f"  MAP: {max_rpm_rec['MAP']}")

# Find richest AFR (minimum, excluding pre-start readings >15)
valid_afr_records = [r for r in records if clean_float(r['AFR']) < 15]
if valid_afr_records:
    min_afr_rec = min(valid_afr_records, key=lambda r: clean_float(r['AFR']))
    print(f"\nRichest AFR at t={clean_float(min_afr_rec['Time']):.3f}s:")
    print(f"  AFR: {min_afr_rec['AFR']}")
    print(f"  RPM: {min_afr_rec['RPM']}")
    print(f"  PW: {min_afr_rec['PW']}")

# Last 5 records
print(f"\n{'='*80}")
print("LAST 5 SAMPLES:")
print(f"{'='*80}")
print(f"{'Time':>8s} {'RPM':>6s} {'MAP':>5s} {'TPS':>5s} {'AFR':>6s} {'PW':>6s} {'VE1':>5s}")
print("-"*50)

for rec in records[-5:]:
    try:
        print(f"{clean_float(rec['Time']):8.3f} {clean_float(rec['RPM']):6.0f} {clean_float(rec['MAP']):5.0f} "
              f"{clean_float(rec['TPS']):5.1f} {clean_float(rec['AFR']):6.1f} {clean_float(rec['PW']):6.2f} "
              f"{clean_float(rec['VE1']):5.0f}")
    except:
        pass

print(f"\n{'='*80}")
