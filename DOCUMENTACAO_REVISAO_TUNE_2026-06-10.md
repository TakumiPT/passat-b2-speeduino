# 📋 Documentação — Revisão Completa da Tune (CurrentTune.msq)

**Data:** 10 de junho de 2026
**Projeto:** VW Passat B2 (1984) — 1.6 DT EA827 — Conversão EFI Monoponto
**ECU:** Speeduino v0.4.4c SMD — Firmware 2025.01.6
**Revisão por:** GitHub Copilot — Supervisor 👑 + ecu_tuner 📊

---

## 1. Hardware de Referência

| Item | Valor |
|---|---|
| Motor | EA827 1.6 (1595 cc, 8v, taqués hidráulicos) |
| Injeção | Monoponto TBI, 1 injetor IWM500.01 (2 Ω, low-Z) |
| Driver injetor | VNLD5090-E + balastro 1.8 Ω 25 W (3.3 Ω PROIBIDO) |
| Pressão de combustível | ~1.2 bar (~37 lb/hr) — reqFuel calculado p/ 3.0 bar (60 lb/hr) |
| Ignição | Distribuidor mecânico + Bosch Módulo 124 (avanço centrífugo/vácuo do distribuidor — **estado a confirmar**) |
| Lambda | Bosch LSU 4.9 + TinyWB Rev1 — **AVARIADO** (pino 6 UN sem contacto, AFR preso em 19.7) |
| IAC | Stepper via DRV8825 — em depuração, idle atual no parafuso (~1100-1200 RPM) |

> ⚠️ **VE > 100% em WOT é ESPERADO** (fator ≈1.62 pelo desvio de pressão do reqFuel). NÃO corrigir para baixo.

---

## 2. 🔴 Problemas CRÍTICOS Encontrados

### 2.1 injOpen = 1.2 ms (spec aprovada: 1.1 ms)
Com o balastro 1.8 Ω o valor aprovado é **1.1 ms**. O excesso de 0.1 ms adiciona ~3-5% de combustível ao idle.

> ℹ️ **Correção de revisão (13-jun-2026):** a antiga "Tabela do IAC invertida" foi **despromovida** de crítico para aviso (ver §3 e §9). Com `iacStepperInv=Yes` o home do stepper muda de extremo, o que pode tornar a tabela ascendente CORRETA. Só um teste de bancada decide — não é um erro confirmado.

---

## 3. 🟡 Avisos (corrigir quando conveniente)

| Item | Valor atual | Problema | Ação |
|---|---|---|---|
| `CTPSEnabled` | On (Inverted) | Input de CTPS que não existe — pino a flutuar | Desligar |
| TPS cal | tpsMin=30 / tpsMax=147 | Historicamente TPS só chega a ~60% → flood clear (80%) inalcançável | Recalibrar a pedal a fundo |
| Cranking quente | 200% @ 70 °C | Algo rico (típico 140-160%) | Baixar se arranque quente fumar |
| Direção tabela IAC | sobe com temp. (0→165) | Pode estar certa OU invertida conforme o home (`iacStepperInv=Yes`) | **Verificar em bancada** antes de ativar o stepper |
| Avanço total | Tabela até 40° | Soma-se ao avanço mecânico/vácuo **se o distribuidor não estiver trancado (a confirmar)** | Verificar com pistola de ponto |
| `egoLimit` | 15% | Demasiada autoridade para primeiro closed-loop | Reduzir p/ 5-7% quando ativar |
| `numTeeth=12 / missingTeeth=1` | — | Resíduo ignorado pelo Basic Distributor | Inofensivo (limpar por arrumação) |

---

## 4. ✅ Confirmado Correto (NÃO mexer)

