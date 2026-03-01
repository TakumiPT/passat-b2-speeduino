# Peak-and-Hold Injector Driver PCB
## Single Channel — Inline Ballast Resistor Replacement
### VW Passat B2 Gol G2 SPI Monopoint

Replaces the ballast resistor between Speeduino and the 2Ω low-impedance injector.
**No soldering on the Speeduino board — uses the existing INJ1 output wire as a sense signal.**

---

## Why Peak-and-Hold?

| Method | Peak Current | Hold Current | Power Wasted | Injector Response |
|--------|-------------|-------------|-------------|-------------------|
| **Direct drive** (no resistor) | 7A continuous | 7A | 98W heat in MOSFET | Fast open |
| **Ballast resistor** (current) | ~3A | ~3A | 27W heat in resistor | Slow open ⚠️ |
| **Peak-and-Hold** (this PCB) | 7A for 1.5ms | 1.2A | ~2W average | Fast open ✅ |

The ballast resistor slows injector opening (higher `injOpen` needed) and wastes energy as heat. Peak-and-hold gives you fast opening AND low power consumption.

---

## Schematic

### Current Wiring (with ballast resistor)
```
+12V ─→─ Injector+ ─→─ Injector- ─→─ [Ballast Resistor] ─→─ Speeduino INJ1 output ─→─ GND
                                       (limits current         (onboard MOSFET
                                        through MOSFET)         switches ground)
```

### New Wiring (with P&H module)
```
+12V ─→─ Injector+ ─→─ Injector- ─→─ P&H Module "INJ-" terminal
                                            │
                              P&H Module IRLZ44N → GND
                                            │
Speeduino INJ1 output wire ────────────→─ P&H Module "SIG" terminal
 (same wire that went through               (sense only, ~1mA through
  the ballast resistor to injector,          internal 10kΩ pullup)
  now carries only sense signal)
```

**What changed:**
- Ballast resistor **removed** (was between injector- and Speeduino INJ1 output)
- Injector negative goes to **P&H module INJ-** instead of through resistor to Speeduino
- Speeduino INJ1 output wire becomes a **sense signal** only (~1mA, zero stress on Speeduino MOSFET)
- +12V → Injector+ stays the same as before (unchanged)

### Detailed Circuit

```
                              +12V (ignition switched, 10A fuse)
                               │
                    ┌──────────┤
                    │          │
                    │     ┌────┴────┐
                    │     │  100µF  │ C1 (electrolytic, 25V)
                    │     │  + 100nF│ C2 (ceramic, in parallel)
                    │     └────┬────┘
                    │          │
        ┌───────────┤          │
        │           │      ┌───┴───┐
        │           │      │AMS1117│
        │           │      │ -5.0  │ U1 (5V regulator)
        │           │      │IN  OUT│──→ Arduino Nano 5V pin
        │           │      └───┬───┘
        │           │          │
        │           │       ┌──┴──┐
        │           │       │100nF│ C3 (output cap)
        │           │       └──┬──┘
        │           │          │
        │           │         GND
        │           │
        │      LED1 ▼ (green, power indicator)
        │           │
        │        [1kΩ] R3
        │           │
        │          GND
        │
        │
   INJ+ ●──────────┤
        │           │
     ┌──┴──┐   ┌───┴───┐
     │ INJ │   │ D1    │ 1N5819 Schottky flyback
     │ 2Ω  │   │ ┌─┘   │ Cathode (band) to +12V
     │ Gol │   │▲│     │ Anode to INJ-
     │ G2  │   └───────┘
     └──┬──┘
        │
   INJ- ●─────── IRLZ44N Drain ──┐
                                   │
                    ┌──────────────┤ Q1 (IRLZ44N)
                    │              │ TO-220 package
                 Gate             Source
                    │              │
              ┌─────┤             GND (power ground)
              │     │
           [220Ω]   │
            R1      │
              │  ┌──┴──┐  ┌──┴──┐
              │  │10kΩ │  │100nF│
              │  │ R2  │  │ C4  │
              │  └──┬──┘  └──┬──┘
              │     │        │
    Arduino   │    GND      GND
    Nano D9 ──┘
    (PWM out)


    Speeduino INJ1    ──→  Arduino Nano D2 (input, INPUT_PULLUP)
    output wire             (interrupt — senses when Speeduino fires)
                            LOW = fire (active low, onboard MOSFET pulls down)
                            HIGH = idle (internal pullup)

    Speeduino GND     ──→  Arduino Nano GND
                       ──→  PCB GND (all grounds connected)
```

