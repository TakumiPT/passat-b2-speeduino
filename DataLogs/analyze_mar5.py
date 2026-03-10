"""
Comprehensive analysis of 2026-03-05_20.55.47.csv datalog
VW Passat B2 DT 1.6 Speeduino - Monopoint TBI
"""
import csv
import sys
import os

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "2026-03-05_20.55.47.csv")

# Column indices (from header inspection)
COL = {
    'Time': 0, 'SecL': 1, 'RPM': 2, 'MAP': 3, 'TPS': 5,
    'AFR': 6, 'Lambda': 7, 'IAT': 8, 'CLT': 9, 'Engine': 10,
    'DFCO': 11, 'Gego': 12, 'Gair': 13, 'Gbattery': 14,
    'Gwarm': 15, 'Gbaro': 16, 'Gammae': 17, 'AccelEnrich': 18,
    'VE_Current': 19, 'VE1': 20, 'PW': 22, 'AFRTarget': 26,
    'DutyCycle': 28, 'TPSDOT': 30, 'Advance': 31,
    'Dwell': 32, 'BatteryV': 34, 'RPMs': 35,
    'SyncLoss': 46, 'LoopsSec': 47, 'IACvalue': 43,
    'BaroPressure': 44, 'HardLimiter': 41
}

def safe_float(val, default=0.0):
    try:
        return float(val.strip().replace('"', ''))
    except (ValueError, AttributeError):
        return default

def safe_int(val, default=0):
    try:
        return int(float(val.strip().replace('"', '')))
    except (ValueError, AttributeError):
        return default

