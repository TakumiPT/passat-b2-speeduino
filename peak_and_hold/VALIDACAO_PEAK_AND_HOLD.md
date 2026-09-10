# ✅ VALIDAÇÃO DO DESIGN PEAK-AND-HOLD
## VW Passat B2 1.6 DT — Injetor Magneti Marelli IWM500.01 (2.0Ω low-Z)
**Data:** 2026-08-12 · **Autor:** Nó Hardware Engineer · **Estado:** VALIDADO (com 1 correção)

---

## 1. Resumo da Validação

O circuito peak-and-hold existente em `peak_and_hold/` está **tecnicamente correto** e cumpre o objetivo de proteger a bobine do injetor. Foi encontrada **1 correção necessária** no firmware (valor de hold) e **1 melhoria recomendada** (díodo flyback).

| Parâmetro | Spec pedido | Design atual | Veredicto |
|-----------|-------------|--------------|-----------|
| Corrente de peak | ~4A por ~1.5ms | **3.8A** em 1.5ms | ✅ OK |
| Corrente de hold | ~1.2A (PWM) | **1.04A** (HOLD_DUTY=44) | ⚠️ **CORRIGIR → 51** |
| Tensão | 12V (bateria) | 12V (ignição) | ✅ OK |
| Potência na bobine (WOT) | < 4.5W design | **~1.5W** (vs 13.2W atual) | ✅ Excelente |
| Dissipação no MOSFET | — | **~0.03W** (hold) | ✅ Sem dissipador |
| Proteção flyback | — | 1N5819 | ⚠️ Melhorar → 1N5822 |

**Resultado:** O design protege a bobine. Com a correção do `HOLD_DUTY`, fica exatamente dentro do spec.

---

## 2. Porquê Peak-and-Hold? (o problema que resolve)

O injetor IWM500.01 é **low-impedance (2Ω)** e foi desenhado para ser conduzido com **peak-and-hold** (como no Bosch Mono-Motronic original): muita corrente para abrir rápido, pouca para manter aberto.

### O problema atual (com resistor de lastro 1.8Ω)
```
+12V → Injetor (2Ω) → Resistor 1.8Ω → Speeduino INJ1 → GND
```
- Corrente contínua: I = 13.8V / (2Ω + 1.8Ω) = **3.63A**
- Potência na bobine: P = I² × R = 3.63² × 2 = **26.4W** (a 100% duty)
- A WOT (50% duty): **13.2W** — a bobine dissipa **3× a potência de design (4.5W)**
- **Risco:** a bobine aquece e pode derreter em regimes altos prolongados

### A solução peak-and-hold
| Fase | Corrente | Duração | Potência na bobine |
|------|----------|---------|--------------------|
| **Peak** (abrir) | ~4A | 1.5ms | 32W (só 1.5ms, energia pequena) |
| **Hold** (manter) | 1.2A | resto do pulso | 2.88W |
| **Média a WOT** | — | — | **~1.5W** ✅ |

**Resultado:** abre rápido (como sem resistor) mas a bobine só dissipa ~1.5W em vez de 13.2W. **~9× menos calor.**

---

## 3. Esquema Elétrico Completo

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
          │      │ -5.0  │ IN→OUT → Arduino Nano 5V
          │      └───┬───┘
          │          │
          │       ┌──┴──┐
          │       │100nF│ C3 (saída)
          │       └──┬──┘
          │          │
          │         GND
          │
          │      LED1 ▼ (verde, indicador)
          │        [1kΩ] R3
          │          │
          │         GND
          │
     INJ+ ●──────────┤
          │          │
       ┌──┴──┐   ┌───┴───┐
       │ INJ │   │ D1    │ 1N5822 Schottky flyback
       │ 2Ω  │   │ ┌─┘   │ Cátodo (banda) → +12V
       │     │   │▲│     │ Ânodo → INJ-
       └──┬──┘   └───────┘
          │
     INJ- ●─────── IRLZ44N Drain ──┐
                                    │
                     ┌──────────────┤ Q1 (IRLZ44N, TO-220)
                     │              │
                  Gate             Source
                     │              │
               ┌─────┤             GND (terra de potência)
               │     │
            [220Ω]   │
             R1      │
               │  ┌──┴──┐  ┌──┴──┐
               │  │10kΩ │  │100nF│
               │  │ R2  │  │ C4  │
               │  └──┬──┘  └──┬──┘
               │     │        │
    Arduino    │    GND      GND
    Nano D9 ───┘
    (PWM out)

    Speeduino INJ1 output ──→ Arduino Nano D2 (INPUT_PULLUP)
                              LOW = injetar (ativo-baixo)
                              HIGH = parado

    Speeduino GND ──→ Arduino Nano GND ──→ PCB GND (terra comum)