### Critical Wiring Notes

1. **Signal ground and power ground must connect** at ONE point (star ground) to prevent ground loops
2. **Use 16 AWG wire** (1.5mm²) for +12V → Injector → MOSFET → GND path (carries 7A peak)
3. **Use any thin wire** for sense signal (Speeduino INJ1 output → Arduino D2, only ~1mA)
4. **Flyback diode D1 orientation:** Band (cathode) towards +12V. Anode towards MOSFET drain.
5. **IRLZ44N pinout** (looking at front, text facing you): **Gate | Drain | Source** (left to right)
6. **Injector positive (+) stays wired to +12V** — same as now, no change on that side
7. **Do NOT connect injector negative back to Speeduino INJ1 output** — only the sense wire goes there

### The 4 Wires

| Terminal | Wire | From/To | Gauge |
|----------|------|---------|-------|
| **12V** | Red | Ignition switched +12V (same as injector+) | 16 AWG (1.5mm²) |
| **INJ-** | Any | Injector negative terminal (was going to ballast resistor) | 16 AWG (1.5mm²) |
| **SIG** | Any | Speeduino INJ1 output (was on other side of ballast resistor) | 22 AWG (thin, sense only ~1mA) |
| **GND** | Black | Car chassis ground / Speeduino GND | 16 AWG (1.5mm²) |

---

## Bill of Materials

| Ref | Component | Value | Package | Qty | Notes |
|-----|-----------|-------|---------|-----|-------|
| U2 | Arduino Nano | ATmega328P | 2×15 pin | 1 | Chinese clone OK. "Old Bootloader" in Arduino IDE |
| Q1 | **IRLZ44N** | N-ch MOSFET | TO-220 | 1 | **Logic-level!** Fully on at 5V gate. Do NOT use IRFZ44N (needs 10V) |
| D1 | 1N5819 | Schottky diode | DO-41 | 1 | Fast flyback. 1N5822 also OK. NOT 1N4007 (too slow) |
| U1 | AMS1117-5.0 | 5V regulator | SOT-223 | 1 | Powers Nano from car 12V. Alternative: LM7805 (TO-220) |
| C1 | Electrolytic cap | 100µF 25V | Radial | 1 | Input filter |
| C2 | Ceramic cap | 100nF | Through-hole | 1 | Input decoupling (parallel with C1) |
| C3 | Ceramic cap | 100nF | Through-hole | 1 | AMS1117 output cap |
| C4 | Ceramic cap | 100nF | Through-hole | 1 | Gate noise filter |
| R1 | Resistor | 220Ω ¼W | Axial | 1 | Gate current limit |
| R2 | Resistor | 10kΩ ¼W | Axial | 1 | Gate pulldown (prevents floating) |
| R3 | Resistor | 1kΩ ¼W | Axial | 1 | Power LED current limit |
| LED1 | LED | Green 3mm | Through-hole | 1 | Power indicator |
| J1 | Screw terminal | 2-pos 5.08mm | PCB mount | 1 | +12V / GND input |
| J2 | Screw terminal | 2-pos 5.08mm | PCB mount | 1 | INJ- / SIG input |
| — | Pin headers | 2×15 female | 2.54mm | 2 | Arduino Nano socket |

### Approximate Cost
- IRLZ44N: ~€0.50
- Arduino Nano clone: ~€3.00
- AMS1117-5.0: ~€0.30
- All passives + LED: ~€1.00
- Screw terminals: ~€1.00
- PCB (JLCPCB, 5 boards): ~€2.00 + shipping
- **Total: ~€8-10** (vs €0.50 for a ballast resistor, but proper engineering)

### Where to Buy
- **AliExpress:** IRLZ44N, Arduino Nano, AMS1117 (cheapest, 2-4 week shipping)
- **Amazon.de:** Same parts, faster shipping, slightly more expensive
- **Conrad.de / Reichelt.de:** All parts available, quality guaranteed
- **JLCPCB.com:** PCB fabrication ($2 for 5 boards, upload Gerber files)

