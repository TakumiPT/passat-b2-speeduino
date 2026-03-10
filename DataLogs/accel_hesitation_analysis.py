#!/usr/bin/env python3
"""
Acceleration Hesitation Analysis — 2026-03-01_19.05.30.csv
VW Passat B2 DT 1.6L Speeduino — TBI Monopoint

Analyzes EVERY throttle press event for signs of hesitation/choking:
- RPM drops during acceleration (stumble)
- Lean spikes (AFR > 15.5 during accel)
- Insufficient acceleration enrichment
- Timing issues
"""

import csv
import sys
from collections import defaultdict

CSV_FILE = "2026-03-01_19.05.30.csv"

# Column indices (0-based, from header analysis)
COL = {
    'Time': 0, 'RPM': 2, 'MAP': 3, 'TPS': 5, 'AFR': 6,
    'CLT': 9, 'Engine': 10, 'AccelEnrich': 18, 'VE': 19,
    'PW': 22, 'AFR_Target': 26, 'DutyCycle': 28,
    'TPS_DOT': 30, 'Advance': 31, 'BattV': 34, 'RPM_S': 35,
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
    """Read CSV, skip 2 header rows (names + units)."""
    rows = []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header1 = next(reader)  # column names
        header2 = next(reader)  # units
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
            }
            rows.append(row)
    return rows

def find_accel_events(data):
    """
    Find acceleration events: TPS increases by >= 2% within a short window.
    An event starts when TPS begins rising and ends when TPS stabilizes or drops.
    """
    events = []
    i = 0
    n = len(data)

    while i < n - 1:
        # Look for TPS rising
        if data[i+1]['tps'] > data[i]['tps'] + 1.0 and data[i]['rpm'] > 0:
            # Found start of accel event
            start_idx = i
            start_tps = data[i]['tps']
            start_rpm = data[i]['rpm']
            start_time = data[i]['time']

            # Track until TPS stops rising (allow brief plateaus)
            peak_tps = start_tps
            peak_idx = i
            plateau_count = 0
            j = i + 1

            while j < n:
                if data[j]['tps'] > peak_tps:
                    peak_tps = data[j]['tps']
                    peak_idx = j
                    plateau_count = 0
                elif data[j]['tps'] < peak_tps - 2.0:
                    break  # TPS dropping significantly
                else:
                    plateau_count += 1
                    if plateau_count > 15:  # ~1s of plateau = end of event
                        break
                j += 1

            # Extend window 1.5s after peak to see RPM response
            end_time = data[peak_idx]['time'] + 1.5
            end_idx = peak_idx
            while end_idx < n - 1 and data[end_idx]['time'] < end_time:
                end_idx += 1

            tps_change = peak_tps - start_tps
            if tps_change >= 3.0:  # Minimum 3% TPS change = real throttle press
                event = {
                    'start_idx': start_idx,
                    'peak_idx': peak_idx,
                    'end_idx': min(end_idx, n - 1),
                    'start_time': start_time,
                    'end_time': data[min(end_idx, n-1)]['time'],
                    'start_tps': start_tps,
                    'peak_tps': peak_tps,
                    'tps_change': tps_change,
                    'start_rpm': start_rpm,
                    'samples': data[start_idx:min(end_idx+1, n)],
                }
                events.append(event)

            i = max(peak_idx + 1, j)
        else:
            i += 1

    return events

