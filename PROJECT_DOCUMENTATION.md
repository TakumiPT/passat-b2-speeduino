# VW Passat B2 1.6 DT - Speeduino Conversion Project

## 📋 Complete Project Documentation

---

## 1. Vehicle & Engine Specifications

### Vehicle
| Parameter | Value |
|-----------|-------|
| Make/Model | Volkswagen Passat B2 |
| Year | 1984 |
| Market | European |

### Engine
| Parameter | Value |
|-----------|-------|
| Engine Code | DT |
| Displacement | 1599 cc |
| Configuration | Inline 4-cylinder |
| Compression Ratio | 9.0:1 |
| Power | 75 PS @ 5200 RPM |
| Firing Order | 1-3-4-2 |
| Fuel | 95 RON gasoline |

### Original Systems Replaced
| System | Original | New |
|--------|----------|-----|
| Fuel Injection | Carb Pierburg 2e2 | Speeduino EFI |
| Injector | N/A | Gol G2 SPI Monopoint (~60 lb/hr, 2 ohm) |
| ECU | None | Speeduino v0.4.3d |

### Systems Retained (Mechanical)
| System | Status |
|--------|--------|
| Ignition | Stock distributor with Bosch Module 124 |
| Vacuum Advance | Active (connected to manifold) |
| Centrifugal Advance | Active (mechanical weights inside distributor) |

---

## 2. Speeduino Configuration

### Base Settings
```
ECU: Speeduino v0.4.3d
Firmware: 2025.01.6
Algorithm: Speed Density (MAP-based)
Injection Type: Throttle Body (monopoint)
Cylinders: 4
Engine Type: Even fire
Trigger Pattern: Basic Distributor
Required Fuel: 4.3 ms
```

### Trigger System
| Parameter | Value |
|-----------|-------|
| Pattern | Basic Distributor |
| Sensor | Hall effect |
| Teeth | 1 per distributor revolution |
| Missing | N/A |
| Crank RPM Threshold | 300 RPM |

---

## 3. Ignition System (CRITICAL INFORMATION)

### Current Configuration
**Speeduino does NOT control ignition timing.**

The distributor has BOTH:
1. **Vacuum Advance** - Adds timing based on manifold vacuum
2. **Centrifugal Advance** - Adds timing based on RPM (mechanical weights)

### Why Not Speeduino Ignition?
If Speeduino controlled ignition, its timing tables would ADD to the mechanical advance, causing:
- Over-advanced timing
- Detonation/knock
- Engine damage

### Timing Specifications
| Condition | Timing |
|-----------|--------|
| Base timing (vacuum disconnected) | ~10° BTDC |
| Idle timing (vacuum connected) | 18° ± 1° BTDC |
| Full mechanical advance | Base + up to 15° (centrifugal) + up to 12° (vacuum) |

### Future Option
To enable Speeduino ignition control:
1. Replace distributor with one WITHOUT centrifugal weights, OR
2. Weld/lock centrifugal weights in place
3. Disconnect vacuum advance
4. Configure Speeduino ignition tables from scratch

---

## 4. Fuel System

### Injector
| Parameter | Value |
|-----------|-------|
| Type | Gol G2 SPI Monopoint |
| Flow Rate | ~60 lb/hr (~630 cc/min) |
| Impedance | 2 ohm (low-Z, requires resistor or peak-hold driver) |
| Location | Throttle body (single injector) |

### Fuel Tables Configured

#### VE Table Highlights
| RPM | 30 kPa | 50 kPa | 70 kPa | 100 kPa |
|-----|--------|--------|--------|---------|
| 500 | 45% | 75% | 100% | 125% |
| 1000 | 40% | 65% | 85% | 110% |
| 2000 | 35% | 55% | 75% | 100% |
| 3000 | 32% | 50% | 70% | 95% |

#### AFR Targets
| Condition | Target AFR |
|-----------|------------|
| Idle | 14.7:1 (stoich) |
| Cruise | 14.7:1 |
| Light load | 14.0-14.7:1 |
| WOT | 12.5-12.8:1 (rich for power) |

### Enrichments

#### Warmup Enrichment (WUE)
| Temperature | Enrichment |
|-------------|------------|
| -40°C | 180% |
| 0°C | 168% |
| 20°C | 134% |
| 40°C | 114% |
| 60°C | 106% |
| 80°C | 102% |
| 90°C | 100% |

#### Cranking Enrichment
| Temperature | Enrichment |
|-------------|------------|
| -40°C | 280% |
| 0°C | 230% |
| 30°C | 210% |
| 70°C | 200% |

