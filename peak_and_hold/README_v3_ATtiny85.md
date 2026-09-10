# ⚡ PEAK-AND-HOLD v3.0 — ATtiny85
## Driver de Injetor Monoponto — VW Passat B2 1.6 DT
### Injetor Magneti Marelli IWM500.01 (2.0Ω low-Z) · Speeduino v0.4.4c

**Data:** 2026-08-12 · **Autor:** Nó Hardware Engineer · **Estado:** PROPOSTA v3 (redesign completo)

---

## 1. Resumo Executivo

O design v2 (Arduino Nano) funcionava, mas tinha 7 limitações. Esta v3 resolve **todas**:

| Limitação v2 | Solução v3 |
|--------------|-----------|
| Arduino Nano overkill | **ATtiny85** (8 pinos, €1.20) |
| Sem proteção de corrente | **Sense resistor + comparador LM393** (corta a gate em curto) |
| Sem fail-safe robusto | **Timeout de sinal** + **pulldown de hardware** |
| Sem indicação de estado | **LED de diagnóstico** (peak/hold/erro) |
| Sem proteção de tensão | **TVS (SMBJ16A)** + **díodo flyback 1N5822** |
| Sem watchdog | **Watchdog interno ATtiny85** (reinicia em 2s) |
| Calibração manual | **Calibração automática do hold** (feedback do comparador) |

**Custo:** ~€6–8 (vs €8–10 da v2) — mais barato E mais robusto.

---

## 2. Esquema Elétrico Completo (v3)

```
                    +12V (ignição, FUSÍVEL 10A)
                     │
          ┌──────────┤
          │          │
          │     ┌────┴────┐
          │     │  100µF  │ C1 (eletrolítico 25V)
          │     │ + 100nF │ C2 (cerâmico, paralelo)
          │     └────┬────┘
          │          │
          │      ┌───┴───┐
          │      │AMS1117│ U1 (regulador 5V)
          │      │ -5.0  │ IN→OUT → ATtiny85 VCC
          │      └───┬───┘
          │          │
          │       ┌──┴──┐
          │       │100nF│ C3 (saída)
          │       └──┬──┘
          │          │
          │         GND
          │
          │      TVS1 ── SMBJ16A (supressor de picos 12V)
          │      (entre +12V e GND, protege contra picos)
          │
     INJ+ ●──────────┤
          │          │
       ┌──┴──┐   ┌───┴───┐
       │ INJ │   │ D1    │ 1N5822 Schottky flyback
       │ 2Ω  │   │ ┌─┘   │ Cátodo (banda) → +12V
       │     │   │▲│     │ Ânodo → INJ-
       └──┬──┘   └───────┘
          │
     INJ- ●─────── Q1 Drain ──┐
                              │
               ┌──────────────┤ Q1 (IRLZ44N, TO-220)
               │              │
            Gate             Source
               │              │
         ┌─────┤              │
         │     │          ┌───┴───┐
      [220Ω]   │          │ R4    │ 0.05Ω 2W (sense resistor)
       R1      │          │ 50mΩ  │
         │     │          └───┬───┘
         │  ┌──┴──┐          │
         │  │10kΩ │         GND (terra de potência)
         │  │ R2  │
         │  └──┬──┘
         │     │
    ATtiny85   │
    PB4 ───────┘ (PWM gate, 31.25kHz)
    (OC1A)

    ── COMPARADOR A (proteção de corrente) ──
    R4 (0.05Ω) → tensão proporcional à corrente
    I = 4A → V = 4 × 0.05 = 0.2V
    I = 7A → V = 7 × 0.05 = 0.35V
    LM393: V+ = R4, V- = referência 0.25V (≈5A)
    Saída LM393 → PB1 (ATtiny85) + Gate Q1 (corta direto)
    Se I > 5A → LM393 puxa a gate para GND → MOSFET desliga

    ── COMPARADOR B (feedback de hold) ──
    R4 → LM393 (2º canal) com referência 0.06V (≈1.2A)
    Saída → PB3 (ATtiny85) → calibração automática do hold

    ── SINAL ──
    Speeduino INJ1 output ──→ PB2 (ATtiny85, INPUT_PULLUP)
                              LOW = injetar (ativo-baixo)
                              HIGH = parado

    ── LED ──
    PB0 → [330Ω] → LED → GND (diagnóstico)

    ── GND ──
    Todos os terras ligam num único ponto (terra estrela)
```

