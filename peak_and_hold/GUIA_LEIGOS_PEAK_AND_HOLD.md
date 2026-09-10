# 🛠️ GUIA PARA LEIGOS — Peak-and-Hold Injector Driver
## Como montar e entender o circuito que protege o teu injector

**VW Passat B2 1.6 DT · Gol G2 SPI Monoponto · Speeduino v0.4.4c**

> Este guia é para **qualquer pessoa**, mesmo sem conhecimentos de eletrónica.
> Explica o PORQUÊ, o COMO e o QUE COMPRAR, passo a passo.

---

## 🎯 O QUE É ISTO E PORQUE PRECISAS

### O problema (em linguagem simples)

O teu injector é como uma **porta com mola forte**. Para a abrir, precisas de um **empurrão forte** (muita corrente). Mas depois de aberta, só precisas de **segurá-la** (pouca corrente).

O teu carro agora faz assim:
- Dá **sempre** o empurrão forte (3.6A) durante todo o tempo que o injector está aberto
- Isto é como segurar a porta com toda a força o tempo todo → **cansa e aquece**

**Resultado:** a bobine do injector aquece 3 a 5× mais do que devia. Com o tempo, pode derreter.

### A solução (peak-and-hold)

Faz como o fabricante original desenhava:
1. **PEAK** (empurrão): dá corrente forte (~4A) por **1.5 milissegundos** → abre a porta
2. **HOLD** (segurar): reduz para corrente fraca (~1.2A) → mantém a porta aberta

**Resultado:** abre rápido E aquece pouco. **~9× menos calor.**

---

## 📊 COMPARAÇÃO SIMPLES

| Método | Empurrão | Segurar | Calor na bobine | Veredicto |
|--------|----------|---------|-----------------|-----------|
| **Directo** (sem nada) | 7A sempre | 7A sempre | 98W 🔥🔥🔥 | Perigoso |
| **Resistor 1.8Ω** (atual) | 3.6A sempre | 3.6A sempre | 13W 🔥🔥 | Funciona, mas aquece |
| **Peak-and-Hold** (este) | 4A por 1.5ms | 1.2A | **1.5W** ✅ | **Melhor** |

---

## 🧰 O QUE PRECISAS COMPRAR (BOM)

| Componente | Quantidade | Valor | Onde | Custo aprox. |
|------------|-----------|-------|------|--------------|
| Arduino Nano | 1 | — | AliExpress/Amazon | €3–5 |
| MOSFET IRLZ44N | 1 | Lógica-level | Loja eletrónica | €1–2 |
| Díodo Schottky 1N5822 | 1 | 3A | Loja eletrónica | €0.50 |
| Regulador AMS1117-5.0 | 1 | 5V | Loja eletrónica | €0.50 |
| Condensador 100µF 25V | 1 | Eletrolítico | Loja eletrónica | €0.30 |
| Condensador 100nF | 3 | Cerâmico | Loja eletrónica | €0.10 cada |
| Resistência 220Ω | 1 | 1/4W | Loja eletrónica | €0.05 |
| Resistência 10kΩ | 1 | 1/4W | Loja eletrónica | €0.05 |
| Resistência 1kΩ | 1 | 1/4W | Loja eletrónica | €0.05 |
| LED verde | 1 | — | Loja eletrónica | €0.10 |
| Fusível 10A + porta-fusível | 1 | — | Loja auto | €2 |
| Fio 16 AWG (1.5mm²) | 2m | Vermelho+Preto | Loja auto | €3 |
| Fio 22 AWG | 1m | Sinal | Loja auto | €1 |
| **Total** | | | | **~€12–15** |

---

## 🔌 COMO LIGAR (4 fios — muito simples)

O módulo tem **4 terminais**. Liga assim:

```
┌─────────────────────────────────────────────────────────┐
│                    +12V (ignição)                        │
│                      │  (com fusível 10A)                │
│   ┌──────────┐       │                                  │
│   │ INJECTOR │+──────┘                                  │
│   │  (2Ω)    │-──────→  TERMINAL "INJ-" do módulo       │
│   └──────────┘                                          │
│                                                         │
│   Speeduino INJ1 output ──→  TERMINAL "SIG" do módulo   │
│   (só sinal, ~1mA)                                      │
│                                                         │
│   Chassis / GND Speeduino ──→  TERMINAL "GND" do módulo │
│                                                         │
│   +12V ignição ─────────────→  TERMINAL "12V" do módulo │
└─────────────────────────────────────────────────────────┘
```

### Passo a passo

1. **Desliga a bateria** (segurança primeiro!)
2. **Remove o resistor de lastro 1.8Ω** (já não é preciso)
3. **Liga o injector+ ao +12V** (como está agora, não muda)
4. **Liga o injector- ao terminal "INJ-"** do módulo
5. **Liga a saída INJ1 do Speeduino ao terminal "SIG"** do módulo
6. **Liga o chassis ao terminal "GND"** do módulo
7. **Liga o +12V da ignição ao terminal "12V"** do módulo
8. **Religa a bateria**