#### After Start Enrichment (ASE)
| Temperature | Extra Fuel | Duration |
|-------------|------------|----------|
| -20°C | 100% | 25 sec |
| 0°C | 90% | 20 sec |
| 40°C | 60% | 15 sec |
| 80°C | 30% | 6 sec |

#### Prime Pulse
| Temperature | Pulse Width |
|-------------|-------------|
| -20°C | 8.0 ms |
| 0°C | 6.0 ms |
| 40°C | 3.0 ms |
| 82°C | 2.0 ms |

#### Acceleration Enrichment (AE)
| TPS Rate (%/s) | Added Fuel |
|----------------|------------|
| 70 | 40% |
| 220 | 70% |
| 430 | 100% |
| 790 | 130% |

- Mode: TPS-based
- Taper: 5000-6200 RPM

---

## 5. Idle Air Control (IAC)

### Hardware
| Parameter | Value |
|-----------|-------|
| Part Number | Bosch 0269980492 |
| Type | 4-wire bipolar stepper motor |
| Physical Limit | 165 steps |
| Operation | INVERTED (0=open, 165=closed) |
| Driver | DRV8825 on Speeduino v0.4 board |

### Throttle Body Configuration
The throttle body has a **butterfly bypass screw** that provides base idle air.

**Philosophy:**
```
Total Idle Air = Butterfly Screw (fixed base) + IAC (variable supplement)
```

At operating temperature (~80°C):
- Butterfly screw provides ALL idle air
- IAC is fully closed (165 steps)
- IAC only opens when cold for extra air

### Software Configuration

#### General Settings
| Setting | Value | Notes |
|---------|-------|-------|
| iacAlgorithm | Stepper Open Loop | Can switch to Closed Loop |
| iacStepHome | 165 | Home/closed position |
| iacMaxSteps | 162 | Safe software limit |
| iacStepHyster | 3 | Deadband |
| iacStepTime | 3 ms | Step timing |
| iacStepperInv | No | Normal polarity |
| iacStepperPower | When Active | Saves power |

#### Closed Loop Settings (for future use)
| Setting | Value | Notes |
|---------|-------|-------|
| iacCLminValue | 0 | Fully open limit |
| iacCLmaxValue | 162 | Fully closed limit (safe) |
| idleKP | 0.5 | P-gain |
| idleKI | 0.09375 | I-gain |
| idleKD | 0.0 | D-gain (disabled) |

#### Cranking Table (iacCrankSteps)
| Temperature | Steps | Valve Position |
|-------------|-------|----------------|
| -21°C | 0 | Fully OPEN |
| 0°C | 54 | 67% open |
| 37°C | 111 | 33% open |
| 79°C | 165 | Fully CLOSED |

**Recommendation:** Close at 65°C instead of 79°C

#### Running Table (iacOLStepVal)
| Temperature | Steps | Valve Position |
|-------------|-------|----------------|
| -26°C | 0 | Fully OPEN |
| 2°C | 18 | 89% open |
| 22°C | 36 | 78% open |
| 39°C | 54 | 67% open |
| 53°C | 72 | 56% open |
| 66°C | 93 | 44% open |
| 82°C | 111 | 33% open |
| 96°C | 129 | 22% open |
| 107°C | 147 | 11% open |
| 117°C | 165 | Fully CLOSED |

**Recommendation:** Close at 80°C instead of 117°C

#### Target Idle RPM Table (iacCLValues)
| Temperature | Target RPM |
|-------------|------------|
| -26°C | 1200 |
| 2°C | 1100 |
| 22°C | 1050 |
| 39°C | 1000 |
| 53°C | 940 |
| 66°C | 840 |
| 82°C+ | 800 |

---

## 6. DRV8825 Stepper Driver

### Location
Plug-in module on Speeduino v0.4 board in the IAC socket.

### Pinout
```
         ┌─────────────────┐
VMOT ────┤ VMOT       EN  ├──── Enable
 GND ────┤ GND        M0  ├──── GND (Full Step)
   B2 ───┤ B2         M1  ├──── GND (Full Step)
   B1 ───┤ B1         M2  ├──── GND (Full Step)
   A1 ───┤ A1        RST  ├──── VCC
   A2 ───┤ A2        SLP  ├──── VCC
   FLT ──┤ FLT       STP  ├──── Step signal
 GND ────┤ GND       DIR  ├──── Direction
         └────[●]─────────┘
              ↑
        Potentiometer
```

