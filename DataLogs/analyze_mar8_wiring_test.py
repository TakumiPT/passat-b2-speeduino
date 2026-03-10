"""
Analyze March 8 datalog after TinyWB rewiring (GND + 12V moved to screw terminals).
Check: Is AFR still pegged at 19.7, or is it working now?
"""
import csv
import os

filepath = os.path.join(os.path.dirname(__file__), '2026-03-08_13.52.26.csv')

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
        elif h_clean in ('bat', 'battery', 'batvoltage'):
            cols['bat'] = i
        elif h_clean in ('pw', 'pw1', 'pulsewidth'):
            cols['pw'] = i
        elif h_clean in ('tps', 'tps(adc)'):
            cols['tps'] = i
    
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

print("=" * 70)
print("MARCH 8 DATALOG ANALYSIS — After TinyWB Rewiring")
print("=" * 70)
print(f"Total samples: {len(rows)}")

if not rows:
    print("No data found!")
    exit()

# Running samples (RPM > 400)
running = [r for r in rows if r.get('rpm') is not None and r['rpm'] > 400]
cranking = [r for r in rows if r.get('rpm') is not None and 100 < r['rpm'] <= 400]
key_on = [r for r in rows if r.get('rpm') is not None and r['rpm'] <= 100 and r.get('bat') is not None and r['bat'] > 6]

print(f"Running samples (RPM > 400): {len(running)}")
print(f"Cranking samples (100-400 RPM): {len(cranking)}")
print(f"Key on, engine off: {len(key_on)}")

# Duration
if rows:
    duration = rows[-1].get('time', 0) - rows[0].get('time', 0) if rows[0].get('time') is not None else 0
    print(f"Duration: {duration:.0f}s ({duration/60:.1f} min)")

# Battery voltage
bat_running = [r['bat'] for r in running if r.get('bat') and r['bat'] > 5]
if bat_running:
    print(f"\nBattery voltage (running): {min(bat_running):.1f}V - {max(bat_running):.1f}V (avg {sum(bat_running)/len(bat_running):.1f}V)")

# CLT
clt_vals = [r['clt'] for r in running if r.get('clt')]
if clt_vals:
    print(f"CLT: {min(clt_vals):.0f}°C → {max(clt_vals):.0f}°C")

# ========== AFR ANALYSIS (CRITICAL) ==========
print("\n" + "=" * 70)
print("O2 SENSOR STATUS — DID THE REWIRING FIX IT?")
print("=" * 70)

afr_all = [r['afr'] for r in rows if r.get('afr') is not None]
if afr_all:
    print(f"Total AFR samples: {len(afr_all)}")
    
    # Count by value ranges
    pegged_197 = sum(1 for a in afr_all if a >= 19.6)
    pegged_149 = sum(1 for a in afr_all if 14.8 <= a < 15.0)
    normal = sum(1 for a in afr_all if 10.0 <= a < 19.0 and not (14.8 <= a < 15.0))
    low = sum(1 for a in afr_all if a < 10.0)
    
    print(f"\nAFR distribution:")
    print(f"  Pegged at 19.7 (max): {pegged_197} ({100*pegged_197/len(afr_all):.1f}%)")
    print(f"  At 14.9 (heater off): {pegged_149} ({100*pegged_149/len(afr_all):.1f}%)")
    print(f"  Normal range (10-19): {normal} ({100*normal/len(afr_all):.1f}%)")
    print(f"  Below 10 (bogus): {low} ({100*low/len(afr_all):.1f}%)")
    
    # AFR stats
    afr_min = min(afr_all)
    afr_max = max(afr_all)
    afr_avg = sum(afr_all) / len(afr_all)
    
    print(f"\nAFR range: {afr_min:.1f} - {afr_max:.1f} (avg {afr_avg:.1f})")
    
    # Check if sensor is actually reacting
    afr_running = [r['afr'] for r in running if r.get('afr') is not None]
    if len(afr_running) > 10:
        afr_std = (sum((a - afr_avg)**2 for a in afr_running) / len(afr_running)) ** 0.5
        print(f"AFR variability (std dev): {afr_std:.2f}")
        
        if afr_std < 0.5:
            print("  ⚠️  AFR is CONSTANT — sensor NOT reacting (still broken or heater not working)")
        elif afr_std < 2.0:
            print("  ⚠️  AFR barely moving — sensor may be warming up or marginal")
        else:
            print("  ✅ AFR is REACTING — sensor is responding to engine conditions")
    
    # Timeline analysis - does AFR change over time?
    print("\n--- AFR Timeline (first 60s vs last 60s) ---")
    early = [r['afr'] for r in rows[:900] if r.get('afr')]  # ~60s at 15Hz
    late = [r['afr'] for r in rows[-900:] if r.get('afr')]
    
    if early:
        print(f"First 60s: AFR avg {sum(early)/len(early):.1f} (range {min(early):.1f}-{max(early):.1f})")
    if late:
        print(f"Last 60s:  AFR avg {sum(late)/len(late):.1f} (range {min(late):.1f}-{max(late):.1f})")
    
    # Verdict
    print("\n" + "=" * 70)
    if pegged_197 > len(afr_all) * 0.9:
        print("VERDICT: ❌ O2 SENSOR STILL BROKEN")
        print("AFR still pegged at 19.7. Possible causes:")
        print("  1. Heater still not getting clean GND (DB9 cable issue?)")
        print("  2. TinyWB module defective")
        print("  3. LSU 4.9 sensor dead (check heater resistance at pins 3&4)")
        print("  4. Wiring error in the rewire (12V/GND swapped?)")
    elif pegged_149 > len(afr_all) * 0.8:
        print("VERDICT: ⚠️  O2 HEATER NOT WORKING")
        print("AFR stuck at 14.9 = TinyWB default when heater disconnected.")
        print("  - Check 12V getting to TinyWB VM pin")
        print("  - Check continuity from TinyWB H+ to LSU pin 4")
        print("  - Check continuity from TinyWB H- to LSU pin 3")
    elif normal > len(afr_all) * 0.7:
        print("VERDICT: ✅ O2 SENSOR WORKING!")
        print("AFR readings are in normal range and reacting to engine conditions.")
        print("Rewiring SUCCESSFUL — GND offset fixed.")
    else:
        print("VERDICT: ⚠️  O2 SENSOR MARGINAL / INCONCLUSIVE")
        print("AFR readings are mixed. Sensor may be:")
        print("  - Still warming up (needs 15-30s)")
        print("  - Intermittent connection (DB9 pins loose)")
        print("  - Partially working but unreliable")
    print("=" * 70)

