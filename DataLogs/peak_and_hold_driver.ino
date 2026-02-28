/*
 * DIY Peak-and-Hold Injector Driver for Speeduino
 * 
 * Hardware: Arduino Nano + IRFZ44N MOSFETs (one per injector)
 * Purpose: Convert low-current Speeduino signals to peak-and-hold high-current drive
 * 
 * THEORY OF OPERATION:
 * ====================
 * Low-impedance injectors (1.4Ω) draw ~9A continuously, which is hard on the ECU.
 * Peak-and-hold reduces current after initial opening:
 * 
 *   1. PEAK PHASE (0-2ms): Full 12V → ~9A → Opens injector quickly
 *   2. HOLD PHASE (2ms-end): PWM at 25% duty → ~2A → Keeps injector open
 * 
 * This reduces heat, allows longer pulse widths, and protects the Speeduino.
 * 
 * WIRING PER CHANNEL:
 * ===================
 * 
 *   Speeduino INJ1 → Arduino D2 (INPUT_PIN_1)
 *   Speeduino INJ2 → Arduino D3 (INPUT_PIN_2)
 *   Speeduino INJ3 → Arduino D4 (INPUT_PIN_3)
 *   Speeduino INJ4 → Arduino D5 (INPUT_PIN_4)
 *   Speeduino GND  → Arduino GND
 * 
 *   Arduino D9  → 220Ω resistor → IRFZ44N Gate (Channel 1)
 *   Arduino D10 → 220Ω resistor → IRFZ44N Gate (Channel 2)
 *   Arduino D11 → 220Ω resistor → IRFZ44N Gate (Channel 3)
 *   Arduino D6  → 220Ω resistor → IRFZ44N Gate (Channel 4)
 * 
 *   IRFZ44N Gate → 10kΩ resistor → GND (pulldown, prevents floating)
 *   IRFZ44N Source → GND (power ground)
 *   IRFZ44N Drain → Injector negative terminal
 * 
 *   Injector positive terminal → +12V (from fuel pump relay or main power)
 *   Injector negative to +12V → 1N4007 diode → (flyback protection)
 * 
 * PARTS LIST (for 4 channels):
 * ============================
 * - Arduino Nano (Chinese clone OK) - Already have
 * - 4x IRFZ44N N-channel MOSFET - Already have
 * - 4x 1N4007 diode (flyback protection) - ~$0.40
 * - 4x 220Ω resistor 1/4W (gate current limit) - ~$0.20
 * - 4x 10kΩ resistor 1/4W (gate pulldown) - ~$0.20
 * - Breadboard or perfboard - ~$1-2
 * - Wire, connectors - ~$1
 * 
 * Total additional cost: ~$3-5
 * 
 * TUNING PARAMETERS:
 * ==================
 */

// ADJUST THESE VALUES FOR YOUR INJECTORS:
const unsigned int PEAK_TIME_US = 2000;      // Peak phase duration in microseconds (2ms = 2000us)
                                              // Increase if injector opens slowly
                                              // Decrease to reduce peak current time
                                              
const byte HOLD_DUTY_CYCLE = 64;             // Hold phase PWM (0-255, where 255=100%)
                                              // 64 = 25% duty cycle ≈ 2A hold current
                                              // Increase if injector closes during hold
                                              // Decrease to reduce heating

const unsigned int MIN_PULSE_WIDTH_US = 500; // Minimum pulse to activate peak-and-hold (500us)
                                              // Below this, just pulse normally (too short for P&H)

/*
 * PIN DEFINITIONS:
 * ================
 */

// Input pins from Speeduino (injector signals)
const byte INPUT_PIN_1 = 2;   // Speeduino INJ1
const byte INPUT_PIN_2 = 3;   // Speeduino INJ2
const byte INPUT_PIN_3 = 4;   // Speeduino INJ3
const byte INPUT_PIN_4 = 5;   // Speeduino INJ4

// Output pins to MOSFET gates (PWM capable pins)
const byte OUTPUT_PIN_1 = 9;   // To IRFZ44N gate for INJ1
const byte OUTPUT_PIN_2 = 10;  // To IRFZ44N gate for INJ2
const byte OUTPUT_PIN_3 = 11;  // To IRFZ44N gate for INJ3
const byte OUTPUT_PIN_4 = 6;   // To IRFZ44N gate for INJ4

/*
 * CHANNEL STATE TRACKING:
 * =======================
 */