---

## Perfboard Layout

Build on a **70mm × 50mm** (7×5 cm) perfboard with 2.54mm pitch holes.

```
    Row:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
         ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
    A    │  │  │J1│J1│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │J2│J2│  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    B    │  │  │12V GND│  │C1│C1│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │IN│IN│  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    C    │  │  │  │  │  │ +│C2│  │U1│U1│U1│  │  │  │  │  │  │  │  │  │  │  │  │J+│J-│  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    D    │  │  │  │  │  │  │  │  │  │C3│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    E    │  │  │  │  │  │R3│  │  │  │  │  │  │  │  │  │D1│D1│D1│D1│D1│D1│D1│D1│  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    F    │  │  │  │  │  │LED│  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    G    │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    H    │  │  │  │  │N  A  N  O     L  E  F  T     H  E  A  D  E  R     (D13..5V)│  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    I    │  │  │  │  │   ════════ ARDUINO NANO (component side up) ════════  │  │  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    J    │  │  │  │  │N  A  N  O     R  I  G  H  T    H  E  A  D  E  R    (D2..VIN)│  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    K    │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    L    │  │J3│J3│  │  │R1│R1│R1│R1│  │  │  │Q1│Q1│Q1│  │  │  │R2│R2│R2│R2│  │C4│C4│  │  │
         ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
    M    │  │SIG GND│  │  │  │  │  │  │  │  │G  D  S │  │  │  │  │  │  │  │  │  │  │  │  │
         └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘

    Q1 = IRLZ44N (Gate=L12, Drain=L13, Source=L14)
    D1 = 1N5819 (Band/cathode towards +12V rail, anode towards Q1 drain)

    TRACES (solder bridges on bottom):
    ─── J1 pin1 (12V)  → C1+ → U1 IN → D1 cathode → +12V rail
    ─── J1 pin2 (GND)  → C1- → U1 GND → Q1 Source → Nano GND
    ─── U1 OUT → C3 → Nano 5V pin
    ─── Nano D9 → R1 → Q1 Gate
    ─── Q1 Gate → R2 → GND
    ─── Q1 Gate → C4 → GND
    ─── Q1 Drain → J2 INJ- → D1 anode
    ─── J2 SIG → Nano D2
    ─── R3 → LED → GND  (from 12V rail)
```

> **Note:** The perfboard layout above is approximate. Place components, then solder wire bridges on the bottom side following the trace list. Use 16 AWG wire for the power traces (+12V and GND rails).

---

## PCB Design (for JLCPCB / PCBWay)

### Board Specifications
- **Size:** 65mm × 45mm (2-layer)
- **Thickness:** 1.6mm standard
- **Copper:** 2oz (for the power traces handling 7A peak)
- **Surface finish:** HASL (cheapest)
- **Color:** Any (green is cheapest)

### Design Guidelines for EasyEDA / KiCad

1. **Power traces** (+12V, GND, injector): **2.5mm wide minimum** (7A peak, 1.5A continuous)
2. **Signal traces** (gate, input): 0.5mm standard
3. **MOSFET thermal pad:** Add copper pour under Q1 tab for heat dissipation
4. **Ground plane:** Fill unused copper with GND pour  
5. **Mounting holes:** 4x M3 in corners (3.2mm drill)
6. **Arduino Nano:** 2×15 pin female headers, 15.24mm (600mil) spacing between rows

### Component Placement

```
    ┌─────────────────────────────────────────────────────────┐
    │ ○                                                    ○  │
    │   [J1]              [LED1]                   [J2]       │
    │  12V GND          (green)                  INJ- SIG     │
    │                                                         │
    │  [C1][C2]  [U1]                      ┌────────────┐     │
    │  100µ 100n AMS1117  [C3]             │  IRLZ44N   │     │
    │                     100n             │    Q1       │     │
    │                                      │  (heatsink  │     │
    │  ┌─────────────────────────────┐     │   optional) │     │
    │  │                             │     └────────────┘     │
    │  │      ARDUINO NANO           │    [R1]  [R2]  [C4]   │
    │  │      (socketed)             │    220Ω  10kΩ  100n   │
    │  │                             │                        │
    │  │         USB ←               │     [D1] 1N5819       │
    │  └─────────────────────────────┘         ↑band         │
    │                                                         │
    │   [J3]                                                  │
    │  SIG GND                                                │
    │ ○                                                    ○  │
    └─────────────────────────────────────────────────────────┘
```