### Ligações (4 fios — iguais à v2)
| Terminal | Fio | De → Para | Bitola |
|----------|-----|-----------|--------|
| **12V** | Vermelho | Ignição +12V (mesmo do injetor+) | 16 AWG (1.5mm²) |
| **INJ-** | Qualquer | Terminal negativo do injetor | 16 AWG (1.5mm²) |
| **SIG** | Qualquer | Saída Speeduino INJ1 | 22 AWG (só ~1mA) |
| **GND** | Preto | Chassis / GND Speeduino | 16 AWG (1.5mm²) |

> **Injetor positivo (+) fica ligado ao +12V** — não muda nada nesse lado.

---

## 3. Bill of Materials (BOM) — v3

| Ref | Componente | Valor | Encapsulamento | Qtd | Custo | Notas |
|-----|-----------|-------|----------------|-----|-------|-------|
| U2 | **ATtiny85-20PU** | 8-bit AVR | DIP-8 | 1 | €1.20 | Substitui o Nano (€3) |
| Q1 | **IRLZ44N** | MOSFET N-ch logic-level | TO-220 | 1 | €0.50 | **NÃO usar IRFZ44N** |
| U3 | **LM393** | Comparador dual | DIP-8 | 1 | €0.40 | Proteção de corrente + feedback |
| D1 | **1N5822** | Schottky 3A 40V | DO-201 | 1 | €0.50 | Flyback |
| TVS1 | **SMBJ16A** | Supressor de picos 16V | SMB | 1 | €0.30 | Proteção de tensão |
| U1 | AMS1117-5.0 | Regulador 5V | SOT-223 | 1 | €0.30 | Alimenta o ATtiny85 |
| C1 | Eletrolítico | 100µF 25V | Radial | 1 | €0.30 | Filtro de entrada |
| C2 | Cerâmico | 100nF | Through-hole | 1 | €0.10 | Desacoplamento entrada |
| C3 | Cerâmico | 100nF | Through-hole | 1 | €0.10 | Saída do regulador |
| C4 | Cerâmico | 100nF | Through-hole | 1 | €0.10 | Filtro de ruído da gate |
| R1 | Resistor | 220Ω ¼W | Axial | 1 | €0.05 | Limite de corrente da gate |
| R2 | Resistor | 10kΩ ¼W | Axial | 1 | Pulldown da gate (fail-safe) |
| R3 | Resistor | 330Ω ¼W | Axial | 1 | €0.05 | LED diagnóstico |
| **R4** | **Resistor sense** | **0.05Ω 2W** | Axial | 1 | €0.30 | **NOVO** — medição de corrente |
| R5 | Resistor | 10kΩ ¼W | Axial | 2 | €0.10 | Divisor referência LM393 |
| R6 | Resistor | 1kΩ ¼W | Axial | 2 | €0.10 | Divisor referência LM393 |
| LED1 | LED | Bicolor (verde/vermelho) | Through-hole | 1 | €0.30 | Diagnóstico |
| J1 | Terminal parafuso | 2 pos 5.08mm | PCB | 1 | €0.50 | +12V / GND |
| J2 | Terminal parafuso | 2 pos 5.08mm | PCB | 1 | €0.50 | INJ- / SIG |
| — | Soquete | DIP-8 | 2.54mm | 2 | €0.20 | ATtiny85 + LM393 |
| F1 | **Fusível** | **10A** | Porta-fusível | 1 | €2.00 | **OBRIGATÓRIO** no +12V |

**Custo total:** ~**€6–8** (vs €8–10 da v2)

### Onde comprar
- **AliExpress:** ATtiny85, IRLZ44N, LM393, AMS1117 (mais barato, 2-4 semanas)
- **Amazon.de / Reichelt / Conrad:** mais rápido, ligeiramente mais caro
- **JLCPCB:** PCB ($2 por 5 placas)

---

## 4. Firmware — `peak_and_hold_v3_ATtiny85.ino`

O firmware completo está no ficheiro `peak_and_hold_v3_ATtiny85.ino`. Resumo das funcionalidades:

### 4.1 Watchdog (novo)
```c
wdt_enable(WDTO_2S);   // se o loop travar, reinicia em 2s
// no loop:
wdt_reset();           // alimenta o watchdog
```
Se o firmware travar (loop infinito, bug), o watchdog reinicia o ATtiny85 em 2 segundos. O MOSFET desliga no arranque → injetor fecha.

