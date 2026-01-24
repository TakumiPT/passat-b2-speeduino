# VW Passat B2 1.6 DT - Speeduino EFI Conversion

Comprehensive documentation for converting a 1984 VW Passat B2 with 1.6L DT engine from mechanical to Speeduino electronic fuel injection.

## 🚗 Project Overview

- **Vehicle:** 1984 VW Passat B2
- **Engine:** 1.6L DT (1599cc, 75 PS)
- **ECU:** Speeduino v0.4.3d
- **Injector:** Gol G2 SPI Monopoint (~60 lb/hr)
- **IAC:** Bosch 0269980492 (4-wire stepper)

## ⚠️ Important Notes

1. **Ignition is mechanical** - Distributor has vacuum AND centrifugal advance
2. **IAC is inverted** - 0 steps = open, 165 steps = closed
3. **Never disconnect IAC with power on** - Damages DRV8825 driver

## 📁 Repository Structure

```
DataLogs/
├── .github/
│   └── copilot-instructions.md  # AI assistant context
├── *.mlg                        # TunerStudio binary datalogs
├── *.csv                        # Converted datalogs
├── *_analysis.py               # Python analysis scripts
├── *_ANALYSIS.txt              # Analysis results
├── PROJECT_DOCUMENTATION.md    # Full project docs
└── README.md                   # This file
```

## 🔧 Quick Commands

### Convert MLG to CSV
```bash
cd DataLogs
npx mlg-converter --format=csv <filename>.mlg
```

### Read tune settings
```bash
grep -E "iac|idle" "C:\Users\User1\Documents\TunerStudioProjects\Passat2025\CurrentTune.msq"
```

## 📊 Key Parameters

| Parameter | Idle Value | Notes |
|-----------|------------|-------|
| RPM | 800 | Target warm idle |
| MAP | 30-50 kPa | Higher = vacuum leak |
| AFR | 14.7 | Stoichiometric |
| IAC | 165 steps | Closed when warm |

## 📖 Documentation

- [Full Project Documentation](PROJECT_DOCUMENTATION.md)
- [Copilot Instructions](.github/copilot-instructions.md)

## 🛠️ Current Status

- ✅ VE table tuned
- ✅ AE (Acceleration Enrichment) optimized
- ✅ IAC limits corrected
- ✅ DRV8825 driver working
- ⏳ IAC installation pending
- ⏳ Final idle tuning pending

---
*Last updated: January 24, 2026*
