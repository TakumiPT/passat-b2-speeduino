# Investigation Findings — 2026-08-09

## Summary

This file captures the latest findings for the VW Passat B2 1.6 DT Speeduino EFI conversion so the current state can be committed to Git.

## Key Findings

- **New wideband sensor validated and installed.** The old Bosch LSU 4.9 was confirmed bad due to a failed heater circuit and fouling. The new LSU responds correctly to a free-air / flame test with the TinyWB controller.
- **Wideband output behavior clarified.** TinyWB free-air ceiling is 19.7 AFR, not 20.9. Current tuning remains open-loop until a hot-engine log is captured with the new sensor.
- **Cold-start fix confirmed.** The engine now starts on first crank without brake cleaner or key cycling with the new priming and cranking enrichment values.
- **IAC idle control remains dead.** The Bosch 0269980492 stepper and DRV8825 driver were replaced, but the IAC still does not move. Idle control is currently mechanical via the butterfly screw.
- **Battery is a remaining secondary blocker.** The existing battery is weak; low resting voltage and cranking sag mean the engine is still vulnerable to inconsistent starting.
- **Wideband tuning is still blocked.** AFR-based VE autotuning is not safe until the new LSU is logged in a stable operating condition.
- **Project log and status documents should be backed up.** This findings file is created for git backup to preserve the current diagnosis.

## Current Status

- Wideband (LSU + TinyWB): **new sensor installed, validated, open-loop until verified hot-engine operation**
- Cold start: **fixed with confirmed priming/cranking values**
- IAC: **not moving, mechanical idle only**
- Battery: **weak, replace or charge fully**
- VE tuning: **frozen until wideband is validated and true WOT/pedal travel is confirmed**

## Actions Taken

- Validated new LSU with flame test and correct rich/lean response.
- Confirmed old LSU failure mode was heater + fouling, not an ECU tuning fault.
- Logged the current state in `INVESTIGATION_FINDINGS_2026-08-09.md`.
- Updated `README.md` to reference this findings snapshot.

## Recommended Next Steps

1. Install the new LSU in the exhaust and capture a hot running log.
2. Replace or fully charge the battery to remove voltage sag as a starting failure factor.
3. Diagnose IAC wiring and mechanics to restore active idle control.
4. Do not change AFR/VE tuning until the new wideband sensor is verified in a hot-engine log.
5. Keep a git commit focused on this diagnosis state and the new findings document.