def analyze_event(event, event_num):
    """Analyze a single acceleration event for hesitation indicators."""
    samples = event['samples']
    if not samples:
        return None

    # Find min RPM during event (stumble detection)
    min_rpm = min(s['rpm'] for s in samples if s['rpm'] > 0) if any(s['rpm'] > 0 for s in samples) else 0
    max_rpm = max(s['rpm'] for s in samples)
    start_rpm = event['start_rpm']

    # RPM dip detection: RPM drops below start RPM during acceleration
    min_rpm_after_start = float('inf')
    min_rpm_time = 0
    for s in samples[1:]:  # skip first sample
        if 0 < s['rpm'] < min_rpm_after_start:
            min_rpm_after_start = s['rpm']
            min_rpm_time = s['time']

    rpm_dip = start_rpm - min_rpm_after_start if min_rpm_after_start < start_rpm else 0

    # AFR analysis during accel
    afr_values = [s['afr'] for s in samples if s['afr'] > 0 and s['rpm'] > 300]
    max_afr = max(afr_values) if afr_values else 0
    min_afr = min(afr_values) if afr_values else 0
    avg_afr = sum(afr_values) / len(afr_values) if afr_values else 0

    # Lean spike detection
    lean_spikes = [s for s in samples if s['afr'] > 15.5 and s['rpm'] > 300]

    # Very lean detection (AFR > 17 = misfires likely)
    very_lean = [s for s in samples if s['afr'] > 17.0 and s['rpm'] > 300]

    # Accel enrichment active?
    ae_active = [s for s in samples if s['accel_enrich'] > 100]
    max_ae = max(s['accel_enrich'] for s in samples) if samples else 0

    # TPS DOT (rate of change)
    max_tps_dot = max(s['tps_dot'] for s in samples)
    avg_tps_dot = sum(s['tps_dot'] for s in samples) / len(samples)

    # PW analysis
    pw_values = [s['pw'] for s in samples if s['pw'] > 0]
    max_pw = max(pw_values) if pw_values else 0
    min_pw = min(pw_values) if pw_values else 0

    # CLT at event
    clt = samples[0]['clt']

    # MAP analysis
    map_values = [s['map'] for s in samples if s['rpm'] > 0]
    max_map = max(map_values) if map_values else 0

    # Classify hesitation severity
    severity = "NONE"
    reasons = []

    if rpm_dip > 200:
        severity = "SEVERE"
        reasons.append(f"RPM dropped {rpm_dip} from {start_rpm} to {min_rpm_after_start}")
    elif rpm_dip > 80:
        severity = "MODERATE"
        reasons.append(f"RPM dropped {rpm_dip} from {start_rpm} to {min_rpm_after_start}")
    elif rpm_dip > 30:
        severity = "MILD"
        reasons.append(f"RPM dipped {rpm_dip} from {start_rpm} to {min_rpm_after_start}")

    if very_lean:
        severity = "SEVERE" if severity != "SEVERE" else severity
        reasons.append(f"Very lean: AFR {max_afr:.1f} ({len(very_lean)} samples >17.0)")
    elif lean_spikes:
        if severity == "NONE":
            severity = "MODERATE"
        reasons.append(f"Lean spike: AFR {max_afr:.1f} ({len(lean_spikes)} samples >15.5)")

    if max_tps_dot > 100 and max_ae <= 100:
        reasons.append(f"NO accel enrichment despite TPS DOT {max_tps_dot:.0f}%/s")
        if severity == "NONE":
            severity = "MODERATE"

    if rpm_dip > 30 and len(ae_active) == 0:
        reasons.append("Stumble with NO acceleration enrichment active")

    return {
        'event_num': event_num,
        'start_time': event['start_time'],
        'end_time': event['end_time'],
        'duration': event['end_time'] - event['start_time'],
        'start_tps': event['start_tps'],
        'peak_tps': event['peak_tps'],
        'tps_change': event['tps_change'],
        'start_rpm': start_rpm,
        'max_rpm': max_rpm,
        'rpm_dip': rpm_dip,
        'min_rpm_after_start': min_rpm_after_start if min_rpm_after_start < float('inf') else 0,
        'min_rpm_time': min_rpm_time,
        'avg_afr': avg_afr,
        'max_afr': max_afr,
        'min_afr': min_afr,
        'lean_spikes': len(lean_spikes),
        'very_lean': len(very_lean),
        'max_ae': max_ae,
        'ae_samples': len(ae_active),
        'max_tps_dot': max_tps_dot,
        'max_pw': max_pw,
        'min_pw': min_pw,
        'clt': clt,
        'max_map': max_map,
        'severity': severity,
        'reasons': reasons,
        'samples': samples,
    }