### Ordering from JLCPCB
1. Design in **EasyEDA** (free, https://easyeda.com) — draw the schematic, auto-route PCB
2. Click **"Fabrication" → "One-click order"** → exports directly to JLCPCB
3. Select: 2-layer, 1.6mm, **2oz copper**, HASL, quantity 5
4. Cost: ~$2 + ~$5 shipping = **~$7 for 5 boards**
5. Delivery: 7-14 days to Portugal

---

## Installation in Vehicle

### Step 1: Bench Test (MANDATORY before vehicle install)
1. Upload `peak_and_hold_1ch.ino` to Arduino Nano
2. Open Serial Monitor at 115200 baud — should show "Ready"
3. Briefly connect D2 to +5V with a jumper wire → LED lights
4. If you have an oscilloscope, check D9: 5V for 1.5ms then 17% PWM

### Step 2: Wiring Changes (4 wires, no Speeduino board mods)

**Remove:**
- Ballast resistor (completely removed, not needed)

**Disconnect:**
- Injector negative wire from ballast resistor / Speeduino INJ1 output
  (this wire now goes to P&H module INJ- terminal instead)

**Connect:**
```
Car +12V (ignition switched)   → P&H module "12V" terminal
Injector negative wire         → P&H module "INJ-" terminal
  (was going through ballast    (module MOSFET now switches
   resistor to Speeduino)        the ground for the injector)
Speeduino INJ1 output wire     → P&H module "SIG" terminal
  (was on other side of the     (now carries only ~1mA sense signal,
   ballast resistor)             Speeduino MOSFET under zero load)
Car chassis ground             → P&H module "GND" terminal
```

**Injector positive (+) stays wired to +12V** — same as now, no change on that side.

### Step 3: TunerStudio Changes
- Set `injOpen` (Opening Time) to **1.0 ms** (was higher to compensate for ballast resistor's slow opening)
- The peak-and-hold circuit opens the injector at full voltage — faster than with a ballast resistor

### Step 4: Verify
1. Start engine
2. Check AFR on datalog — should be similar to before but response should be crisper
3. Monitor MOSFET temperature — should stay cool (< 40°C)
4. If engine runs lean → `injOpen` may need slight increase
5. If engine runs rich → `injOpen` may need slight decrease

---

## Enclosure

Use a small ABS project box (~80mm × 55mm × 25mm). Drill holes for:
- 3x screw terminal access (J1, J2, J3)
- 1x LED window (or use clear hot glue)
- Optional: Arduino Nano USB port (for reprogramming without opening)

Mount near the Speeduino ECU to keep signal wires short. Keep away from exhaust heat.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Injector always on | Gate floating HIGH | Check R2 pulldown (10kΩ to GND) |
| Injector never fires | Wrong signal input | Check INVERT_INPUT setting. Try the other polarity. |
| MOSFET gets hot | Wrong part (IRFZ44N vs IRLZ44N) | Replace with **IRLZ44N** (logic-level) |
| Engine runs rich after install | injOpen too high | Reduce injOpen from ballast-compensated value to 1.0ms |
| Arduino resets randomly | Power supply noise | Add 100µF cap closer to Nano VIN, check ground connections |
| No Serial output | Wrong bootloader | Try "ATmega328P (Old Bootloader)" in Arduino IDE |

---

## Why IRLZ44N and Not IRFZ44N?

| Parameter | IRFZ44N | IRLZ44N |
|-----------|---------|---------|
| Gate threshold | 2-4V | 1-2V |
| Rds(on) at Vgs=5V | ~100mΩ (partially on!) | 22mΩ (fully on) |
| Rds(on) at Vgs=10V | 17.5mΩ | 22mΩ |
| Power at 7A, 5V gate | 7² × 0.1 = **4.9W** 🔥 | 7² × 0.022 = **1.1W** ✅ |
| Need gate driver? | YES (for 5V logic) | NO |

The IRFZ44N at 5V gate drive is in the **linear region** — it acts as a variable resistor, not a switch. This generates excessive heat and can destroy the MOSFET. The IRLZ44N is the logic-level version designed for 5V microcontroller drive.