def analyze():
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        header1 = next(reader)  # Column names
        header2 = next(reader)  # Units
        for row in reader:
            if len(row) < 50:
                continue
            rows.append(row)

    total = len(rows)
    print(f"=" * 80)
    print(f"DATALOG ANALYSIS: 2026-03-05_20.55.47")
    print(f"Total samples: {total}")
    print(f"=" * 80)

    # Extract key columns
    times = [safe_float(r[COL['Time']]) for r in rows]
    rpms = [safe_float(r[COL['RPM']]) for r in rows]
    maps = [safe_float(r[COL['MAP']]) for r in rows]
    tps = [safe_float(r[COL['TPS']]) for r in rows]
    afrs = [safe_float(r[COL['AFR']]) for r in rows]
    clts = [safe_float(r[COL['CLT']]) for r in rows]
    iats = [safe_float(r[COL['IAT']]) for r in rows]
    pws = [safe_float(r[COL['PW']]) for r in rows]
    ves = [safe_float(r[COL['VE1']]) for r in rows]
    duties = [safe_float(r[COL['DutyCycle']]) for r in rows]
    batts = [safe_float(r[COL['BatteryV']]) for r in rows]
    gwarms = [safe_float(r[COL['Gwarm']]) for r in rows]
    gammaes = [safe_float(r[COL['Gammae']]) for r in rows]
    accel_enrich = [safe_float(r[COL['AccelEnrich']]) for r in rows]
    afr_targets = [safe_float(r[COL['AFRTarget']]) for r in rows]
    gegos = [safe_float(r[COL['Gego']]) for r in rows]
    iac_vals = [safe_float(r[COL['IACvalue']]) for r in rows]
    sync_loss = [safe_float(r[COL['SyncLoss']]) for r in rows]
    hard_limiters = [safe_float(r[COL['HardLimiter']]) for r in rows]
    advances = [safe_float(r[COL['Advance']]) for r in rows]
    tpsdots = [safe_float(r[COL['TPSDOT']]) for r in rows]
    baros = [safe_float(r[COL['BaroPressure']]) for r in rows]

    duration = times[-1] - times[0] if times else 0
    print(f"\nDuration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Time range: {times[0]:.1f}s to {times[-1]:.1f}s")
    print(f"Sample rate: {total/duration:.1f} samples/sec" if duration > 0 else "")

    # ========== SECTION 1: ENGINE STATE OVERVIEW ==========
    print(f"\n{'='*80}")
    print("SECTION 1: ENGINE STATE OVERVIEW")
    print(f"{'='*80}")

    running = [i for i in range(total) if rpms[i] > 400]
    cranking = [i for i in range(total) if 0 < rpms[i] <= 400]
    off = [i for i in range(total) if rpms[i] == 0]
    print(f"\nEngine OFF samples: {len(off)} ({100*len(off)/total:.1f}%)")
    print(f"Cranking samples (RPM 1-400): {len(cranking)} ({100*len(cranking)/total:.1f}%)")
    print(f"Running samples (RPM>400): {len(running)} ({100*len(running)/total:.1f}%)")

    if running:
        r_rpms = [rpms[i] for i in running]
        print(f"\nRunning RPM: min={min(r_rpms):.0f}, max={max(r_rpms):.0f}, "
              f"avg={sum(r_rpms)/len(r_rpms):.0f}")

    # Identify start/stop events
    print(f"\n--- Start/Stop Events ---")
    state = 'off'
    events = []
    for i in range(total):
        if state == 'off' and rpms[i] > 0:
            state = 'cranking'
            events.append(('CRANK_START', i, times[i], clts[i]))
        elif state == 'cranking' and rpms[i] > 400:
            state = 'running'
            events.append(('ENGINE_RUNNING', i, times[i], clts[i]))
        elif state == 'running' and rpms[i] == 0:
            state = 'off'
            events.append(('ENGINE_STOP', i, times[i], clts[i]))
        elif state == 'cranking' and rpms[i] == 0:
            state = 'off'
            events.append(('CRANK_FAIL', i, times[i], clts[i]))

    for ev in events:
        print(f"  {ev[0]:20s} at t={ev[2]:8.1f}s  (sample #{ev[1]}, CLT={ev[3]:.1f}°C)")

    # ========== SECTION 2: TEMPERATURE ANALYSIS ==========
    print(f"\n{'='*80}")
    print("SECTION 2: TEMPERATURE ANALYSIS")
    print(f"{'='*80}")

    print(f"\nCLT (Coolant): start={clts[0]:.1f}°C, end={clts[-1]:.1f}°C, "
          f"min={min(clts):.1f}°C, max={max(clts):.1f}°C")
    print(f"IAT (Intake):  start={iats[0]:.1f}°C, end={iats[-1]:.1f}°C, "
          f"min={min(iats):.1f}°C, max={max(iats):.1f}°C")

    # CLT progression over time
    print(f"\nCLT progression (every 60s):")
    for t_mark in range(0, int(duration) + 1, 60):
        idx = min(range(total), key=lambda i: abs(times[i] - times[0] - t_mark))
        print(f"  t={t_mark:4d}s: CLT={clts[idx]:.1f}°C, RPM={rpms[idx]:.0f}")

    # Cold vs hot classification
    cold_samples = [i for i in running if clts[i] < 70]
    hot_samples = [i for i in running if clts[i] >= 70]
    print(f"\nRunning cold (<70°C): {len(cold_samples)} samples ({100*len(cold_samples)/max(len(running),1):.1f}%)")
    print(f"Running hot (≥70°C):  {len(hot_samples)} samples ({100*len(hot_samples)/max(len(running),1):.1f}%)")

    # ========== SECTION 3: FUEL MIXTURE ANALYSIS ==========
    print(f"\n{'='*80}")
    print("SECTION 3: FUEL MIXTURE ANALYSIS (AFR)")
    print(f"{'='*80}")

    if running:
        r_afrs = [afrs[i] for i in running if afrs[i] > 5 and afrs[i] < 25]
        if r_afrs:
            print(f"\nRunning AFR: min={min(r_afrs):.1f}, max={max(r_afrs):.1f}, "
                  f"avg={sum(r_afrs)/len(r_afrs):.1f}")

            # AFR distribution
            afr_bands = [
                ('Very Rich (<11.0)', 0, 11.0),
                ('Rich (11.0-13.0)', 11.0, 13.0),
                ('Slightly Rich (13.0-14.0)', 13.0, 14.0),
                ('Stoich (14.0-15.0)', 14.0, 15.0),
                ('Slightly Lean (15.0-16.0)', 15.0, 16.0),
                ('Lean (16.0-18.0)', 16.0, 18.0),
                ('Very Lean (>18.0)', 18.0, 99.0),
            ]
            print(f"\nAFR Distribution (running):")
            for label, lo, hi in afr_bands:
                count = sum(1 for a in r_afrs if lo <= a < hi)
                pct = 100 * count / len(r_afrs)
                bar = '#' * int(pct / 2)
                print(f"  {label:30s}: {count:5d} ({pct:5.1f}%) {bar}")

        # AFR vs target analysis
        print(f"\nAFR vs Target (running, valid AFR):")
        afr_error = []
        for i in running:
            if 5 < afrs[i] < 25 and afr_targets[i] > 5:
                err = afrs[i] - afr_targets[i]
                afr_error.append(err)
        if afr_error:
            avg_err = sum(afr_error) / len(afr_error)
            print(f"  Average AFR error: {avg_err:+.2f} (positive = lean of target)")
            print(f"  Min error: {min(afr_error):+.2f}, Max error: {max(afr_error):+.2f}")

        # Hot idle AFR (the Feb 28 fix area)
        hot_idle = [i for i in running if clts[i] >= 70 and rpms[i] < 1200 and maps[i] < 50]
        if hot_idle:
            hi_afrs = [afrs[i] for i in hot_idle if 5 < afrs[i] < 25]
            hi_targets = [afr_targets[i] for i in hot_idle if afr_targets[i] > 5]
            if hi_afrs:
                print(f"\n  HOT IDLE (CLT≥70, RPM<1200, MAP<50):")
                print(f"    Samples: {len(hot_idle)}")
                print(f"    AFR: avg={sum(hi_afrs)/len(hi_afrs):.1f}, "
                      f"min={min(hi_afrs):.1f}, max={max(hi_afrs):.1f}")
                if hi_targets:
                    print(f"    Target: avg={sum(hi_targets)/len(hi_targets):.1f}")

        # Cold running AFR (ASE issue area)
        cold_run = [i for i in running if clts[i] < 50]
        if cold_run:
            cr_afrs = [afrs[i] for i in cold_run if 5 < afrs[i] < 25]
            if cr_afrs:
                print(f"\n  COLD RUNNING (CLT<50°C):")
                print(f"    Samples: {len(cold_run)}")
                print(f"    AFR: avg={sum(cr_afrs)/len(cr_afrs):.1f}, "
                      f"min={min(cr_afrs):.1f}, max={max(cr_afrs):.1f}")
                print(f"    CLT range: {min(clts[i] for i in cold_run):.1f} - {max(clts[i] for i in cold_run):.1f}°C")

    # ========== SECTION 4: WARMUP ENRICHMENT ==========
    print(f"\n{'='*80}")
    print("SECTION 4: WARMUP ENRICHMENT (WUE / Gwarm)")
    print(f"{'='*80}")

    if running:
        print(f"\nGwarm (WUE multiplier) during running:")
        gwarm_vals = [gwarms[i] for i in running]
        if gwarm_vals:
            print(f"  Range: {min(gwarm_vals):.0f}% - {max(gwarm_vals):.0f}%")
            # Gwarm by CLT band
            clt_bands = [(0, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 100)]
            print(f"\n  Gwarm by CLT band (running):")
            for lo, hi in clt_bands:
                band_idx = [i for i in running if lo <= clts[i] < hi]
                if band_idx:
                    gw = [gwarms[i] for i in band_idx]
                    af = [afrs[i] for i in band_idx if 5 < afrs[i] < 25]
                    af_avg = sum(af)/len(af) if af else 0
                    print(f"    CLT {lo:3d}-{hi:3d}°C: Gwarm={sum(gw)/len(gw):.0f}% "
                          f"(n={len(band_idx):5d}), AFR avg={af_avg:.1f}")

    # ========== SECTION 5: PULSE WIDTH & DUTY CYCLE ==========
    print(f"\n{'='*80}")
    print("SECTION 5: PULSE WIDTH & DUTY CYCLE")
    print(f"{'='*80}")

    if running:
        r_pws = [pws[i] for i in running]
        r_duties = [duties[i] for i in running]
        print(f"\nPulse Width (running): min={min(r_pws):.2f}ms, max={max(r_pws):.2f}ms, "
              f"avg={sum(r_pws)/len(r_pws):.2f}ms")
        print(f"Duty Cycle (running): min={min(r_duties):.1f}%, max={max(r_duties):.1f}%, "
              f"avg={sum(r_duties)/len(r_duties):.1f}%")

        # Duty cycle safety check (>80% = potential fuel starvation)
        high_duty = [i for i in running if duties[i] > 80]
        if high_duty:
            print(f"\n  ⚠️  HIGH DUTY CYCLE (>80%): {len(high_duty)} samples!")
            for i in high_duty[:10]:
                print(f"    t={times[i]:.1f}s RPM={rpms[i]:.0f} MAP={maps[i]:.0f} Duty={duties[i]:.1f}%")
        else:
            print(f"\n  ✅ No high duty cycle (>80%) events")

        # Duty cycle by RPM band
        print(f"\n  Duty by RPM band (running):")
        rpm_bands = [(400,800), (800,1200), (1200,2000), (2000,3000), (3000,4000), (4000,5000), (5000,7000)]
        for lo, hi in rpm_bands:
            band = [i for i in running if lo <= rpms[i] < hi]
            if band:
                d = [duties[i] for i in band]
                print(f"    RPM {lo:5d}-{hi:5d}: duty avg={sum(d)/len(d):.1f}%, "
                      f"max={max(d):.1f}%, n={len(band)}")

    # ========== SECTION 6: VE TABLE ANALYSIS ==========
    print(f"\n{'='*80}")
    print("SECTION 6: VE TABLE VALUES")
    print(f"{'='*80}")

    if running:
        r_ves = [ves[i] for i in running]
        print(f"\nVE (running): min={min(r_ves):.0f}%, max={max(r_ves):.0f}%, "
              f"avg={sum(r_ves)/len(r_ves):.0f}%")

        # VE by RPM/MAP zones (most important cells)
        print(f"\n  VE by zone (running):")
        zones = [
            ("Idle", 400, 1200, 0, 50),
            ("Low cruise", 1200, 2500, 30, 60),
            ("High cruise", 2500, 3500, 40, 70),
            ("Light load", 1200, 3000, 50, 80),
            ("WOT low RPM", 1200, 3000, 80, 110),
            ("WOT high RPM", 3000, 6500, 80, 110),
        ]
        for label, rlo, rhi, mlo, mhi in zones:
            zone = [i for i in running if rlo <= rpms[i] < rhi and mlo <= maps[i] < mhi]
            if zone:
                v = [ves[i] for i in zone]
                a = [afrs[i] for i in zone if 5 < afrs[i] < 25]
                a_avg = sum(a)/len(a) if a else 0
                print(f"    {label:20s}: VE avg={sum(v)/len(v):5.0f}%, "
                      f"AFR avg={a_avg:.1f}, n={len(zone)}")

    # ========== SECTION 7: ACCELERATION ENRICHMENT ==========
    print(f"\n{'='*80}")
    print("SECTION 7: ACCELERATION ENRICHMENT")
    print(f"{'='*80}")

    ae_active = [i for i in running if accel_enrich[i] > 100]
    print(f"\nAE active samples: {len(ae_active)} ({100*len(ae_active)/max(len(running),1):.1f}% of running)")
    if ae_active:
        ae_vals = [accel_enrich[i] for i in ae_active]
        print(f"AE values when active: min={min(ae_vals):.0f}%, max={max(ae_vals):.0f}%, "
              f"avg={sum(ae_vals)/len(ae_vals):.0f}%")

        # Check for lean spikes during acceleration (TPS DOT > 0)
        accel_events = [i for i in running if tpsdots[i] > 30]
        if accel_events:
            lean_during_accel = [i for i in accel_events if afrs[i] > 15.5 and afrs[i] < 25]
            print(f"\nAcceleration events (TPS DOT > 30): {len(accel_events)}")
            print(f"Lean during acceleration (AFR>15.5): {len(lean_during_accel)}")
            if lean_during_accel:
                print(f"  ⚠️  Lean acceleration events detected!")
                for i in lean_during_accel[:10]:
                    print(f"    t={times[i]:.1f}s RPM={rpms[i]:.0f} MAP={maps[i]:.0f} "
                          f"AFR={afrs[i]:.1f} TPS_DOT={tpsdots[i]:.0f} AE={accel_enrich[i]:.0f}%")

    # ========== SECTION 8: BATTERY VOLTAGE ==========
    print(f"\n{'='*80}")
    print("SECTION 8: BATTERY VOLTAGE")
    print(f"{'='*80}")

    print(f"\nBattery V: min={min(batts):.1f}V, max={max(batts):.1f}V, avg={sum(batts)/len(batts):.1f}V")
    if running:
        r_batts = [batts[i] for i in running]
        print(f"Running:   min={min(r_batts):.1f}V, max={max(r_batts):.1f}V, avg={sum(r_batts)/len(r_batts):.1f}V")
    if cranking:
        c_batts = [batts[i] for i in cranking]
        print(f"Cranking:  min={min(c_batts):.1f}V, max={max(c_batts):.1f}V, avg={sum(c_batts)/len(c_batts):.1f}V")

    low_batt = [i for i in range(total) if batts[i] < 11.0 and rpms[i] > 0]
    if low_batt:
        print(f"\n  ⚠️  Low battery (<11V while engine active): {len(low_batt)} samples")

    # ========== SECTION 9: SYNC & STABILITY ==========
    print(f"\n{'='*80}")
    print("SECTION 9: SYNC & STABILITY")
    print(f"{'='*80}")

    max_sync_loss = max(sync_loss) if sync_loss else 0
    print(f"\nSync losses: max count = {max_sync_loss:.0f}")
    if max_sync_loss > 0:
        print(f"  ⚠️  Sync losses detected!")

    # Rev limiter hits
    limiter_hits = sum(1 for h in hard_limiters if h > 0)
    print(f"Hard limiter hits: {limiter_hits}")

    # RPM stability at idle
    if hot_samples:
        idle_hot = [i for i in hot_samples if rpms[i] < 1200 and maps[i] < 50]
        if idle_hot:
            idle_rpms = [rpms[i] for i in idle_hot]
            rpm_std = (sum((r - sum(idle_rpms)/len(idle_rpms))**2 for r in idle_rpms) / len(idle_rpms)) ** 0.5
            print(f"\nHot idle RPM stability:")
            print(f"  Average: {sum(idle_rpms)/len(idle_rpms):.0f} RPM")
            print(f"  Std dev: {rpm_std:.0f} RPM")
            print(f"  Range: {min(idle_rpms):.0f} - {max(idle_rpms):.0f} RPM")
            if rpm_std > 50:
                print(f"  ⚠️  Unstable idle (std dev > 50 RPM)")
            else:
                print(f"  ✅ Stable idle")

    # ========== SECTION 10: DRIVING PROFILE ==========
    print(f"\n{'='*80}")
    print("SECTION 10: DRIVING PROFILE")
    print(f"{'='*80}")

    if running:
        # RPM histogram
        print(f"\nRPM distribution (running):")
        rpm_hist = [(400,800), (800,1200), (1200,1500), (1500,2000), (2000,2500),
                    (2500,3000), (3000,3500), (3500,4000), (4000,5000), (5000,6500)]
        for lo, hi in rpm_hist:
            count = sum(1 for i in running if lo <= rpms[i] < hi)
            pct = 100 * count / len(running)
            bar = '#' * int(pct / 2)
            print(f"  {lo:5d}-{hi:5d}: {count:5d} ({pct:5.1f}%) {bar}")

        # MAP histogram
        print(f"\nMAP distribution (running):")
        map_hist = [(0,20), (20,30), (30,40), (40,50), (50,60), (60,70),
                    (70,80), (80,90), (90,105)]
        for lo, hi in map_hist:
            count = sum(1 for i in running if lo <= maps[i] < hi)
            pct = 100 * count / len(running)
            bar = '#' * int(pct / 2)
            print(f"  {lo:3d}-{hi:3d} kPa: {count:5d} ({pct:5.1f}%) {bar}")

        # Max RPM reached
        max_rpm = max(r_rpms)
        max_rpm_idx = rpms.index(max_rpm)
        print(f"\nMax RPM: {max_rpm:.0f} at t={times[max_rpm_idx]:.1f}s "
              f"(MAP={maps[max_rpm_idx]:.0f}, AFR={afrs[max_rpm_idx]:.1f})")

    # ========== SECTION 11: IAC ANALYSIS ==========
    print(f"\n{'='*80}")
    print("SECTION 11: IAC VALVE")
    print(f"{'='*80}")

    if running:
        r_iac = [iac_vals[i] for i in running]
        print(f"\nIAC position (running): min={min(r_iac):.0f}, max={max(r_iac):.0f}, "
              f"avg={sum(r_iac)/len(r_iac):.0f}")
        print(f"(Note: IAC algorithm = None, IAC physically disconnected)")

    # ========== SECTION 12: ENRICHMENT CORRECTIONS ==========
    print(f"\n{'='*80}")
    print("SECTION 12: ENRICHMENT CORRECTIONS (Gammae)")
    print(f"{'='*80}")

    if running:
        r_gammae = [gammaes[i] for i in running]
        r_gego = [gegos[i] for i in running]
        print(f"\nGammae (total correction): min={min(r_gammae):.0f}%, max={max(r_gammae):.0f}%, "
              f"avg={sum(r_gammae)/len(r_gammae):.0f}%")
        print(f"Gego (O2 correction):     min={min(r_gego):.0f}%, max={max(r_gego):.0f}%, "
              f"avg={sum(r_gego)/len(r_gego):.0f}%")
        print(f"(Note: egoAlgorithm='No correction' in MSQ — Gego should be 100%)")

    # ========== SECTION 13: BAROMETRIC PRESSURE ==========
    print(f"\n{'='*80}")
    print("SECTION 13: BAROMETRIC PRESSURE")
    print(f"{'='*80}")

    if baros:
        print(f"\nBaro: min={min(baros):.0f} kPa, max={max(baros):.0f} kPa, "
              f"avg={sum(baros)/len(baros):.0f} kPa")
        # Portugal is near sea level, expect ~101 kPa
        avg_baro = sum(baros) / len(baros)
        if avg_baro < 95:
            print(f"  ⚠️  Low baro — altitude or sensor issue?")
        else:
            print(f"  ✅ Normal for sea level")

    # ========== SECTION 14: KNOWN ISSUES CHECK ==========
    print(f"\n{'='*80}")
    print("SECTION 14: KNOWN ISSUES STATUS CHECK")
    print(f"{'='*80}")

    # Issue 5: VE hot idle (should be ~14.7 AFR now)
    if hot_idle:
        hi_afrs_valid = [afrs[i] for i in hot_idle if 5 < afrs[i] < 25]
        if hi_afrs_valid:
            avg_hi_afr = sum(hi_afrs_valid) / len(hi_afrs_valid)
            print(f"\n[Issue 5] Hot idle AFR: avg={avg_hi_afr:.1f} (target: 14.7)")
            if abs(avg_hi_afr - 14.7) < 1.0:
                print(f"  ✅ Hot idle AFR looks good (within 1.0 of 14.7)")
            elif avg_hi_afr < 13.0:
                print(f"  ⚠️  Still running RICH at hot idle")
            elif avg_hi_afr > 16.0:
                print(f"  ⚠️  Running LEAN at hot idle")

    # Issue 6b: ASE cold start — check if still lean in first 17s
    if events:
        for ev_idx, ev in enumerate(events):
            if ev[0] == 'ENGINE_RUNNING':
                start_time = ev[2]
                ase_window = [i for i in running if start_time <= times[i] <= start_time + 25]
                if ase_window:
                    ase_afrs = [afrs[i] for i in ase_window if 5 < afrs[i] < 25]
                    ase_clts = [clts[i] for i in ase_window]
                    if ase_afrs and ase_clts:
                        avg_clt = sum(ase_clts) / len(ase_clts)
                        avg_ase_afr = sum(ase_afrs) / len(ase_afrs)
                        print(f"\n[Issue 6b] ASE period (first 25s after start #{ev_idx+1}):")
                        print(f"  CLT at start: {ase_clts[0]:.1f}°C")
                        print(f"  AFR during ASE: avg={avg_ase_afr:.1f}")
                        if avg_ase_afr > 15.5:
                            print(f"  ⚠️  ASE FIX STILL NEEDED — too lean during ASE")
                        elif avg_ase_afr < 11.0:
                            print(f"  ⚠️  ASE too rich")
                        else:
                            print(f"  ✅ ASE enrichment adequate")

    # Issue 7: Rev limiter
    if max(rpms) > 6200:
        print(f"\n[Issue 7] ⚠️  RPM exceeded 6200! Max={max(rpms):.0f}")
    else:
        print(f"\n[Issue 7] ✅ Rev limiter OK — max RPM {max(rpms):.0f}")

    # Issue 11: Ballast resistor check — check if injector is still direct drive
    # (PW at cranking should tell us about injector response)
    if cranking:
        crank_pws = [pws[i] for i in cranking if pws[i] > 0]
        if crank_pws:
            print(f"\n[Injector] Cranking PW: avg={sum(crank_pws)/len(crank_pws):.2f}ms, "
                  f"max={max(crank_pws):.2f}ms")

    # ========== SECTION 15: SUMMARY & RECOMMENDATIONS ==========
    print(f"\n{'='*80}")
    print("SECTION 15: SUMMARY & RECOMMENDATIONS")
    print(f"{'='*80}")

    issues = []
    good = []

    # Check overall mixture
    if running:
        r_afrs_valid = [afrs[i] for i in running if 5 < afrs[i] < 25]
        if r_afrs_valid:
            avg_afr = sum(r_afrs_valid) / len(r_afrs_valid)
            if avg_afr > 15.5:
                issues.append(f"Overall running lean (avg AFR {avg_afr:.1f})")
            elif avg_afr < 12.5:
                issues.append(f"Overall running rich (avg AFR {avg_afr:.1f})")
            else:
                good.append(f"Overall mixture reasonable (avg AFR {avg_afr:.1f})")

    # Check idle stability
    if hot_samples:
        idle_hot2 = [i for i in hot_samples if rpms[i] < 1200 and maps[i] < 50]
        if idle_hot2:
            idle_rpms2 = [rpms[i] for i in idle_hot2]
            if idle_rpms2:
                rpm_std2 = (sum((r - sum(idle_rpms2)/len(idle_rpms2))**2 for r in idle_rpms2) / len(idle_rpms2)) ** 0.5
                if rpm_std2 > 50:
                    issues.append(f"Unstable hot idle (RPM std dev {rpm_std2:.0f})")
                else:
                    good.append(f"Stable hot idle (RPM std dev {rpm_std2:.0f})")

    # Check duty cycle
    if running:
        max_duty = max(r_duties)
        if max_duty > 80:
            issues.append(f"High duty cycle detected ({max_duty:.0f}%) — injector capacity limit?")
        else:
            good.append(f"Duty cycle within limits (max {max_duty:.0f}%)")

    # Check battery
    if cranking:
        min_crank_v = min(c_batts)
        if min_crank_v < 9.0:
            issues.append(f"Low cranking voltage ({min_crank_v:.1f}V) — battery/starter issue?")
        else:
            good.append(f"Cranking voltage OK ({min_crank_v:.1f}V)")

    print(f"\n✅ GOOD:")
    for g in good:
        print(f"  - {g}")
    print(f"\n⚠️  ISSUES:")
    if issues:
        for iss in issues:
            print(f"  - {iss}")
    else:
        print(f"  - None detected!")

    print(f"\n{'='*80}")
    print("END OF ANALYSIS")
    print(f"{'='*80}")

if __name__ == '__main__':
    analyze()