### Microstepping (M0, M1, M2)
| M0 | M1 | M2 | Mode |
|----|----|----|------|
| GND | GND | GND | **Full Step** (required) |

### Potentiometer Adjustment

**Per Speeduino Manual:**

1. Power OFF Speeduino
2. Turn potentiometer **clockwise** to internal limit (don't force)
3. Power ON with 12V
4. Measure voltage: potentiometer center to GND
5. Note the reading (e.g., 7V)
6. Power OFF
7. Turn potentiometer **counter-clockwise** to internal limit
8. Power ON, measure again (e.g., 2V)
9. **USE THE POSITION WITH HIGHER VOLTAGE**

**Note:** Don't expect specific voltages. Clones vary. Just use the higher reading.

### Healthy vs Dead Driver

| Output Pins | Healthy Driver | Dead Driver |
|-------------|----------------|-------------|
| A1, A2, B1, B2 | 1-5V (varying) | 12V (passing VMOT) |

If outputs show constant 12V, the driver chip is dead and passing motor voltage directly.

### Protection Rules
1. **NEVER disconnect IAC while Speeduino is ON** - Back-EMF kills driver
2. **Check wiring before power-on** - Shorts kill driver
3. **Add heatsink** if available - Prevents overheating
4. **Don't exceed potentiometer limits** - Don't force past internal stops

---

## 7. Datalog Analysis

### Converting MLG to CSV

TunerStudio saves datalogs in binary `.mlg` format. To analyze in spreadsheets or Python:

```bash
# Navigate to DataLogs folder
cd "c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs"

# Install mlg-converter (first time only)
npm install -g mlg-converter
# OR use npx (no install needed)

# Convert specific file
npx mlg-converter --format=csv 2025-12-20_16.57.13.mlg

# Convert most recent MLG file
npx mlg-converter --format=csv $(ls -t *.mlg | head -1)
```

### CSV Format
- **Delimiter:** Semicolon (;)
- **First Row:** Headers
- **Sample Rate:** ~15 samples/second
- **Encoding:** UTF-8

### Key Parameters to Monitor

| Parameter | Column | Normal Idle | Normal Cruise | Issue Indicators |
|-----------|--------|-------------|---------------|------------------|
| RPM | RPM | 700-900 | 2000-4000 | 0 = stalled, >1200 = racing |
| MAP | MAP | 30-50 kPa | 60-90 kPa | >95 kPa at idle = vacuum leak |
| CLT | CLT | -20 to 100°C | 80-95°C | >105°C = overheating |
| IAT | IAT | Ambient | Ambient+20 | >60°C = heat soak |
| AFR | AFR | 14.0-14.7 | 14.0-14.7 | >16 = lean, <11 = very rich |
| PW | PW | 2-4 ms | 4-10 ms | 0 = no injection |
| VE | VE | 40-60% | 60-100% | Calculated from table |
| Battery | Batt | 13.5-14.5V | 13.5-14.5V | <12V = charging issue |
| IAC | IAC | 50-100 steps | 165 (closed) | 0 = fully open |

### Sample Python Analysis

```python
import pandas as pd

# Read CSV with semicolon delimiter
df = pd.read_csv('2025-12-20_16.57.13.csv', delimiter=';')

# Check column names
print(df.columns.tolist())

# Basic statistics
print(df[['RPM', 'MAP', 'CLT', 'AFR']].describe())

# Find cranking events
cranking = df[(df['RPM'] > 0) & (df['RPM'] < 300)]
print(f"Cranking events: {len(cranking)} samples")

# Find idle events
idle = df[(df['RPM'] >= 600) & (df['RPM'] <= 1000)]
print(f"Idle samples: {len(idle)}")

# Plot RPM over time
import matplotlib.pyplot as plt
plt.plot(df['Time'], df['RPM'])
plt.xlabel('Time (s)')
plt.ylabel('RPM')
plt.title('Engine RPM')
plt.show()
```

---

## 8. Known Issues & Solutions

### Issue 1: Engine Starts Then Dies
**Symptoms:**
- Long/rough cranking
- Engine fires, runs for 1-2 seconds
- Stalls
- Holding throttle slightly keeps it running

**Root Cause:** No idle air

**Solutions:**
1. Install IAC (proper fix)
2. Open butterfly bypass screw 1-2 turns (temporary)
3. Create small vacuum leak (testing only)

### Issue 2: Intake Backfires During Cranking
**Symptoms:**
- Backfire through intake manifold
- Powder/burnt smell
- Poor starting

**Root Causes:**
1. Timing too advanced → Adjust distributor
2. VE table too lean → Increase VE at low RPM/high MAP
3. Both combined

**Solutions Applied:**
- VE increased to 125% at 100 kPa / 500 RPM
- Timing to be checked with timing light

### Issue 3: Old DRV8825 Outputting 12V
**Symptoms:**
- IAC not responding
- Driver outputs 12V instead of 1-5V

**Root Cause:** Driver chip fried (passing VMOT directly)

**Solution:** Replace DRV8825 module

---

## 9. Future Improvements

### Fuel System
| Feature | Status | Benefit |
|---------|--------|---------|
| DFCO | Off | Fuel economy, engine braking |
| EGO Closed Loop | Off | Auto-tune AFR at cruise |
| AFR Protection | Off | Prevent lean damage |
| Baro Correction | Off | Altitude compensation |

### Ignition System
| Feature | Status | Requirement |
|---------|--------|-------------|
| Speeduino Ignition | Not possible | Lock/remove centrifugal advance |

### Idle Control
| Feature | Status | Benefit |
|---------|--------|---------|
| Closed Loop IAC | Ready | Better load compensation |
| Idle Up | Off | Instant load compensation |

---

## 10. File Reference

### Configuration Files
| File | Location | Purpose |
|------|----------|---------|
| CurrentTune.msq | Passat2025\ | TunerStudio tune file |
| projectCfg | Passat2025\ | Project configuration |

### Documentation Files
| File | Purpose |
|------|---------|
| DISTRIBUTOR_BASE_TIMING_FIX.txt | Timing adjustment procedure |
| CLOSED_LOOP_IAC_FIX.txt | IAC limits fix |
| TUNE_STATUS_AND_FUTURE_IMPROVEMENTS.txt | Overall tune status |
| VE_TABLE_RECOMMENDED.md | VE table values |

### Analysis Scripts
| File | Purpose |
|------|---------|
| analyze_csv.py | General datalog analysis |
| iac_settings_analysis.py | IAC configuration analysis |
| ignition_timing_analysis.py | Timing analysis |
| ve_afr_analysis.py | VE and AFR analysis |

---

## 11. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│         VW PASSAT B2 1.6 DT - SPEEDUINO QUICK REFERENCE    │
├─────────────────────────────────────────────────────────────┤
│ ENGINE: 1599cc, 9.0:1 CR, 75 PS, Firing 1-3-4-2            │
│ FUEL: 95 RON, AFR 14.7 (cruise), 12.5 (WOT)                │
│ IGNITION: Mechanical distributor (18° BTDC @ idle)         │
├─────────────────────────────────────────────────────────────┤
│ IAC: Bosch 0269980492                                       │
│   Physical limit: 165 steps                                 │
│   Safe max: 162 steps                                       │
│   Operation: 0=OPEN, 165=CLOSED                            │
│   Close temp: 80°C (running), 65°C (cranking)              │
├─────────────────────────────────────────────────────────────┤
│ DRV8825:                                                    │
│   Healthy output: 1-5V on A1/A2/B1/B2                      │
│   Dead output: 12V (passing VMOT)                          │
│   Adjustment: Use higher VREF voltage                       │
├─────────────────────────────────────────────────────────────┤
│ DATALOGS:                                                   │
│   npx mlg-converter --format=csv <file>.mlg                │
│   Delimiter: semicolon (;)                                  │
├─────────────────────────────────────────────────────────────┤
│ IDLE:                                                       │
│   Target: 800 RPM @ 80°C                                   │
│   Cold: 1200 RPM @ -20°C                                   │
│   Butterfly screw: Sets base air                            │
│   IAC: Adds cold air only                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Changelog

| Date | Change |
|------|--------|
| 2025-11-19 | Project started, first datalogs |
| 2025-12-02 | VE table analysis, identified lean idle |
| 2025-12-08 | VE table fixed (125% at idle/WOT) |
| 2025-12-09 | AE optimized, timing issues identified |
| 2025-12-11 | IAC limits fixed (90-162 → 0-162) |
| 2025-12-20 | IAC deep analysis, DRV8825 setup |
| 2026-01-02 | IAC tables reviewed |
| 2026-01-03 | DRV8825 potentiometer adjusted |
| 2026-01-04 | Start/stall issue diagnosed (no idle air) |
| 2026-01-24 | Documentation created |

---

*Documentation generated: January 24, 2026*
