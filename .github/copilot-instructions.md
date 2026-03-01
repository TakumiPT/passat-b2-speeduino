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
- **Valvetrain:** SOHC 8V, belt-driven, **hydraulic lifters** (Hydrostößel)
- **Original Fuel System:** Pierburg 2E2 carburetor (removed, converted to EFI)
- **Current Fuel System:** Gol G2 SPI Monopoint (~60 lb/hr @ 3 bar rated, 2 ohm low-Z injector)
- **Fuel Pump:** 3 bar (electric, in-tank or inline)
- **Fuel Pressure at TBI:** 1.0-1.5 bar (regulated by fuel pressure regulator built into the TBI unit)
- **Injector Driver:** Direct drive — NO ballast resistor, NO peak-and-hold module (as of 2026-02-28 datalogs)
- **ECU:** Speeduino v0.4.4c SMD (assembled, from diy-efi.co.uk, £155), firmware 2025.01.6

### Injector Sizing — CRITICAL NOTE

This is a **single injector feeding all 4 cylinders** (TBI/Monopoint). Do NOT compare with MPI sizing.

- Rated flow: ~60 lb/hr **@ 3 bar** (injector datasheet pressure)
- Actual flow @ 1.0 bar: ~35 lb/hr (flow scales with √pressure)
- Actual flow @ 1.5 bar: ~42 lb/hr
- Engine demand at WOT: ~37 lb/hr (75 PS × 0.5 lb/hr/HP)
- **The injector is right-sized or slightly undersized**, NOT oversized
- At 80% max duty: flow margin is tight at 1.0 bar (~28 lb/hr usable)
- VE values above 100% are normal and expected for this setup
- High VE values do NOT indicate misconfiguration

### Injector Current — Analysis Complete (SAFE)

With NO ballast resistor and direct drive from Speeduino's onboard VNLD5090-E:
- Current: 14V / 2Ω = **7A** when injector is open
- VNLD5090-E is rated for **13A drain current** → 7A = **54% of rated capacity**
- **VERDICT: 7A direct drive is SAFE** — well within the VNLD5090-E specifications
- Device has built-in overcurrent limiting, power limiting, and thermal shutdown with auto-restart
- Even at 50% injector duty (WOT 6000 RPM), average MOSFET power ≈ 1.5-2.5W — manageable for SOIC-8 on PCB with copper fill
- **Options (in order of benefit to injector longevity):**
  1. Peak-and-hold module (see `peak_and_hold/` folder) — best for injector: 7A peak for 1.5ms, then 1.2A hold
  2. Ballast resistor (3.3Ω 25W) — simple: limits current to ~2.6A, requires `injOpen` increase to 1.5-2.0ms
  3. Do nothing — **SAFE for the Speeduino board** (VNLD5090 handles it fine), but injector sees more current than necessary
- **Fuel:** 95 RON gasoline
- **Production Period:** 08/1983 – 03/1988

### Speeduino Board Hardware (v0.4.4c SMD)

**Board:** Speeduino v0.4.4c SMD assembled version
**Source:** diy-efi.co.uk (£155 / £186 inc VAT) — currently out of stock
**Hardware repo:** https://github.com/speeduino/Hardware/tree/main/v0.4/SMD/Latest

#### Injector Outputs — VNLD5090-E (CRITICAL COMPONENT)

The injector channels use **STMicroelectronics VNLD5090-E** smart low-side drivers (OMNIFET III family), NOT bare MOSFETs:

| IC | Ref | Channels | Outputs | MCU Pins |
|----|-----|----------|---------|----------|
| U1 | VNLD5090-E | Ch.A, Ch.B | INJ-1-OUT, INJ-2-OUT | D8, D11 |
| U3 | VNLD5090-E | Ch.A, Ch.B | INJ-3-OUT, INJ-4-OUT | D9, D10 |

**VNLD5090-E Key Specifications:**
- **Drain current: 13A** (per ST product page)
- AEC-Q100 qualified (automotive grade)
- Built-in protections: overcurrent limiting, power limiting, thermal shutdown (auto-restart), ESD, overvoltage clamp
- Fast demagnetization of inductive loads at turn-off (built-in flyback clamping)
- Package: SOIC-8
- Datasheet: https://www.st.com/resource/en/datasheet/vnld5090-e.pdf

