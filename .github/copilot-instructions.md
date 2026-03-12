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
- **Current Fuel System:** Gol G2 SPI Monopoint throttle body with **Magneti Marelli IWM500.01** injector (GREEN variant, for 1.6-1.8L engines)
- **Injector Part Numbers:** IWM500.01 / IWM50001 / 501.002.02 / 50100202
- **Injector Resistance:** 2Ω (measured — low impedance, designed for peak-and-hold drive)
- **Injector Flow (from Brazilian bench test table @ design pressure):**
  - Gasoline: 43 ml/test @ 1.0 bar → estimated ~250-260 cc/min @ 1.0 bar (~34 lb/hr)
  - Alcohol: 54 ml/test @ 1.5 bar → estimated ~310-350 cc/min @ 1.5 bar (~44 lb/hr)
  - Equivalent @ 3.0 bar: ~450-500 cc/min (~58-65 lb/hr) — matches the ~60 lb/hr config
  - **Note:** Values are "primeira vazão (bico frio)" — first flow, cold injector
- **Injector Color Variants:** GREEN (1.6-1.8L), BLACK (2.2-2.4L / CM0006644C), ORANGE (0.8-1.4L / IWM523.00)
- **Original SPI Applications:** VW Gol/Parati/Saveiro/Logus/Pointer/Quantum/Pampa, Fiat Elba/Prêmio/Palio/Fiorino, Ford Escort, Renault 19 (Brazilian market SPI systems, 1994-1999)
- **Fuel Pump:** 3 bar (electric, in-tank or inline)
- **Fuel Pressure at TBI:** 1.0-1.5 bar (regulated by fuel pressure regulator built into the TBI unit)
- **Injector Driver:** Direct drive — 1.8Ω 25W ballast resistor arrived 2026-03-12, pending installation
- **O2 Sensor:** Wideband (DIY-EFI TinyWB Rev1 controller + Bosch LSU 4.9), egoType="Wide Band" in TunerStudio
- **O2 Sensor Connector:** Bosch JPT 6-pin (LSU 4.9 standard connector)
- **ECU:** Speeduino v0.4.4c SMD (assembled, from diy-efi.co.uk, £155), firmware 2025.01.6
- **Key Switch:** Old VW style — only ON and START positions (no separate ACC)

### Injector Sizing — CRITICAL NOTE

This is a **single injector feeding all 4 cylinders** (TBI/Monopoint). Do NOT compare with MPI sizing.

- **Model:** Magneti Marelli IWM500.01 (confirmed from injector body markings)
- Rated flow: ~60 lb/hr **@ 3.0 bar** (calculated from Brazilian bench test data, scaling with √pressure)
- Actual flow @ 1.0 bar: ~34 lb/hr (measured test condition for gasoline)
- Actual flow @ 1.5 bar: ~44 lb/hr (measured test condition for alcohol)
- Engine demand at WOT: ~37 lb/hr (75 PS × 0.5 lb/hr/HP)
- **The injector is right-sized or slightly undersized**, NOT oversized
- At 80% max duty: flow margin is tight at 1.0 bar (~27 lb/hr usable)
- VE values above 100% are normal and expected for this setup
- High VE values do NOT indicate misconfiguration

### Injector Current — WHAT WILL BREAK? (Full Failure Analysis)

**ANSWER: The INJECTOR will fail. The Speeduino board will NOT fail.**

#### Why the Speeduino is SAFE:
- VNLD5090-E rated **13A** — your injector draws **7A** (54% of capacity)
- Built-in thermal shutdown with auto-restart — if it ever gets too hot, it protects itself
- Built-in overcurrent limiting — cannot be destroyed by overcurrent
- Estimated Rds(on) ~70mΩ → power = 7² × 0.07 = **3.4W instantaneous**, ~0.17W average at idle (5% duty)
- SOIC-8 on PCB with copper pour → adequate heat sinking
- **The VNLD5090-E will NOT break. Period.**

#### Why the INJECTOR is at risk:
The IWM500.01 was designed for **peak-and-hold drive** by the original Magneti Marelli 1AVB / Bosch Mono-Motronic ECU:
- **Original design:** ~4A peak (1-2ms to open) → ~1.0-1.5A hold (PWM)
- **Original hold power:** 1.5² × 2Ω = **4.5W** in the coil
- **Your current setup:** 7A continuous for the entire pulse width
- **Your current power:** 7² × 2Ω = **98W instantaneous** in the coil (22× designed hold power!)

| Operating Condition | Duty Cycle | Avg Power in Coil | Risk Level |
|---------------------|------------|-------------------|------------|
| Idle (800 RPM) | ~2-5% | 2-5W | LOW — injector survives fine |
| Light cruise (2500 RPM) | ~8-12% | 8-12W | MODERATE — extra heat, slow degradation |
| Hard acceleration | ~25-35% | 25-35W | HIGH — coil insulation stressed |
| WOT (5000+ RPM) | ~40-50% | 40-50W | **DANGER — will damage injector** |

#### How the injector fails (progressive):
1. **Coil insulation softens** — enamel wire insulation (class F, rated ~155°C) degrades from repeated overheating
2. **Shorted turns develop** — insulation breaks down between adjacent coil windings
3. **Impedance changes** — 2Ω drops to ~1.5Ω or lower → current INCREASES → thermal runaway
4. **Erratic fueling** — changed impedance means different flow characteristics
5. **Open circuit** — coil wire burns through → no fuel → lean misfire → potential engine damage

#### Practical risk assessment for YOUR driving:
- **City driving (mostly idle + light cruise):** Injector will probably last months to years — duty cycles are low
- **Spirited driving / highway merging at WOT:** Accelerated injector degradation
- **Sustained WOT (track day, uphill at full throttle):** Could damage injector in one session
- **Datalog evidence:** Your logs show 98.6% of time at <10% duty — for your normal driving, the risk is LOW but cumulative