- `dfcoEnabled=Off` — obrigatório (distribuidor mecânico, risco de backfire)
- `knock_mode=Off` — obrigatório (taqués hidráulicos dão falsos positivos)
- `egoAlgorithm="No correction"` — correto enquanto o sensor está avariado
- reqFuel=4.3 ms, TBI, 1 injetor, simultâneo, divider=1, Speed-Density (MAP), stoich 14.7
- mapMin=10 / mapMax=260 — calibração MPX4250 correta
- Trigger: Basic Distributor, FALLING, Single Channel, Going Low — correto p/ Bosch 124
- Dwell: 4.5 ms cranking / 3.0 ms run / limite 8 ms
- Limitadores: soft 6000 (-20°, 2 s) / hard 6200 corte total
- `engineProtectMaxRPM=2500` — é o RPM MÍNIMO para proteções atuarem (não é limitador)
- Curva de correção de tensão do injetor POPULADA (ver §10)
- AE, WUE, AFR targets — estrutura sã (refinar só após wideband funcionar)

---

## 5. Tabela VE — MAP (kPa) × RPM (%)

Linhas = MAP (carga, kPa) · Colunas = RPM · Valores = VE %

| MAP\RPM | 500 | 700 | 900 | 1100 | 1300 | 1600 | 1900 | 2200 | 2500 | 3000 | 3500 | 4000 | 4500 | 5000 | 5600 | 6200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **100** | 89 | 92 | 92 | 93 | 92 | 93 | 93 | 94 | 94 | 94 | 92 | 89 | 86 | 83 | 81 | 78 |
| **96** | 87 | 88 | 90 | 90 | 90 | 91 | 91 | 92 | 92 | 91 | 90 | 87 | 84 | 81 | 79 | 76 |
| **90** | 81 | 84 | 85 | 85 | 86 | 87 | 86 | 86 | 86 | 86 | 84 | 83 | 80 | 77 | 76 | 72 |
| **86** | 77 | 79 | 80 | 81 | 82 | 81 | 83 | 83 | 83 | 83 | 81 | 79 | 77 | 74 | 72 | 70 |
| **76** | 69 | 72 | 75 | 74 | 75 | 76 | 76 | 77 | 77 | 77 | 75 | 74 | 71 | 69 | 67 | 64 |
| **70** | 65 | 69 | 70 | 71 | 71 | 72 | 72 | 72 | 73 | 72 | 71 | 69 | 68 | 65 | 63 | 61 |
| **66** | 60 | 64 | 66 | 67 | 68 | 67 | 68 | 68 | 68 | 68 | 67 | 65 | 64 | 62 | 60 | 58 |
| **60** | 55 | 60 | 61 | 63 | 63 | 64 | 65 | 65 | 65 | 65 | 64 | 62 | 61 | 59 | 57 | 55 |
| **56** | 51 | 56 | 58 | 59 | 60 | 61 | 61 | 62 | 62 | 62 | 61 | 59 | 58 | 56 | 55 | 52 |
| **50** | 47 | 51 | 54 | 55 | 56 | 57 | 58 | 58 | 59 | 58 | 58 | 56 | 55 | 53 | 52 | 51 |
| **46** | 44 | 47 | 50 | 52 | 53 | 54 | 55 | 55 | 55 | 55 | 55 | 54 | 52 | 51 | 50 | 49 |
| **40** | 42 | 45 | 47 | 49 | 50 | 51 | 52 | 53 | 53 | 53 | 52 | 52 | 50 | 49 | 48 | 47 |
| **36** | 41 | 43 | 44 | 46 | 47 | 49 | 50 | 50 | 51 | 51 | 50 | 49 | 48 | 47 | 46 | 45 |
| **30** | 41 | 41 | 42 | 44 | 45 | 46 | 47 | 48 | 48 | 48 | 48 | 47 | 46 | 45 | 44 | 43 |
| **26** | 41 | 41 | 41 | 42 | 43 | 44 | 45 | 45 | 46 | 46 | 46 | 45 | 44 | 43 | 42 | 41 |
| **16** | 40 | 40 | 40 | 40 | 40 | 41 | 41 | 41 | 41 | 41 | 41 | 41 | 40 | 39 | 38 | 37 |

### 5.1 Correções de suavização propostas (review estrutural)