**Injector output circuit (per channel):**
```
MCU pin → 1kΩ → VNLD5090 input
                  ↓
100kΩ pulldown → GND (ensures OFF when MCU not driving)

VNLD5090 output → 1N4448WX diode → INJ-x-OUT terminal
                → 2.4kΩ + LED ← 12V-SW (status indicator, lights when channel ON)
                → GND pins to ground
```

**NO current-limiting resistors on injector outputs.** The 10Ω resistors (R13, R14, R27, R28) are on the IGNITION outputs only.

#### 7A Current Analysis (This Car's Setup)

| Parameter | Without Resistor (now) | With 3.3Ω Resistor | With Peak-and-Hold |
|-----------|----------------------|--------------------|--------------------|
| Peak current | 7A | 2.6A | 7A (1.5ms only) |
| Hold current | 7A (full pulse) | 2.6A (full pulse) | 1.2A (PWM) |
| VNLD5090 utilization | 54% of 13A rating | 20% of 13A rating | ~1mA (sense only) |
| VNLD5090 instant power | ~3.4W (est. 70mΩ Rds) | ~0.5W | negligible |
| Avg power @ idle (2% duty) | 0.07W | 0.01W | negligible |
| Avg power @ WOT (45% duty) | 1.5W | 0.22W | negligible |
| VNLD5090 risk | **SAFE** ✅ | Very safe ✅ | Zero load ✅ |
| Injector heating | High (7A continuous) | Normal (2.6A) | Optimal (1.2A hold) |
| `injOpen` setting | 1.0ms | 1.5-2.0ms | 1.0ms |
| Tune changes needed | None | `injOpen` only | None (P&H handles it) |

**Bottom line:** The Speeduino board is NOT at risk. The VNLD5090-E handles 7A with ample margin. The main concern is injector longevity — 7A continuous through a 2Ω coil generates more heat than the injector was designed for (original system used higher voltage/higher resistance or P&H driving). A ballast resistor or P&H module benefits the **injector**, not the Speeduino.

#### Ignition Outputs — IXDN602

| IC | Ref | Channels | Outputs | MCU Pins | Series Resistors |
|----|-----|----------|---------|----------|-----------------|
| U2 | IXDN602 | A, B | IGN-1-OUT, IGN-2-OUT | D38, D40 | R13 (10Ω), R14 (10Ω) |
| U4 | IXDN602 | A, B | IGN-3-OUT, IGN-4-OUT | D50, D52 | R27 (10Ω), R28 (10Ω) |

- IXDN602 = 2A peak MOSFET gate driver (drives external ignition coil MOSFETs/IGBTs)
- Power rail: Vdrive (selectable via JP1 jumper: 5V or 12V-SW)
- Decoupling: 0.1µF + 1µF per driver IC
- **Not used** on this car (ignition still mechanical distributor)

#### Other Components
| Ref | Part | Function |
|-----|------|----------|
| Q1, Q2, Q3 | SSM3K357R (SOT-23) | Small N-ch MOSFETs for auxiliary outputs |
| U5 | MPX4250AP | Onboard MAP sensor |
| U6 | SP720ABTG | ESD protection |
| U8 | LM2940S-5.0 | 5V voltage regulator |
| D15 | SMBJ40A-Q | TVS diode (transient suppression) |
| F1, F2 | 0ZCC0050FF2C | Polyfuses (resettable, on logic supply, NOT in injector path) |

### Hydraulic Lifters — Important Implications

The DT engine uses **hydraulic valve lifters** (Hydrostößel). This has two critical consequences:

1. **RPM Limitation:** Hydraulic lifters can "pump up" (fail to bleed down fast enough) at high RPM, preventing valves from fully closing. Safe limit ~6200-6500 RPM. Compare with later EA827 8V EFI engines (ABU/AEA in Golf 3) that switched to **solid lifters** (Tassenstößel) and had factory 6500 RPM limiters.