def print_detailed_event(result):
    """Print detailed timeline for events with hesitation."""
    print(f"\n  --- Detailed Timeline (Event #{result['event_num']}) ---")
    print(f"  {'Time':>8s}  {'RPM':>5s}  {'TPS':>5s}  {'MAP':>4s}  {'AFR':>5s}  {'PW':>6s}  {'AE':>4s}  {'TPS_DOT':>7s}  {'Adv':>4s}  {'VE':>4s}")
    print(f"  {'─'*8}  {'─'*5}  {'─'*5}  {'─'*4}  {'─'*5}  {'─'*6}  {'─'*4}  {'─'*7}  {'─'*4}  {'─'*4}")
    for s in result['samples']:
        marker = ""
        if s['afr'] > 17.0 and s['rpm'] > 300:
            marker = " ← VERY LEAN!"
        elif s['afr'] > 15.5 and s['rpm'] > 300:
            marker = " ← lean"
        if s['rpm'] < result['start_rpm'] - 50 and s['rpm'] > 0:
            marker += " ← RPM DIP"
        print(f"  {s['time']:8.2f}  {s['rpm']:5d}  {s['tps']:5.1f}  {s['map']:4d}  {s['afr']:5.1f}  {s['pw']:6.3f}  {s['accel_enrich']:4d}  {s['tps_dot']:7.1f}  {s['advance']:4.1f}  {s['ve']:4d}{marker}")