| MAP (kPa) | RPM | Atual → Proposto |
|---:|---:|---:|
| 50 | 2500 | 59 → 58 |
| 56 | 6200 | 52 → 53 |
| 66 | 1600 | 67 → 68 |
| 70 | 2500 | 73 → 72 |
| 76 | 900 | 75 → 74 |
| 76 | 1100 | 74 → 75 |
| 86 | 1600 | 81 → 82 |
| 90 | 1600 | 87 → 86 |
| 90 | 5600 | 76 → 74 |
| 100 | 1300 | 92 → 93 |

Notas da review VE:
- Monotonicidade das colunas: ✅ PASSA
- Queda de VE após 4000 RPM: correta para motor 8v monoponto — NÃO aplanar
- VE final esperado em WOT após wideband funcionar: ~105-117% no pico
- Se for preciso WOT antes do sensor estar arranjado: +5% só nas linhas 96/100 kPa (segurança)

---

## 6. Tabela de Avanço de Ignição — MAP (kPa) × RPM (graus)

Linhas = MAP (kPa) · Colunas = RPM · Valores = ° APMS

| MAP\RPM | 500 | 1000 | 1500 | 2000 | 2500 | 3000 | 3500 | 4000 | 4500 | 5000 | 5500 | 6000 | 6500 | 7000 | 8000 | 9000 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **100** | 14 | 18 | 20 | 22 | 24 | 26 | 28 | 30 | 32 | 33 | 33 | 33 | 33 | 32 | 31 | 30 |
| **96** | 16 | 20 | 22 | 24 | 26 | 28 | 30 | 32 | 34 | 34 | 34 | 34 | 34 | 33 | 32 | 31 |
| **88** | 18 | 22 | 24 | 26 | 28 | 30 | 32 | 34 | 35 | 35 | 35 | 35 | 35 | 34 | 33 | 32 |
| **80** | 18 | 24 | 26 | 28 | 30 | 32 | 34 | 35 | 36 | 36 | 36 | 36 | 36 | 35 | 34 | 33 |
| **74** | 18 | 26 | 28 | 30 | 32 | 33 | 35 | 36 | 37 | 37 | 37 | 37 | 37 | 36 | 35 | 34 |
| **66** | 18 | 28 | 30 | 32 | 33 | 34 | 36 | 37 | 38 | 38 | 38 | 38 | 38 | 37 | 36 | 35 |
| **56** | 18 | 30 | 32 | 33 | 34 | 35 | 37 | 38 | 39 | 39 | 39 | 39 | 39 | 38 | 37 | 36 |
| **50** | 18 | 30 | 32 | 34 | 35 | 36 | 38 | 39 | 40 | 40 | 40 | 40 | 40 | 39 | 38 | 37 |
| **46** | 18 | 30 | 32 | 34 | 36 | 37 | 39 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 39 | 38 |
| **40** | 18 | 30 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 39 |
| **36** | 18 | 30 | 34 | 36 | 37 | 39 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **30** | 18 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **26** | 18 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **20** | 18 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **16** | 18 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **10** | 18 | 32 | 34 | 36 | 38 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |

Notas:
- Coluna de 500 RPM ≈ 18° na maioria das cargas (mas **16° a 96 kPa e 14° a 100 kPa**) = boa prática (evita hunting do idle)
- ⚠️ Os 40° de carga leve PODEM SOMAR-SE ao avanço mecânico/vácuo **se o distribuidor não estiver trancado (a confirmar)** — verificar avanço TOTAL com pistola de ponto antes de confiar
- `FixAng=12` inerte (fixAngEnable=Off); cranking usa `CrankAng=12` ✅

---

## 7. Tabela de AFR Alvo — MAP (kPa) × RPM

Linhas = MAP (kPa) · Colunas = RPM · Valores = AFR