2. **Knock Sensor Incompatible:** Hydraulic lifters produce broadband noise in the 4-10 kHz range, which overlaps the knock frequency of this engine (6-8 kHz). A knock sensor would constantly false-trigger. **Do NOT install a knock sensor** on this engine. Use conservative timing maps (32-33° max WOT vs 36° theoretical) as substitute for knock protection.

### EA827 Family RPM Comparison
| Engine | CR | Lifters | Factory Rev Limit | Notes |
|--------|------|---------|-------------------|-------|
| DT (Passat B2) | 9.0:1 | Hydraulic | None (carb) | Peak power @ 5000 |
| ABU (Golf 3) | 9.0:1 | Solid | 6500 RPM | SPI, 75 PS @ 5000 |
| AEA (Golf 3) | 9.0:1 | Solid | 6500 RPM | MPI, 75 PS @ 5000 |
| ABF (Golf 3 GTI 16V) | 10.0:1 | Solid | 7200 RPM | 150 PS @ 6000 |

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

### Vacuum System Layout

From Haynes manual Fig. 3.2 — current state after carb removal:

| Connection | Diameter | Status | Notes |
|-----------|----------|--------|-------|
| **Brake servo** | 10mm hose | ✅ Connected, working | Has its own check valve on servo. Separate from everything else. |
| **Distributor vacuum advance** | 3-4mm | ✅ Connected | Single nipple on distributor ("A" = Black hose). Connects to manifold vacuum. |
| **Green plastic ball** | 3-4mm, single nipple | ❌ Not needed | Vacuum reservoir for Pierburg 2E2 carb pulldown mechanism. Obsolete with EFI. |
| **Vacuum Unit Stage II** | N/A | ❌ Removed | Was part of the carb body, not a separate component. |
| **Econometer / Gear change indicator** | N/A | ❌ Not fitted | Optional from factory, this car doesn't have them. |

### Thermostatic Air Cleaner (Warmluftregelung)