### 4.2 Fail-safe por timeout (novo)
```c
if ((unsigned long)(millis() - lastSignalMs) > SIGNAL_TIMEOUT_MS) {
  OCR1A = 0;   // fecha o injetor
  blinkError(5, 50);   // 5 piscas = perdeu o sinal
}
```
Se o Speeduino parar de mandar sinal (fio partido, ECU desligada), o injetor fecha em 100ms. **Nunca fica preso aberto.**

### 4.3 Proteção de corrente (novo — hardware + firmware)
- **Hardware:** o comparador LM393 mede a tensão no sense resistor R4 (0.05Ω). Se a corrente passar de ~5A, o LM393 puxa a gate do MOSFET para GND → desliga **instantaneamente** (microssegundos, sem depender do firmware).
- **Firmware:** o ATtiny85 lê o comparador (PB1). Se detetar sobrecorrente 5× seguidas, desliga e pisca 10× (código de erro).

### 4.4 Calibração automática do hold (novo)
```c
if (digitalRead(PIN_HOLD_FB) == HIGH) {
  if (holdDuty < HOLD_DUTY_MAX) holdDuty++;   // corrente baixa → sobe
} else {
  if (holdDuty > HOLD_DUTY_MIN) holdDuty--;   // corrente alta → desce
}
```
O comparador B mede a corrente de hold. O firmware ajusta o duty automaticamente para manter ~1.2A. **Não precisas de ajustar `HOLD_DUTY` à mão.**

### 4.5 LED de diagnóstico (novo)
| Estado | LED |
|--------|-----|
| Boot OK | 3 piscas lentas |
| Peak (1.5ms) | Aceso (verde) |
| Hold | Aceso (verde, mais fraco) |
| Fail-safe de sinal | 5 piscas rápidas |
| Sobrecorrente | 10 piscas rápidas (vermelho) |

---

## 5. Explicação das Melhorias vs Design Antigo

### 5.1 ATtiny85 em vez de Arduino Nano
| | v2 (Nano) | v3 (ATtiny85) |
|--|-----------|---------------|
| Custo | €3.00 | €1.20 |
| Pinos | 30 (muitos desperdiçados) | 8 (suficientes) |
| Consumo | ~30mA | ~5mA |
| Tamanho | 45×18mm | 9×7mm |
| Complexidade | Alta (headers, bootloader) | Baixa (DIP-8, soquete) |

O ATtiny85 tem tudo o que precisamos: Timer1 PWM (31.25kHz), interrupção INT0, watchdog, 5 pinos I/O. **Menos é mais.**

### 5.2 Proteção de corrente (sense resistor + comparador)
- **Antes:** se o injetor curto-circuitasse, o MOSFET IRLZ44N queimava (sem proteção).
- **Agora:** o LM393 monitoriza a corrente via R4 (0.05Ω). Acima de ~5A, corta a gate em microssegundos. **O MOSFET sobrevive a um curto.**

### 5.3 Fail-safe robusto
- **Antes:** só o pulldown R2 (10kΩ) protegia. Se o Arduino travasse com o MOSFET ligado, o injetor ficava aberto.
- **Agora:** 3 camadas — (1) pulldown R2, (2) timeout de sinal no firmware, (3) watchdog que reinicia. **Tripla proteção.**

### 5.4 LED de diagnóstico
- **Antes:** só um LED de alimentação. Difícil saber o que se passa.
- **Agora:** LED bicolor com códigos de erro (peak/hold/fail-safe/sobrecorrente). **Diagnóstico instantâneo.**

### 5.5 Proteção de tensão (TVS)
- **Antes:** sem proteção contra picos de 12V (carga do alternador, relés).
- **Agora:** TVS SMBJ16A absorve picos acima de 16V. **Protege o regulador e o ATtiny85.**

### 5.6 Watchdog
- **Antes:** se o Arduino travasse, ficava travado até desligar.
- **Agora:** watchdog reinicia em 2s. **Auto-recuperação.**

### 5.7 Calibração automática
- **Antes:** ajustar `PEAK_TIME_US` e `HOLD_DUTY` à mão.
- **Agora:** o comparador B + firmware ajustam o hold automaticamente. **Zero ajuste manual.**