| MAP\RPM | 500 | 700 | 900 | 1200 | 1500 | 1800 | 2200 | 2700 | 3000 | 3400 | 3900 | 4300 | 4800 | 5200 | 5700 | 6200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **100** | 12.2 | 12.2 | 12.3 | 12.3 | 12.4 | 12.5 | 12.5 | 12.5 | 12.5 | 12.5 | 12.6 | 12.7 | 12.8 | 12.9 | 13.0 | 13.2 |
| **96** | 12.2 | 12.2 | 12.3 | 12.3 | 12.4 | 12.5 | 12.5 | 12.5 | 12.5 | 12.5 | 12.6 | 12.7 | 12.8 | 12.9 | 13.0 | 13.2 |
| **90** | 12.5 | 12.5 | 12.5 | 12.6 | 12.6 | 12.7 | 12.8 | 12.8 | 12.8 | 12.8 | 12.9 | 13.0 | 13.0 | 13.1 | 13.2 | 13.4 |
| **86** | 12.8 | 12.8 | 12.8 | 12.9 | 12.9 | 13.0 | 13.0 | 13.0 | 13.0 | 13.0 | 13.1 | 13.2 | 13.2 | 13.3 | 13.4 | 13.5 |
| **76** | 13.0 | 13.0 | 13.0 | 13.1 | 13.1 | 13.2 | 13.2 | 13.2 | 13.2 | 13.2 | 13.3 | 13.4 | 13.4 | 13.5 | 13.6 | 13.7 |
| **70** | 13.2 | 13.2 | 13.3 | 13.3 | 13.4 | 13.5 | 13.5 | 13.5 | 13.5 | 13.5 | 13.6 | 13.7 | 13.7 | 13.8 | 13.9 | 14.0 |
| **66** | 13.5 | 13.5 | 13.6 | 13.6 | 13.7 | 13.8 | 13.8 | 13.8 | 13.8 | 13.8 | 13.9 | 14.0 | 14.0 | 14.1 | 14.2 | 14.3 |
| **60** | 13.8 | 13.8 | 13.9 | 13.9 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.1 | 14.2 | 14.2 | 14.3 | 14.4 | 14.5 |
| **56** | 14.0 | 14.0 | 14.1 | 14.1 | 14.2 | 14.2 | 14.2 | 14.2 | 14.2 | 14.2 | 14.3 | 14.4 | 14.4 | 14.5 | 14.5 | 14.6 |
| **50** | 14.3 | 14.3 | 14.4 | 14.4 | 14.5 | 14.5 | 14.5 | 14.5 | 14.5 | 14.5 | 14.5 | 14.6 | 14.6 | 14.7 | 14.7 | 14.7 |
| **46** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |
| **40** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |
| **36** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |
| **30** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |
| **26** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |
| **16** | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 | 14.7 |

✅ Estrutura sensata: 14.7 em cruzeiro → 12.2-13.2 em WOT.

---

## 8. Curvas de Enriquecimento

### 8.1 Cranking (arranque)

| Temp (°C) | Enriquecimento (%) |
|---:|---:|
| -40 | 280 |
| 0 | 230 |
| 30 | 210 |
| 70 | 200 ⚠️ (algo rico, típico 140-160) |

### 8.2 ASE (Afterstart Enrichment)

| Temp (°C) | % | Duração (s) |
|---:|---:|---:|
| -20 | 100 | 25 |
| 0 | 90 | 20 |
| 40 | 60 | 15 |
| 80 | 30 | 6 |

### 8.3 WUE (Warmup Enrichment)

| Temp (°C) | -40 | -26 | 10 | 19 | 28 | 37 | 50 | 65 | 80 | 90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **%** | 195 | 190 | 182 | 154 | 150 | 138 | 122 | 110 | 102 | 100 |

### 8.4 Prime Pulse

| Temp (°C) | -20 | 0 | 40 | 82 |
|---|---:|---:|---:|---:|
| **ms** | 8.0 | 6.0 | 3.0 | 2.0 |

### 8.5 AE — Aceleração (TPS, PW Adder)

| TPS rate (%/s) | 70 | 220 | 430 | 790 |
|---|---:|---:|---:|---:|
| **Adder (%)** | 50 | 80 | 110 | 140 |

`aeTime=300 ms` · `taeThresh=40 %/s` · taper 5000→6200 RPM · `aeColdPct=100` (sem boost frio)

---

## 9. Tabelas IAC (⚠️ DIREÇÃO A VERIFICAR EM BANCADA)

