# 🔥 SYSTEM ARCHITECTURE: MULTI-AGENT HIERARCHY (Passat B2 Speeduino)

This project defines real subagents in `.github/agents/`. The assistant MUST
delegate to them using the `runSubagent` tool whenever the user's request
touches one of the technical domains below. Do NOT just describe the nodes —
actually invoke them.

## 🧭 Routing Rules — when to call which subagent

Match the user's intent to ONE primary domain, then delegate:

| User intent / keywords                                                                 | Primary subagent       |
|----------------------------------------------------------------------------------------|------------------------|
| VE tables, reqFuel, AFR target, lambda, TinyWB, ignition map, TunerStudio settings,    | `ecu_tuner`            |
| MSQ values, datalog interpretation, closed-loop, ASE/WUE, fuel trims                   |                        |
| Injector current/heat, coil overheating, P&H circuit, ballast resistor (1.8Ω/3.3Ω),    | `hardware_engineer`    |
| Speeduino board v0.4.4c wiring, VNLD5090-E driver, injOpen due to resistor             |                        |
| Fuel pressure (1.2–2.0 bar), FPR adjustment, injector sizing (IWM500.01 / ICD00105),   | `mechanical_expert`    |
| Turbo upgrade math, EA827 mechanical limits, hydraulic lifters, monoponto vs MPI       |                        |
| Symptom spans 2+ domains (e.g. "misfire at WOT", "overheating at high duty"),          | `supervisor` (it will  |
| diagnostic where root cause is unclear, full datalog review, planning a change         | fan out to specialists)|

Heuristics:
- If exactly ONE domain applies → call that specialist directly (one `runSubagent`).
- If TWO or more domains apply, OR the user gives a symptom/log without a clear
  category → call `supervisor` and let it orchestrate.
- Trivial/meta questions (e.g. "what file is this?", git, formatting, English
  translation) → answer directly, NO subagent.

## 🛠️ How to invoke

Use the `runSubagent` tool with:
- `agentName`: one of `supervisor`, `ecu_tuner`, `hardware_engineer`,
  `mechanical_expert`.
- `prompt`: include (a) the user's question verbatim, (b) any relevant numbers
  already known from `/memories/repo/passat-quick-reference.md` (injector 2Ω,
  IWM500.01, fw 2025.01.6, current FPR ~1.2 bar, etc.), and (c) what you want
  returned (e.g. "give the VE scaling factor and the affected RPM/MAP zones").
- `description`: 3–5 words.

Multiple independent specialists can be called in parallel in the same tool
batch. Dependent calls (specialist needs supervisor's plan) must be sequential.

## 📐 Hard constraints the subagents must respect

These are non-negotiable facts of this build. Pass them through in prompts when
relevant so the subagent doesn't second-guess them:

- Injector IWM500.01 is 2Ω, direct-driven by VNLD5090-E (~7 A continuous,
  98 W instantaneous). High-duty operation is a thermal risk for the injector
  coil, not the driver.
- Firmware Speeduino 2025.01.6. reqFuel was computed at 60 lb/hr @ 3.0 bar
  but the rail runs ~1.2 bar (~37 lb/hr), so VE > 100% at WOT is EXPECTED —
  do not "correct" it down.
- Lambda: Bosch LSU 4.9 + TinyWB Rev1, `egoType="Wide Band"`.
- Ballast resistor: 1.8Ω 25W is the approved temporary fix → set
  `injOpen = 1.1 ms`. The 3.3Ω resistor is FORBIDDEN (failed cranking).
- Knock sensor must NOT be installed (hydraulic lifters cause false triggers).
- DFCO must stay OFF while ignition is on the mechanical distributor
  (backfire risk).

## 📤 Output format

Start every reply that used delegation with a single header line listing the
subagents actually invoked, e.g.:

`**[Subagents: 👑 supervisor → ⚡ hardware_engineer → 📊 ecu_tuner]**`

Then give ONE unified, plain-language answer (Portuguese if the user wrote in
Portuguese). Do NOT dump each subagent's raw report; synthesize.

If you answered without any subagent (trivial/meta), do NOT print the header.
