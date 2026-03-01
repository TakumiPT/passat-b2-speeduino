/*
 * Peak-and-Hold Injector Driver — Single Channel (Inline)
 * For VW Passat B2 with Gol G2 SPI Monopoint TBI
 * 
 * REPLACES THE BALLAST RESISTOR — no Speeduino board modifications!
 * 
 * Hardware: Arduino Nano + IRLZ44N logic-level MOSFET
 * Injector: Gol G2 SPI (~2Ω, low impedance)
 * Fuel pressure at injector: 1.0-1.5 bar
 * 
 * HOW IT WORKS:
 * =============
 * Currently you have:
 *   +12V → Injector → Ballast Resistor → Speeduino INJ1 output → GND
 *                      (limits current)   (onboard MOSFET switches ground)
 * 
 * With this module:
 *   Speeduino INJ1 output wire → P&H module SENSE input (detects fire signal)
 *   +12V → Injector → P&H module IRLZ44N → GND (module switches ground)
 * 
 * The Speeduino's onboard MOSFET still fires, but only drives a 10kΩ
 * pull-up resistor (~1.2mA, zero stress). The IRLZ44N on this board
 * handles all the injector current with peak-and-hold.
 * 
 * INLINE WIRING (replaces ballast resistor):
 * ===========================================
 * 
 *   BEFORE (with ballast resistor):
 *   ┌──────────┐        ┌──────────┐        ┌────────┐        ┌──────────────┐
 *   │   +12V   ├───→────┤Injector  ├───→────┤Resistor├───→────┤Speeduino INJ1│
 *   └──────────┘        └──────────┘        └────────┘        │output → GND  │
 *                                           (limits current)  └──────────────┘
 * 
 *   AFTER (with P&H module):
 *   ┌──────────┐        ┌──────────┐       ┌──────────────────────┐
 *   │   +12V   ├──→─────┤Injector  ├──→────┤ P&H MODULE          │
 *   └──────────┘        └──────────┘       │                     │
 *                                          │  INJ- → IRLZ44N → GND
 *   Speeduino INJ1 output ──→──────────────┤  SIG  (sense input) │
 *                                          └──────────────────────┘
 * 
 *   The injector negative is NO LONGER connected to Speeduino's INJ1.
 *   The Speeduino INJ1 output wire only carries the sense signal (~1mA).
 *   The ballast resistor is REMOVED.
 * 
 * PHYSICAL CONNECTIONS TO THE MODULE (4 wires):
 * =============================================
 *   Wire 1: +12V (ignition switched) → PCB terminal "12V"
 *   Wire 2: Injector negative (-)    → PCB terminal "INJ-"
 *   Wire 3: Speeduino INJ1 output    → PCB terminal "SIG"
 *   Wire 4: Car chassis ground       → PCB terminal "GND"
 * 
 *   Injector positive (+) goes directly to +12V (no resistor, no module)
 * 
 * SENSE INPUT SIGNAL:
 * ===================
 * Speeduino v0.4 INJ1 output = open-drain (onboard MOSFET):
 *   - MOSFET ON (injection active)  → pin pulled to GND = LOW
 *   - MOSFET OFF (no injection)     → pin floating      = HIGH (via pullup)
 * 
 * So: LOW = Speeduino wants to fire, HIGH = idle
 * This is ACTIVE LOW → we set INVERT_INPUT = true
 * 
 * The module has an internal 10kΩ pull-up to 5V, so the floating
 * state reads as HIGH. When the Speeduino fires, it pulls to GND
 * through the onboard MOSFET (only ~0.5mA flows — no stress at all).
 * 
 * VERSION: 2.1 (2026-03-01) - Inline design, no Speeduino mods
 * LICENSE: Free to use, modify, distribute. No warranty.
 */

// ═══════════════════════════════════════════════════════════
//  CONFIGURATION — Adjust for your injector
// ═══════════════════════════════════════════════════════════

const unsigned int PEAK_TIME_US = 1500;  // Peak phase: 1.5ms
                                          // 2Ω injectors open fast
                                          // Increase to 2000 if injector
                                          // doesn't open reliably

const byte HOLD_DUTY = 44;               // Hold PWM (0-255)
                                          // 44/255 = 17% ≈ 1.2A hold
                                          // Increase if injector drops
                                          // out during long pulses
                                          // Max safe value: ~80 (~2.4A)

const bool INVERT_INPUT = true;           // true = LOW means fire
                                          //   (Speeduino INJ1 output:
                                          //    onboard MOSFET pulls LOW
                                          //    when injecting)
                                          // This is the correct setting
                                          // for inline installation

// ═══════════════════════════════════════════════════════════
//  PIN DEFINITIONS
// ═══════════════════════════════════════════════════════════

const byte INPUT_PIN  = 2;    // Speeduino INJ1 signal (interrupt capable!)
const byte OUTPUT_PIN = 9;    // IRLZ44N gate (Timer1 PWM = 31.25kHz)
const byte LED_PIN    = 13;   // Onboard LED = activity indicator