> **Correção de revisão (13-jun-2026):** anteriormente marcadas como "invertidas/erradas" — isso foi **excesso de confiança**. Com `iacStepperInv=Yes` o stepper faz o homing para o extremo oposto, por isso a tabela ascendente (0 passos a frio → 165 a quente) pode estar **CORRETA** (se home = válvula aberta). Não é decidível só pelo MSQ — **testar em bancada**: enviar passos e ver se a válvula abre ou fecha. Só depois reescrever, se necessário.

### 9.1 iacOLStepVal (run) — valores atuais

| Temp (°C) | -26 | 2 | 22 | 39 | 53 | 66 | 82 | 96 | 107 | 117 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Passos** | 0 | 24 | 54 | 90 | 126 | 156 | 165 | 165 | 165 | 165 |

Interpretação depende do home: se **home = válvula fechada**, está invertida (frio devia ter mais passos); se **home = válvula aberta** (provável, dado `iacStepperInv=Yes`), está correta. Confirmar em bancada.

### 9.2 iacCrankSteps

| Temp (°C) | -21 | 0 | 37 | 65 |
|---|---:|---:|---:|---:|
| **Passos** | 0 | 0 | 54 | 141 |

Config: `Stepper Open Loop` · stepTime=3 ms · home=165 ⚠️ (> max 162) · hyster=3 · inv=Yes · power=When Active (usar "Always On" só p/ testes de bancada) · Vref do DRV8825 deve ser ~0.35 V (0.7 A), NUNCA 3 V

---

## 10. Correção de Tensão do Injetor (populada ✅)

| Tensão (V) | 6.6 | 9.4 | 12.1 | 14.8 | 16.9 | 20.3 |
|---|---:|---:|---:|---:|---:|---:|
| **Correção (%)** | 255 | 176 | 127 | 100 | 86 | 70 |

Modo: "Open Time only" — adequado. Confirmar comportamento ao idle com variação de carga elétrica.

---

## 11. Plano de Ação Prioritizado

### Agora (sem wideband)
1. `injOpen` 1.2 → **1.1 ms**
2. `CTPSEnabled` → **Off**
3. Recalibrar **TPS** a pedal a fundo (confirmar 100% em log)
4. **Verificar direção das tabelas IAC em bancada** (NÃO assumir que estão erradas; ver §9) + corrigir `iacStepHome=165` → ≤ 162 — antes de ativar o stepper; Vref ~0.35 V
5. Aplicar as 10 correções de células VE (§5.1)
6. Verificar avanço TOTAL com pistola de ponto (idle e cruzeiro)
7. Arrumação: zerar numTeeth/missingTeeth; baixar cranking quente se necessário

### Depois do pino 6 do JPT arranjado (terminais 2.8 mm a caminho)
1. Datalog limpo 2-3 min → confirmar AFR vivo
2. Ativar closed-loop com `egoLimit` 5-7% (não 15%)
3. Afinar VE com dados reais: cruzeiro (30-70 kPa / 1500-3500 RPM) primeiro, depois WOT (esperar VE ~105-117%)
4. Refinar WUE/ASE com logs de aquecimento
5. Vigiar duty do injetor em WOT (limite térmico do IWM500.01)
6. **DFCO continua OFF** enquanto a ignição estiver no distribuidor mecânico

---

## 12. Restrições Permanentes do Projeto

- ❌ Sensor de knock NUNCA instalar (taqués hidráulicos = falsos positivos)
- ❌ DFCO OFF enquanto houver distribuidor mecânico (risco de backfire)
- ❌ Balastro 3.3 Ω PROIBIDO (falhou no cranking) — usar 1.8 Ω + injOpen 1.1 ms
- ✅ VE > 100% em WOT é esperado e suportado (máx 255 na Speeduino)

*Documento gerado a partir da revisão do CurrentTune.msq (writeDate 01-jun-2026) e datalogs de maio/junho de 2026.*

**Histórico de revisões:** 10-jun-2026 (criação) · 13-jun-2026 (auto-revisão: IAC despromovida de crítico→verificar em bancada com raciocínio correto do `iacStepperInv`; correção da nota dos 18° → 16°/14° nas cargas altas; avanço do distribuidor marcado "a confirmar").*