#### RECOMMENDATION (in order of priority):
1. **Best: Build the P&H circuit** (see `peak_and_hold/` folder) — 7A peak for 1.5ms, 1.2A hold. Injector runs at designed parameters. No tune changes.
2. **Good: Add a 1.8Ω 25W wirewound ceramic resistor** in series with injector wire — limits current to ~3.8A @ 14.4V, still opens at cranking voltage (2.24A > 2.0A pull-in). Increase `injOpen` to ~1.1ms. (3.3Ω tested 2026-03-01 and FAILED — current too low to open injector during cranking.)
3. **Acceptable for now: Do nothing** — the Speeduino board is safe regardless. The injector is at low-to-moderate risk during normal city driving. Monitor for misfires, rough running, or changed fuel trims as signs of injector degradation.

**Important:** If the injector fails, it fails GRADUALLY (not catastrophically). You'll notice rough running, changed fuel behavior, or misfires before total failure. You have time to act.
- **Fuel:** 95 RON gasoline
- **Production Period:** 08/1983 – 03/1988

### Speeduino Board Hardware (v0.4.4c SMD)

**Board:** Speeduino v0.4.4c SMD assembled version
**Source:** diy-efi.co.uk (£155 / £186 inc VAT) — currently out of stock
**Hardware repo:** https://github.com/speeduino/Hardware/tree/main/v0.4/SMD/Prior%20Versions/0.4.4c
**Note:** The "Latest" folder on GitHub is v0.4.4**d**. Your actual board v0.4.4c is under "Prior Versions/0.4.4c/".

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

| Parameter | Without Resistor (now) | With 1.8Ω Resistor (recommended) | With Peak-and-Hold |
|-----------|----------------------|--------------------|--------------------||
| Peak current | 7A | 3.8A | 7A (1.5ms only) |
| Hold current | 7A (full pulse) | 3.8A (full pulse) | 1.2A (PWM) |
| VNLD5090 utilization | 54% of 13A rating | 29% of 13A rating | ~1mA (sense only) |
| VNLD5090 instant power | ~3.4W (est. 70mΩ Rds) | ~1.0W | negligible |
| Avg power @ idle (2% duty) | 0.07W | 0.02W | negligible |
| Avg power @ WOT (45% duty) | 1.5W | 0.45W | negligible |
| VNLD5090 risk | **SAFE** ✅ | Very safe ✅ | Zero load ✅ |
| Injector heating | High (7A continuous) | Moderate (3.8A) | Optimal (1.2A hold) |
| `injOpen` setting | 1.0ms | ~1.1ms | 1.0ms |
| Tune changes needed | None | `injOpen` only | None (P&H handles it) |

**Bottom line:** The Speeduino board is NOT at risk. The VNLD5090-E handles 7A with ample margin. The main concern is injector longevity — 7A continuous through a 2Ω coil generates more heat than the injector was designed for (original system used higher voltage/higher resistance or P&H driving). A ballast resistor or P&H module benefits the **injector**, not the Speeduino.

#### Ignition Outputs — TC4424A (v0.4.4c) / IXDN602 (v0.4.4d)

**Your v0.4.4c board uses TC4424A** (Microchip TC4424AVOA). The newer v0.4.4d uses IXDN602.

| IC | Ref | Channels | Outputs | MCU Pins | Series Resistors |
|----|-----|----------|---------|----------|-----------------|
| U2 | TC4424A | A, B | IGN-1-OUT, IGN-2-OUT | D38, D40 | R13 (10Ω), R14 (10Ω) |
| U4 | TC4424A | A, B | IGN-3-OUT, IGN-4-OUT | D50, D52 | R27 (10Ω), R28 (10Ω) |

- TC4424A = 3A dual MOSFET gate driver (drives external ignition coil MOSFETs/IGBTs)
- Power rail: Vdrive (selectable via JP1 jumper: 5V or 12V-SW)
- Decoupling: 0.1µF + 1µF per driver IC
- **Not used** on this car (ignition still mechanical distributor)

#### Tacho Output (Proto Area 4)
- **Pin:** Speeduino pin 17 → SSM3K357R MOSFET → tacho output terminal
- **JP2 Jumper:** Selects tacho output voltage — **5V** or **12V**
- **Set JP2 = 12V** for the old VW Passat B2 instrument cluster tachometer (reads from coil terminal 1 / Klemme 1)
- Direct wire from Speeduino tacho output to cluster — no relay, no transistor needed

**TunerStudio Tacho Settings:**
```
tachoPin: Board Default
tachoDiv: Half          (4-cylinder = 2 pulses per revolution)
tachoDuration: 3 ms     (fixed pulse width for old analog tach)
tachoMode: Fixed Duration (NOT "Match Dwell" — Speeduino doesn't control ignition yet)
useTachoSweep: Off      (set On for startup needle sweep — cosmetic)
tachoSweepMaxRPM: 6200  (match hardRevLim)
```

#### Other Components
| Ref | Part | Function |
|-----|------|----------|
| Q1, Q2, Q3 | SSM3K357R (SOT-23) | Small N-ch MOSFETs for auxiliary outputs (fuel pump relay, fan relay, tacho). Drive relay coils (~150mA) only — NOT direct motor/pump loads (rated ~3A but SOT-23 thermal limit ~200-500mA continuous) |
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

### Coolant System — Sensors & Flange

**Coolant Flange:** VW 026.121.133.9 (right side of cylinder head)

The original Passat B2 had **2 thermoswitches** in this flange, both part of the Pierburg 2E2 carb cold-start circuit (manifold heater, choke heater, pull-down heater):

