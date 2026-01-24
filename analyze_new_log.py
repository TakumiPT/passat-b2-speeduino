#!/usr/bin/env python3
"""
Analysis of new MLG file after fixes: 2025-11-19_11.29.51.mlg
Car is now running with default settings and corrected distributor timing
User suspects needs acceleration enrichment adjustment
"""

import csv
import statistics

# Read the CSV file
data = []
with open('2025-11-19_11.29.51.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        data.append(row)

print("=" * 80)
print("NEW DATA LOG ANALYSIS - After Fixes")
print("=" * 80)
print(f"\nTotal samples: {len(data)}")
print(f"Duration: {float(data[-1]['Time']):.1f} seconds")
print()

# Convert relevant fields
times = []
rpms = []
maps = []
tpss = []
afrs = []
pws = []
accel_enrichs = []
ves = []
advances = []
iacs = []
tps_dots = []
battery_vs = []
clts = []

for row in data:
    try:
        times.append(float(row['Time']))
        rpms.append(float(row['RPM']))
        maps.append(float(row['MAP']))
        tpss.append(float(row['TPS']))
        afrs.append(float(row['AFR']))
        pws.append(float(row['PW']))
        accel_enrichs.append(float(row['Accel Enrich']))
        ves.append(float(row['VE _Current']))
        advances.append(float(row['Advance _Current']))
        iacs.append(float(row['IAC value']))
        tps_dots.append(float(row['TPS DOT']))
        battery_vs.append(float(row['Battery V']))
        clts.append(float(row['CLT']))
    except (ValueError, KeyError):
        continue

print("=" * 80)
print("OVERALL STATISTICS")
print("=" * 80)
print(f"\nCoolant Temperature: {statistics.mean(clts):.1f} C (range: {min(clts):.1f}-{max(clts):.1f} C)")
print(f"Battery Voltage: {statistics.mean(battery_vs):.1f}V (range: {min(battery_vs):.1f}-{max(battery_vs):.1f}V)")
print()
print(f"RPM: avg={statistics.mean(rpms):.0f}, min={min(rpms):.0f}, max={max(rpms):.0f}")
print(f"MAP: avg={statistics.mean(maps):.1f} kPa, min={min(maps):.1f}, max={max(maps):.1f} kPa")
print(f"TPS: avg={statistics.mean(tpss):.1f}%, min={min(tpss):.1f}%, max={max(tpss):.1f}%")
print(f"AFR: avg={statistics.mean(afrs):.2f}:1, min={min(afrs):.2f}:1, max={max(afrs):.2f}:1")
print(f"Pulsewidth: avg={statistics.mean(pws):.2f}ms, min={min(pws):.2f}ms, max={max(pws):.2f}ms")
print(f"VE: avg={statistics.mean(ves):.1f}%, min={min(ves):.1f}%, max={max(ves):.1f}%")
print(f"Timing Advance: avg={statistics.mean(advances):.1f} deg, min={min(advances):.1f} deg, max={max(advances):.1f} deg")
print(f"IAC: avg={statistics.mean(iacs):.0f} steps, min={min(iacs):.0f}, max={max(iacs):.0f}")
print()

print("=" * 80)
print("ACCELERATION ENRICHMENT ANALYSIS")
print("=" * 80)
print()

# Find throttle opening events (TPS DOT > 10%/s = throttle opening)
accel_events = []
for i in range(len(tps_dots)):
    if tps_dots[i] > 10:  # Significant throttle opening
        accel_events.append({
            'time': times[i],
            'tps_dot': tps_dots[i],
            'tps': tpss[i],
            'rpm': rpms[i],
            'map': maps[i],
            'accel_enrich': accel_enrichs[i],
            'afr': afrs[i],
            'pw': pws[i],
            've': ves[i]
        })

print(f"Acceleration events detected (TPS DOT > 10%/s): {len(accel_events)}")
print()

if len(accel_events) > 0:
    print("ACCELERATION EVENT DETAILS:")
    print("-" * 80)
    print(f"{'Time':<8} {'TPS DOT':<10} {'TPS':<7} {'RPM':<6} {'AE%':<8} {'AFR':<8} {'PW':<8}")
    print(f"{'(s)':<8} {'(%/s)':<10} {'(%)':<7} {'(rpm)':<6} {'(%)':<8} {'(:1)':<8} {'(ms)':<8}")
    print("-" * 80)
    
    for event in accel_events[:20]:  # Show first 20 events
        print(f"{event['time']:<8.2f} {event['tps_dot']:<10.1f} {event['tps']:<7.1f} "
              f"{event['rpm']:<6.0f} {event['accel_enrich']:<8.0f} {event['afr']:<8.2f} "
              f"{event['pw']:<8.3f}")
    
    if len(accel_events) > 20:
        print(f"... and {len(accel_events) - 20} more events")
    
    print()
    print("ACCELERATION ENRICHMENT STATISTICS:")
    print("-" * 80)
    ae_values = [e['accel_enrich'] for e in accel_events]
    afr_during_accel = [e['afr'] for e in accel_events]
    
    print(f"Accel Enrichment: avg={statistics.mean(ae_values):.0f}%, "
          f"min={min(ae_values):.0f}%, max={max(ae_values):.0f}%")
    print(f"AFR during accel: avg={statistics.mean(afr_during_accel):.2f}:1, "
          f"min={min(afr_during_accel):.2f}:1, max={max(afr_during_accel):.2f}:1")
    print()
    
    # Analyze if going lean during acceleration
    lean_events = [e for e in accel_events if e['afr'] > 14.7]
    rich_events = [e for e in accel_events if e['afr'] < 13.5]
    good_events = [e for e in accel_events if 13.5 <= e['afr'] <= 14.7]
    
    print(f"Lean during accel (AFR > 14.7): {len(lean_events)} events ({len(lean_events)/len(accel_events)*100:.1f}%)")
    print(f"Rich during accel (AFR < 13.5): {len(rich_events)} events ({len(rich_events)/len(accel_events)*100:.1f}%)")
    print(f"Good during accel (13.5-14.7): {len(good_events)} events ({len(good_events)/len(accel_events)*100:.1f}%)")
    print()
    
    if len(lean_events) > len(accel_events) * 0.3:  # More than 30% lean
        print("WARNING: Engine going LEAN during acceleration!")
        print("   Recommendation: INCREASE Acceleration Enrichment")
        print()
    elif len(rich_events) > len(accel_events) * 0.3:  # More than 30% rich
        print("WARNING: Engine going RICH during acceleration!")
        print("   Recommendation: DECREASE Acceleration Enrichment")
        print()
    else:
        print("OK Acceleration enrichment appears reasonable")
        print()

else:
    print("No significant acceleration events detected (TPS DOT < 10%/s)")
    print("This log may be mostly idle/steady-state driving")
    print()

print("=" * 80)
print("IDLE CONDITION ANALYSIS")
print("=" * 80)
print()

# Idle = TPS < 1%, RPM < 1200
idle_samples = []
for i in range(len(tpss)):
    if tpss[i] < 1.0 and rpms[i] < 1200:
        idle_samples.append({
            'time': times[i],
            'rpm': rpms[i],
            'map': maps[i],
            'afr': afrs[i],
            'pw': pws[i],
            'iac': iacs[i],
            've': ves[i],
            'advance': advances[i]
        })

if len(idle_samples) > 0:
    print(f"Idle samples: {len(idle_samples)} ({len(idle_samples)/len(data)*100:.1f}% of log)")
    print()
    
    idle_rpms = [s['rpm'] for s in idle_samples]
    idle_maps = [s['map'] for s in idle_samples]
    idle_afrs = [s['afr'] for s in idle_samples]
    idle_iacs = [s['iac'] for s in idle_samples]
    idle_advances = [s['advance'] for s in idle_samples]
    
    print(f"Idle RPM: avg={statistics.mean(idle_rpms):.0f}, min={min(idle_rpms):.0f}, max={max(idle_rpms):.0f}")
    print(f"Idle MAP: avg={statistics.mean(idle_maps):.1f} kPa, min={min(idle_maps):.1f}, max={max(idle_maps):.1f} kPa")
    print(f"Idle AFR: avg={statistics.mean(idle_afrs):.2f}:1, min={min(idle_afrs):.2f}:1, max={max(idle_afrs):.2f}:1")
    print(f"Idle IAC: avg={statistics.mean(idle_iacs):.0f} steps, min={min(idle_iacs):.0f}, max={max(idle_iacs):.0f}")
    print(f"Idle Timing: avg={statistics.mean(idle_advances):.1f} deg, min={min(idle_advances):.1f} deg, max={max(idle_advances):.1f} deg")
    print()
    
    # Check idle stability
    rpm_std = statistics.stdev(idle_rpms) if len(idle_rpms) > 1 else 0
    afr_std = statistics.stdev(idle_afrs) if len(idle_afrs) > 1 else 0
    
    print(f"Idle RPM stability (std dev): {rpm_std:.1f} RPM")
    print(f"Idle AFR stability (std dev): {afr_std:.2f}")
    print()
    
    if statistics.mean(idle_rpms) < 850:
        print("WARNING: Idle RPM is LOW (< 850). Consider increasing idle target RPM.")
    elif statistics.mean(idle_rpms) > 950:
        print("WARNING: Idle RPM is HIGH (> 950). Consider decreasing idle target RPM.")
    else:
        print("OK Idle RPM is in good range (850-950)")
    print()
    
    if statistics.mean(idle_maps) > 45:
        print("WARNING: Idle MAP is HIGH (> 45 kPa). Possible issues:")
        print("   - Throttle plate not closing fully")
        print("   - IAC closed too much")
        print("   - Still some vacuum leak")
    elif statistics.mean(idle_maps) < 35:
        print("NOTICE: Idle MAP is LOW (< 35 kPa). Very good vacuum!")
        print("   Vacuum advance should be working well at this level.")
    else:
        print("OK Idle MAP is in good range (35-45 kPa) - no vacuum leak!")
    print()

else:
    print("No clear idle conditions found in this log")
    print()

print("=" * 80)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 80)
print()

