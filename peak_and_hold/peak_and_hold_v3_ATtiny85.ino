/*
 * ═══════════════════════════════════════════════════════════════════
 *  PEAK-AND-HOLD INJECTOR DRIVER v3.0 — ATtiny85
 *  VW Passat B2 1.6 DT — Injetor Magneti Marelli IWM500.01 (2Ω low-Z)
 *  ═══════════════════════════════════════════════════════════════════
 *
 *  MELHORIAS vs v2 (Arduino Nano):
 *   ✅ ATtiny85 — mais barato, mais simples, 8 pinos, menos fiação
 *   ✅ Watchdog interno — reinicia automaticamente se o firmware travar
 *   ✅ Fail-safe por timeout — fecha o injetor se perder o sinal
 *   ✅ Proteção de corrente (hardware) — comparador LM393 corta a gate
 *   ✅ Calibração automática do hold — ajusta o duty para ~1.2A
 *   ✅ LED de diagnóstico — peak / hold / erro
 *   ✅ TVS — protege contra picos de tensão (no esquema)
 *
 *  PINOS ATtiny85 (DIP-8):
 *   PB4 (pino 3): PWM gate MOSFET (Timer1 OC1A) — 31.25kHz
 *   PB0 (pino 5): LED diagnóstico
 *   PB2 (pino 7): sinal Speeduino INJ1 (INT0) — ativo-baixo
 *   PB1 (pino 6): comparador A — sobrecorrente (fail-safe, LOW = erro)
 *   PB3 (pino 2): comparador B — feedback hold (LOW = corrente ≥ 1.2A)
 *
 *  SINAL: LOW = injetar (Speeduino INJ1 open-drain, ativo-baixo)
 *  ═══════════════════════════════════════════════════════════════════
 */

#include <avr/wdt.h>

// ═══════════════════════════════════════════════════════════════════
//  CONFIGURAÇÃO — ajustar para o teu injetor
// ═══════════════════════════════════════════════════════════════════

const uint16_t PEAK_TIME_US   = 1500;   // fase peak: 1.5ms (abrir rápido)
const uint8_t  HOLD_DUTY_INIT = 51;     // duty inicial (20% ≈ 1.2A)
const uint8_t  HOLD_DUTY_MIN  = 20;     // limite mínimo (≈0.5A)
const uint8_t  HOLD_DUTY_MAX  = 80;     // limite máximo (≈2.4A)
const uint16_t SIGNAL_TIMEOUT_MS = 100; // fail-safe: fecha se sem sinal

// ═══════════════════════════════════════════════════════════════════
//  PINOS
// ═══════════════════════════════════════════════════════════════════

#define PIN_GATE    PB4   // PWM gate (Timer1 OC1A)
#define PIN_LED     PB0   // LED diagnóstico
#define PIN_SIGNAL  PB2   // sinal Speeduino (INT0)
#define PIN_OC      PB1   // comparador A: sobrecorrente (LOW = erro)
#define PIN_HOLD_FB PB3   // comparador B: feedback hold (LOW = corrente OK)

// ═══════════════════════════════════════════════════════════════════
//  ESTADO
// ═══════════════════════════════════════════════════════════════════

volatile bool injectorActive = false;
volatile bool inPeak = false;
volatile unsigned long pulseStart = 0;
volatile unsigned long lastSignalMs = 0;
volatile unsigned long ocCount = 0;
uint8_t holdDuty = HOLD_DUTY_INIT;

// ═══════════════════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════════════════

void setup() {
  // Pinos
  pinMode(PIN_GATE, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_SIGNAL, INPUT_PULLUP);
  pinMode(PIN_OC, INPUT_PULLUP);      // comparador A: normal = HIGH
  pinMode(PIN_HOLD_FB, INPUT_PULLUP); // comparador B: normal = HIGH

  // MOSFET desligado no arranque (fail-safe)
  digitalWrite(PIN_GATE, LOW);
  digitalWrite(PIN_LED, LOW);

  // Timer1 PWM 31.25kHz na PB4 (OC1A)
  // Prescaler 1 → 8MHz / 256 = 31.25kHz (inaudível)
  TCCR1 = (1 << COM1A1) | (1 << PWM1A) | (1 << CS10);
  OCR1A = 0;   // duty 0

  // Interrupção INT0 no PB2 (mudança de estado)
  GIMSK |= (1 << INT0);
  MCUCR |= (1 << ISC00);   // qualquer mudança de estado

  // Watchdog: 2s (se o loop travar, reinicia)
  wdt_enable(WDTO_2S);

  // Boot blink: 3x = arranque OK
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED, HIGH);
    delay(100);
    digitalWrite(PIN_LED, LOW);
    delay(100);
  }
}

