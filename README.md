# VW Passat B2 1.6 DT — Speeduino EFI Conversion

**Carburetor-to-EFI conversion** of a 1984 VW Passat B2 (Santana/Quantum) with the **1.6L DT engine** (EA827 family), using a **Speeduino v0.4.4c** ECU and a **Brazilian Gol G2 SPI Monopoint** throttle body.

> Also applicable to: **Golf 2 / Jetta 2** (same EA827 block), Passat B2 Santana, VW Quantum, and any air-cooled-to-water-cooled EA827 swap using TBI injection with a low-impedance injector.

---

## Table of Contents

- [Project Status](#project-status)
- [Hardware](#hardware)
- [Why This Exists](#why-this-exists)
- [The Injector Current Problem](#the-injector-current-problem)
- [Ballast Resistor Engineering](#ballast-resistor-engineering)
- [Test Results (2026-03-01)](#test-results-2026-03-01--historical)
- [Latest Findings Snapshot](#latest-findings-snapshot)
- [Tune Configuration](#tune-configuration)
- [Current Active Problems](#current-active-problems-2026-07-26)
- [Known Issues & Fixes](#known-issues--fixes)
- [Repository Structure](#repository-structure)
- [Working with Datalogs](#working-with-datalogs)
- [Future Plans](#future-plans)
- [References](#references)

---

## Latest Findings Snapshot

A dedicated findings snapshot for the current diagnosis state was created on **2026-08-09** in `INVESTIGATION_FINDINGS_2026-08-09.md`.

## Project Status

| Milestone | Status |
|-----------|--------|
| Pierburg 2E2 carburetor removed | ✅ Done |
| Gol G2 TBI throttle body mounted | ✅ Done |
| Speeduino v0.4.4c wired (fuel only) | ✅ Done |
| Engine starts and runs on EFI | ✅ Done (2026-03-01) |
| VE table baseline tuned | 🔧 In progress (shape good, WOT ~30% lean) |
| WUE (warmup enrichment) calibrated | 🔧 In progress |
| Ballast resistor installed (injector protection) | ✅ Done (1.8Ω 25W) |
| Wideband O2 (LSU 4.9 + TinyWB) working | 🔴 Broken (pin 6 JPT contact fault) |
| IAC stepper moving | 🔴 Not moving (diagnostic in progress) |
| TPS calibrated | 🔴 Needs recalibration (span 117 ADC) |
| AE (accel enrichment) calibrated | 🔴 Below backfire threshold |
| IPO inspection passed | ⏳ Pending |
| VIKA electronic distributor installed | ⏳ After IPO |
| Speeduino ignition control enabled | ⏳ After distributor swap |
| Peak-and-Hold injector driver built | ⏳ Long-term |

---

## Hardware

### Engine

| Parameter | Value |
|-----------|-------|
| Vehicle | VW Passat B2 (Type 32B), 1984 |
| Engine code | **DT** (EA827 family) |
| Displacement | 1595 cc (81mm bore × 77.4mm stroke) |
| Compression ratio | 9.0:1 |
| Power | 55 kW (75 PS) @ 5000 RPM |
| Torque | 125 N·m @ 2500 RPM |
| Valvetrain | SOHC 8V, **hydraulic lifters** |
| Original fuel system | Pierburg 2E2 carburetor (removed) |
| Ignition | Mechanical distributor + Bosch Module 124 (TCI) |
| Fuel | 95 RON gasoline |

### EFI System

| Component | Part | Notes |
|-----------|------|-------|
| ECU | Speeduino v0.4.4c SMD | [diy-efi.co.uk](https://diy-efi.co.uk), firmware 2025.01.6 |
| Throttle body | VW Gol G2 SPI Monopoint | Single-point injection above throttle plate |
| Injector | **Magneti Marelli IWM500.01** (GREEN) | 2Ω low-impedance, single injector feeds all 4 cylinders |
| Fuel pump | Electric, 3 bar | In-tank or inline |
| Fuel pressure | 1.0–1.5 bar | Regulated by TBI built-in FPR |
| IAC valve | Bosch 0269980492 | 4-wire bipolar stepper, 165 steps, inverted operation |
| MAP sensor | MPX4250AP | Onboard Speeduino |
| CLT sensor | **Bosch NTC** (unknown part#) | In coolant flange VW 026.121.133.9 (top, M10×1). To be replaced by **MTE-Thomson 4053** (2055Ω NTC) in bottom (M12×1.5) |
| Gauge sender | Facet 7.3073 (back of head) | **MTE-Thomson 3018** (= VW 027 919 501) purchased — goes in top (M10×1) |
| Trigger | Hall sensor in distributor | "Basic Distributor" pattern |

### Injector Details

The **IWM500.01** is a Brazilian-market SPI injector used in VW Gol, Parati, Saveiro, Fiat Palio, Ford Escort, and Renault 19 (1994–1999). It was originally driven by **Magneti Marelli 1AVB** or **Bosch Mono-Motronic** ECUs using peak-and-hold current control.

| Parameter | Value |
|-----------|-------|
| Part numbers | IWM500.01 / IWM50001 / 501.002.02 |
| Coil resistance | **2Ω** (measured) |
| Flow @ 1.0 bar | ~34 lb/hr (250–260 cc/min) |
| Flow @ 3.0 bar | ~60 lb/hr (450–500 cc/min) |
| Color variant | GREEN (1.6–1.8L engines) |
| Drive method (original) | Peak-and-hold: ~4A peak → 1.2A hold (PWM) |
| Drive method (current) | Direct: 7A continuous through VNLD5090-E |

> **Ballast resistor installed:** 1.8Ω / 25W wirewound in series with injector. `injOpen` should be 1.1ms (currently 1.2ms in tune — see Known Issues P8).

> **Single injector for 4 cylinders.** Do not compare flow rates with MPI injectors. VE values above 100% are normal and expected.

### Speeduino Board — Injector Driver

The v0.4.4c board uses **STMicroelectronics VNLD5090-E** smart low-side drivers (not bare MOSFETs):

- Rated for **13A** per channel — the 7A injector current is 54% of capacity
- Built-in overcurrent limiting, thermal shutdown (auto-restart), ESD, overvoltage clamp
- **The Speeduino board is NOT at risk.** The VNLD5090-E handles 7A with ample margin.
- The concern is **injector coil longevity**, not board damage.

### Coolant System Sensors

The original Passat B2 coolant flange (**VW 026.121.133.9**, right side of cylinder head) had 2 thermoswitches (**035 919 369 C** top/M10 + **026 919 369** bottom) for the Pierburg 2E2 carb cold-start circuit.

| Position | Thread | Original | Current | Planned |
|----------|--------|----------|---------|----------|
| Top | M10×1 | 035 919 369 C (removed) | **Bosch NTC** (unknown part#) → Speeduino CLT | **MTE-Thomson 3018** (= VW 027 919 501) — dashboard gauge sender |
| Bottom | M12×1.5 | 026 919 369 | Still installed (original) | **MTE-Thomson 4053** (= VW 026 906 161 B / HELLA 6PT 009 309-291, 2055Ω@25°C) — ECU sensor → Speeduino CLT |
| Back of head | — | Facet 7.3073 | Dashboard gauge sender | Redundant when 3018 installed in top |

> **Fitment confirmed** (owner-tested 2026-03-03): 3018 fits top (M10×1), 4053 fits bottom (M12×1.5). Both sensors purchased — no additional purchase needed.
>
> **Manifold heater:** The electric heater under the intake manifold is **dead** — the top thermoswitch (035 919 369 C) was replaced by the Bosch NTC sensor, breaking the heater circuit. Higher ASE values compensate for cold manifold fuel condensation.
>
> **Calibration:** HELLA 6PT 009 309-291 (equivalent of 4053) datasheet provides resistance values: **2055Ω @ 25°C**, **327Ω @ 80°C** (verified on Spareto + ak24parts). TunerStudio 3-point calibration: 0°C=6057Ω (calculated), 25°C=2055Ω, 80°C=327Ω. See [.github/copilot-instructions.md](.github/copilot-instructions.md) for full details.

---

## Why This Exists

The Pierburg 2E2 is a complex vacuum-operated carburetor with:
- Automatic choke (electric heating element)
- Pull-down diaphragm with vacuum reservoir
- Idle cut-off solenoid
- Overrun fuel cut valve
- Enrichment jet with temperature-sensitive vacuum delay

When these components age (40+ years), the carburetor becomes unreliable. Finding replacement diaphragms, gaskets, and adjustment tools is increasingly difficult.

**The Gol G2 SPI throttle body** is a direct bolt-on replacement concept:
- Same manifold flange pattern (or simple adapter)
- Single injector into a mixing chamber — fuel distribution through the manifold just like a carb
- Much simpler than MPI conversion (no injector bungs, no fuel rail, no individual runners)
- Thousands were produced for the Brazilian market — parts are available and cheap

---

## The Injector Current Problem

The IWM500.01 was designed for **peak-and-hold drive** (4A peak, 1.2A hold). Speeduino drives it at **7A continuous** through the entire pulse width.

### What breaks?

**The INJECTOR — not the board.** The Speeduino VNLD5090-E is rated for 13A and has built-in protection. But the injector coil dissipates:

$$P_{coil} = I^2 \times R = 7^2 \times 2 = 98\text{W (instantaneous)}$$

At the original 1.2A hold: $P = 1.2^2 \times 2 = 2.9\text{W}$ — a 34× difference.

| Condition | Duty Cycle | Avg Coil Power | Risk |
|-----------|-----------|---------------|------|
| Idle (800 RPM) | 2–5% | 2–5W | LOW |
| Cruise (2500 RPM) | 8–12% | 8–12W | MODERATE |
| WOT (5000 RPM) | 40–50% | 40–50W | **HIGH** |

The injector fails **gradually**: coil insulation softens → shorted turns → impedance drops → current increases → thermal runaway → open circuit.

### Solutions (in order of complexity)

| Solution | Hold Current | Coil Power | Tune Change | Complexity |
|----------|-------------|-----------|------------|-----------|
| **1.8Ω ballast resistor** | 3.8A | 28.7W | injOpen +0.1ms | Wire one resistor |
| **Peak-and-Hold circuit** | 1.2A | 2.9W | None | Build PCB (see `peak_and_hold/`) |
| **Do nothing** (current) | 7.0A | 98W | None | — |

---

## Ballast Resistor Engineering

### Why 3.3Ω failed (tested 2026-03-01)

The 3.3Ω resistor was tested and the engine **did not start**. This is not a tuning issue — it's Ohm's law:

$$I_{steady} = \frac{V}{R_{total}} = \frac{V}{R_{inj} + R_{ballast}} = \frac{9.0\text{V}}{2.0 + 3.3} = 1.70\text{A}$$

The IWM500.01 needs approximately **2.0A** to overcome the return spring and fuel pressure ($I_{pull\text{-}in}$). At 9.0V cranking voltage, the 3.3Ω limits current to 1.70A — **below the pull-in threshold**. The injector physically cannot open. No amount of `injOpen` time adjustment can fix this because the steady-state current never reaches the required value:

$$I_{max}(t \to \infty) = \frac{V}{R} = \frac{9.0}{5.3} = 1.70\text{A} < 2.0\text{A}$$

The minimum battery voltage to open the injector with 3.3Ω: $V_{min} = I_{pull} \times R_{total} = 2.0 \times 5.3 = 10.6\text{V}$. Cranking voltage never reaches 10.6V.

> `injOpen` compensates for **slow** opening (the injector does eventually open, just takes longer). It cannot compensate for **no** opening (the current never reaches the pull-in threshold). This is a critical distinction.

### What `injOpen` can and cannot fix

| Situation | `injOpen` helps? | Why |
|-----------|-----------------|-----|
| Resistor makes injector open **slower** | ✅ Yes | Compensates for the delay |
| Resistor prevents injector from opening **at all** | ❌ No | $I_{steady} < I_{pull\text{-}in}$ — impossible |

### Complete resistor evaluation

Design constraints:
- **A)** $I_{steady}(V_{crank\text{-}min}) \geq 2.0\text{A}$ — injector MUST open during cranking
- **B)** $I_{steady}(V_{run\text{-}high}) \leq 4.0\text{A}$ — injector coil must not overheat
- **C)** Standard wirewound power resistor values
- **D)** Power rating ≥ peak dissipation

| R_ballast | R_total | I @ 8.5V | I @ 14.4V | Opens at crank? | Coil power | Verdict |
|-----------|---------|----------|-----------|-----------------|-----------|---------|
| 0Ω (none) | 2.0Ω | 4.25A | 7.20A | ✅ | 103.7W | ⚠️ Coil overheats |
| 1.0Ω | 3.0Ω | 2.83A | 4.80A | ✅ | 46.1W | ⚠️ Still too hot |
| 1.5Ω | 3.5Ω | 2.43A | 4.11A | ✅ | 33.9W | Acceptable (alt.) |
| **1.8Ω** | **3.8Ω** | **2.24A** | **3.79A** | **✅** | **28.7W** | **✅ Recommended** |
| 2.2Ω | 4.2Ω | 2.02A | 3.43A | ⚠️ Marginal | 23.5W | Tight start margin |
| 2.7Ω | 4.7Ω | 1.81A | 3.06A | ❌ | 18.8W | No start |
| 3.3Ω | 5.3Ω | 1.60A | 2.72A | ❌ | 14.8W | No start (tested) |

### Recommended: 1.8Ω / 25W wirewound

$$I_{crank} = \frac{8.5\text{V}}{3.8\Omega} = 2.24\text{A} \quad (+12\% \text{ above pull-in})$$

$$I_{run} = \frac{14.4\text{V}}{3.8\Omega} = 3.79\text{A} \quad (47\% \text{ reduction vs no resistor})$$

| Parameter | Without resistor | With 1.8Ω | Improvement |
|-----------|-----------------|-----------|-------------|
| Hold current @ 14.4V | 7.20A | 3.79A | −47% |
| Coil power @ 14.4V | 103.7W | 28.7W | −72% |
| `injOpen` setting | 1.0ms | ~1.1ms | +0.1ms |
| VE / reqFuel changes | — | None | — |
| Start at 8.5V | ✅ (4.25A) | ✅ (2.24A) | — |

**Specification:** 1.8Ω ±5%, 25W minimum, **wirewound ceramic** (Vishay RS, Ohmite OY, or TE CGS series — NOT carbon film, which will burn at 26W peak).

### Why not other values?

- **1.0Ω:** Current at 14.4V = 4.80A — still too much heat ($P_{coil} = 46\text{W}$)
- **1.5Ω:** Works, but current at 14.4V = 4.11A — slightly above 4A target. Use if 1.8Ω unavailable.
- **2.2Ω:** Current at 8.5V = 2.02A — only 1% above pull-in. Will fail on cold mornings (weaker battery → lower cranking voltage).
- **3.3Ω:** Proven failure at cranking voltage (MLG2 data). $I_{steady} = 1.70\text{A} < 2.0\text{A}$.

### Implementation procedure

1. **First:** Get the baseline tune right without resistor (current priority — engine runs, but AFR needs work)
2. **Then:** Wire 1.8Ω 25W wirewound in series with injector ground wire
3. **Adjust:** `injOpen` from 1.0ms → 1.1ms in TunerStudio (starting point)
4. **Fine-tune** `injOpen` by logging AFR during tip-in transients (lean spike = increase, rich spike = decrease)
5. **Verify:** Cold start (CLT ≤ 30°C) and warm restart (CLT ~50°C — where 3.3Ω failed)

---

## Test Results (2026-03-01) — Historical

> Newer datalogs exist in `DataLogs/` (2026-05-24 through 2026-07-25). Latest analysis: 2026-07-25 — wideband pin 6 fault confirmed (79.3% pegged, 195 transitions in 96s).

Two test sessions were logged consecutively.

### MLG1 — Baseline: No resistor, corrected voltage table

**Result: Engine STARTED and ran for 158 seconds. User turned key off (not a stall).**

| Metric | Value | Assessment |
|--------|-------|-----------|
| Records | 2834 (16 cranking, 2367 running) | — |
| Avg running AFR | 14.3 | ✅ Near stoichiometric |
| AFR < 13.5 (rich) | 61% | Expected during warmup |
| AFR 13.5–15.5 (good) | 12% | Needs improvement |
| AFR > 15.5 (lean) | 26% | ⚠️ Lean at CLT 40–50°C |
| Idle RPM | avg 911 (σ = 60) | ⚠️ Poor stability |
| Max RPM | 1528 | Idle only, no driving |
| Sync losses | 0 | ✅ Trigger solid |
| Duty cycle | 5–12% | ✅ Safe for injector |
| Engine stop | User turned key OFF at CLT 47°C | ✅ Not a stall — intentional shutdown |

**AFR warmup progression:**

| Time Window | AFR | CLT | Gwarm (WUE) |
|------------|-----|-----|-------------|
| 0–15s | 17.2 (lean) | 26°C | 151% |
| 15–45s | 12.7–13.7 | 27–29°C | 149–151% |
| 45–105s | 12.6–13.0 | 31–39°C | 136–146% |
| 105–150s | 15.6–18.9 (lean!) | 43–45°C | 129–131% |
| Key OFF | — | 47°C | ~127% |

**Diagnosis:** Engine was running fine at CLT 46–47°C. User intentionally turned ignition off (proven by stable RPM + sharp battery voltage drop 12.8→6.8V in 0.1s). No WUE issue at this temperature. The VE table for hot idle (~80°C+) has not been tuned yet because the engine hasn't reached operating temperature in any datalog so far.

### MLG2 — With 3.3Ω resistor

**Result: Engine DID NOT START. Zero fuel delivery.**

| Metric | Value | Assessment |
|--------|-------|-----------|
| Records | 1092 (115 cranking, 0 running) | — |
| Peak RPM | 262 | Cranking only |
| Avg cranking AFR | 18.5 | Pure air — no combustion |
| AFR trend | 16.3 → 19.7 (rising) | Residual fuel evaporating |
| Battery V cranking | 2.8–10.2V (avg 9.2V) | — |
| PW commanded | avg 4.6ms | ECU working correctly |
| CLT | 49°C | Warm from MLG1 run |

**Root cause:** $I = 9.2\text{V} / 5.3\Omega = 1.74\text{A} < 2.0\text{A}$ pull-in. Injector physically stuck closed. See [Ballast Resistor Engineering](#ballast-resistor-engineering) for full analysis.

The rising AFR (16.3 → 19.7) confirms zero fuel delivery — the O2 sensor is reading residual fuel vapors from MLG1 evaporating, with pure air replacing it.

---

## Tune Configuration

### Key Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| reqFuel | Per engine calculator | 1595cc, 1 injector, ~60 lb/hr @ 3 bar |
| injOpen | 1.0 ms | Increase to ~1.1ms with 1.8Ω resistor |
| Cranking RPM | 400 | Below this = cranking enrichment active |
| Algorithm | Speed Density (MAP) | — |
| Trigger | Basic Distributor, Falling edge | VW Hall sensor |
| hardRevLim | 6200 RPM | Hydraulic lifters limit |
| SoftRevLim | 6000 RPM | Inactive until Speeduino controls ignition |
| DFCO | **OFF** | Dangerous with mechanical distributor — see below |
| IAC algorithm | None | Butterfly bypass screw handles idle air |

### Voltage Correction Table (injBatRates)

Compensates for injector opening speed at different battery voltages:

| Voltage | 6.6V | 9.4V | 12.1V | 14.8V | 16.9V | 20.3V |
|---------|------|------|-------|-------|-------|-------|
| Correction | 255% | 176% | 127% | 100% | 86% | 70% |

### Why DFCO must stay OFF

With a **mechanical distributor**, deceleration creates high manifold vacuum (20–25 kPa). The mechanical advance responds by advancing timing to 35–40° BTDC. When DFCO restores fuel after the cut period, combustion occurs with extreme advance + lean mixture = **intake backfire risk**. Only enable after installing the VIKA electronic distributor with Speeduino ignition control.

---

## Current Active Problems (2026-07-30)

| # | Problem | Impact | Next Action |
|---|---------|--------|-------------|
| P1 | Wideband pin 6 contact fault — AFR pegged 17–19 across ALL cells | Blocks ALL VE/AFR-based tuning | Install JPT 2.8mm terminals |
| P2 | IAC stepper not moving | No idle air control | Multimeter diagnostic (Vref, sleep/reset, VMOT, continuity) |
| P3 | Cold start fails after days parked | Needs brake cleaner OR fresh gasoline spray on butterfly | **Apply new priming (9/7/6/4 ms) + cranking enrich (300/260/240/230 %)** in TS + Burn |
| P4 | Dies on fast throttle stab | Dangerous stall | Apply AE fix (after cable/TPS fix) |
| P5 | VE table can't be autotuned (WB unreliable) + WOT never reached | High-load cells untested | Freeze VE map. Fix P1 + P6 first, then autotune. |
| P6 | **Pedal only reaches ~60 % of butterfly travel** (cable slack / adjustment) | Engine never at WOT; TPS-thresholded logic (tpsflood, egoTPSMax, iacTPSlimit) unreachable; ~30–40 % power loss | Adjust throttle cable at TBI adjuster; then recalibrate TPS at full pedal |
| P7 | CTPSEnabled floating input | Cosmetic | Set Off |
| P8 | injOpen 1.2ms (should be 1.1ms) | Idle/cruise rich | Change to 1.1ms |

### Cold-start (P3) — 2026-07-30 diagnosis

Symptom: after ~1 week parked, engine won't start. A small brake-cleaner spray, or a squirt of fresh gasoline directly on the butterfly, makes it fire immediately. Once running (hot), the car drives fine.

Root cause: TBI cold-crank fuelling too weak. At summer ambient (~30–40 °C engine) the priming pulse interpolates to only ~4.5 ms — after subtracting `injOpen` 1.2 ms, that's ~3.3 ms of actual injection to wet a single-injector butterfly feeding 1600 cc. Cranking enrichment (200 % at 70 °C) is Speeduino's default for port injection and is slightly lean for TBI.

Ruled out: bleed-down (user waits for prime pump to finish before cranking), ignition (brake cleaner proves spark works), fuel pressure (car drives fine hot), injector/driver/ballast (running-state OK).

Recommended changes (user applies via TunerStudio + Burn — never edit `CurrentTune.msq` directly):

| Table | Old values | New values |
|---|---|---|
| `primePulse` (ms) at -20/0/40/82 °C | 8.0 / 6.0 / 4.0 / 2.5 | **9.0 / 7.0 / 6.0 / 4.0** |
| `crankingEnrichValues` (%) at -40/0/30/70 °C | 280 / 230 / 210 / 200 | **300 / 260 / 240 / 230** |

Keep untouched: `injOpen`=1.2 ms, `reqFuel`=4.3 ms, `crankingPct`=20 %, `primingDelay`=2.0 s.

### Pedal-only-60 % (P6) — 2026-07-30 discovery

User recalibrated TPS at the TBI (butterfly closed=0 %, fully open=100 %). Then discovered pushing the pedal to the floor only rotates the butterfly to ~60 % of its full travel.

Consequences:
- **The engine has never physically been at WOT.** All prior "WOT" analysis was on a partially open butterfly.
- Every datalog with `TPS = 100 %` (recorded before the butterfly-based recalibration) actually meant ~60 % butterfly.
- `tpsflood`=80, `egoTPSMax`=70, `iacTPSlimit`=90 → all unreachable.
- AE (TPS-based) under-measures throttle-DOT by 1.67×.
- MAP-based fuel and ignition (both algorithms = MAP) are unaffected → cruise VE analysis up to ~70 kPa remains valid.

Fix at the throttle cable adjuster on the TBI end: loosen jam nuts → helper presses pedal to floor → adjust so butterfly lever just reaches its mechanical stop → back off ~1 turn (so idle TPS stays at 0 %) → retighten. Then recalibrate TPS in TS (pedal fully pressed = 100 %).

### VE table (page 1) — 2026-07-30 review

- Shape is structurally OK: hand-crafted, monotonic, peak 94 % at 5000 RPM (correct for `reqFuel` computed at 3.0 bar vs actual rail 1.2 bar → VE < 100 % expected).
- July 2026 datalog binning (5390 warm-running samples): every visited RPM/MAP cell reads AFR 17.5–19.7 vs target 14.7 = fake −20 to −38 % lean. This is the P1 wideband fault, not real leanness. **DO NOT run VEAnalyze — it would raise every visited cell +30 % and flood the engine.**
- The VE map is frozen until P1 (wideband) and P6 (cable/pedal) are resolved.

See [DOCUMENTACAO_REVISAO_TUNE_2026-06-10.md](DOCUMENTACAO_REVISAO_TUNE_2026-06-10.md) for the older full tune review.

---

## Known Issues & Fixes

| # | Issue | Status | Fix |
|---|-------|--------|-----|
| P1 | Wideband AFR pegged 19.7 ~80% (pin 6 JPT terminal no grip) | 🔴 Open | JPT 2.8mm female crimp terminals ordered |
| P2 | IAC stepper not moving (replaced motor + DRV8825) | 🔴 Open | Diagnostic: Vref, nSLEEP/nRESET, VMOT, coil continuity |
| P3 | Cold start fails after long parking (needs brake cleaner / fresh gasoline squirt on butterfly) | 🔴 Open | Apply primePulse 9/7/6/4 ms + crankingEnrich 300/260/240/230 % in TS + Burn |
| P4 | Dies on fast throttle stab (transient bog/stall) | 🔴 Open | AE fix: taeRates 110/210/330/380, taeThresh 25, aeTime 450 |
| P5 | VE table can't be autotuned yet (WB unreliable) + WOT never physically reached | 🔴 Blocked | Freeze VE. Fix P1 (WB) + P6 (cable) first, then autotune. |
| P6 | **Pedal only reaches ~60 % butterfly travel** (cable adjustment). Engine never at WOT. | 🔴 Open | Adjust throttle cable at TBI; then recalibrate TPS with pedal at floor = 100 % |
| P7 | CTPSEnabled=On with no CTPS wired (floating input) | 🟡 Open | Set Off |
| P8 | injOpen=1.2ms, should be 1.1ms (ballast 1.8Ω approved) | 🟡 Open | Change to 1.1ms |
| 1 | VE table too lean at idle (68%) | ✅ Fixed | Increased to 125% at 100kPa/500RPM |
| 2 | IAC closed-loop max was 54 (should be 162) | ✅ Fixed | Changed to 162 (98% of 165 physical limit) |
| 3 | Rev limiter too high (7000 RPM) | ✅ Fixed | Set to 6200 RPM (hydraulic lifters) |
| 4 | Hot idle rich (AFR 12.5–12.8 vs target 14.7) | ✅ Fixed | 5 VE cells corrected at hot idle |
| 5 | Cold running lean (AFR 16–17.6 at 28–50°C) | ✅ Fixed | WUE bins increased by 4–17% |
| 6 | Voltage correction flat (98–110%) | ✅ Fixed | Corrected to 70–255% range |
| 7 | 3.3Ω resistor prevents start | ✅ Superseded | 1.8Ω installed (see analysis above) |
| 8 | Apparent lean stall at CLT 40–50°C | ✅ Resolved | Not a stall — user turned key off intentionally |
| 9 | Poor idle stability (σ=60 RPM) | 🔧 Open | Needs IAC or butterfly adjustment |
| 10 | No hot running data (CLT 80°C+) | 🔧 Open | Need longer datalog |
| 11 | ASE too low for cold start (AFR 17 at 26°C) | 🔧 Open | Change asePct to 155/151/101/30 |
| 12 | Intake manifold heater dead | ℹ️ Known | Top thermoswitch 035 919 369 C replaced by Bosch NTC; ASE compensates |

---

## Repository Structure

```
├── CurrentTune.msq              # Active TunerStudio tune file
├── Current.table                # VE table export
├── ia.table                     # Ignition advance table export
├── .github/
│   └── copilot-instructions.md  # Full technical reference for AI assistants
├── dashboard/                   # TunerStudio dashboard layouts
│   ├── dashboard.dash           # Main dashboard
│   ├── veTable1Map.dash         # VE map view
│   ├── afrTable1Map.dash        # AFR target map
│   └── ...
├── DataLogs/                    # MLG datalogs + CSV conversions + analysis
│   ├── *.mlg                    # TunerStudio binary datalogs
│   ├── *.csv                    # Converted CSV (semicolon-delimited)
│   ├── *.json                   # Converted JSON (with field metadata)
│   ├── analyze_*.py             # Python analysis scripts
│   └── ballast_resistor_engineering.py  # Complete resistor analysis
├── peak_and_hold/               # Peak-and-hold injector driver
│   ├── peak_and_hold_1ch.ino    # Arduino firmware (ATtiny85)
│   └── README.md                # P&H circuit design & schematic
├── projectCfg/                  # TunerStudio project configuration
├── restorePoints/               # TunerStudio auto-saved tune backups
└── TuneView/                    # TunerStudio view layouts
```

---

## Working with Datalogs

### Converting MLG to CSV/JSON

TunerStudio saves datalogs in `.mlg` binary format. Convert with:

```bash
# Install once
npm install -g mlg-converter

# Convert to CSV (semicolon-delimited)
npx mlg-converter --format=csv 2026-03-01_19.05.30.mlg

# Convert to JSON (includes field metadata with scale factors)
npx mlg-converter --format=json 2026-03-01_19.05.30.mlg
```

### JSON scale factors

JSON stores raw integer values. Apply these scales:

| Field | Scale | Example |
|-------|-------|---------|
| AFR | ×0.1 | raw 149 → 14.9 |
| Battery V | ×0.1 | raw 91 → 9.1V |
| PW | ×0.001 | raw 5190 → 5.190ms |
| TPS | ×0.5 | raw 14 → 7.0% |
| Accel Enrich | ×2.0 | raw 50 → 100% |
| Dwell | ×0.001 | raw 3000 → 3.0ms |
| RPM, MAP, CLT, IAT, VE | ×1.0 | No scaling needed |

### Running analysis scripts

```bash
cd DataLogs

# Requires Python 3.x
py analyze_mar1_performance.py      # Performance analysis of March 1 test
py ballast_resistor_engineering.py  # Complete resistor calculations
```

---

## Future Plans

### Phase 1: Fix Now (no wideband needed)
- IAC diagnostic: measure Vref (0.35V), nSLEEP/nRESET (5V), VMOT (12V), coil continuity
- TPS recalibration: by hand at TBI, get true tpsMin/tpsMax ADC values
- Battery test: 75Ah swap or charge 45Ah fully
- Fresh gasoline if car sat >2 weeks
- injOpen 1.2 → 1.1ms (ballast 1.8Ω approved value)
- AE fix: taeRates 110/210/330/380, taeThresh 25, aeTime 450ms (after TPS recalibration)
- VE 500 RPM cells: 89→72, 87→70, 81→68
- CTPSEnabled → Off

### Phase 2: After Wideband Fixed (pin 6 JPT terminals)
- Clean datalog → verify AFR live
- Enable closed-loop (egoLimit 5-7%, not 15%)
- WOT pull (2nd/3rd gear, 2000→6000 RPM) → scale VE 86-100kPa to ~125-135%
- Fine AE tuning with AFR feedback
- Re-check injector duty at WOT (thermal constraint)

### Phase 3: IPO Inspection
- Pass Portuguese vehicle inspection
- Document emissions readings

### Phase 4: Electronic Distributor (VIKA 99050306801)
- Replace mechanical distributor (with vacuum + centrifugal advance)
- Install VIKA electronic distributor (Hall sensor only, no mechanical advance)
- Enable Speeduino ignition control
- Wire Speeduino IGN1 → Bosch Module 124 input
- Calibrate trigger angle with timing light
- Enable DFCO (safe with electronic timing control)

### Phase 5: Peak-and-Hold Driver
- Build P&H circuit from `peak_and_hold/` design
- 7A peak (1.5ms) → 1.2A hold (PWM)
- Remove ballast resistor
- Injector runs at factory design parameters

---

## The EA827 Family — What Else This Applies To

The DT engine shares its block with many VW/Audi engines. This project's tune data, injector analysis, and wiring approach apply to any EA827 8V using TBI:

| Engine | Displacement | CR | Power | Lifters | Notes |
|--------|-------------|------|-------|---------|-------|
| **DT** (this car) | 1.6L | 9.0:1 | 75 PS | Hydraulic | Rev limit 6200 |
| ABU (Golf 3) | 1.6L | 9.0:1 | 75 PS | Solid | Factory SPI, rev limit 6500 |
| AEA (Golf 3) | 1.6L | 9.0:1 | 75 PS | Solid | Factory MPI |
| JU | 1.6L | — | 75 PS @ 5500 | — | Verify block stamping |

> **Hydraulic lifters:** No knock sensor (broadband noise in 4–10 kHz overlaps knock frequency 6–8 kHz → constant false triggers). Use conservative timing maps instead (32–33° max WOT vs 36° theoretical).

---

## References

- [Speeduino Wiki](https://wiki.speeduino.com/)
- [Speeduino v0.4.4c Hardware (GitHub)](https://github.com/speeduino/Hardware/tree/main/v0.4/SMD/Prior%20Versions/0.4.4c)
- [VNLD5090-E Datasheet (ST)](https://www.st.com/resource/en/datasheet/vnld5090-e.pdf)
- [TunerStudio MS](https://www.tunerstudio.com/)
- [mlg-converter (npm)](https://www.npmjs.com/package/mlg-converter)

---

## License

This project documents a personal vehicle build. Tune files, analysis scripts, and documentation are shared for educational purposes. Use at your own risk — every engine is different. Always verify with your own datalogs and a wideband O2 sensor.