else:
    print("No AFR data in log!")

# RPM/MAP/PW for engine health
print("\n" + "=" * 70)
print("ENGINE HEALTH (independent of O2 sensor)")
print("=" * 70)

if running:
    rpm_vals = [r['rpm'] for r in running if r.get('rpm')]
    map_vals = [r['map'] for r in running if r.get('map')]
    pw_vals = [r['pw'] for r in running if r.get('pw')]
    
    if rpm_vals:
        print(f"RPM: {min(rpm_vals):.0f} - {max(rpm_vals):.0f} (avg {sum(rpm_vals)/len(rpm_vals):.0f})")
    if map_vals:
        print(f"MAP: {min(map_vals):.0f} - {max(map_vals):.0f} kPa (avg {sum(map_vals)/len(map_vals):.0f})")
    if pw_vals:
        print(f"PW: {min(pw_vals):.1f} - {max(pw_vals):.1f} ms (avg {sum(pw_vals)/len(pw_vals):.1f})")
    
    # Idle stability
    idle = [r for r in running if r.get('rpm', 0) < 1200 and r.get('map', 100) < 60]
    if idle:
        idle_rpm = [r['rpm'] for r in idle if r.get('rpm')]
        if idle_rpm and len(idle_rpm) > 10:
            avg_rpm = sum(idle_rpm) / len(idle_rpm)
            rpm_std = (sum((r - avg_rpm)**2 for r in idle_rpm) / len(idle_rpm)) ** 0.5
            print(f"\nIdle RPM: {avg_rpm:.0f} ±{rpm_std:.0f}")
            if rpm_std < 30:
                print("  ✅ Idle stability: EXCELLENT")
            elif rpm_std < 60:
                print("  ✅ Idle stability: GOOD")
            elif rpm_std < 100:
                print("  ⚠️  Idle stability: FAIR (some roughness)")
            else:
                print("  ❌ Idle stability: ROUGH")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
if pegged_197 > len(afr_all) * 0.9:
    print("1. Measure LSU 4.9 heater resistance (pins 3&4, should be 2-4Ω)")
    print("2. Check voltage at TinyWB H+12V pin with car running (should pulse ~12V)")
    print("3. Inspect DB9 cable solder joints for cracks/cold solder")
    print("4. Try different TinyWB module if available (test if TinyWB is dead)")
elif pegged_149 > len(afr_all) * 0.8:
    print("1. Verify 12V is connected to TinyWB VM pin (not just H+ to sensor)")
    print("2. Check fuse/wiring from screw terminal to TinyWB")
    print("3. Measure voltage at LSU pins 3&4 with car running")
else:
    print("✅ O2 sensor appears to be working — focus on alternator and shifter!")
    print("1. Fix alternator (should charge at 14V+, currently only 12.8V)")
    print("2. Fix shifter bushings (can only use 3rd gear)")
    print("3. Record longer datalog with working sensor for tuning")