The air filter box has a **thermostatic air intake system** (TAC):
- **Control box:** Vacuum-operated flap on air filter housing
- **Temperature regulator:** Bimetallic sensor inside air filter housing, connected to intake manifold vacuum
- **Heat source:** Heizbirne (heat shroud) on exhaust manifold — **present and intact**
- **Hot air duct:** Corrugated aluminum tube from Heizbirne to air box — **MISSING, needs replacement** (~60mm Alu-Flexrohr + 2 clamps)
- **How it works:** Cold → sensor closes vacuum bleed → flap opens to hot air. Warm (>25-35°C) → bleed opens → spring pushes flap to cold air.
- **Still useful with TBI:** Single-point injection injects above throttle plate; warm air helps fuel stay atomized through manifold. Less critical than with carb, but keep the system working.
- **If flap stuck on HOT:** ~3-5% power loss (hot air = less dense). Check occasionally.

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
iacAlgorithm: None (IAC physically disconnected — butterfly screw handles idle air)
iacStepHome: 165 steps (home position = fully closed)
iacMaxSteps: 162 steps (safe software limit)
iacCLminValue: 0 steps (full range for closed loop)
iacCLmaxValue: 162 steps (safe closed loop limit) ✅ FIXED (was 54)
iacStepHyster: 3 steps
iacStepTime: 3 ms
iacStepperInv: No (tables are inverted instead)
```

> ✅ **FIXED (2026-02-28):** `iacCLmaxValue` changed from 54 → 162.
> IAC algorithm set to "None" because IAC valve is physically disconnected. Butterfly bypass screw handles all idle air.

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

### 5. VE Table Hot Idle — FIXED (2026-02-28)
- **Problem:** Hot idle running rich (AFR 12.5-12.8 vs target 14.7)
- **Analysis:** Datalog analysis of 2026-02-28_17.53.41.mlg + 2026-02-28_18.10.43.mlg (20,697 data points, hot CLT≥75°C filtered)
- **Fix:** 5 cells corrected:
  - RPM 1200 / MAP 30 kPa: **→ 36** (reduced from over-rich value)
  - RPM 1200 / MAP 36 kPa: **→ 34**
  - RPM 1200 / MAP 40 kPa: **→ 34**
  - RPM 1800 / MAP 26 kPa: **→ 43**
  - RPM 2200 / MAP 26 kPa: **→ 45**
- **Reference files:** DataLogs/ve_refined_analysis.js, DataLogs/VE_TABLE_CORRECTED.xlsx

### 6. WUE (Warmup Enrichment) — FIXED (2026-02-28)
- **Problem:** Cold running too lean (AFR 16-17.6 at CLT 28-50°C)
- **Analysis:** Cold start data from 2026-02-28_17.53.41.mlg (CLT < 75°C segments)
- **Fix:** WUE bins corrected:
  - -40°C: 195 (+16) | -20°C: 190 (+16) | 0°C: 182 (+17)
  - 20°C: 154 (+16) | 28°C: 150 (+17) | 37°C: 138 (+10)
  - 50°C: 122 (+4) | 65°C: 110 (unchanged) | 76°C: 102 (unchanged) | 85°C+: 100
- **Reference files:** DataLogs/create_wue_excel.js, DataLogs/WUE_TABLE_CORRECTED.xlsx

### 7. Rev Limiter — FIXED (2026-02-28)
- **Problem:** Engine reached 7060 RPM in datalog with no protection. hardRevLim was 7000 (too high for DT).
- **Analysis:**
  - DT cam makes no power above 5500 RPM
  - Hydraulic lifters safe to ~6200-6500 RPM
  - VW cluster redline starts ~6200 RPM
  - 40-year-old valve springs, gudgeon pin clips — conservative approach
  - Mean piston speed at 6200 = 15.9 m/s (safe, limit ~18-20 m/s)
- **Fix:**
  - `hardRevLim`: **6200 RPM** (fuel cut — this is the only effective one)
  - `SoftRevLim`: **6000 RPM** (useless until Speeduino controls ignition, but set correctly for future)
- **Note:** If engine is rebuilt with new springs: can increase to 6500.

### 8. iacCLmaxValue — FIXED (2026-02-28)
- **Problem:** Was 54, limiting closed-loop IAC range to 33% of physical travel
- **Fix:** Changed to **162** (98% of 165-step physical limit, 3-step safety margin)

### 9. DFCO (Deceleration Fuel Cut-Off) — MUST STAY OFF
- **Problem:** DFCO is dangerous with mechanical distributor
- **Reason:** On deceleration, manifold vacuum reaches ~20-25 kPa → mechanical distributor advances timing to 35-40° BTDC. When DFCO restores fuel after the cut period, combustion occurs with extreme advance + lean mixture = **intake backfire risk**.
- **Original car:** Pierburg 2E2 carb had an overrun control valve that never fully cut fuel, just leaned it out gradually. DFCO is a different (abrupt) approach that doesn't work with mechanical advance.
- **Fix:** Keep `dfcoEnabled = 0`. Only enable after installing VIKA electronic distributor with Speeduino ignition control (Speeduino will retard timing on fuel restore).

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
7. **Don't enable DFCO with mechanical distributor** - Distributor advances 35-40° at high vacuum on decel. Fuel restore after cut → lean + extreme advance = backfire. Only enable after VIKA electronic distributor + Speeduino ignition control.
8. **Don't install a knock sensor on this engine** - Hydraulic lifters produce 4-10 kHz noise that overlaps knock frequency (6-8 kHz). Constant false triggers. Use conservative timing maps instead.
9. **Don't set hardRevLim above 6200 RPM** - Hydraulic lifters, 40-year-old springs, DT cam makes no power above 5500. If engine rebuilt with new springs: 6500 max.
10. **Don't remove the thermostatic air cleaner** - TBI injects above throttle plate; warm intake air helps fuel atomization through manifold, especially during cold starts.
11. **Don't assume the injector driver is a bare MOSFET** - It's a VNLD5090-E smart low-side driver rated for 13A with built-in protections. 7A from the injector is 54% of its rating — SAFE. The concern is injector longevity, not Speeduino board damage.

## Useful References

- TunerStudio project: `C:\Users\User1\Documents\TunerStudioProjects\Passat2025\`
- Current tune: `CurrentTune.msq`
- Datalogs: `DataLogs\` folder
- Speeduino Wiki: https://wiki.speeduino.com/
- GitHub Repository: https://github.com/TakumiPT/passat-b2-speeduino (private)
