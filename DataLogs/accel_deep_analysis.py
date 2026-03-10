#!/usr/bin/env python3
"""
Deep Acceleration & RPM Instability Analysis — 2026-03-01_19.05.30.csv
VW Passat B2 DT 1.6L Speeduino — TBI Monopoint

Lower thresholds to catch every TPS movement, plus RPM instability analysis.
The user heard "choking or hesitation" — could be:
1. Small throttle changes causing stumble
2. RPM oscillation/hunting at idle
3. Brief lean spikes even at steady state
"""

import csv
import sys

CSV_FILE = "2026-03-01_19.05.30.csv"

COL = {
    'Time': 0, 'RPM': 2, 'MAP': 3, 'TPS': 5, 'AFR': 6,
    'CLT': 9, 'Engine': 10, 'AccelEnrich': 18, 'VE': 19,
    'PW': 22, 'AFR_Target': 26, 'DutyCycle': 28,
    'TPS_DOT': 30, 'Advance': 31, 'BattV': 34, 'RPM_S': 35,
    'Gammae': 17, 'Gwarm': 15,
}

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def read_data(filename):
    rows = []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # header names
        next(reader)  # units
        for line in reader:
            if len(line) < 36:
                continue
            row = {
                'time': safe_float(line[COL['Time']]),
                'rpm': safe_int(line[COL['RPM']]),
                'map': safe_int(line[COL['MAP']]),
                'tps': safe_float(line[COL['TPS']]),
                'afr': safe_float(line[COL['AFR']]),
                'clt': safe_int(line[COL['CLT']]),
                'engine': safe_int(line[COL['Engine']]),
                'accel_enrich': safe_int(line[COL['AccelEnrich']]),
                've': safe_int(line[COL['VE']]),
                'pw': safe_float(line[COL['PW']]),
                'afr_target': safe_float(line[COL['AFR_Target']]),
                'duty': safe_float(line[COL['DutyCycle']]),
                'tps_dot': safe_float(line[COL['TPS_DOT']]),
                'advance': safe_float(line[COL['Advance']]),
                'batt_v': safe_float(line[COL['BattV']]),
                'rpm_s': safe_float(line[COL['RPM_S']]),
                'gammae': safe_int(line[COL['Gammae']]),
                'gwarm': safe_int(line[COL['Gwarm']]),
            }
            rows.append(row)
    return rows

