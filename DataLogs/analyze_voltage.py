"""
Alternator/battery voltage analysis - correlate with RPM and TPS
VW Passat B2 DT 1.6 Speeduino
"""
import csv
import os

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "2026-03-05_20.55.47.csv")

COL = {
    'Time': 0, 'RPM': 2, 'MAP': 3, 'TPS': 5, 'AFR': 6,
    'CLT': 9, 'BatteryV': 34, 'Gbattery': 14, 'PW': 22,
}

def safe_float(val, default=0.0):
    try:
        return float(val.strip().replace('"', ''))
    except (ValueError, AttributeError):
        return default

def analyze():
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # headers
        next(reader)  # units
        for row in reader:
            if len(row) < 50:
                continue
            rows.append(row)

    total = len(rows)
    times = [safe_float(r[COL['Time']]) for r in rows]
    rpms = [safe_float(r[COL['RPM']]) for r in rows]
    tps_vals = [safe_float(r[COL['TPS']]) for r in rows]
    batts = [safe_float(r[COL['BatteryV']]) for r in rows]
    maps = [safe_float(r[COL['MAP']]) for r in rows]
    gbatts = [safe_float(r[COL['Gbattery']]) for r in rows]
    afrs = [safe_float(r[COL['AFR']]) for r in rows]

    print("=" * 90)
    print("ALTERNATOR / BATTERY VOLTAGE ANALYSIS")
    print("=" * 90)

    # Timeline: voltage vs RPM vs TPS every 10 seconds
    print(f"\n{'Time':>6s} {'RPM':>5s} {'TPS':>5s} {'MAP':>4s} {'BattV':>6s} {'Gbatt':>6s} {'AFR':>5s} {'Note'}")
    print("-" * 90)

    running = [i for i in range(total) if rpms[i] > 400]
    if not running:
        print("No running samples!")
        return

    # Show every 10 seconds during running
    start_t = times[running[0]]
    for t_mark in range(0, int(times[running[-1]] - start_t) + 1, 10):
        target = start_t + t_mark
        idx = min(range(total), key=lambda i: abs(times[i] - target))
        note = ""
        if batts[idx] < 10:
            note = "⚠️ VERY LOW"
        elif batts[idx] < 11:
            note = "⚠️ LOW"
        elif batts[idx] < 12.5:
            note = "low (no charge?)"
        elif batts[idx] >= 13.0:
            note = "✅ CHARGING"
        if tps_vals[idx] > 2:
            note += " [THROTTLE OPEN]"
        print(f"{t_mark:5d}s {rpms[idx]:5.0f} {tps_vals[idx]:5.1f} {maps[idx]:4.0f} "
              f"{batts[idx]:6.1f}V {gbatts[idx]:5.0f}% {afrs[idx]:5.1f} {note}")

    # Find first moment voltage goes above 12.5V (alternator engages)
    print(f"\n{'='*90}")
    print("ALTERNATOR ENGAGEMENT DETECTION")
    print(f"{'='*90}")

    first_charge = None
    for i in running:
        if batts[i] >= 12.5:
            first_charge = i
            break

    if first_charge:
        # Show 5 seconds before and after
        t_charge = times[first_charge]
        print(f"\nFirst voltage ≥12.5V at t={t_charge:.1f}s (sample #{first_charge})")
        print(f"\nContext around alternator engagement:")
        print(f"{'Time':>8s} {'RPM':>5s} {'TPS':>5s} {'MAP':>4s} {'BattV':>6s} {'Note'}")
        print("-" * 60)
        window = [i for i in range(total) if t_charge - 5 <= times[i] <= t_charge + 5]
        for i in window:
            note = "<<< CHARGE START" if i == first_charge else ""
            if tps_vals[i] > 2:
                note += " [THROTTLE]"
            print(f"{times[i]:8.1f} {rpms[i]:5.0f} {tps_vals[i]:5.1f} {maps[i]:4.0f} "
                  f"{batts[i]:6.1f}V {note}")
    else:
        print("\n⚠️ Voltage NEVER reached 12.5V during running!")

    # Voltage vs RPM correlation
    print(f"\n{'='*90}")
    print("VOLTAGE vs RPM CORRELATION")
    print(f"{'='*90}")

    rpm_bands = [(400,800), (800,1000), (1000,1200), (1200,1500), (1500,2000), (2000,3000)]
    print(f"\n{'RPM Band':>15s} {'Avg V':>6s} {'Min V':>6s} {'Max V':>6s} {'N':>6s} {'Status'}")
    print("-" * 60)
    for lo, hi in rpm_bands:
        band = [i for i in running if lo <= rpms[i] < hi]
        if band:
            bv = [batts[i] for i in band]
            avg_v = sum(bv)/len(bv)
            status = "✅ CHARGING" if avg_v >= 13.0 else ("⚠️ LOW" if avg_v < 12.0 else "marginal")
            print(f"  {lo:5d}-{hi:5d}: {avg_v:6.1f} {min(bv):6.1f} {max(bv):6.1f} {len(band):6d} {status}")

    # Voltage vs TPS correlation
    print(f"\n{'='*90}")
    print("VOLTAGE vs TPS (THROTTLE) CORRELATION")
    print(f"{'='*90}")

    tps_bands = [(0,1), (1,3), (3,10), (10,30), (30,60), (60,100)]
    print(f"\n{'TPS Band':>15s} {'Avg V':>6s} {'Min V':>6s} {'Max V':>6s} {'Avg RPM':>8s} {'N':>6s}")
    print("-" * 60)
    for lo, hi in tps_bands:
        band = [i for i in running if lo <= tps_vals[i] < hi]
        if band:
            bv = [batts[i] for i in band]
            br = [rpms[i] for i in band]
            print(f"  {lo:3d}-{hi:3d}%: {sum(bv)/len(bv):6.1f} {min(bv):6.1f} {max(bv):6.1f} "
                  f"{sum(br)/len(br):8.0f} {len(band):6d}")

    # Check: does voltage drop back when throttle closes?
    print(f"\n{'='*90}")
    print("TPS vs VOLTAGE TRANSITIONS")
    print(f"{'='*90}")
    print("\nLooking for throttle blips and voltage response:")

    # Find TPS transitions (idle→throttle→idle)
    blip_count = 0
    for i in range(10, total - 10):
        if rpms[i] > 400 and tps_vals[i-5] < 2 and tps_vals[i] > 5 and tps_vals[i+5] < 2:
            blip_count += 1
            if blip_count <= 5:  # Show first 5
                print(f"\n  Throttle blip #{blip_count} at t={times[i]:.1f}s:")
                for j in range(i-3, i+6):
                    if 0 <= j < total:
                        marker = " <<<" if j == i else ""
                        print(f"    t={times[j]:.1f}s TPS={tps_vals[j]:5.1f}% "
                              f"RPM={rpms[j]:5.0f} V={batts[j]:.1f}V{marker}")
    if blip_count == 0:
        # Show the sustained throttle period instead
        print("\nNo brief blips found. Looking for sustained throttle periods:")
        in_throttle = False
        throttle_events = []
        for i in running:
            if tps_vals[i] > 3 and not in_throttle:
                in_throttle = True
                throttle_events.append(('OPEN', i, times[i], tps_vals[i], rpms[i], batts[i]))
            elif tps_vals[i] <= 1 and in_throttle:
                in_throttle = False
                throttle_events.append(('CLOSE', i, times[i], tps_vals[i], rpms[i], batts[i]))

        for ev in throttle_events[:20]:
            print(f"  {ev[0]:6s} t={ev[2]:.1f}s TPS={ev[3]:.1f}% RPM={ev[4]:.0f} V={ev[5]:.1f}V")

    # AFR accuracy check: does AFR reading change with voltage?
    print(f"\n{'='*90}")
    print("AFR vs VOLTAGE — TinyWB ACCURACY CHECK")
    print(f"{'='*90}")
    print("\nIf TinyWB reads lean only at low voltage, the lean readings may be false.")

    # Hot idle only (CLT≥70, RPM 800-1200, MAP<50) to isolate voltage effect
    clts = [safe_float(r[COL['CLT']]) for r in rows]
    hot_idle = [i for i in running if clts[i] >= 70 and 800 <= rpms[i] <= 1200 and maps[i] < 50]

    if hot_idle:
        v_bands = [(0,10), (10,10.5), (10.5,11), (11,11.5), (11.5,12), (12,12.5), (12.5,13), (13,15)]
        print(f"\n  Hot idle (CLT≥70, RPM 800-1200, MAP<50):")
        print(f"  {'Voltage':>12s} {'Avg AFR':>8s} {'Count':>6s}")
        print(f"  " + "-" * 30)
        for vlo, vhi in v_bands:
            band = [i for i in hot_idle if vlo <= batts[i] < vhi]
            if band:
                af = [afrs[i] for i in band if 5 < afrs[i] < 25]
                if af:
                    print(f"  {vlo:.1f}-{vhi:.1f}V: {sum(af)/len(af):8.1f} {len(af):6d}")

    print(f"\n{'='*90}")
    print("CONCLUSION")
    print(f"{'='*90}")

    # Summary stats
    idle_low_v = [i for i in running if rpms[i] < 1200 and batts[i] < 12.0]
    idle_ok_v = [i for i in running if rpms[i] < 1200 and batts[i] >= 12.5]
    print(f"\nIdle samples with V < 12.0: {len(idle_low_v)}")
    print(f"Idle samples with V ≥ 12.5: {len(idle_ok_v)}")

    if idle_ok_v:
        pct_charged = 100 * len(idle_ok_v) / (len(idle_low_v) + len(idle_ok_v))
        print(f"Percentage charging at idle: {pct_charged:.1f}%")
    else:
        print("Alternator NEVER charges at idle!")

    avg_running_v = sum(batts[i] for i in running) / len(running)
    if avg_running_v < 12.0:
        print(f"\n⚠️ Average running voltage {avg_running_v:.1f}V — ALTERNATOR PROBLEM")
        print("  Possible causes:")
        print("  1. Belt slipping (especially at idle — tightens under load/RPM)")
        print("  2. Bad voltage regulator")
        print("  3. Worn alternator brushes")
        print("  4. Bad ground connection to alternator")
        print("  5. Speeduino battery sense wire picking up voltage drop")

if __name__ == '__main__':
    analyze()
