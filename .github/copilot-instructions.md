# GitHub Copilot Instructions - VW Passat B2 1.6 DT Speeduino Project

## Project Overview

This is a **Speeduino ECU tuning project** for a 1984 VW Passat B2 with a 1.6L DT engine. The goal is to convert the original mechanical fuel injection to electronic fuel injection using Speeduino.

## Critical Context for AI Assistants

### Vehicle Information
- **Vehicle:** VW Passat B2 (1984)
- **Engine Code:** DT (EA827 family)
- **Displacement:** 1595cc (97 cu in)
- **Bore × Stroke:** 81mm × 77.4mm (oversquare, 1.05 ratio)
- **Compression Ratio:** 9.0:1
- **Power:** 55 kW (75 PS / 74 HP) @ 5000 RPM
- **Torque:** 125 N⋅m (92 lb-ft) @ 2500 RPM
- **Original Fuel System:** Carburetor (converted to EFI)
- **Current Fuel System:** Gol G2 SPI Monopoint (~60 lb/hr, 2 ohm injector)
- **ECU:** Speeduino v0.4.3d, firmware 2025.01.6
- **Fuel:** 95 RON gasoline
- **Production Period:** 08/1983 – 03/1988

> **Note:** There's also a JU engine code with same power but @ 5500 RPM. Verify your block stamping.

### Ignition System (CRITICAL!)
- **Type:** Stock mechanical distributor with BOTH:
  - ✅ Vacuum advance (connected to manifold)
  - ✅ Centrifugal advance (mechanical weights inside)