def main():
    print("=" * 100)
    print("DEEP ACCELERATION & RPM INSTABILITY ANALYSIS — 2026-03-01_19.05.30")
    print("=" * 100)

    data = read_data(CSV_FILE)
    running = [d for d in data if d['rpm'] > 300]
    print(f"\nTotal samples: {len(data)}, Running (RPM>300): {len(running)}")

    if not running:
        print("No running data!")
        return

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: TPS Distribution — What is the driver doing?
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 1: TPS (Throttle Position) Distribution")
    print(f"{'─' * 100}")

    tps_vals = [d['tps'] for d in running]
    print(f"  TPS range: {min(tps_vals):.1f}% – {max(tps_vals):.1f}%")
    print(f"  TPS = 0%:   {sum(1 for t in tps_vals if t == 0)}/{len(tps_vals)} samples ({100*sum(1 for t in tps_vals if t == 0)/len(tps_vals):.1f}%)")
    print(f"  TPS 0-1%:   {sum(1 for t in tps_vals if 0 < t <= 1)}/{len(tps_vals)} samples")
    print(f"  TPS 1-5%:   {sum(1 for t in tps_vals if 1 < t <= 5)}/{len(tps_vals)} samples")
    print(f"  TPS 5-20%:  {sum(1 for t in tps_vals if 5 < t <= 20)}/{len(tps_vals)} samples")
    print(f"  TPS 20-50%: {sum(1 for t in tps_vals if 20 < t <= 50)}/{len(tps_vals)} samples")
    print(f"  TPS >50%:   {sum(1 for t in tps_vals if t > 50)}/{len(tps_vals)} samples")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: ALL TPS changes (any increase ≥ 0.5%)
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 2: ALL TPS Increases (≥ 0.5% change)")
    print(f"{'─' * 100}")

    # Find every sample-to-sample TPS increase
    tps_increases = []
    for i in range(1, len(running)):
        delta = running[i]['tps'] - running[i-1]['tps']
        if delta >= 0.5:
            tps_increases.append({
                'idx': i,
                'time': running[i]['time'],
                'tps_before': running[i-1]['tps'],
                'tps_after': running[i]['tps'],
                'delta': delta,
                'rpm': running[i]['rpm'],
                'afr': running[i]['afr'],
                'map': running[i]['map'],
                'tps_dot': running[i]['tps_dot'],
            })

    print(f"  Found {len(tps_increases)} sample-to-sample TPS increases ≥ 0.5%")
    if tps_increases:
        print(f"\n  {'Time':>8s}  {'TPS Before':>10s}  {'TPS After':>10s}  {'Delta':>6s}  {'RPM':>5s}  {'AFR':>5s}  {'MAP':>4s}  {'TPS_DOT':>7s}")
        print(f"  {'─'*8}  {'─'*10}  {'─'*10}  {'─'*6}  {'─'*5}  {'─'*5}  {'─'*4}  {'─'*7}")
        for t in tps_increases:
            print(f"  {t['time']:8.2f}  {t['tps_before']:10.1f}  {t['tps_after']:10.1f}  {t['delta']:6.1f}  {t['rpm']:5d}  {t['afr']:5.1f}  {t['map']:4d}  {t['tps_dot']:7.0f}")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: RPM Instability — hunting, surging, stumbles
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 3: RPM Instability (drops, surges, oscillation)")
    print(f"{'─' * 100}")

    # Find RPM drops > 50 RPM sample-to-sample
    rpm_drops = []
    for i in range(1, len(running)):
        delta_rpm = running[i]['rpm'] - running[i-1]['rpm']
        if delta_rpm < -50:
            rpm_drops.append({
                'time': running[i]['time'],
                'rpm_before': running[i-1]['rpm'],
                'rpm_after': running[i]['rpm'],
                'delta': delta_rpm,
                'tps': running[i]['tps'],
                'afr': running[i]['afr'],
                'map': running[i]['map'],
                'pw': running[i]['pw'],
                'clt': running[i]['clt'],
            })

    print(f"\n  RPM drops > 50 RPM (sample-to-sample): {len(rpm_drops)}")
    if rpm_drops:
        print(f"\n  {'Time':>8s}  {'RPM Before':>10s}  {'RPM After':>10s}  {'ΔRPM':>6s}  {'TPS':>5s}  {'AFR':>5s}  {'MAP':>4s}  {'PW':>6s}  {'CLT':>4s}")
        print(f"  {'─'*8}  {'─'*10}  {'─'*10}  {'─'*6}  {'─'*5}  {'─'*5}  {'─'*4}  {'─'*6}  {'─'*4}")
        for d in rpm_drops:
            marker = ""
            if d['afr'] > 15.5:
                marker = " ← LEAN"
            if d['afr'] > 17.0:
                marker = " ← VERY LEAN!"
            print(f"  {d['time']:8.2f}  {d['rpm_before']:10d}  {d['rpm_after']:10d}  {d['delta']:6d}  {d['tps']:5.1f}  {d['afr']:5.1f}  {d['map']:4d}  {d['pw']:6.3f}  {d['clt']:4d}{marker}")

    # RPM oscillation analysis (rolling window, check variance)
    print(f"\n  RPM 2-second rolling window analysis:")
    window_size = 30  # ~2 seconds at 15 Hz
    max_oscillation = 0
    max_osc_time = 0
    osc_events = []
    for i in range(window_size, len(running)):
        window = running[i-window_size:i]
        rpms = [w['rpm'] for w in window]
        rpm_range = max(rpms) - min(rpms)
        if rpm_range > 100:
            avg_rpm = sum(rpms) / len(rpms)
            if rpm_range > max_oscillation:
                max_oscillation = rpm_range
                max_osc_time = running[i]['time']
            osc_events.append({
                'time': running[i]['time'],
                'rpm_range': rpm_range,
                'avg_rpm': avg_rpm,
                'min_rpm': min(rpms),
                'max_rpm': max(rpms),
                'clt': running[i]['clt'],
                'tps': running[i]['tps'],
            })

    if osc_events:
        # Group consecutive oscillation events
        print(f"  Found {len(osc_events)} windows with >100 RPM variation")
        print(f"  Worst oscillation: {max_oscillation} RPM @ {max_osc_time:.1f}s")
        # Show top 10 worst
        osc_sorted = sorted(osc_events, key=lambda x: x['rpm_range'], reverse=True)
        print(f"\n  Top 10 worst oscillation windows:")
        print(f"  {'Time':>8s}  {'RPM Range':>10s}  {'Min':>5s}  {'Max':>5s}  {'Avg':>6s}  {'TPS':>5s}  {'CLT':>4s}")
        for o in osc_sorted[:10]:
            print(f"  {o['time']:8.2f}  {o['rpm_range']:10d}  {o['min_rpm']:5d}  {o['max_rpm']:5d}  {o['avg_rpm']:6.0f}  {o['tps']:5.1f}  {o['clt']:4d}")
    else:
        print("  ✅ No significant RPM oscillation (all 2s windows < 100 RPM variation)")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: AFR Anomalies — lean spikes while running
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 4: AFR Anomalies (lean spikes, rich spikes)")
    print(f"{'─' * 100}")

    afr_vals = [d['afr'] for d in running if d['afr'] > 0]
    print(f"\n  AFR range: {min(afr_vals):.1f} – {max(afr_vals):.1f}")
    print(f"  AFR distribution:")
    print(f"    < 12.0 (very rich):   {sum(1 for a in afr_vals if a < 12.0)} samples")
    print(f"    12.0-13.0 (rich):     {sum(1 for a in afr_vals if 12.0 <= a < 13.0)} samples")
    print(f"    13.0-14.0 (normal):   {sum(1 for a in afr_vals if 13.0 <= a < 14.0)} samples")
    print(f"    14.0-15.0 (stoich):   {sum(1 for a in afr_vals if 14.0 <= a < 15.0)} samples")
    print(f"    15.0-16.0 (lean):     {sum(1 for a in afr_vals if 15.0 <= a < 16.0)} samples")
    print(f"    16.0-17.0 (very lean):{sum(1 for a in afr_vals if 16.0 <= a < 17.0)} samples")
    print(f"    > 17.0 (misfire risk):{sum(1 for a in afr_vals if a > 17.0)} samples")

    # Find lean spikes (AFR > 15.5)
    lean_spikes = [(d['time'], d['afr'], d['rpm'], d['tps'], d['map'], d['pw'], d['clt'])
                   for d in running if d['afr'] > 15.5]
    if lean_spikes:
        print(f"\n  ⚠️  {len(lean_spikes)} samples with AFR > 15.5:")
        print(f"  {'Time':>8s}  {'AFR':>5s}  {'RPM':>5s}  {'TPS':>5s}  {'MAP':>4s}  {'PW':>6s}  {'CLT':>4s}")
        for s in lean_spikes[:30]:
            print(f"  {s[0]:8.2f}  {s[1]:5.1f}  {s[2]:5d}  {s[3]:5.1f}  {s[4]:4d}  {s[5]:6.3f}  {s[6]:4d}")
        if len(lean_spikes) > 30:
            print(f"  ... and {len(lean_spikes)-30} more")
    else:
        print("\n  ✅ No lean spikes (AFR stays ≤ 15.5)")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: Choking/Stumble Events — RPM drop + context
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 5: Possible Choking/Stumble Events (RPM recovery analysis)")
    print(f"{'─' * 100}")

    # Look for RPM drops followed by recovery while TPS is stable or rising
    stumbles = []
    for i in range(2, len(running) - 5):
        rpm_now = running[i]['rpm']
        rpm_prev = running[i-1]['rpm']
        rpm_prev2 = running[i-2]['rpm']

        # RPM was stable or rising, then drops
        if rpm_prev >= rpm_prev2 - 20 and rpm_now < rpm_prev - 30:
            # Check if TPS is stable or rising (not a lift-off)
            tps_now = running[i]['tps']
            tps_prev = running[i-1]['tps']
            if tps_now >= tps_prev - 0.5:  # Not lifting off throttle
                # Check next few samples for recovery
                future_rpms = [running[i+j]['rpm'] for j in range(1, min(6, len(running)-i))]
                if future_rpms and max(future_rpms) > rpm_now + 20:
                    stumbles.append({
                        'time': running[i]['time'],
                        'rpm_before': rpm_prev,
                        'rpm_dip': rpm_now,
                        'rpm_recovery': max(future_rpms),
                        'dip_size': rpm_prev - rpm_now,
                        'tps': tps_now,
                        'afr': running[i]['afr'],
                        'map': running[i]['map'],
                        'pw': running[i]['pw'],
                        'ae': running[i]['accel_enrich'],
                        'clt': running[i]['clt'],
                        'advance': running[i]['advance'],
                    })

    if stumbles:
        print(f"\n  Found {len(stumbles)} stumble events (RPM dip + recovery, throttle not lifting)")
        print(f"\n  {'Time':>8s}  {'RPM before':>10s}  {'RPM dip':>8s}  {'Dip size':>8s}  {'Recovery':>8s}  {'TPS':>5s}  {'AFR':>5s}  {'MAP':>4s}  {'PW':>6s}  {'AE':>4s}  {'CLT':>4s}")
        print(f"  {'─'*8}  {'─'*10}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*5}  {'─'*5}  {'─'*4}  {'─'*6}  {'─'*4}  {'─'*4}")
        for s in stumbles:
            marker = ""
            if s['afr'] > 15.5:
                marker = " ← LEAN"
            if s['dip_size'] > 100:
                marker += " ← BIG DIP"
            print(f"  {s['time']:8.2f}  {s['rpm_before']:10d}  {s['rpm_dip']:8d}  {s['dip_size']:8d}  {s['rpm_recovery']:8d}  {s['tps']:5.1f}  {s['afr']:5.1f}  {s['map']:4d}  {s['pw']:6.3f}  {s['ae']:4d}  {s['clt']:4d}{marker}")
    else:
        print("\n  ✅ No stumble events detected (no RPM dip with recovery while throttle held/rising)")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: Full timeline showing every notable event
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 6: Full Running Timeline (every 1 second, plus all anomalies)")
    print(f"{'─' * 100}")

    print(f"\n  {'Time':>8s}  {'RPM':>5s}  {'TPS':>5s}  {'MAP':>4s}  {'AFR':>5s}  {'PW':>6s}  {'AE':>4s}  {'TPSDOT':>7s}  {'VE':>4s}  {'CLT':>4s}  {'Adv':>4s}  {'Batt':>5s}  Notes")
    print(f"  {'─'*8}  {'─'*5}  {'─'*5}  {'─'*4}  {'─'*5}  {'─'*6}  {'─'*4}  {'─'*7}  {'─'*4}  {'─'*4}  {'─'*4}  {'─'*5}  {'─'*30}")

    last_printed_time = -2
    for i, d in enumerate(running):
        notes = []

        # Check for anomalies at every sample
        if d['afr'] > 15.5 and d['rpm'] > 300:
            notes.append("LEAN")
        if d['afr'] > 17.0 and d['rpm'] > 300:
            notes.append("VERY_LEAN!")
        if d['afr'] < 11.0 and d['rpm'] > 300:
            notes.append("VERY_RICH!")
        if d['accel_enrich'] > 100:
            notes.append(f"AE={d['accel_enrich']}%")
        if d['tps_dot'] > 20:
            notes.append(f"TPS_DOT={d['tps_dot']:.0f}")
        if i > 0 and running[i]['rpm'] < running[i-1]['rpm'] - 50:
            notes.append(f"RPM_DROP={running[i-1]['rpm']-running[i]['rpm']}")

        # Print every second or if there's something notable
        should_print = (d['time'] - last_printed_time >= 1.0) or len(notes) > 0

        if should_print:
            note_str = ", ".join(notes) if notes else ""
            print(f"  {d['time']:8.2f}  {d['rpm']:5d}  {d['tps']:5.1f}  {d['map']:4d}  {d['afr']:5.1f}  {d['pw']:6.3f}  {d['accel_enrich']:4d}  {d['tps_dot']:7.1f}  {d['ve']:4d}  {d['clt']:4d}  {d['advance']:4.1f}  {d['batt_v']:5.1f}  {note_str}")
            last_printed_time = d['time']

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: Gammae / enrichment analysis during running
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'─' * 100}")
    print("SECTION 7: Enrichment Corrections Active")
    print(f"{'─' * 100}")

    gammae_vals = [d['gammae'] for d in running]
    gwarm_vals = [d['gwarm'] for d in running]
    print(f"\n  Gammae (total correction): {min(gammae_vals)}–{max(gammae_vals)}% (mean {sum(gammae_vals)/len(gammae_vals):.0f}%)")
    print(f"  Gwarm (warmup enrichment): {min(gwarm_vals)}–{max(gwarm_vals)}% (mean {sum(gwarm_vals)/len(gwarm_vals):.0f}%)")

    # When does Gwarm drop to 100%?
    gwarm_100 = [d for d in running if d['gwarm'] == 100]
    gwarm_not100 = [d for d in running if d['gwarm'] > 100]
    if gwarm_100:
        print(f"  Gwarm = 100% (no WUE): from {gwarm_100[0]['time']:.1f}s (CLT={gwarm_100[0]['clt']}°C)")
    if gwarm_not100:
        print(f"  Gwarm > 100% (WUE active): {len(gwarm_not100)} samples, CLT range {min(d['clt'] for d in gwarm_not100)}–{max(d['clt'] for d in gwarm_not100)}°C")

    print(f"\n{'=' * 100}")
    print("END OF ANALYSIS")
    print(f"{'=' * 100}")

if __name__ == '__main__':
    main()