# Overall assessment
print("CURRENT STATUS AFTER FIXES:")
print("-" * 80)
print(f"OK Engine running (avg {statistics.mean(rpms):.0f} RPM)")
print(f"OK Battery voltage improved ({statistics.mean(battery_vs):.1f}V)")

if len(idle_samples) > 0:
    if statistics.mean(idle_maps) < 45:
        print(f"OK Vacuum leak FIXED (MAP {statistics.mean(idle_maps):.1f} kPa at idle)")
    if statistics.mean(idle_rpms) > 850:
        print(f"OK Idle RPM improved ({statistics.mean(idle_rpms):.0f} RPM)")

print()
print("AREAS TO CHECK:")
print("-" * 80)

# Check for lean condition during acceleration
if len(accel_events) > 0:
    lean_pct = len([e for e in accel_events if e['afr'] > 14.7]) / len(accel_events) * 100
    if lean_pct > 30:
        ae_values = [e['accel_enrich'] for e in accel_events]
        print(f"FIX NEEDED: ACCELERATION ENRICHMENT: {lean_pct:.0f}% of accel events are LEAN")
        print("   Action: INCREASE Acceleration Enrichment Amount")
        print("   Typical settings: 50-100% enrichment for TPS DOT 50-100%/s")
        print("   Your current max AE: ~{:.0f}%".format(max(ae_values) if len(ae_values) > 0 else 0))
        print()

# Check AFR overall
if statistics.mean(afrs) > 14.7:
    print(f"FIX NEEDED: OVERALL MIXTURE: Slightly LEAN (avg {statistics.mean(afrs):.2f}:1)")
    print("   May need small VE table adjustment (+2-5%)")
    print()

# Check for rich condition
if statistics.mean(afrs) < 13.5:
    print(f"FIX NEEDED: OVERALL MIXTURE: Slightly RICH (avg {statistics.mean(afrs):.2f}:1)")
    print("   May need small VE table adjustment (-2-5%)")
    print()

print("=" * 80)