// ═══════════════════════════════════════════════════════════════════
//  INTERRUPÇÃO SINAL — resposta em microssegundos
// ═══════════════════════════════════════════════════════════════════

ISR(INT0_vect) {
  bool state = digitalRead(PIN_SIGNAL);
  if (!state) {
    // ── INJETAR (ativo-baixo) ──
    pulseStart = micros();
    inPeak = true;
    injectorActive = true;
    OCR1A = 255;              // PEAK: 100% (abrir rápido)
    digitalWrite(PIN_LED, HIGH);
  } else {
    // ── PARAR ──
    OCR1A = 0;
    injectorActive = false;
    inPeak = false;
    digitalWrite(PIN_LED, LOW);
  }
  lastSignalMs = millis();
}

// ═══════════════════════════════════════════════════════════════════
//  MAIN LOOP
// ═══════════════════════════════════════════════════════════════════

void loop() {
  wdt_reset();   // alimenta o watchdog (se travar, reinicia)

  // 1. Transição peak → hold
  if (injectorActive && inPeak) {
    if ((unsigned long)(micros() - pulseStart) >= PEAK_TIME_US) {
      inPeak = false;
      OCR1A = holdDuty;   // HOLD: corrente reduzida
    }
  }

  // 2. Calibração automática do hold (via comparador B)
  //    Mantém a corrente de hold em ~1.2A sem ajuste manual.
  if (injectorActive && !inPeak) {
    if (digitalRead(PIN_HOLD_FB) == HIGH) {
      // corrente < 1.2A → aumenta o duty
      if (holdDuty < HOLD_DUTY_MAX) holdDuty++;
    } else {
      // corrente ≥ 1.2A → diminui o duty
      if (holdDuty > HOLD_DUTY_MIN) holdDuty--;
    }
    OCR1A = holdDuty;
  }

  // 3. Fail-safe: sem sinal há demasiado tempo → fecha o injetor
  if (injectorActive) {
    if ((unsigned long)(millis() - lastSignalMs) > SIGNAL_TIMEOUT_MS) {
      OCR1A = 0;
      injectorActive = false;
      inPeak = false;
      digitalWrite(PIN_LED, LOW);
      blinkError(5, 50);   // 5 piscas = fail-safe de sinal
    }
  }

  // 4. Proteção de corrente (comparador A — fail-safe de hardware)
  //    O comparador corta a gate diretamente; aqui só sinalizamos.
  if (digitalRead(PIN_OC) == LOW) {
    ocCount++;
    if (ocCount > 5) {
      OCR1A = 0;
      injectorActive = false;
      inPeak = false;
      blinkError(10, 30);  // 10 piscas = sobrecorrente
    }
  } else {
    ocCount = 0;
  }

  delay(1);
}

// ═══════════════════════════════════════════════════════════════════
//  LED DE ERRO
// ═══════════════════════════════════════════════════════════════════

void blinkError(int times, int ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(PIN_LED, HIGH);
    delay(ms);
    digitalWrite(PIN_LED, LOW);
    delay(ms);
  }
}

/*
 * ═══════════════════════════════════════════════════════════════════
 *  CÓDIGO DE DIAGNÓSTICO DO LED
 *  ═══════════════════════════════════════════════════════════════════
 *  3 piscas lentas no arranque  → boot OK
 *  LED aceso durante o pulso    → peak (1.5ms) + hold
 *  5 piscas rápidas             → fail-safe de sinal (perdeu o Speeduino)
 *  10 piscas rápidas            → sobrecorrente (curto no injetor)
 *  ═══════════════════════════════════════════════════════════════════
 */