// ═══════════════════════════════════════════════════════════
//  STATE TRACKING
// ═══════════════════════════════════════════════════════════

volatile bool injectorActive = false;
volatile unsigned long pulseStartTime = 0;
volatile bool inPeakPhase = false;

// ═══════════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════════

void setup() {
  // Configure pins
  if (INVERT_INPUT) {
    pinMode(INPUT_PIN, INPUT_PULLUP);   // Pullup for open-drain output
  } else {
    pinMode(INPUT_PIN, INPUT);          // Direct logic signal
  }
  pinMode(OUTPUT_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  digitalWrite(OUTPUT_PIN, LOW);  // MOSFET off at startup
  digitalWrite(LED_PIN, LOW);
  
  // Set Timer1 PWM frequency to 31.25kHz (inaudible)
  // Timer1 controls pins 9 and 10
  TCCR1B = (TCCR1B & 0b11111000) | 0x01;  // Prescaler = 1
  
  // Use interrupt for fastest response to Speeduino signal
  // Pin 2 = INT0 on Arduino Nano
  if (INVERT_INPUT) {
    attachInterrupt(digitalPinToInterrupt(INPUT_PIN), onSignalChange, CHANGE);
  } else {
    attachInterrupt(digitalPinToInterrupt(INPUT_PIN), onSignalChange, CHANGE);
  }
  
  // Serial debug (optional, comment out for production)
  Serial.begin(115200);
  Serial.println(F("Peak & Hold v2.0 — Single Channel"));
  Serial.print(F("Injector: 2 ohm @ 1-1.5 bar"));
  Serial.print(F("  Peak: ")); Serial.print(PEAK_TIME_US);
  Serial.print(F("us  Hold: ")); Serial.print((HOLD_DUTY * 100) / 255);
  Serial.println(F("%"));
  Serial.println(F("Ready."));
}

// ═══════════════════════════════════════════════════════════
//  INTERRUPT HANDLER — fires on signal edge
// ═══════════════════════════════════════════════════════════

void onSignalChange() {
  bool signalState = digitalRead(INPUT_PIN);
  if (INVERT_INPUT) signalState = !signalState;
  
  if (signalState) {
    // ── RISING EDGE: Start injection ──
    pulseStartTime = micros();
    inPeakPhase = true;
    injectorActive = true;
    analogWrite(OUTPUT_PIN, 255);      // PEAK: full power
    digitalWrite(LED_PIN, HIGH);
  } else {
    // ── FALLING EDGE: Stop injection ──
    analogWrite(OUTPUT_PIN, 0);        // MOSFET off
    injectorActive = false;
    inPeakPhase = false;
    digitalWrite(LED_PIN, LOW);
  }
}

// ═══════════════════════════════════════════════════════════
//  MAIN LOOP — handles peak→hold transition
// ═══════════════════════════════════════════════════════════

void loop() {
  // Check if we need to transition from PEAK to HOLD
  if (injectorActive && inPeakPhase) {
    unsigned long elapsed = micros() - pulseStartTime;
    if (elapsed >= PEAK_TIME_US) {
      inPeakPhase = false;
      analogWrite(OUTPUT_PIN, HOLD_DUTY);  // HOLD: reduced current
    }
  }
  
  // No delay needed — loop runs at ~8MHz on Nano
  // (62.5ns per instruction, handles transition within 1-2µs)
}

/*
 * ═══════════════════════════════════════════════════════════
 *  TUNING GUIDE
 * ═══════════════════════════════════════════════════════════
 * 
 * SYMPTOM                        → FIX
 * ──────────────────────────────────────────────────
 * Injector doesn't open          → Increase PEAK_TIME_US to 2000
 * Injector opens but drops out   → Increase HOLD_DUTY to 64 (25%)
 * MOSFET gets warm               → Decrease HOLD_DUTY to 32 (12%)
 * Buzzing noise                  → Normal at low PWM. 31kHz should
 *                                  be inaudible. Check wiring.
 * Engine runs lean               → Check signal connection. Verify
 *                                  with Serial monitor that pulses
 *                                  are detected.
 * Engine runs pig rich           → Check INVERT_INPUT setting.
 *                                  Wrong polarity = injector always on.
 * 
 * BENCH TEST PROCEDURE:
 * ═══════════════════════════════════════════════════════════
 * 1. Upload code to Arduino Nano via USB
 * 2. Open Serial Monitor at 115200 baud
 * 3. Connect a jumper wire to D2
 * 4. Touch jumper to +5V briefly = simulates injection pulse
 * 5. Observe: LED should light, Serial shows "Ready"
 * 6. Connect oscilloscope to OUTPUT_PIN (D9):
 *    - Should see 5V DC for 1.5ms (PEAK)
 *    - Then PWM at 17% duty (HOLD)
 *    - Then 0V when signal removed
 * 7. If all correct, proceed to vehicle installation
 */
