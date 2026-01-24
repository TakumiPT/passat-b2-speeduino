# GitHub Copilot Instructions - VW Passat B2 1.6 DT Speeduino Project

## Project Overview

This is a **Speeduino ECU tuning project** for a 1984 VW Passat B2 with a 1.6L DT engine. The goal is to convert the original mechanical fuel injection to electronic fuel injection using Speeduino.

## Critical Context for AI Assistants

### Vehicle Information
- **Vehicle:** VW Passat B2 (1984)
- **Engine Code:** DT (1599cc)
- **Compression Ratio:** 9.0:1
- **Power:** 75 PS @ 5200 RPM
- **Fuel System:** Gol G2 SPI Monopoint (~60 lb/hr, 2 ohm injector)
- **ECU:** Speeduino v0.4.3d, firmware 2025.01.6
- **Fuel:** 95 RON gasoline

### Ignition System (CRITICAL!)
- **Type:** Stock mechanical distributor with BOTH:
  - ✅ Vacuum advance (connected to manifold)
  - ✅ Centrifugal advance (mechanical weights inside)
- **Control:** NOT Speeduino controlled - still mechanical
- **Trigger:** Hall sensor distributor (Basic Distributor pattern)
- **Base Timing:** 18° ± 1° BTDC at 700-800 RPM (with vacuum connected)

**IMPORTANT:** Because the distributor has mechanical advance, Speeduino ignition tables would CONFLICT with the mechanical advance. Currently using "Basic Distributor" trigger with fixed timing output.

### IAC (Idle Air Control)
- **Part Number:** Bosch 0269980492
- **Type:** 4-wire bipolar stepper motor
- **Physical Limit:** 165 steps
- **Operation:** INVERTED (0=fully open, 165=fully closed)
- **Driver:** DRV8825 on Speeduino v0.4 board
- **Auxiliary Air:** Throttle body has butterfly bypass screw for base idle air

### IAC Configuration (CORRECT VALUES)
```
iacAlgorithm: Stepper Open Loop
iacStepHome: 165 steps (home position)
iacMaxSteps: 162 steps (safe software limit)
iacCLminValue: 0 steps (full range for closed loop)
iacCLmaxValue: 162 steps (safe closed loop limit)
iacStepHyster: 3 steps
iacStepTime: 3 ms
```

### IAC Tables Philosophy
Since the throttle body has a **butterfly bypass screw** that provides base idle air:
- IAC provides **supplemental air** for cold start
- At operating temperature (~80°C), IAC should be **fully closed (165 steps)**
- Butterfly screw alone handles warm idle
- IAC only adds extra air when cold

## Working with Datalogs

### MLG to CSV Conversion
TunerStudio saves datalogs in `.mlg` binary format. To analyze them:

```bash
# Navigate to DataLogs folder
cd "c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs"

# Convert MLG to CSV using npx
npx mlg-converter --format=csv <filename>.mlg

# Example:
npx mlg-converter --format=csv 2025-12-20_16.57.13.mlg
```

### CSV Format
- Delimiter: Semicolon (;)
- First row: Headers
- Columns include: Time, RPM, MAP, CLT, IAT, AFR, PW, VE, IAC, battery voltage, etc.
- Sample rate: ~15 samples/second

### Key Columns to Analyze
| Column | Description | Normal Values |
|--------|-------------|---------------|
| Time | Seconds since start | 0+ |
| RPM | Engine speed | 0 (off), 200-300 (crank), 700-900 (idle) |
| MAP | Manifold pressure | 30-50 kPa (idle), 95-100 kPa (WOT) |
| CLT | Coolant temperature | -40 to 120°C |
| IAT | Intake air temperature | -40 to 80°C |
| AFR | Air-fuel ratio | 12.5-14.7 typical |
| PW | Injector pulse width | 0-20 ms |
| VE | Volumetric efficiency | 0-150% |

## Known Issues & Fixes Applied

### 1. VE Table - FIXED
- **Problem:** 68% VE at idle causing lean condition
- **Fix:** Increased to 125% at 100 kPa / 500 RPM
- **Result:** Proper rich mixture, no more intake backfires

### 2. Acceleration Enrichment - OPTIMIZED
- **Mode:** TPS-based (not MAP-based)
- **Threshold:** 30 %/s
- **Time:** 300 ms
- **Values:** 40, 70, 100, 130% at 70/220/430/790 %/s
- **Taper:** 5000-6200 RPM

### 3. IAC Closed Loop Limits - FIXED
- **Problem:** Values 270-720 exceeded physical 165-step limit
- **Fix:** Changed to 0-162 (full safe range)

### 4. Cranking Issues
- **Symptom:** Rough/long cranking, dies after start
- **Cause:** No idle air (IAC not installed, butterfly screw not adjusted)
- **Solution:** Install IAC or temporarily open butterfly screw

## DRV8825 Stepper Driver Configuration

### Potentiometer Adjustment (Per Speeduino Manual)
1. Power OFF
2. Turn potentiometer clockwise to limit
3. Power ON (12V)
4. Measure voltage at potentiometer center vs GND
5. Note reading
6. Power OFF, turn counter-clockwise to limit
7. Power ON, measure again
8. **USE THE POSITION WITH HIGHER VOLTAGE**

**Note:** Clone modules vary. Don't expect specific voltage values - just use higher reading.

### Correct Outputs
| Pin | Working Voltage | Dead Driver |
|-----|-----------------|-------------|
| A1, A2, B1, B2 | 1-5V (varies) | 12V (passing VMOT) |

### M0, M1, M2 Pins
All tied to GND = **Full Step Mode** (required for Speeduino)

## File Naming Convention

### Datalogs
- Format: `YYYY-MM-DD_HH.MM.SS.mlg` and `.csv`
- Example: `2025-12-20_16.57.13.mlg`

### Analysis Files
- Python scripts: `*_analysis.py`
- Results: `*_ANALYSIS.txt` (uppercase = final result)
- Guides: `*_GUIDE.txt`

## Common Commands

```bash
# Read tune file settings
grep -E "setting_name" "C:\Users\User1\Documents\TunerStudioProjects\Passat2025\CurrentTune.msq"

# Get IAC settings
grep -E "iac|idle" "C:\Users\User1\Documents\TunerStudioProjects\Passat2025\CurrentTune.msq"

# Get fuel settings
grep -E "reqFuel|injector|inj" "C:\Users\User1\Documents\TunerStudioProjects\Passat2025\CurrentTune.msq"

# Convert latest MLG
npx mlg-converter --format=csv $(ls -t *.mlg | head -1)
```

## What NOT To Do

1. **Don't recommend Speeduino ignition control** - Distributor has mechanical advance that would conflict
2. **Don't set IAC values above 165** - Physical limit of stepper motor
3. **Don't set iacCLmaxValue above 162** - Need 3-step safety margin
4. **Don't disconnect IAC while Speeduino is powered** - Back-EMF damages driver
5. **Don't assume butterfly screw is open** - User prefers IAC for all idle air control

## Useful References

- TunerStudio project: `C:\Users\User1\Documents\TunerStudioProjects\Passat2025\`
- Current tune: `CurrentTune.msq`
- Datalogs: `DataLogs\` folder
- Speeduino Wiki: https://wiki.speeduino.com/