def main():
    print("=" * 90)
    print("ACCELERATION HESITATION ANALYSIS — 2026-03-01_19.05.30")
    print("VW Passat B2 DT 1.6L — Speeduino TBI Monopoint")
    print("=" * 90)

    # Read data
    data = read_data(CSV_FILE)
    print(f"\nTotal samples: {len(data)}")

    # Basic data overview
    running = [d for d in data if d['rpm'] > 300]
    cranking = [d for d in data if 0 < d['rpm'] <= 300]
    print(f"Running samples (RPM>300): {len(running)}")
    print(f"Cranking samples (0<RPM≤300): {len(cranking)}")

    if running:
        clt_range = f"{min(d['clt'] for d in running)}–{max(d['clt'] for d in running)}°C"
        rpm_range = f"{min(d['rpm'] for d in running)}–{max(d['rpm'] for d in running)}"
        time_range = f"{running[0]['time']:.1f}–{running[-1]['time']:.1f}s"
        print(f"CLT range: {clt_range}")
        print(f"RPM range: {rpm_range}")
        print(f"Time range: {time_range}")

    # Find all acceleration events
    events = find_accel_events(data)
    print(f"\n{'=' * 90}")
    print(f"FOUND {len(events)} ACCELERATION EVENTS (TPS increase ≥ 3%)")
    print(f"{'=' * 90}")

    # Analyze each event
    results = []
    for i, event in enumerate(events, 1):
        result = analyze_event(event, i)
        if result:
            results.append(result)

    # Print summary table
    print(f"\n{'#':>3s}  {'Time':>8s}  {'TPS':>12s}  {'RPM':>14s}  {'RPM Dip':>7s}  {'AFR':>10s}  {'AE%':>5s}  {'TPSDOT':>7s}  {'CLT':>4s}  {'Severity':>10s}")
    print(f"{'─'*3}  {'─'*8}  {'─'*12}  {'─'*14}  {'─'*7}  {'─'*10}  {'─'*5}  {'─'*7}  {'─'*4}  {'─'*10}")

    hesitation_events = []
    for r in results:
        tps_str = f"{r['start_tps']:.0f}→{r['peak_tps']:.0f}%"
        rpm_str = f"{r['start_rpm']}→{r['max_rpm']}"
        afr_str = f"{r['min_afr']:.1f}–{r['max_afr']:.1f}"
        sev_marker = "⚠️" if r['severity'] in ("MODERATE", "SEVERE") else "  "
        print(f"{r['event_num']:3d}  {r['start_time']:8.2f}  {tps_str:>12s}  {rpm_str:>14s}  {r['rpm_dip']:7d}  {afr_str:>10s}  {r['max_ae']:5d}  {r['max_tps_dot']:7.0f}  {r['clt']:4d}  {sev_marker}{r['severity']:>8s}")

        if r['severity'] in ("MILD", "MODERATE", "SEVERE"):
            hesitation_events.append(r)

    # Detailed analysis of problematic events
    print(f"\n{'=' * 90}")
    print(f"HESITATION EVENTS: {len(hesitation_events)} of {len(results)}")
    print(f"{'=' * 90}")

    if not hesitation_events:
        print("\n  ✅ No acceleration hesitation detected in this datalog.")
        print("  All throttle press events show clean RPM response.")
    else:
        for r in hesitation_events:
            print(f"\n  ▶ EVENT #{r['event_num']} @ {r['start_time']:.2f}s — {r['severity']}")
            print(f"    TPS: {r['start_tps']:.0f}% → {r['peak_tps']:.0f}% (Δ{r['tps_change']:.0f}%)")
            print(f"    RPM: {r['start_rpm']} → peak {r['max_rpm']}")
            if r['rpm_dip'] > 0:
                print(f"    RPM DIP: -{r['rpm_dip']} (dropped to {r['min_rpm_after_start']} @ {r['min_rpm_time']:.2f}s)")
            print(f"    AFR: {r['min_afr']:.1f}–{r['max_afr']:.1f} (avg {r['avg_afr']:.1f}, target {r['samples'][0]['afr_target']:.1f})")
            print(f"    Accel Enrichment: max {r['max_ae']}% ({r['ae_samples']} active samples)")
            print(f"    TPS DOT: max {r['max_tps_dot']:.0f}%/s")
            print(f"    PW: {r['min_pw']:.3f}–{r['max_pw']:.3f} ms")
            print(f"    MAP: peak {r['max_map']} kPa")
            print(f"    CLT: {r['clt']}°C")
            for reason in r['reasons']:
                print(f"    ⚠️  {reason}")

            print_detailed_event(r)

    # Overall diagnosis
    print(f"\n{'=' * 90}")
    print("DIAGNOSIS & RECOMMENDATIONS")
    print(f"{'=' * 90}")

    if not hesitation_events:
        print("\nNo hesitation detected. If you're still hearing choking/hesitation,")
        print("it may be:")
        print("  1. Very brief events between log samples (~67ms resolution)")
        print("  2. Mechanical issue (intake leak, fuel pressure drop)")
        print("  3. Ignition-related (distributor advance mismatch)")
        return

    # Categorize issues
    lean_events = [r for r in hesitation_events if r['lean_spikes'] > 0]
    rpm_dip_events = [r for r in hesitation_events if r['rpm_dip'] > 50]
    no_ae_events = [r for r in hesitation_events if r['max_ae'] <= 100 and r['max_tps_dot'] > 50]

    if lean_events:
        print(f"\n  LEAN SPIKES during acceleration: {len(lean_events)} events")
        print("  → Cause: Insufficient fueling during throttle opening")
        print("  → Fix: Increase Acceleration Enrichment (AE) values in TunerStudio")
        worst_afr = max(r['max_afr'] for r in lean_events)
        print(f"  → Worst AFR: {worst_afr:.1f} (stoich=14.7, misfire risk >16.5)")

    if no_ae_events:
        print(f"\n  NO ACCEL ENRICHMENT on {len(no_ae_events)} throttle presses")
        print("  → Cause: TPS DOT below AE threshold (currently 30%/s)")
        max_missed_dot = max(r['max_tps_dot'] for r in no_ae_events)
        print(f"  → Max TPS DOT without AE trigger: {max_missed_dot:.0f}%/s")
        if max_missed_dot > 10:
            print(f"  → Fix: Lower AE threshold from 30%/s to {max(5, int(max_missed_dot * 0.5))}%/s")

    if rpm_dip_events:
        print(f"\n  RPM DIPS (stumble) during acceleration: {len(rpm_dip_events)} events")
        worst_dip = max(r['rpm_dip'] for r in rpm_dip_events)
        print(f"  → Worst dip: {worst_dip} RPM")
        print("  → Typically caused by:")
        print("    a) Lean transient (manifold wall wetting in TBI)")
        print("    b) Insufficient AE duration (too short)")
        print("    c) Timing too advanced at low RPM / high MAP")

    # Check if ASE was active during any problem events
    clt_values = [r['clt'] for r in hesitation_events]
    if any(c < 60 for c in clt_values):
        print(f"\n  ⚠️  COLD ENGINE: Some hesitation at CLT {min(clt_values)}°C")
        print("  → Cold engine + dead manifold heater = more fuel condensation on manifold walls")
        print("  → Bigger AE values needed during warmup")

    print(f"\n{'=' * 90}")
    print("ACCELERATION ENRICHMENT CURRENT SETTINGS (from copilot-instructions.md):")
    print("  Mode: TPS-based")
    print("  Threshold: 30 %/s")
    print("  Time: 300 ms")
    print("  Values: 40, 70, 100, 130% at 70/220/430/790 %/s")
    print("  Taper: 5000-6200 RPM")
    print(f"{'=' * 90}")


if __name__ == '__main__':
    main()