```

### Ligações (4 fios)
| Terminal | Fio | De → Para | Bitola |
|----------|-----|-----------|--------|
| **12V** | Vermelho | Ignição +12V (mesmo do injetor+) | 16 AWG (1.5mm²) |
| **INJ-** | Qualquer | Terminal negativo do injetor | 16 AWG (1.5mm²) |
| **SIG** | Qualquer | Saída Speeduino INJ1 | 22 AWG (só ~1mA) |
| **GND** | Preto | Chassis / GND Speeduino | 16 AWG (1.5mm²) |

> **Injetor positivo (+) fica ligado ao +12V** — não muda nada nesse lado.

---

## 4. Lista de Componentes (BOM)

| Ref | Componente | Valor | Encapsulamento | Qtd | Notas |
|-----|-----------|-------|----------------|-----|-------|
| U2 | Arduino Nano | ATmega328P | 2×15 pin | 1 | Clone chinês OK. "Old Bootloader" no IDE |
| Q1 | **IRLZ44N** | MOSFET N-ch logic-level | TO-220 | 1 | **NÃO usar IRFZ44N** (precisa 10V na gate) |
| D1 | **1N5822** | Díodo Schottky 3A 40V | DO-201 | 1 | Flyback. 1N5819 (1A) também funciona, mas 1N5822 dá mais margem |
| U1 | AMS1117-5.0 | Regulador 5V | SOT-223 | 1 | Alimenta o Nano. Alternativa: LM7805 |
| C1 | Eletrolítico | 100µF 25V | Radial | 1 | Filtro de entrada |
| C2 | Cerâmico | 100nF | Through-hole | 1 | Desacoplamento entrada |
| C3 | Cerâmico | 100nF | Through-hole | 1 | Saída do regulador |
| C4 | Cerâmico | 100nF | Through-hole | 1 | Filtro de ruído da gate |
| R1 | Resistor | 220Ω ¼W | Axial | 1 | Limite de corrente da gate |
| R2 | Resistor | 10kΩ ¼W | Axial | 1 | Pulldown da gate (evita flutuar) |
| R3 | Resistor | 1kΩ ¼W | Axial | 1 | LED de potência |
| LED1 | LED | Verde 3mm | Through-hole | 1 | Indicador de alimentação |
| J1 | Terminal parafuso | 2 pos 5.08mm | PCB | 1 | +12V / GND |
| J2 | Terminal parafuso | 2 pos 5.08mm | PCB | 1 | INJ- / SIG |
| — | Pin headers | 2×15 fêmea | 2.54mm | 2 | Soquete do Nano |
| F1 | **Fusível** | **10A** | Porta-fusível | 1 | **OBRIGATÓRIO** no +12V |

**Custo total:** ~€8–10 (IRLZ44N ~€0.50, Nano ~€3, resto ~€1, PCB ~€2).

---

## 5. Como Funciona — Passo a Passo (para leigos)

Imagina o injetor como uma **porta que precisa de um empurrão forte para abrir, mas depois só de uma força leve para ficar aberta**.

1. **Estado parado:** O Speeduino não está a injetar. A saída INJ1 está "flutuante" (o MOSFET interno está desligado). O módulo puxa essa linha para 5V com o resistor de 10kΩ → o Arduino lê **HIGH** → MOSFET Q1 desligado → injetor fechado.

2. **Speeduino quer injetar:** O MOSFET interno do Speeduino liga e puxa a linha INJ1 para **GND (LOW)**. O Arduino deteta esta mudança numa interrupção (resposta em microssegundos).

3. **Fase PEAK (abrir, ~1.5ms):** O Arduino liga o MOSFET Q1 **totalmente** (PWM 100%). A corrente sobe até ~3.8A. Esta corrente forte abre o injetor **rapidamente** (como se não houvesse resistor).

4. **Fase HOLD (manter):** Após 1.5ms, o Arduino reduz o PWM para **20%** (HOLD_DUTY=51). A corrente média cai para **1.2A** — suficiente para manter o injetor aberto, mas com muito pouco calor.

5. **Speeduino para de injetar:** A linha INJ1 volta a HIGH. O Arduino desliga o MOSFET Q1. O díodo D1 (flyback) absorve o pico de tensão da bobine quando a corrente é cortada (protege o MOSFET).

6. **Repete** a cada pulso de injeção (centenas de vezes por segundo).

> **O que o Arduino faz:** é o "cérebro" que decide quando dar o empurrão forte (peak) e quando reduzir para a força leve (hold). O Speeduino continua a mandar os comandos de injeção — o módulo só "interpreta" e conduz a corrente de forma inteligente.

---

## 6. Ligação ao Speeduino

- **Pino de injetor:** usa a saída **INJ1** (a mesma que hoje passa pelo resistor de lastro).
- **O que muda:** o fio que hoje vai do injetor− para o resistor/Speeduino passa a ir para o terminal **INJ-** do módulo. O fio da saída INJ1 do Speeduino passa a ir para o terminal **SIG** do módulo (só sinal, ~1mA — o MOSFET do Speeduino fica com carga zero).
- **O resistor de lastro é REMOVIDO** (já não é preciso).
- **Polaridade do sinal:** ativo-baixo (LOW = injetar). O firmware tem `INVERT_INPUT = true`, correto para esta cablagem.

### Ajuste no TunerStudio
- `injOpen` (Opening Time): reduzir para **1.0 ms** (o peak-and-hold abre mais rápido que o resistor de lastro, que exigia 1.25ms).
- **Atenção:** o valor atual é 1.25ms por causa do resistor. Com P&H, volta para ~1.0ms. Se ficar pobre, sobe ligeiramente; se rico, desce.

---

## 7. Considerações de Segurança

### Dissipação térmica
- **MOSFET (IRLZ44N):** Rds(on) = 22mΩ. Hold: 1.2² × 0.022 = **0.03W**. Peak: 4² × 0.022 = 0.35W (só 1.5ms). **Não precisa de dissipador.** ✅
- **Bobine do injetor:** ~1.5W média a WOT (vs 13.2W atual). **Protegida.** ✅
- **Regulador AMS1117:** alimenta só o Nano (~30mA). Frio. ✅

### Proteções
- **Fusível 10A** no +12V (obrigatório) — protege contra curto-circuito.
- **Díodo flyback D1 (1N5822)** — absorve o pico indutivo quando o MOSFET corta. Sem ele, o MOSFET morre.
- **Resistor R2 (10kΩ pulldown)** na gate — garante que o MOSFET fica desligado se o Arduino falhar (injetor nunca fica "preso aberto").
- **Terra estrela (star ground)** — todos os terras ligam num único ponto para evitar loops de terra.
- **Fios 16 AWG (1.5mm²)** no caminho de potência (aguenta 7A de pico).

### Falha segura (fail-safe)
- Se o Arduino reiniciar, o MOSFET desliga (R2 puxa a gate para GND) → **injetor fecha** → motor para, mas não inunda. ✅
- Se o Speeduino falhar, a linha INJ1 fica HIGH → injetor fecha. ✅

---

## 8. Teste em Bancada (OBRIGATÓRIO antes de instalar)

### Material
- Fonte de alimentação 12V (ou bateria de carro)
- Arduino Nano + módulo montado
- Multímetro
- Osciloscópio (ideal, mas não obrigatório)
- LED + resistor 1kΩ (para simular o injetor)

### Procedimento
1. **Gravar o firmware** `peak_and_hold_1ch.ino` no Nano (via USB).
2. **Abrir Serial Monitor** a 115200 baud → deve mostrar "Ready".
3. **Teste do sinal:** ligar um fio ao pino D2. Tocar o fio em **GND** (simula o Speeduino a injetar, ativo-baixo) → o LED do Nano acende. Soltar → apaga.
4. **Teste com LED (simula injetor):** ligar +12V → LED → terminal INJ-. Ligar o sinal D2 a GND. O LED deve:
   - Acender **forte** durante ~1.5ms (peak)
   - Depois ficar **mais fraco** (hold a 20%)
   - Apagar quando soltar o sinal
5. **Teste com osciloscópio (se tiver):** na saída D9 deve ver:
   - 5V contínuo por 1.5ms (peak)
   - Depois PWM a 20% (hold)
   - Depois 0V quando o sinal sai
6. **Teste de corrente (com multímetro em série):**
   - Durante o hold, a corrente média deve ser **~1.2A**
   - Se for muito baixa (<1A), aumentar `HOLD_DUTY`; se alta (>1.5A), diminuir
7. **Teste de polaridade do sinal:** confirmar que LOW = injeta. Se o injetor ficar sempre aberto, inverter `INVERT_INPUT` para `false`.
8. **Teste térmico:** deixar a funcionar 10 minutos com o LED. O MOSFET deve estar frio (<40°C).

> **Só depois de passar todos os testes** é que se instala no carro.

---

## 9. Correções Aplicadas

### 9.1 Firmware — `HOLD_DUTY` (CORREÇÃO NECESSÁRIA)
- **Antes:** `HOLD_DUTY = 44` (17%) → corrente de hold = 0.17 × 6A = **1.04A**
- **Depois:** `HOLD_DUTY = 51` (20%) → corrente de hold = 0.20 × 6A = **1.2A** ✅
- **Ficheiro:** `peak_and_hold_1ch.ino`

### 9.2 Díodo flyback (MELHORIA RECOMENDADA)
- **Antes:** 1N5819 (1A) — funciona, mas o pico de flyback pode chegar a 4A
- **Depois:** **1N5822 (3A)** — mais margem de segurança
- Se já tiver 1N5819, pode usar; mas 1N5822 é preferível.

---

## 10. Conclusão

O design peak-and-hold está **validado e pronto a montar** após a correção do `HOLD_DUTY` para 51. Ele:

- ✅ Abre o injetor rápido (~3.8A peak em 1.5ms)
- ✅ Mantém com 1.2A (hold a 20%)
- ✅ Reduz a potência da bobine de 13.2W para ~1.5W (**9× menos calor**)
- ✅ Protege o MOSFET (sem dissipador)
- ✅ É fail-safe (injetor fecha se algo falhar)
- ✅ Não requer modificações na placa Speeduino

**Próximo passo:** montar em bancada, testar conforme a secção 8, e só depois instalar no carro.