| Position | Thread | Original (Passat B2) | Current | Planned |
|----------|--------|---------------------|---------|----------|
| Top | M10×1 | Thermoswitch **035 919 369 C** (removed) | **Bosch NTC sensor** (unknown part#) → Speeduino CLT | **MTE-Thomson 3018** = **VW 027 919 501** / HELLA 6PT 009 309-441 / febi 01939 — dashboard gauge sender (1 pin, NTC) |
| Bottom | M12×1.5 | Thermoswitch **026 919 369** | Still installed (original) | **MTE-Thomson 4053** = **VW 026 906 161 B** / HELLA 6PT 009 309-291 — ECU coolant sensor (2 pin, NTC, 2055Ω@25°C) → Speeduino CLT |

> **⚠️ Source reliability note:** The coolant flange part number (026.121.133.9) is **confirmed by the owner**. Thread sizes are confirmed by **owner physical fitment test** (2026-03-03): MTE-Thomson 3018 (M10×1 per CatE catalog) fits top position, MTE-Thomson 4053 (M12×1.5 per CatE catalog) fits bottom position. Sensors were placed in the holes and fit correctly but were not threaded in. Original thermoswitch numbers (035 919 369 C, 026 919 369), the identity of the current Bosch NTC sensor, and the Facet 7.3073 location are all **user-reported and NOT independently verified**. All MTE-Thomson, HELLA, febi, and Bosch cross-references are independently verified from manufacturer product listings.

**All temperature-related sensors on this engine:**

| Location | Sensor | Function | Status |
|----------|--------|----------|--------|
| Coolant flange (top, M10×1) | Bosch NTC (unknown part#) | Speeduino CLT input | ✅ Installed — planned replacement: **MTE-Thomson 3018** (dashboard gauge) goes here, move CLT to bottom |
| Coolant flange (bottom, M12×1.5) | Original thermoswitch 026 919 369 | 2E2 carb circuit (orphaned) | ✅ Still in place — planned: **MTE-Thomson 4053** (ECU sensor, 2055Ω NTC) → Speeduino CLT |
| Back of cylinder head | Facet 7.3073 | Dashboard gauge sender (original Passat) | ✅ Currently installed — becomes redundant when 3018 installed in top |
| Radiator | Fan thermoswitch | Radiator fan on/off | ✅ Installed, independent circuit |

> **Installation plan:** Both purchased sensors fit the Passat B2 flange (owner-tested 2026-03-03). **3018** (M10×1, 1-pin gauge sender) → top position. **4053** (M12×1.5, 2-pin ECU sensor) → bottom position → Speeduino CLT. No additional sensors needed. The Facet 7.3073 on back of head becomes redundant once 3018 is installed in top position.

### Intake Manifold Heater — DEAD

The intake manifold has an **electric heater** (thick red wire underneath) designed to warm the manifold during cold starts, reducing fuel condensation on cold walls.

- **Original circuit:** Activated by thermoswitch **035 919 369 C** (or **026 919 369**) in coolant flange 026.121.133.9
- **Current status:** **DEAD** — top thermoswitch (035 919 369 C) removed and replaced with Bosch NTC sensor (different electrical behavior, cannot switch the heater circuit). Bottom thermoswitch (026 919 369) still in place but circuit likely broken.
- **Impact:** Cold manifold walls condense more fuel during warmup → higher ASE values needed than Gol G2 factory
- **Mitigation:** ASE fix (issue 6b) compensates with extra fuel. Thermostatic air cleaner provides warm air to help atomization.

### CLT Sensor Calibration

The **current CLT sensor** is an unknown Bosch NTC thermistor. A **MTE-Thomson 4053** (2055Ω @ 25°C NTC) was purchased to replace it. Owner tested fitment (2026-03-03): **4053 fits the bottom position** (M12×1.5) of coolant flange 026.121.133.9.

The Speeduino v0.4 board has a **2490Ω bias resistor** (R10 for CLT, R11 for IAT).

**To calibrate:** TunerStudio → Tools → Calibrate Thermistor Tables → Coolant Temperature Sensor → "3 Point Therm Generator" → enter 3 known resistance-temperature points for the installed sensor.

**Current status:** CLT readings appear plausible in datalogs (26°C cold matching ambient, warming to 47°C during running). Check which calibration is loaded in TunerStudio (may have been calibrated for the Bosch sensor). Verify with a known-accurate thermometer — wrong CLT affects WUE, ASE, cranking enrichment, and all temperature-dependent corrections.

#### MTE-Thomson 4053 — Fits Bottom Position

The MTE-Thomson 4053 has **M12×1.5 thread** (from CatE MTE-Thomson catalog: 19mm hex, M12×1.5). It fits the **bottom position** of coolant flange 026.121.133.9 (owner-tested 2026-03-03, not threaded but physically matched). This will be the Speeduino CLT sensor.

The MTE-Thomson catalog cross-references 4053 → VW 026906161**B** (with B suffix). The HELLA equivalent is **6PT 009 309-291** (verified OE cross-references match exactly). Note: VW 026 906 161 (without B suffix) is a different sensor (M10×1, 2080Ω@25°C) that fits the **top** position — see "VW 026 906 161" section below for reference data.

**MTE-Thomson 4053 — Full OEM Data** (from CatE MTE-Thomson catalog at catalogo.mte-thomson.com.br — MTE-Thomson's official electronic parts catalog; data extracted in previous session, site uses JavaScript SPA and cannot be re-scraped by automated tools):

| Attribute | Value |
|-----------|-------|
| **MTE-Thomson** | **4053** |
| **VW OE Numbers** | **026 906 161 B** (026906161B) / **026 906 161 12** (02690616112) |
| **HELLA Part** | **6PT 009 309-291** (verified on Spareto + ak24parts — identical OE cross-references) |
| Type | PLUG ELETRÔNICO - ÁGUA (ECU coolant temperature sensor) |
| Thread | M12×1.5 |
| Hex | 19mm |
| Pins | 2 |
| Colour | Blue (AZUL) |
| Sensor Type | NTC |
| Resistance @ 25°C | **2055 Ω** (⚠️ CatE catalog said "5kΩ" — **WRONG**, corrected by HELLA 6PT 009 309-291 datasheet: Spareto + ak24parts both show 2055Ω) |
| Resistance @ 80°C | **327 Ω** (from HELLA 6PT 009 309-291 datasheet, verified on Spareto + ak24parts) |
| Resistance @ 0°C | **6057 Ω** (CALCULATED — β=3519K from the two HELLA data points) |

**Other OEM cross-references** (from CatE catalog, 26 numbers total):
Alfa Romeo 46477022/60806379/60813751, Citroën/Peugeot 1338A5, FIAT 46477022/7547977/7695581, FORD V86HF12A648AA, GM/Vauxhall 93184580, Iveco 4850371, Lancia 46477022/7547977/82380901, Opel 1342850/4416020/4500001, Renault 7702087460, plus Alfa/Lancia/Fiat/Opel duplicates across brands.

**Applications:** VW Gol G2 1.6 AP1600 (1994-2009), Parati, Santana, Saveiro, Polo Classic, Quantum, Van. Also used in FIAT (Elba, Fiorino, Palio, Siena, Tempra, Tipo, Uno), Ford Escort BR, Renault 19/Clio, GM Astra/Corsa/Vectra, Alfa Romeo 145/146/155/164, Citroën AX/BX/ZX, Peugeot 106/205/306/309/405, Iveco Daily, Lancia Delta/Dedra/Thema.

**Resistance-temperature sources:**
- Spareto: spareto.com/products/hella-sensor-coolant-temperature/6pt-009-309-291 (shows "Resistor 2055 Ohm" and "Resistor 327 Ohm" at 25°C and 80°C)
- ak24parts: ak24parts.com/en/spareparts/hella-6pt-009-309-291 (shows "Resistor2, 055Ohm, 327Ohm" — same data, different formatting)

**TunerStudio 3-point calibration for MTE-Thomson 4053** (enter in "3 Point Therm Generator"):
- Point 1: **0°C** = **6057 Ω** ⚠️ CALCULATED (β=3519K from the two HELLA data points)
- Point 2: **25°C** = **2055 Ω** ✅ VERIFIED (HELLA 6PT 009 309-291 datasheet, 2 independent sources)
- Point 3: **80°C** = **327 Ω** ✅ VERIFIED (HELLA 6PT 009 309-291 datasheet, 2 independent sources)

**β calculation:** β = ln(2055/327) / (1/298.15 − 1/353.15) = 3519K. Then R(0°C) = 2055 × exp(3519 × (1/273.15 − 1/298.15)) = 6057Ω.

> **⚠️ Only 2 of 3 calibration points are from verified datasheets.** The 0°C value is extrapolated using the Steinhart-Hart β model. Verify with a multimeter + ice water bath after installation.

#### MTE-Thomson 3018 — Dashboard Gauge Sender

| Attribute | Value |
|-----------|-------|
| **MTE-Thomson** | **3018** |
| **VW OE Numbers** | **027 919 501** / **049 919 501** / **175 919 501** (all confirmed by HELLA 6PT 009 309-441 + febi 01939 listings on Spareto + ak24parts) |
| **HELLA Part** | **6PT 009 309-441** |
| **febi Part** | **01939** |
| Type | SENSOR DE TEMPERATURA - INDICADOR NO PAINEL (dashboard gauge sender) |
| Thread | M10×1.0 |
| Hex | 14mm (febi 01939 datasheet on Spareto + ak24parts) / 13mm (HELLA 6PT 009 309-441 datasheet on Spareto + ak24parts) — **manufacturers disagree** |
| Pins | 1 (grounds through body) |
| Colour | Black |
| Sensor Type | NTC |
| Temp Range | 0°C to +125°C |
| Resistance table | **NOT PUBLISHED** by MTE-Thomson, HELLA, febi, or any aftermarket source |
| Speeduino calibration | **NOT NEEDED** — connects to dashboard gauge, not ECU |

**Applications:** VW Gol/Parati/Saveiro/Logus/Pointer/Quantum/Santana/Van, Ford Escort BR.

> **Note:** The 3018 is a **1-pin gauge sender** (not a 2-pin ECU sensor). It connects to the dashboard temperature gauge only. It does NOT connect to the Speeduino and does NOT need TunerStudio calibration.

#### VW 026 906 161 — Alternative OEM CLT Sensor (M10×1 Top Position)

This sensor fits the **top** M10×1 position on coolant flange 026.121.133.9. It is NOT needed if using MTE-Thomson 4053 in the bottom position. Kept here as reference data:

| Attribute | Value |
|-----------|-------|
| **VW OE Number** | **026 906 161** (without B suffix) |
| **HELLA Part** | **6PT 009 107-561** |
| **Bosch Parts** | **0 280 130 026** / **0 280 130 040** |
| Thread | M10×1 |
| Pins | 2 |
| Sensor Type | NTC |
| Colour | White |
| Country of Origin | Brazil |

**Resistance-temperature values** (from HELLA specifications, verified on Spareto + ak24parts):

| Temperature | Resistance | Source |
|-------------|-----------|--------|
| **0°C** | **6577 Ω** | **CALCULATED** (β=3750K from the two HELLA data points — NOT from datasheet) |
| **25°C** | **2080 Ω** | **VERIFIED** — HELLA 6PT 009 107-561 datasheet (2 independent sources) |
| **80°C** | **294 Ω** | **VERIFIED** — HELLA 6PT 009 107-561 datasheet (2 independent sources) |

**Sources:** Spareto (spareto.com/products/hella-sensor-coolant-temperature/6pt-009-107-561) and ak24parts (ak24parts.com/en/spareparts/hella-6pt-009-107-561) — both list identical specs.

**TunerStudio 3-point calibration** (enter these in "3 Point Therm Generator"):
- Point 1: **0°C** = **6577 Ω** ⚠️ CALCULATED, not from datasheet
- Point 2: **25°C** = **2080 Ω** ✅ VERIFIED (HELLA datasheet)
- Point 3: **80°C** = **294 Ω** ✅ VERIFIED (HELLA datasheet)

**β calculation:** β = ln(2080/294) / (1/298.15 − 1/353.15) = 3750K. Then R(0°C) = 2080 × exp(3750 × (1/273.15 − 1/298.15)) = 6577Ω.

> **⚠️ Only 2 of 3 calibration points are from verified datasheets.** The 0°C value is extrapolated using the Steinhart-Hart β model. While this is standard engineering practice for NTC thermistors, the actual 0°C resistance may differ. Verify with a multimeter + ice water bath after purchasing the sensor.

#### Sensor Comparison — 4053 vs VW 026 906 161

| | MTE-Thomson 4053 (purchased) ✅ | VW 026 906 161 / HELLA -561 (alternative) |
|---|---|---|
| Resistance @ 25°C | **2055 Ω** (HELLA 6PT 009 309-291) | 2080 Ω |
| Resistance @ 80°C | **327 Ω** (HELLA 6PT 009 309-291) | 294 Ω |
| Thread | M12×1.5 | M10×1 |
| Colour | Blue | White |
| HELLA equivalent | 6PT 009 309-291 | 6PT 009 107-561 |
| Fits Passat B2 flange | **YES** ✅ bottom position (owner-tested) | YES — top position |
| Calibration data | **2 of 3 verified** (HELLA datasheet), 1 calculated | 2 of 3 verified (HELLA datasheet), 1 calculated |
| Cross-references | VW 026906161**B** | VW 026 906 161 (no B suffix) |

> **Both sensors are ~2kΩ @ 25°C NTC elements** in different housings/threads. The “5kΩ” claimed by CatE catalog for the 4053 was incorrect — corrected by HELLA datasheet.

> **⚠️ "B" suffix matters:** VW 026 906 161 (no suffix) and VW 026 906 161 **B** are physically different sensors — different thread (M10 vs M12), slightly different resistance (2080Ω vs 2055Ω @ 25°C), different colour (White vs Blue). But the NTC elements are similar (~2kΩ class). The MTE-Thomson 4053 cross-references the **B** variant only.

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
iacAlgorithm: Stepper Open Loop (changed from "None" on 2026-03-07)
iacStepHome: 165 steps (home position = fully closed)
iacMaxSteps: 162 steps (safe software limit)
iacCLminValue: 0 steps (full range for closed loop)
iacCLmaxValue: 162 steps (safe closed loop limit) ✅ FIXED (was 54)
iacStepHyster: 3 steps
iacStepTime: 3 ms
iacStepperInv: No (tables are inverted instead)
```

> ✅ **FIXED (2026-02-28):** `iacCLmaxValue` changed from 54 → 162.
> ✅ **CHANGED (2026-03-07):** iacAlgorithm changed from "None" → "Stepper Open Loop".
> IAC valve is physically disconnected. Butterfly bypass screw handles all idle air. Open loop is configured and ready for when IAC is connected.

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
- **Problem (Feb 28):** Cold running too lean (AFR 16-17.6 at CLT 28-50°C)
- **Analysis (Feb 28):** Cold start data from 2026-02-28_17.53.41.mlg (CLT < 75°C segments)
- **Fix (Feb 28):** WUE bins corrected:
  - -40°C: 195 (+16) | -20°C: 190 (+16) | 0°C: 182 (+17)
  - 20°C: 154 (+16) | 28°C: 150 (+17) | 37°C: 138 (+10)
  - 50°C: 122 (+4) | 65°C: 110 (unchanged) | 76°C: 102 (unchanged) | 85°C+: 100
- **Mar 1 re-analysis:** Initially appeared lean at CLT 46-47°C, but further analysis revealed:
  - MLG1 ending was user turning ignition key OFF — NOT a stall (proven: stable RPM 970 + battery 12.8→6.8V in 0.1s = ignition cutoff)
  - IAC disconnected, butterfly screw in fixed Gol G2 factory position — no idle air variability
  - Engine was running fine at CLT 46-47°C with Feb 28 WUE values
  - **No WUE change needed.** Feb 28 values (37°C: 138, 50°C: 122) are correct.
- **Reference files:** DataLogs/wue_definitive.py, DataLogs/wue_ase_refined.py

### 6b. ASE (After Start Enrichment) — NEEDS FIX (2026-03-01)
- **Problem:** First 17s after cold start at 26°C: AFR 17.0 (target: 13.2). After ASE expires, AFR normalizes to 13.1 — proving WUE is correct and only ASE magnitude is insufficient.
- **Analysis:** 2026-03-01_19.05.30.mlg — 255 ASE-period samples (0-17s after start), 1659 post-ASE samples. Gammae with ASE = 270%, without = 159%. Current ASE at 26°C = 69.8% (interpolated 70.5%, matches ✅). Needed: 118.4%. Scale factor: 1.68×.
- **Fix:** ASE% bins (asePct) to change:
  - -20°C: 100 → **155** (TunerStudio max limit; calculated 168 but capped) | 0°C: 90 → **151** | 40°C: 60 → **101** | 80°C: 30 → **30** (keep)
  - 155 cap only affects -20°C bin — at 26°C start the interpolated value is 118.5% (unaffected by cap)
  - ASE duration (aseCount): **NO CHANGE** — 25s, 20s, 15s, 6s (verified correct)
  - ASE bins (aseBins): **NO CHANGE** — -20°C, 0°C, 40°C, 80°C
  - **Note:** Higher ASE needed partly because the intake manifold heater is dead (thermoswitch replaced by CLT sensor)
- **Reference files:** DataLogs/wue_ase_refined.py, DataLogs/wue_ase_fix_analysis.py

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

### 10. VE Table Hot-Idle vs Warmup Interaction — RESOLVED (2026-03-01)
- **Observation:** The Feb 28 hot-idle VE correction (RPM 1200 / MAP 36-40 → 34) creates a valley at RPM 1200 that theoretically affects warmup-temperature running (6.8% less fuel at ~970 RPM due to interpolation toward RPM 1200).
- **Resolution:** Engine ran fine at CLT 46-47°C with original WUE values (138/122) — the VE valley does not cause a real-world problem. No WUE compensation needed, no VE change needed.
- **Status:** Closed. Monitor if idle RPM target changes significantly.

### 11. Ballast Resistor — 3.3Ω FAILED, 1.8Ω ARRIVED (2026-03-12)
- **3.3Ω test (2026-03-01):** Engine did NOT start. 2026-03-01_19.08.45.mlg — 1092 samples, 115 cranking, 0 running. Peak RPM 262. I = 9.2V / 5.3Ω = 1.74A < 2.0A pull-in threshold.
- **1.8Ω 25W wirewound ceramic resistor:** Arrived 2026-03-12. Pending installation.
- **Expected performance with 1.8Ω:** I_crank = 9.2V / 3.8Ω = 2.42A (+21% margin over 2.0A pull-in). I_running = 14.4V / 3.8Ω = 3.79A.
- **Installation:** Wire in series with injector signal (between Speeduino INJ1 output and injector). Mount on metal bracket with airflow (gets warm under load).
- **Tune change:** `injOpen` from 1.0ms → **1.1ms** (lower current = slower opening).
- **Precaution:** Charge battery fully before testing (alternator marginal at 12.8V). If battery cranking voltage drops below 7.6V, even 1.8Ω won't open injector.
- **Reference files:** DataLogs/ballast_resistor_engineering.py, DataLogs/analyze_mar1_performance.py

### 12. IAC Cranking Table — FIXED (2026-03-07)
- **Problem:** Cranking steps table was BACKWARDS — cranking steps were more closed than running steps at the same temperature, causing idle surge/hang after start
- **Analysis:** iac_volumetric_check.py — volumetric flow analysis showed cranking table direction was opposite to running OL table
- **Old values:** iacCrankSteps = 0 / 54 / 111 / 165 at bins -21 / 0 / 37 / 65°C
- **Fix:** iacCrankSteps = **0 / 0 / 54 / 141** at same bins
- **Logic:** Cold engine needs valve MORE open (lower step values) during cranking, not less

### 13. O2 Sensor Wiring — DIAGNOSED (2026-03-07/08)
- **Problem:** AFR pegged at 19.7 (sensor dead) — intermittent failure pattern
- **Root cause:** TinyWB heater 1A return current through thin Speeduino proto area GND trace (~0.2Ω) shifts signal voltage by ~1.5V → AFR reads 19.7 (max). Also: DB9 serial cable (~28AWG) used as sensor cable has loose/intermittent connections.
- **AFR History:**
  - Nov 19 - Dec 11, 2025: WORKING (95-100% normal readings)
  - Dec 20, 2025: DEAD (91.7% pegged at 19.7)
  - Feb 28, 2026: WORKING AGAIN (99-100% normal)
  - Mar 1: Slightly degraded (91% normal)
  - Mar 5-7: DEAD (97% pegged)
  - Mar 8: Partially working after rewiring (45% pegged, 45% normal) — intermittent connection
- **Fix in progress:** Replace DB9 cable with proper LSU 4.9 Bosch JPT 6-pin connector + 18 AWG wiring. Connect heater 12V to fuel pump relay output (safe — no thermal shock from 3s prime gap). GND to Speeduino screw terminal.
- **Reference files:** DataLogs/afr_history.py, DataLogs/analyze_mar8_wiring_test.py

### 14. Alternator Not Charging — ONGOING (2026-03-07)
- **Problem:** Battery voltage only 12.8V while running (alternator not charging)
- **Alternator:** SKGN-0320054, 65A
- **Mar 5:** 10.7V running (belt slipping badly)
- **Mar 7:** 12.8V avg, 13.1V max (belt fixed but still not charging properly)
- **Mar 8:** With LSU disconnected, voltage reached 14V — suggesting electrical load/wiring issue
- **Status:** Needs further investigation — check brushes, voltage regulator, and wiring

### 15. VE Table Low RPM Under Load — IDENTIFIED (2026-03-08)
- **Problem:** Engine bogs/stalls when releasing clutch at green lights. Feels like no power at clutch engagement point ("ponto de embraiagem"). Need 2000+ RPM to avoid stalling in 1st gear.
- **Cause:** VE table at 500-900 RPM / 76-100 kPa only gives 50-57% — too lean under load at low RPM.
- **Contributing factors:**
  - No IAC working → no dashpot function → no extra air during load transients
  - Butterfly screw provides fixed idle air only → can't compensate for sudden load
  - Original Pierburg 2E2 carb had accelerator pump + idle progression circuit that naturally enriched during clutch engagement
- **Fix needed:** Increase VE values at low RPM / high MAP (need O2 sensor working first for proper calibration). Temporary fix: open butterfly screw ¼ turn or open unused vacuum plug slightly.

### 16. Shifter Bushings — FIXED (2026-03-08)
- **Problem:** Could only select 3rd gear — shift rod bushings completely worn after 40+ years
- **Fix:** Replaced bushings — all gears now selectable, needs fine tuning
- **Parts:** Shift rod end bushing (VW 171 711 595A or equivalent), shift lever ball cup (VW 191 711 067)

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

### Current Board Status
- **DRV8825 history:** First module was **dead** (outputting 12V on all coil pins = passing VMOT through). Replaced with new module — outputs 1-5V = correct.
- **VREF potentiometer:** Set to **3V** (the higher of the two limit positions: 2V and 3V)
- **Module type:** Clone (not genuine TI)

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
12. **Don't route O2 heater current through Speeduino proto area GND** - The thin proto traces (~0.2Ω) can't handle the 1A heater return. This causes a voltage offset on the signal, making AFR read 19.7 (max). Use the screw terminal GND for heater return.
13. **Don't use DB9/serial cable for O2 sensor wiring** - Too thin (~28 AWG), pins corrode and lose contact, causes intermittent sensor failures. Use proper LSU 4.9 JPT connector with 18 AWG wiring.
14. **Don't connect TinyWB heater 12V to a source that cycles off during running** - Use fuel pump relay output (continuous while running) or ignition-switched power. The 3-second fuel pump prime gap does NOT cause thermal shock (sensor barely warm in 3s).
15. **Don't blindly increase VE at low RPM / high MAP** - The 500-900 RPM / 76-100 kPa zone needs correction (currently 50-57%, too lean), but wait for working O2 sensor data to calibrate correctly.

## O2 Sensor Wiring (TinyWB + LSU 4.9)

### TinyWB DIY-EFI Rev1 Pinout

**Left side (ECU connections):**
| Pin | Signal | Connect to |
|-----|--------|------------|
| 5V | Logic power | Speeduino 5V (proto area) |
| LIN | AFR signal (0-5V) | Speeduino O2 input (proto area) |
| TX | Serial (unused) | — |
| GND | Power & signal ground | Speeduino GND screw terminal |

**Right side (to LSU 4.9 via JPT 6-pin connector):**
| TinyWB Pin | JPT Pin | Color | Signal | Wire Gauge |
|------------|---------|-------|--------|------------|
| VM | 2 | Yellow | Virtual ground | 20 AWG |
| H- | 3 | White | Heater – (ground return, HIGH current) | 18 AWG |
| UN | 6 | Black | Nernst cell – | 20 AWG |
| IP | 1 | Red | Nernst cell + | 20 AWG |
| H+12V | 4 | Gray | Heater + (12V PWM) | 18 AWG |
| IA | 5 | Light Blue | Pump current – | 20 AWG |

### Power Connections
- **Heater 12V (H+):** Connect to **fuel pump relay output** (ignition-switched, turns off when key OFF, safe 3s prime gap doesn't cause thermal shock)
- **Heater GND (H-):** Returns through TinyWB board → GND pin → **Speeduino GND screw terminal**
- **Logic 5V:** Speeduino 5V proto area (low current, fine on thin traces)
- **Signal (LIN):** Speeduino O2 input proto area (low current, fine on thin traces)
- **Fuse:** 2A inline on heater 12V line

### LSU 4.9 Connector
- **Type:** Bosch JPT (Junior Power Timer) 6-pin
- **Bosch PN:** 1 928 404 617
- **VW equivalent:** 1J0 973 713
- **AliExpress search:** "LSU 4.9 connector" or "Bosch lambda sensor connector 6 pin"

### TinyWB Calibration
- 1.0V = AFR 9.7
- 4.0V = AFR 18.7

## ECU Enclosure & Connector Plan

### Current Setup
- Speeduino v0.4.4c on Arduino Mega — exposed board with screw terminals
- DB27 female connector on aluminum project box (too few pins, not sealed, wrong wire gauge)
- **Wiring reference:** `Speeduino Passat.xlsx` — contains full DB27 pin mapping, wire colors, stepper pin cross-reference, and sensor resistance tables
  - ⚠️ The "Tiny WB Pins" sheet has WRONG signal names (UN≠"Unregulated 12V", IP≠"Ignition Power", IA≠"Ignition Analog Output", VM≠"Voltage Monitor") — see O2 Sensor Wiring section for correct pinout

### Planned Upgrade
- **Enclosure:** Hammond 1590D (153×82×50mm internal) or similar aluminum box
- **Connector:** TE Ampseal 35-pin (776164-1 receptacle, 776231-1 plug)
- **Wire gauge:** All existing wires are 18 AWG — keep as-is. Only new dedicated injector 12V rail needs adding.
- **Panel mount:** Connector flanges from inside, 2× M3 screws, rectangular cutout 38.1×19.1mm

### Relay & Fuse Layout
```
BATTERY (+) ──→ ECU/INJ RELAY (coil: ign switch) ──→ FUSE ──→ ECU + Injector 12V
BATTERY (+) ──→ FUEL PUMP RELAY (coil: Speeduino GND-switch) ──→ FUSE ──→ Pump
                                                                      └→ 2A fuse ──→ O2 Heater
```
- **VW standard order:** Battery → Relay → Fuse → Load
- Fuel pump relay is ground-switched by Speeduino pin 16 (3s prime on power-up, then ON while running)
- O2 heater 12V taps from fuel pump relay output → **2A inline fuse** → TinyWB H+12V (protects TinyWB if LSU heater shorts)

**Why relays are REQUIRED for pump and fan:**
Speeduino outputs (pins 15, 16) use SSM3K357R MOSFETs in tiny SOT-23 packages. These switch **relay coils** (~150mA) to ground — they cannot drive motors directly.

| Load | Current Draw | SSM3K357R Capacity | Direct Drive? |
|------|-------------|-------------------|---------------|
| Relay coil | ~150-200 mA | ~3A (SOT-23 thermal limit ~500mA) | ✅ Fine |
| Fuel pump | 5-8 A | ~3A rating | ❌ Burns MOSFET |
| Radiator fan | 15-30 A | ~3A rating | ❌ Destroys MOSFET |

**Fan note:** The radiator already has an independent fan thermoswitch. Speeduino fan output (pin 15 / T35 pin 30) is optional — only needed for programmable fan control (e.g., turn on at a specific CLT or with A/C).

### Ampseal 35 Pin Assignment (Planned)

Designed with future scalability: ignition control (VIKA distributor), MPI conversion, turbo, launch control.

| T35 | Group | Function | Speeduino Pin | Old DB27 | AWG | Status |
|-----|-------|----------|---------------|----------|-----|--------|
| 1 | POWER | Main 12V (ign-switched) | — | 13 | 18 | CURRENT |
| 2 | POWER | Main GND #1 | 9,10 | 4,16 | 18 | CURRENT |
| 3 | POWER | Main GND #2 | 12 | 17 | 18 | CURRENT |
| 4 | POWER | Injector 12V rail | — | — | 18 | CURRENT 🆕 |
| 5 | POWER | O2 Heater 12V in | — | — | 18 | CURRENT |
| 6 | INJ | INJ1 signal | 1 | 1 | 18 | CURRENT |
| 7 | INJ | INJ2 signal | 2 | — | 18 | FUTURE MPI |
| 8 | INJ | INJ3 signal | 3 | — | 18 | FUTURE MPI |
| 9 | INJ | INJ4 signal | 5 | — | 18 | FUTURE MPI |
| 10 | IGN | IGN1 output | 7 | — | 18 | FUTURE IGN |
| 11 | IAC | Stepper 1A | 31 | 23 | 18 | CURRENT |
| 12 | IAC | Stepper 1B | 32 | 24 | 18 | CURRENT |
| 13 | IAC | Stepper 2A | 30 | 12 | 18 | CURRENT |
| 14 | IAC | Stepper 2B | 29 | 11 | 18 | CURRENT |
| 15 | SENSOR | CLT signal | 19 | 19 | 18 | CURRENT |
| 16 | SENSOR | IAT signal | 20 | 7 | 18 | CURRENT |
| 17 | SENSOR | TPS signal | 22 | 8 | 18 | CURRENT |
| 18 | SENSOR | Sensor 5V | 13,28 | 5,10 | 18 | CURRENT |
| 19 | SENSOR | Sensor GND (shared CLT+IAT+TPS) | 23 | 21 | 18 | CURRENT |
| 20 | TRIGGER | Trigger signal (Hall) | 25 | 22 | 18 | CURRENT |
| 21 | TRIGGER | Trigger 5V | 28 | 10 | 18 | CURRENT |
| 22 | TRIGGER | Trigger GND (separate wire) | 23 | 21 | 18 | CURRENT |
| 23 | LSU | LSU IP (Nernst+, JPT 1) | TinyWB IP | — | 18 | CURRENT |
| 24 | LSU | LSU VM (Virtual GND, JPT 2) | TinyWB VM | — | 18 | CURRENT |
| 25 | LSU | LSU H- (Heater return, JPT 3) | TinyWB H- | — | 18 | CURRENT |
| 26 | LSU | LSU H+ (Heater PWM, JPT 4) | TinyWB H+ | — | 18 | CURRENT |
| 27 | LSU | LSU IA (Pump current-, JPT 5) | TinyWB IA | — | 18 | CURRENT |
| 28 | LSU | LSU UN (Nernst-, JPT 6) | TinyWB UN | — | 18 | CURRENT |
| 29 | OUTPUT | Fuel pump relay drive | 16 | 6 | 18 | CURRENT |
| 30 | OUTPUT | Fan relay drive | 15 | 18 | 18 | CURRENT |
| 31 | OUTPUT | Boost solenoid | 35 | — | 18 | FUTURE TURBO |
| 32 | INPUT | Clutch switch | 18 | — | 18 | FUTURE |
| 33 | SPARE | Spare / Flex fuel | 14 | — | 18 | SPARE |
| 34 | SPARE | Spare / Tacho (optional) | 17 | — | 18 | SPARE |
| 35 | SPARE | Spare | — | — | 18 | SPARE |

**Pin count by group:** POWER 5 + INJ 4 + IGN 1 + IAC 4 + SENSOR 5 + TRIGGER 3 + LSU 6 + OUTPUT 2 + FUTURE 2 + SPARE 3 = **35**

**What needs to change from current DB27 harness:**
- **🆕 NEW WIRE:** T35 pin 4 — dedicated injector 12V rail (separates injector power from ECU power)
- **🆕 ADD:** 2A inline fuse on O2 heater 12V line (protects TinyWB)
- All other wires: **keep existing 18 AWG and colors** — just re-terminate from DB27 crimps to Ampseal crimps

**Scalability notes:**
- **MPI conversion:** Wire INJ2-4 (T35 pins 7-9) to new injectors. Change TunerStudio to "Semi-Sequential" or "Sequential" injection mode. INJ 12V rail (pin 4) splits to all 4 injectors on engine side.
- **Ignition control:** Wire IGN1 (T35 pin 10) to Bosch Module 124 input. Install VIKA 99050306801 distributor (no mechanical advance). Enable Speeduino ignition in TunerStudio.
- **Turbo:** Wire boost solenoid (T35 pin 31) to wastegate actuator or boost control valve. MAP sensor is onboard Speeduino (no extra pin needed). Tune boost table in TunerStudio.
- **Launch control:** Wire clutch switch (T35 pin 32) to normally-open switch on clutch pedal. Configure launch control RPM limit in TunerStudio. Also useful for anti-stall (increase idle when clutch pressed in gear).
- **Flex fuel (E85):** Wire flex fuel sensor (T35 pin 33) to GM-style flex sensor. Proto Area 1 input on Speeduino.

**Full pinout with wire colors in `Speeduino Passat.xlsx` → "Ampseal T35" sheet**

### Where to Buy (Portugal)
- **Mouser:** mouser.pt — 571-776164-1 (receptacle), 571-776231-1 (plug), 571-770680-1 (crimp pins)
- **TME:** tme.eu/pt — Search "Ampseal 776164"
- **AliExpress:** Search "Ampseal 35 pin connector kit" (cheapest, 2-3 weeks)

## User & Environment

- **Language:** Portuguese (car is in Portugal)
- **TunerStudio version:** MegaSquirt (MS) 3.3.01
- **Node.js:** v24.13.0 (available in PATH)
- **Python:** 3.14 — installed at `C:\Users\User1\AppData\Local\Programs\Python\Python314` but **NOT in system PATH**. Use full path or `python3` alias.
- **MLG conversion:** `npx mlg-converter --format=csv <file>.mlg`

## Useful References

- TunerStudio project: `C:\Users\User1\Documents\TunerStudioProjects\Passat2025\`
- Current tune: `CurrentTune.msq`
- Datalogs: `DataLogs\` folder
- Speeduino Wiki: https://wiki.speeduino.com/
- GitHub Repository: https://github.com/TakumiPT/passat-b2-speeduino (private)