> ⚠️ **IMPORTANTE:** O injector- **NÃO** vai mais para o Speeduino. O Speeduino só envia o sinal (~1mA). O módulo faz todo o trabalho de corrente.

---

## 🧠 COMO FUNCIONA (explicação simples)

### O Arduino Nano é o "cérebro"

1. **Vê o sinal** do Speeduino (quando o Speeduino quer injetar, manda um sinal)
2. **Abre o MOSFET** (interruptor de potência) com força total → **PEAK** (4A)
3. **Espera 1.5ms** (tempo para o injector abrir)
4. **Reduz a força** do MOSFET → **HOLD** (1.2A) → mantém aberto
5. **Quando o Speeduino para**, fecha o MOSFET → injector fecha

### O MOSFET é o "interruptor forte"

- É um interruptor eletrónico que aguenta a corrente do injector
- O Arduino controla-o (liga/desliga/regula)

### O díodo é o "amortecedor"

- Quando o injector desliga, a bobine gera um "pico" de energia
- O díodo absorve esse pico → protege o MOSFET

---

## 💻 O FIRMWARE (o programa do Arduino)

O ficheiro `peak_and_hold_1ch.ino` já está pronto. Só precisas de:

1. **Instalar o Arduino IDE** (gratuito em arduino.cc)
2. **Abrir** o ficheiro `peak_and_hold_1ch.ino`
3. **Ligar o Arduino Nano** ao computador (USB)
4. **Carregar** o programa (botão "Upload")
5. **Configurar** (se necessário):
   - `PEAK_TIME_US = 1500` → tempo de empurrão (1.5ms)
   - `HOLD_DUTY = 51` → força de segurar (1.2A)
   - `INVERT_INPUT = true` → sinal ativo-baixo (Speeduino)

---

## 🧪 TESTAR ANTES DE INSTALAR (obrigatório!)

**Nunca instales no carro sem testar em bancada.** Segue estes passos:

### Material para o teste
- Fonte de alimentação 12V (ou bateria)
- Multímetro
- O injector (ou uma lâmpada de 12V como substituto)

### Passos
1. **Liga o módulo** à fonte 12V
2. **Liga o injector** (ou lâmpada) ao módulo
3. **Liga um sinal de teste** ao "SIG" (podes usar um botão que liga a GND)
4. **Carrega o firmware** no Arduino
5. **Pressiona o botão** (simula o Speeduino a injetar)
6. **Ouve/observa:** o injector deve "clicar" (abrir) e a lâmpada deve acender
7. **Mede a corrente:** deve ser ~4A no pico, ~1.2A depois
8. **Se funcionar**, está pronto para o carro

---

## ⚙️ AJUSTE NO TUNERSTUDIO (depois de instalar)

Com o peak-and-hold, o injector abre **mais rápido** (sem o resistor a atrasar).

| Parâmetro | Antes (resistor) | Depois (P&H) |
|-----------|-------------------|--------------|
| `injOpen` | 1.25 ms | **1.0 ms** |

> Aplica no TunerStudio + Burn. **Não edites o MSQ diretamente.**

---

## ⚠️ SEGURANÇA

| Regra | Porquê |
|-------|--------|
| **Fusível 10A** no +12V | Protege contra curto-circuito |
| **Desliga a bateria** antes de mexer | Evita faíscas/choques |
| **Terra estrela** (todos os GND juntos) | Evita ruído elétrico |
| **Testa em bancada primeiro** | Evita danos no carro |
| **Não toques no MOSFET quente** | Pode aquecer em uso |

---

## ❓ PERGUNTAS FREQUENTES

### "Preciso mesmo disto?"
Se o teu injector aquece em condução prolongada (WOT/auto-estrada), **sim**. O resistor 1.8Ω funciona, mas aquece a bobine 3× mais que o design.

### "É difícil de montar?"
**Não.** São ~10 componentes e 4 fios. Se sabes soldar, consegues.

### "Quanto custa?"
**~€12–15** em componentes. Muito mais barato que um injector novo.

### "O que acontece se falhar?"
O módulo tem fail-safe: se o Arduino não receber sinal, o injector fica fechado (motor não injeta). Seguro.

### "E a bateria fraca?"
O peak-and-hold **não resolve** o problema da bateria fraca (5–6V no arranque). Isso é outra coisa — substitui/carrega a bateria.

---

## 📁 FICHEIROS DO PROJETO

| Ficheiro | O que é |
|----------|---------|
| `peak_and_hold_1ch.ino` | O firmware do Arduino (pronto a carregar) |
| `README.md` | Documentação técnica completa |
| `VALIDACAO_PEAK_AND_HOLD.md` | Validação do design (hardware_engineer) |
| `GUIA_LEIGOS_PEAK_AND_HOLD.md` | **Este guia** — para qualquer pessoa |

---

**Boa sorte!** Com este módulo, o teu injector vai abrir rápido, aquecer pouco, e durar muito mais.