---

## 6. Considerações de Segurança

### Dissipação térmica
- **MOSFET (IRLZ44N):** Rds(on) = 22mΩ. Hold: 1.2² × 0.022 = **0.03W**. Peak: 4² × 0.022 = 0.35W (só 1.5ms). **Sem dissipador.** ✅
- **Sense resistor R4 (0.05Ω 2W):** hold: 1.2² × 0.05 = **0.07W**. Peak: 4² × 0.05 = 0.8W (1.5ms). **Folga de 2W.** ✅
- **Bobine do injetor:** ~1.5W média a WOT (vs 13.2W atual). **Protegida.** ✅

### Proteções (camadas)
1. **Fusível 10A** no +12V — protege contra curto-circuito grave.
2. **Díodo flyback D1 (1N5822)** — absorve o pico indutivo quando o MOSFET corta.
3. **TVS SMBJ16A** — absorve picos de tensão da rede do carro.
4. **Comparador LM393** — corta a gate em sobrecorrente (microssegundos).
5. **Pulldown R2 (10kΩ)** — MOSFET desligado se o firmware falhar.
6. **Timeout de sinal** — injetor fecha se perder o Speeduino.
7. **Watchdog** — reinicia se o firmware travar.
8. **Terra estrela** — evita loops de terra.

### Falha segura (fail-safe)
- Se o ATtiny85 reiniciar → MOSFET desliga → **injetor fecha** → motor para, mas não inunda. ✅
- Se o Speeduino falhar → timeout fecha o injetor em 100ms. ✅
- Se o injetor curto-circuitar → comparador corta a gate. ✅

---

## 7. Teste em Bancada (OBRIGATÓRIO antes de instalar)

### Material
- Fonte 12V (ou bateria)
- ATtiny85 + módulo montado
- Multímetro
- Osciloscópio (ideal)
- LED + resistor 1kΩ (simula o injetor)

### Procedimento
1. **Gravar o firmware** no ATtiny85 (via Arduino como ISP, ou USBasp).
2. **Teste de boot:** ligar 12V → LED pisca 3× (boot OK).
3. **Teste de sinal:** ligar PB2 a GND (simula Speeduino a injetar) → LED acende. Soltar → apaga.
4. **Teste com LED (simula injetor):** +12V → LED → INJ-. Ligar sinal → LED acende forte (peak) depois mais fraco (hold).
5. **Teste de corrente:** multímetro em série → hold deve ser ~1.2A.
6. **Teste de sobrecorrente:** curto-circuitar INJ- a GND → LED pisca 10× (proteção ativou).
7. **Teste de fail-safe:** desligar o sinal a meio de um pulso → injetor fecha em 100ms, LED pisca 5×.
8. **Teste térmico:** 10 minutos com o LED → MOSFET frio (<40°C).

> **Só depois de passar todos os testes** é que se instala no carro.

---

## 8. Instalação no Veículo

### Passo 1: Remover
- Resistor de lastro 1.8Ω (já não é preciso).

### Passo 2: Ligar (4 fios)
```
Car +12V (ignição)   → módulo "12V"
Injetor negativo     → módulo "INJ-"
Speeduino INJ1 out   → módulo "SIG"
Chassis / GND        → módulo "GND"
```

### Passo 3: TunerStudio
- `injOpen` → **1.0 ms** (o peak-and-hold abre mais rápido que o resistor de lastro, que exigia 1.25ms).
- Se ficar pobre, sobe ligeiramente; se rico, desce.

### Passo 4: Verificar
1. Arrancar o motor.
2. Verificar AFR no datalog — resposta mais rápida.
3. Monitorizar temperatura do MOSFET (<40°C).
4. Verificar LED — deve acender a cada pulso de injeção.

---

## 9. Conclusão

A v3 resolve **todas as 7 limitações** da v2, é **mais barata** (€6–8 vs €8–10) e **mais robusta**:

- ✅ ATtiny85 (mais barato e simples)
- ✅ Proteção de corrente (LM393 + sense resistor)
- ✅ Fail-safe triplo (pulldown + timeout + watchdog)
- ✅ LED de diagnóstico
- ✅ Proteção TVS
- ✅ Watchdog
- ✅ Calibração automática do hold

**Próximo passo:** montar em bancada, testar conforme a secção 7, e só depois instalar no carro.
