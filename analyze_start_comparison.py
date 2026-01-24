import pandas as pd
import numpy as np

print("=" * 80)
print("SCIENTIFIC ANALYSIS: START ATTEMPTS WITH/WITHOUT BALLAST RESISTOR")
print("=" * 80)
print()

# Load all three start logs
start2 = pd.read_csv('start 2.csv', sep=';')  # WITHOUT resistor
start3 = pd.read_csv('start 3.csv', sep=';')  # WITH resistor
start4 = pd.read_csv('start 4.csv', sep=';')  # WITHOUT resistor again

print("LOG FILES LOADED:")
print(f"  start 2.mlg: {len(start2)} samples - WITHOUT ballast resistor")
print(f"  start 3.mlg: {len(start3)} samples - WITH ballast resistor")
print(f"  start 4.mlg: {len(start4)} samples - WITHOUT ballast resistor")
print()

# Function to analyze a start log
def analyze_start(df, name, has_resistor):
    print("=" * 80)
    print(f"{name} - {'WITH' if has_resistor else 'WITHOUT'} BALLAST RESISTOR")
    print("=" * 80)
    print()
    
    # Check if this is actually a cranking/start log
    min_rpm = df['RPM'].min()
    max_rpm = df['RPM'].max()
    
    print(f"RPM RANGE: {min_rpm:.0f} - {max_rpm:.0f} RPM")
    
    if min_rpm < 400:
        print(f"✓ Contains cranking data (RPM < 400 detected)")
        
        # Find cranking period
        cranking = df[df['RPM'] < 400].copy()
        running = df[df['RPM'] >= 400].copy()
        
        print()
        print("CRANKING PHASE:")
        print(f"  Duration: {cranking['Time'].min():.2f}s - {cranking['Time'].max():.2f}s")
        print(f"  Samples: {len(cranking)}")
        print(f"  RPM range: {cranking['RPM'].min():.0f} - {cranking['RPM'].max():.0f}")
        print(f"  Pulsewidth avg: {cranking['PW'].mean():.2f} ms")
        print(f"  Battery voltage avg: {cranking['Battery V'].mean():.2f}V")
        print(f"  Coolant temp: {cranking['CLT'].iloc[0]:.1f}°C")
        
        if len(running) > 0:
            print()
            print("ENGINE STARTED:")
            print(f"  Time to start: {running['Time'].iloc[0]:.2f}s")
            print(f"  First stable RPM: {running['RPM'].iloc[0]:.0f}")
            print()
            print("FIRST 5 SECONDS AFTER START:")
            first_5s = running[running['Time'] <= (running['Time'].iloc[0] + 5.0)]
            if len(first_5s) > 0:
                print(f"  RPM avg: {first_5s['RPM'].mean():.0f}")
                print(f"  RPM range: {first_5s['RPM'].min():.0f} - {first_5s['RPM'].max():.0f}")
                print(f"  Pulsewidth avg: {first_5s['PW'].mean():.2f} ms")
                print(f"  AFR avg: {first_5s['AFR'].mean():.2f}:1")
                print(f"  IAC avg: {first_5s['IAC value'].mean():.1f} steps")
                print(f"  IAC range: {first_5s['IAC value'].min():.0f} - {first_5s['IAC value'].max():.0f} steps")
    else:
        print(f"✗ NO cranking data - engine already running at {min_rpm:.0f} RPM")
    
    print()
    print("IAC BEHAVIOR ANALYSIS:")
    print("-" * 80)
    
    # Get first 30 seconds to analyze IAC
    first_30s = df[df['Time'] <= 30.0].copy()
    
    iac_min = first_30s['IAC value'].min()
    iac_max = first_30s['IAC value'].max()
    iac_avg = first_30s['IAC value'].mean()
    iac_std = first_30s['IAC value'].std()
    
    print(f"IAC Position (first 30s):")
    print(f"  Minimum: {iac_min:.0f} steps")
    print(f"  Maximum: {iac_max:.0f} steps")
    print(f"  Average: {iac_avg:.1f} steps")
    print(f"  Std Dev: {iac_std:.1f} steps")
    print(f"  Range: {iac_max - iac_min:.0f} steps of movement")
    
    # Check if IAC is actually moving
    if iac_std < 5:
        print(f"  ⚠️ WARNING: IAC barely moving (std dev < 5)")
    
    # Correlation between RPM and IAC
    if len(first_30s) > 10:
        rpm_stable = first_30s[first_30s['Time'] > 5.0]  # After initial startup
        if len(rpm_stable) > 10:
            corr = rpm_stable['RPM'].corr(rpm_stable['IAC value'])
            print(f"  RPM-IAC correlation: {corr:.3f}")
            if abs(corr) < 0.3:
                print(f"    → IAC changes NOT affecting RPM (should be negative correlation)")
    
    # Check IAC target vs actual
    rpm_target_avg = first_30s['Idle Target RPM'].mean()
    rpm_actual_avg = first_30s['RPM'].mean()
    rpm_delta_avg = first_30s['Idle RPM Delta'].mean()
    
    print()
    print(f"IDLE CONTROL:")
    print(f"  Target RPM: {rpm_target_avg:.0f}")
    print(f"  Actual RPM: {rpm_actual_avg:.0f}")
    print(f"  Average error: {rpm_delta_avg:.0f} RPM")
    
    print()
    print("FUEL DELIVERY:")
    print("-" * 80)
    
    # Idle fuel analysis (after warmup, closed throttle)
    idle_period = df[(df['Time'] > 10) & (df['TPS'] < 2) & (df['RPM'] > 400)].copy()
    
    if len(idle_period) > 10:
        print(f"Pulsewidth: {idle_period['PW'].mean():.2f} ms (avg)")
        print(f"AFR: {idle_period['AFR'].mean():.2f}:1 (avg)")
        print(f"VE: {idle_period['VE _Current'].mean():.1f}%")
        print(f"Battery: {idle_period['Battery V'].mean():.2f}V")
        
        # Check for rich/lean condition
        afr_avg = idle_period['AFR'].mean()
        if afr_avg < 13.5:
            print(f"  ⚠️ RICH condition (AFR {afr_avg:.1f} < 13.5)")
        elif afr_avg > 15.5:
            print(f"  ⚠️ LEAN condition (AFR {afr_avg:.1f} > 15.5)")
    
    print()
    return {
        'name': name,
        'has_resistor': has_resistor,
        'samples': len(df),
        'rpm_min': min_rpm,
        'rpm_max': max_rpm,
        'iac_min': iac_min,
        'iac_max': iac_max,
        'iac_range': iac_max - iac_min,
        'iac_std': iac_std
    }

