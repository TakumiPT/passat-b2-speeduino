"""
Analyze ONLY the post-alternator-charge period (t>930s)
CLT=95°C, Battery=12.5-12.9V — clean data for VE tuning
"""
import csv
import os

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "2026-03-05_20.55.47.csv")

COL = {
    'Time': 0, 'RPM': 2, 'MAP': 3, 'TPS': 5, 'AFR': 6,
    'CLT': 9, 'PW': 22, 'BatteryV': 34, 'VE1': 20,
    'Gwarm': 15, 'Gammae': 17, 'Gbattery': 14, 'AccelEnrich': 18,
    'AFRTarget': 26, 'DutyCycle': 28, 'TPSDOT': 30,
}

def sf(val, default=0.0):
    try:
        return float(val.strip().replace('"', ''))
    except:
        return default

def analyze():
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader); next(reader)
        for row in reader:
            if len(row) < 50:
                continue
            rows.append(row)

    # Filter: t >= 930s, RPM > 400 (running), battery >= 12.0V
    good = []
    for r in rows:
        t = sf(r[COL['Time']])
        rpm = sf(r[COL['RPM']])
        batt = sf(r[COL['BatteryV']])
        if t >= 930 and rpm > 400 and batt >= 12.0:
            good.append(r)

    print("=" * 80)
    print("CLEAN DATA ANALYSIS: t≥930s, V≥12.0V, CLT~95°C")
    print(f"Samples: {len(good)} (from {len(rows)} total)")
    print("=" * 80)

    times = [sf(r[COL['Time']]) for r in good]
    rpms = [sf(r[COL['RPM']]) for r in good]
    maps = [sf(r[COL['MAP']]) for r in good]
    tps_vals = [sf(r[COL['TPS']]) for r in good]
    afrs = [sf(r[COL['AFR']]) for r in good]
    clts = [sf(r[COL['CLT']]) for r in good]
    pws = [sf(r[COL['PW']]) for r in good]
    batts = [sf(r[COL['BatteryV']]) for r in good]
    ves = [sf(r[COL['VE1']]) for r in good]
    gwarms = [sf(r[COL['Gwarm']]) for r in good]
    gammaes = [sf(r[COL['Gammae']]) for r in good]
    gbatts = [sf(r[COL['Gbattery']]) for r in good]
    ae_vals = [sf(r[COL['AccelEnrich']]) for r in good]
    afr_tgts = [sf(r[COL['AFRTarget']]) for r in good]
    duties = [sf(r[COL['DutyCycle']]) for r in good]

    print(f"\nTime range: {min(times):.1f}s - {max(times):.1f}s ({max(times)-min(times):.0f}s duration)")
    print(f"CLT: {min(clts):.0f} - {max(clts):.0f}°C")
    print(f"Battery: {min(batts):.1f} - {max(batts):.1f}V (avg {sum(batts)/len(batts):.1f}V)")
    print(f"Gwarm: {min(gwarms):.0f} - {max(gwarms):.0f}% (should be ~100% at 95°C)")
    print(f"Gbattery: {min(gbatts):.0f} - {max(gbatts):.0f}%")

    # Split into idle and driving
    idle = [i for i in range(len(good)) if tps_vals[i] < 2 and rpms[i] < 1300]
    driving = [i for i in range(len(good)) if tps_vals[i] >= 2 or rpms[i] >= 1300]

    print(f"\nIdle samples (TPS<2, RPM<1300): {len(idle)}")
    print(f"Driving samples: {len(driving)}")

    # ============ IDLE ANALYSIS ============
    print(f"\n{'='*80}")
    print("IDLE ANALYSIS (TPS<2%, RPM<1300, CLT~95°C, V≥12V)")
    print(f"{'='*80}")

    if idle:
        i_rpms = [rpms[i] for i in idle]
        i_maps = [maps[i] for i in idle]
        i_afrs = [afrs[i] for i in idle if 5 < afrs[i] < 25]
        i_ves = [ves[i] for i in idle]
        i_pws = [pws[i] for i in idle]
        i_tgts = [afr_tgts[i] for i in idle if afr_tgts[i] > 5]

        print(f"\nRPM:  avg={sum(i_rpms)/len(i_rpms):.0f}, range={min(i_rpms):.0f}-{max(i_rpms):.0f}")
        print(f"MAP:  avg={sum(i_maps)/len(i_maps):.0f} kPa, range={min(i_maps):.0f}-{max(i_maps):.0f}")
        print(f"VE:   avg={sum(i_ves)/len(i_ves):.0f}%, range={min(i_ves):.0f}-{max(i_ves):.0f}")
        print(f"PW:   avg={sum(i_pws)/len(i_pws):.2f}ms, range={min(i_pws):.2f}-{max(i_pws):.2f}")
        if i_afrs:
            print(f"AFR:  avg={sum(i_afrs)/len(i_afrs):.1f}, range={min(i_afrs):.1f}-{max(i_afrs):.1f}")
        if i_tgts:
            print(f"Target: avg={sum(i_tgts)/len(i_tgts):.1f}")

        if i_afrs and i_tgts:
            actual = sum(i_afrs)/len(i_afrs)
            target = sum(i_tgts)/len(i_tgts)
            error_pct = ((actual / target) - 1) * 100
            print(f"\n  AFR error: {actual:.1f} vs {target:.1f} = {error_pct:+.1f}%")
            print(f"  VE correction needed: multiply current VE by {target/actual:.3f}")
            avg_ve = sum(i_ves)/len(i_ves)
            corrected_ve = avg_ve * (actual / target)
            print(f"  Current VE ≈ {avg_ve:.0f}% → should be ≈ {corrected_ve:.0f}%")

        # Idle by MAP bin (to find which VE cells to change)
        print(f"\n  Idle by MAP bin:")
        print(f"  {'MAP':>8s} {'RPM avg':>8s} {'VE':>5s} {'AFR':>6s} {'Target':>7s} {'Error':>7s} {'VE fix':>7s} {'N':>5s}")
        print(f"  " + "-" * 60)
        for mlo, mhi in [(30,34), (34,38), (38,42), (42,46), (46,50)]:
            band = [i for i in idle if mlo <= maps[i] < mhi]
            if band:
                b_afr = [afrs[i] for i in band if 5 < afrs[i] < 25]
                b_tgt = [afr_tgts[i] for i in band if afr_tgts[i] > 5]
                b_ve = [ves[i] for i in band]
                b_rpm = [rpms[i] for i in band]
                if b_afr and b_tgt:
                    avg_a = sum(b_afr)/len(b_afr)
                    avg_t = sum(b_tgt)/len(b_tgt)
                    avg_v = sum(b_ve)/len(b_ve)
                    err = ((avg_a / avg_t) - 1) * 100
                    fix_ve = avg_v * (avg_a / avg_t)
                    print(f"  {mlo:3d}-{mhi:3d}: {sum(b_rpm)/len(b_rpm):8.0f} {avg_v:5.0f} "
                          f"{avg_a:6.1f} {avg_t:7.1f} {err:+6.1f}% {fix_ve:7.0f} {len(band):5d}")

    # ============ DRIVING ANALYSIS ============
    print(f"\n{'='*80}")
    print("DRIVING / THROTTLE ANALYSIS (TPS≥2% or RPM≥1300)")
    print(f"{'='*80}")

    if driving:
        # Show each driving moment in detail
        print(f"\n  Time-series of driving events:")
        print(f"  {'Time':>7s} {'RPM':>5s} {'TPS':>5s} {'MAP':>4s} {'AFR':>5s} {'Tgt':>5s} {'VE':>4s} {'PW':>5s} {'Duty':>5s} {'V':>5s}")
        print(f"  " + "-" * 65)
        # Sample every ~1 second to keep it readable
        last_t = 0
        for i in driving:
            if times[i] - last_t >= 0.5:
                print(f"  {times[i]:7.1f} {rpms[i]:5.0f} {tps_vals[i]:5.1f} {maps[i]:4.0f} "
                      f"{afrs[i]:5.1f} {afr_tgts[i]:5.1f} {ves[i]:4.0f} {pws[i]:5.2f} "
                      f"{duties[i]:5.1f} {batts[i]:5.1f}")
                last_t = times[i]

        # Driving by RPM/MAP zone
        print(f"\n  Driving zones summary:")
        print(f"  {'Zone':>25s} {'RPM':>5s} {'MAP':>4s} {'AFR':>5s} {'Tgt':>5s} {'VE':>4s} {'Err%':>6s} {'VE fix':>7s} {'N':>4s}")
        print(f"  " + "-" * 75)
        zones = [
            ("1200-1500 / MAP 30-50", 1200, 1500, 30, 50),
            ("1200-1500 / MAP 50-70", 1200, 1500, 50, 70),
            ("1500-2000 / MAP 30-50", 1500, 2000, 30, 50),
            ("1500-2000 / MAP 50-70", 1500, 2000, 50, 70),
            ("1500-2000 / MAP 70-100", 1500, 2000, 70, 100),
            ("2000-3000 / MAP 30-50", 2000, 3000, 30, 50),
            ("2000-3000 / MAP 50-70", 2000, 3000, 50, 70),
            ("2000-3000 / MAP 70-100", 2000, 3000, 70, 100),
        ]
        for label, rlo, rhi, mlo, mhi in zones:
            z = [i for i in driving if rlo <= rpms[i] < rhi and mlo <= maps[i] < mhi]
            if z:
                z_afr = [afrs[i] for i in z if 5 < afrs[i] < 25]
                z_tgt = [afr_tgts[i] for i in z if afr_tgts[i] > 5]
                z_ve = [ves[i] for i in z]
                if z_afr and z_tgt:
                    avg_a = sum(z_afr)/len(z_afr)
                    avg_t = sum(z_tgt)/len(z_tgt)
                    avg_v = sum(z_ve)/len(z_ve)
                    err = ((avg_a / avg_t) - 1) * 100
                    fix_ve = avg_v * (avg_a / avg_t)
                    print(f"  {label:>25s} {sum(rpms[i] for i in z)/len(z):5.0f} "
                          f"{sum(maps[i] for i in z)/len(z):4.0f} {avg_a:5.1f} {avg_t:5.1f} "
                          f"{avg_v:4.0f} {err:+5.1f}% {fix_ve:7.0f} {len(z):4d}")

    # ============ OVERALL VERDICT ============
    print(f"\n{'='*80}")
    print("VERDICT: CLEAN-DATA PERIOD (t≥930s, V≥12V, CLT=95°C)")
    print(f"{'='*80}")

    valid_afrs = [afrs[i] for i in range(len(good)) if 5 < afrs[i] < 25]
    valid_tgts = [afr_tgts[i] for i in range(len(good)) if afr_tgts[i] > 5]
    if valid_afrs and valid_tgts:
        overall_afr = sum(valid_afrs)/len(valid_afrs)
        overall_tgt = sum(valid_tgts)/len(valid_tgts)
        print(f"\n  Overall AFR: {overall_afr:.1f} (target {overall_tgt:.1f})")
        print(f"  Error: {((overall_afr/overall_tgt)-1)*100:+.1f}% lean")
        print(f"  VE multiplier needed: {overall_afr/overall_tgt:.3f}x")
        if overall_afr > 15.5:
            print(f"\n  ⚠️  STILL LEAN even with good voltage and hot engine!")
            print(f"  → The lean condition is REAL, not a voltage/sensor artifact.")
            print(f"  → VE table needs to be increased.")
        else:
            print(f"\n  ✅ AFR is reasonable with good voltage — the lean issue")
            print(f"     was caused by low alternator voltage affecting fueling.")

if __name__ == '__main__':
    analyze()