struct InjectorChannel {
  byte inputPin;
  byte outputPin;
  bool lastState;
  unsigned long pulseStartTime;
  bool inPeakPhase;
};

InjectorChannel channels[4] = {
  {INPUT_PIN_1, OUTPUT_PIN_1, LOW, 0, false},
  {INPUT_PIN_2, OUTPUT_PIN_2, LOW, 0, false},
  {INPUT_PIN_3, OUTPUT_PIN_3, LOW, 0, false},
  {INPUT_PIN_4, OUTPUT_PIN_4, LOW, 0, false}
};

/*
 * SETUP: Initialize pins and serial debug
 * ========================================
 */

void setup() {
  // Configure input pins from Speeduino
  for (int i = 0; i < 4; i++) {
    pinMode(channels[i].inputPin, INPUT);
    pinMode(channels[i].outputPin, OUTPUT);
    digitalWrite(channels[i].outputPin, LOW); // Start with injectors off
  }
  
  // Set PWM frequency for pins 9 and 10 to 31.25kHz (reduces audible noise)
  // Timer 1: Pins 9 and 10
  TCCR1B = (TCCR1B & 0b11111000) | 0x01; // Set prescaler to 1 (31.25kHz PWM)
  
  // Set PWM frequency for pin 11 to 31.25kHz
  // Timer 2: Pins 11 and 3
  TCCR2B = (TCCR2B & 0b11111000) | 0x01; // Set prescaler to 1 (31.25kHz PWM)
  
  // Pin 6 uses Timer 0 (default ~1kHz is OK for this application)
  
  // Serial for debugging (optional - comment out if not needed)
  Serial.begin(115200);
  Serial.println(F("Peak-and-Hold Injector Driver v1.0"));
  Serial.print(F("Peak time: "));
  Serial.print(PEAK_TIME_US);
  Serial.println(F(" us"));
  Serial.print(F("Hold duty cycle: "));
  Serial.print((HOLD_DUTY_CYCLE * 100) / 255);
  Serial.println(F("%"));
  Serial.println(F("Ready."));
}

/*
 * MAIN LOOP: Process each channel independently
 * =============================================
 */

void loop() {
  unsigned long currentTime = micros(); // High-resolution timestamp
  
  // Process all 4 channels
  for (int i = 0; i < 4; i++) {
    processChannel(channels[i], currentTime);
  }
}

/*
 * PROCESS CHANNEL: Handle peak-and-hold logic for one injector
 * =============================================================
 */

void processChannel(InjectorChannel &channel, unsigned long currentTime) {
  bool currentState = digitalRead(channel.inputPin);
  
  // RISING EDGE: Injector signal just went HIGH (start of pulse)
  if (currentState == HIGH && channel.lastState == LOW) {
    channel.pulseStartTime = currentTime;
    channel.inPeakPhase = true;
    
    // Start PEAK phase: Full power (100% duty cycle)
    analogWrite(channel.outputPin, 255); // Full 12V to injector
    
    #ifdef DEBUG_SERIAL
    Serial.print(F("CH"));
    Serial.print(channel.inputPin - 1);
    Serial.println(F(": PEAK START"));
    #endif
  }
  
  // INJECTOR IS ACTIVE (HIGH signal from Speeduino)
  else if (currentState == HIGH) {
    unsigned long pulseTime = currentTime - channel.pulseStartTime;
    
    // Transition from PEAK to HOLD phase after PEAK_TIME_US microseconds
    if (channel.inPeakPhase && pulseTime >= PEAK_TIME_US) {
      channel.inPeakPhase = false;
      
      // Switch to HOLD phase: Reduced current via PWM
      analogWrite(channel.outputPin, HOLD_DUTY_CYCLE); // ~25% duty = 2A hold
      
      #ifdef DEBUG_SERIAL
      Serial.print(F("CH"));
      Serial.print(channel.inputPin - 1);
      Serial.println(F(": HOLD START"));
      #endif
    }
    
    // Still in PEAK phase - keep full power
    // (analogWrite already set to 255, no action needed)
  }
  
  // FALLING EDGE: Injector signal just went LOW (end of pulse)
  else if (currentState == LOW && channel.lastState == HIGH) {
    unsigned long pulseWidth = currentTime - channel.pulseStartTime;
    
    // Turn off injector
    analogWrite(channel.outputPin, 0); // MOSFET off, injector closes
    channel.inPeakPhase = false;
    
    #ifdef DEBUG_SERIAL
    Serial.print(F("CH"));
    Serial.print(channel.inputPin - 1);
    Serial.print(F(": OFF ("));
    Serial.print(pulseWidth);
    Serial.println(F(" us)"));
    #endif
  }
  
  // Update state for next iteration
  channel.lastState = currentState;
}