# Analyze each log
results = []
results.append(analyze_start(start2, "START 2", False))
results.append(analyze_start(start3, "START 3", True))
results.append(analyze_start(start4, "START 4", False))

print("=" * 80)
print("COMPARATIVE SUMMARY")
print("=" * 80)
print()

print(f"{'Log':<15} {'Resistor':<12} {'Samples':<10} {'IAC Range':<12} {'IAC Movement'}")
print("-" * 80)
for r in results:
    movement = "ACTIVE" if r['iac_std'] > 5 else "STUCK/MINIMAL"
    resistor = "YES" if r['has_resistor'] else "NO"
    print(f"{r['name']:<15} {resistor:<12} {r['samples']:<10} {r['iac_range']:<12.0f} {movement}")

print()
print("=" * 80)
print("IAC PROBLEM DIAGNOSIS")
print("=" * 80)
print()

# Check if IAC is stuck
all_iac_stds = [r['iac_std'] for r in results]
avg_iac_std = np.mean(all_iac_stds)

if avg_iac_std < 10:
    print("❌ PROBLEM DETECTED: IAC NOT MOVING EFFECTIVELY")
    print()
    print("Possible causes:")
    print("  1. IAC physically stuck/binding inside throttle body")
    print("  2. IAC pintle hitting mechanical limit")
    print("  3. DRV8825 current pot set too low (weak motor)")
    print("  4. Wiring issue (motor not getting full current)")
    print("  5. IAC configuration inverted incorrectly")
    print()
    print("You said: 'i took it out side of the monopoint and see it was moving'")
    print("         'but in side it looks or feels that it's doing nothing'")
    print()
    print("This suggests: IAC motor works, but pintle is MECHANICALLY BLOCKED")
    print("               or hitting HARD LIMIT inside the throttle body.")
    print()
    print("RECOMMENDATION:")
    print("  1. Remove IAC from throttle body")
    print("  2. Manually operate it through full range (0-165 steps)")
    print("  3. Observe pintle movement - does it extend/retract full distance?")
    print("  4. Measure pintle travel (should be ~8-10mm total)")
    print("  5. Check throttle body IAC bore for carbon buildup")
    print("  6. Check if pintle is hitting bottom of bore")
else:
    print("✓ IAC appears to be moving normally")

print()