- **Control:** NOT Speeduino controlled - still mechanical
- **Trigger:** Hall sensor distributor (Basic Distributor pattern)
- **Base Timing:** 18° ± 1° BTDC at 700-800 RPM (with vacuum connected)
- **Ignition Module:** Bosch Module 124 (TCI - Transistorized Coil Ignition)
- **Coil Primary Resistance:** 0.52-0.76 Ω
- **Coil Secondary Resistance:** 2400-3500 Ω
- **Spark Plugs:** NGK BP6-E (gap: 0.6-0.8 mm)
- **Firing Order:** 1-3-4-2 (cylinder #1 at timing belt end)
- **Rotor Rotation:** Clockwise

**IMPORTANT:** Because the distributor has mechanical advance, Speeduino ignition tables would CONFLICT with the mechanical advance. Currently using "Basic Distributor" trigger with fixed timing output.

### New Electronic Distributor (PURCHASED - NOT YET INSTALLED)
**Plan:** First make car run reliably with current setup → Pass IPO (inspection) → Then install electronic distributor for Speeduino ignition control.

- **Part:** VIKA 99050306801
- **Source:** https://www.auto-doc.pt/vika/13158585
- **OE Numbers:** 050905205AR, 050905237DX, 050905205AP, 02690521536
- **Type:** Electronic distributor WITHOUT mechanical advance
  - ❌ No vacuum advance
  - ❌ No centrifugal advance
  - ✅ Hall sensor trigger only
- **Advantage:** Speeduino has 100% timing control - no conflict with mechanical advance!
- **Status:** Purchased, waiting for installation after IPO

### Future Speeduino Ignition Conversion

When ready to convert from mechanical to Speeduino-controlled ignition (after IPO):

#### Hardware Requirements
- ✓ Speeduino v4 board (already installed)
- ✓ Factory Bosch Module 124 (ignition amplifier - keep it!)
- ✓ **VIKA 99050306801 electronic distributor** (purchased, no mechanical advance!)
- ✓ Speeduino IGN1 output wire to Bosch Module 124 input (NEEDS WIRING)
- ✓ Timing light (essential for trigger angle calibration!)

**With the new electronic distributor:**
- No need to disconnect vacuum advance (it doesn't have one!)
- Speeduino has 100% timing control
- Simpler installation - just swap distributors and enable Speeduino ignition

#### Wiring Change Required
**Current (Fuel-Only):**
```
Distributor Hall → Bosch Module 124 → Coil (independent ignition)
Distributor Hall → Speeduino (RPM reading only)
```

**After Ignition Conversion:**
```
Distributor Hall → Speeduino RPM input
Speeduino IGN1 → Bosch Module 124 input → Coil
(Speeduino controls timing, Bosch Module amplifies signal)
```

#### TunerStudio Configuration Steps

**STEP 1: Basic Spark Settings**
- Menu: Settings → Engine Constants → Trigger Setup
- Trigger Pattern: "Basic Distributor"
- Trigger Angle: 0 (calibrate later!)
- Trigger Edge: "FALLING" (VW Hall sensor)

**STEP 2: Enable Ignition Control (CRITICAL!)**
- Menu: Settings → Engine Constants → Spark/Dwell Settings
- Ignition bypass enabled: **ON** ← This enables Speeduino ignition control!

**STEP 3: Dwell Settings**
- Use dwell map: No
- Cranking dwell: **4.5 ms**
- Running dwell: **3.0 ms**
- Dwell limit: 8.0 ms

**STEP 4: Cranking Timing**
- Menu: Settings → Spark Settings → Cranking Options
- Fixed cranking timing: **12° BTDC**

**STEP 5: Trigger Angle Calibration (MOST IMPORTANT!)**

This calibrates Speeduino to your specific distributor position:

1. PHYSICALLY disconnect vacuum advance hose (plug both ends)
2. In TunerStudio: Tools → Enable Fixed Timing → Set to 18° → Activate
3. Start engine (runs at fixed 18°)
4. Connect timing light to cylinder #1 wire
5. Point at crankshaft pulley, read actual timing
6. Calculate: `Trigger Angle = 18° - Actual Reading`
   - Example: Light shows 78° → Trigger Angle = 18 - 78 = **-60°**
7. Enter calculated value in: Settings → Spark Settings → Trigger Setup → Trigger Angle
8. Verify with timing light (should now show exactly 18°)
9. Disable Fixed Timing Mode

**Expected trigger angle for VW Passat B2: -60° to -90°** (varies by distributor)

#### Ignition Advance Table for 95 RON (Recommended)

Copy/paste this into TunerStudio Spark Table (Tuning → Spark Table):

**Table format:** RPM columns (500-7000), MAP rows (100-10 kPa), values in degrees BTDC

```
RPM→     500  1000  1500  2000  2500  3000  3500  4000  4500  5000  5500  6000  6500  7000
MAP↓
100kPa    14    18    20    22    24    26    28    30    32    33    33    33    33    32
 96kPa    16    20    22    24    26    28    30    32    34    34    34    34    34    33
 88kPa    18    22    24    26    28    30    32    34    35    35    35    35    35    34
 80kPa    18    24    26    28    30    32    34    35    36    36    36    36    36    35
 74kPa    18    26    28    30    32    33    35    36    37    37    37    37    37    36
 66kPa    18    28    30    32    33    34    36    37    38    38    38    38    38    37
 56kPa    18    30    32    33    34    35    37    38    39    39    39    39    39    38
 50kPa    18    30    32    34    35    36    38    39    40    40    40    40    40    39
 46kPa    18    30    32    34    36    37    39    40    40    40    40    40    40    40
 40kPa    18    30    32    34    36    38    40    40    40    40    40    40    40    40
 36kPa    18    30    34    36    37    39    40    40    40    40    40    40    40    40
 30kPa    18    32    34    36    38    40    40    40    40    40    40    40    40    40
 26kPa    18    32    34    36    38    40    40    40    40    40    40    40    40    40
 20kPa    18    32    34    36    38    40    40    40    40    40    40    40    40    40
 16kPa    18    32    34    36    38    40    40    40    40    40    40    40    40    40
 10kPa    18    32    34    36    38    40    40    40    40    40    40    40    40    40
```

**Table characteristics:**
- Idle (500-1000 RPM): **18° BTDC** = matches factory spec exactly
- WOT (100 kPa): **32-33° BTDC** = conservative, 2-4° safety margin
- Light load cruise (30-50 kPa): **38-40° BTDC** = maximum fuel economy
- High RPM protection: Retards 1-2° above 6000 RPM

**Scientific basis for this table:**
- 9.0:1 compression + 95 RON = safe up to 36° WOT
- Table uses 32-34° WOT = 2-4° knock margin
- No catalytic converter = can handle higher EGT
- Small valve overlap (8°) = stable combustion

#### Alternative Tables for Different Fuel

**91 RON (if knock detected):** Reduce all WOT values (100 kPa row) by 4°
**98 RON (premium):** Can add +2° to WOT values for more power

#### Knock Detection
If you hear metallic pinging/rattling under load:
1. Immediately reduce throttle
2. Reduce timing in problem area by 2-4°
3. Or switch to 91 RON table values

#### Verification After Setup
- Dashboard should show "Ign. Timing" values (not blank)
- At idle: Should show ~18° BTDC
- Rev to 2000 RPM: Should show 24-32°
- Timing light should confirm values match

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
iacStepHome: 165 steps (home position = fully closed)
iacMaxSteps: 162 steps (safe software limit)
iacCLminValue: 0 steps (full range for closed loop)
iacCLmaxValue: 162 steps (safe closed loop limit) ⚠️ CURRENTLY 54 IN MSQ - NEEDS FIX!
iacStepHyster: 3 steps
iacStepTime: 3 ms
iacStepperInv: No (tables are inverted instead)
```

> ⚠️ **ISSUE IN CurrentTune.msq:** `iacCLmaxValue = 54` should be `162`!
> This severely limits closed-loop range. Fix before enabling closed-loop mode.

### IAC Tables Philosophy
Since the throttle body has a **butterfly bypass screw** that provides base idle air:
- IAC provides **supplemental air** for cold start
- At operating temperature (~80°C), IAC should be **fully closed (165 steps)**
- Butterfly screw alone handles warm idle
- IAC only adds extra air when cold

**Why iacStepperInv = "No" works:**
The Bosch 0269980492 is physically inverted (extending plunger = closing valve). Instead of setting `iacStepperInv = Yes`, the **tables** are inverted:
- Table shows HIGH step values for COLD (=physically closed, but home position)
- Table shows LOW step values for HOT (=physically open for idle air)
- This works because `iacStepHome = 165` sets home to physically closed position

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

1. **Don't mix mechanical and electronic ignition advance** - If using Speeduino ignition, disconnect vacuum advance first!
2. **Don't set IAC values above 165** - Physical limit of stepper motor
3. **Don't set iacCLmaxValue above 162** - Need 3-step safety margin
4. **Don't disconnect IAC while Speeduino is powered** - Back-EMF damages driver
5. **Don't assume butterfly screw is open** - User prefers IAC for all idle air control
6. **Don't skip trigger angle calibration** - Without it, timing will be wrong by 60-90°!

## Useful References

- TunerStudio project: `C:\Users\User1\Documents\TunerStudioProjects\Passat2025\`
- Current tune: `CurrentTune.msq`
- Datalogs: `DataLogs\` folder
- Speeduino Wiki: https://wiki.speeduino.com/
- GitHub Repository: https://github.com/TakumiPT/passat-b2-speeduino (private)