/*
 * INSTALLATION INSTRUCTIONS:
 * ==========================
 * 
 * 1. UPLOAD CODE:
 *    - Connect Arduino Nano to PC via USB
 *    - Open this file in Arduino IDE
 *    - Select: Tools → Board → Arduino Nano
 *    - Select: Tools → Processor → ATmega328P (Old Bootloader) for Chinese clones
 *    - Select correct COM port
 *    - Click Upload
 * 
 * 2. BUILD HARDWARE:
 *    - Wire according to diagram above
 *    - Use 220Ω resistors between Arduino pins and MOSFET gates
 *    - Use 10kΩ resistors from MOSFET gates to ground
 *    - Install 1N4007 diodes across injectors (cathode to +12V)
 *    - Use thick wire (16-18 AWG) for injector power and ground
 * 
 * 3. BENCH TEST:
 *    - Power Arduino from USB or 12V (Vin pin)
 *    - Connect oscilloscope or LED to output pin
 *    - Manually pulse input pins HIGH/LOW
 *    - Verify PEAK (2ms full power) then HOLD (PWM) behavior
 * 
 * 4. INSTALL IN VEHICLE:
 *    - Disconnect battery negative terminal
 *    - Cut wires between Speeduino and injectors
 *    - Route Speeduino signals to Arduino inputs
 *    - Route Arduino outputs through MOSFETs to injectors
 *    - Power Arduino from +12V (max 12V on Vin, or use 5V regulator)
 *    - Reconnect battery, test injector operation
 * 
 * 5. SPEEDUINO CONFIGURATION:
 *    - Set Opening Time back to 1.0ms (no resistor compensation needed)
 *    - Test and tune as normal
 *    - Monitor injector operation via datalog
 * 
 * TUNING TIPS:
 * ============
 * 
 * If injector doesn't open reliably:
 *   → Increase PEAK_TIME_US (try 2500, then 3000)
 * 
 * If injector closes during long pulses:
 *   → Increase HOLD_DUTY_CYCLE (try 80, then 96)
 * 
 * If MOSFETs get too hot:
 *   → Decrease HOLD_DUTY_CYCLE (try 48, then 32)
 *   → Add heatsinks to IRFZ44N MOSFETs
 * 
 * If injectors make buzzing noise:
 *   → Normal - PWM frequency causes vibration
 *   → Increase PWM frequency (already set to 31kHz, should be quiet)
 * 
 * SAFETY NOTES:
 * =============
 * 
 * ⚠️  ALWAYS disconnect battery before wiring
 * ⚠️  Double-check MOSFET pinout (Gate, Drain, Source)
 * ⚠️  Install flyback diodes or injectors will destroy MOSFETs
 * ⚠️  Use proper wire gauge (injectors draw 9A peak)
 * ⚠️  Test on bench before installing in vehicle
 * ⚠️  Monitor for overheating during first runs
 * 
 * TROUBLESHOOTING:
 * ================
 * 
 * Injector always on:
 *   → MOSFET gate stuck HIGH, check wiring
 *   → Add/check 10kΩ pulldown resistor
 * 
 * Injector doesn't fire:
 *   → Check Speeduino signal reaching Arduino input
 *   → Verify MOSFET wiring (Drain to injector, Source to GND)
 *   → Test with multimeter: Gate should pulse 0V/5V
 * 
 * MOSFET gets very hot:
 *   → Not switching fast enough (add 220Ω gate resistor)
 *   → Not fully turning on (check 5V gate voltage)
 *   → Too much hold current (reduce HOLD_DUTY_CYCLE)
 *   → Add heatsink to IRFZ44N
 * 
 * Erratic injector behavior:
 *   → Poor ground connection (use star ground)
 *   → EMI interference (route signal wires away from ignition)
 *   → Weak power supply (use dedicated 12V line)
 * 
 * DEBUG MODE:
 * ===========
 * To enable serial debugging, uncomment this line near top of file:
 * #define DEBUG_SERIAL
 * 
 * Then monitor Serial output at 115200 baud to see injector events.
 * 
 * LICENSE:
 * ========
 * Free to use, modify, and distribute.
 * No warranty. Use at your own risk.
 * 
 * VERSION HISTORY:
 * ================
 * v1.0 - 2025-11-23 - Initial release
 */
