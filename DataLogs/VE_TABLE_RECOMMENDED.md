# VE Table - Recommended for VW Passat B2 1.6L DT + Gol G2 SPI

## Configuration
- **Engine:** VW 1.6L DT (75 PS @ 5200 RPM, 130 Nm @ 3000 RPM)
- **Injection:** Gol G2 SPI Monopoint (60 lb/hr single injector)
- **ECU:** Speeduino v0.4, firmware 2025.01.6
- **Req_Fuel:** 4.3 ms
- **Date:** December 2025

---

## RPM Bins (16 columns)
```
500, 700, 900, 1200, 1500, 1800, 2200, 2700, 3000, 3400, 3900, 4300, 4800, 5200, 5700, 6200
```

## MAP/Load Bins (16 rows) - kPa
```
16, 26, 30, 36, 40, 46, 50, 56, 60, 66, 70, 76, 86, 90, 96, 100
```

---

## RECOMMENDED VE TABLE (Copy this to TunerStudio)

**Changes from original:** Idle zone (RPM 500-1200, MAP 16-50 kPa) reduced by ~25% for IPO emissions compliance.

|MAP\RPM| 500 | 700 | 900 |1200 |1500 |1800 |2200 |2700 |3000 |3400 |3900 |4300 |4800 |5200 |5700 |6200 |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
|**16** |  28 |  28 |  29 |  30 |  32 |  34 |  36 |  38 |  40 |  42 |  44 |  46 |  48 |  50 |  48 |  46 |
|**26** |  29 |  29 |  30 |  31 |  34 |  36 |  38 |  41 |  43 |  45 |  48 |  50 |  52 |  54 |  52 |  50 |
|**30** |  30 |  30 |  31 |  32 |  36 |  38 |  41 |  44 |  46 |  49 |  52 |  54 |  56 |  58 |  56 |  54 |
|**36** |  32 |  32 |  33 |  35 |  39 |  42 |  45 |  48 |  51 |  54 |  57 |  59 |  61 |  63 |  61 |  59 |
|**40** |  34 |  34 |  35 |  37 |  41 |  44 |  48 |  51 |  54 |  57 |  60 |  62 |  64 |  66 |  64 |  62 |
|**46** |  36 |  36 |  37 |  40 |  44 |  48 |  52 |  55 |  58 |  61 |  64 |  66 |  68 |  70 |  68 |  66 |
|**50** |  38 |  38 |  40 |  43 |  47 |  51 |  55 |  58 |  61 |  64 |  67 |  69 |  71 |  73 |  71 |  69 |
|**56** |  42 |  42 |  44 |  47 |  51 |  55 |  59 |  62 |  65 |  68 |  71 |  73 |  75 |  77 |  75 |  73 |
|**60** |  45 |  45 |  47 |  50 |  54 |  58 |  62 |  65 |  68 |  71 |  74 |  76 |  78 |  80 |  78 |  76 |
|**66** |  48 |  48 |  50 |  53 |  57 |  61 |  65 |  68 |  71 |  74 |  77 |  79 |  81 |  83 |  81 |  79 |
|**70** |  50 |  50 |  52 |  55 |  59 |  63 |  67 |  70 |  73 |  76 |  79 |  81 |  83 |  85 |  83 |  81 |
|**76** |  52 |  52 |  54 |  57 |  61 |  65 |  69 |  72 |  75 |  78 |  81 |  83 |  85 |  87 |  85 |  83 |
|**86** |  54 |  54 |  56 |  59 |  63 |  67 |  71 |  74 |  77 |  80 |  83 |  85 |  87 |  89 |  87 |  85 |
|**90** |  55 |  55 |  57 |  60 |  64 |  68 |  72 |  75 |  78 |  81 |  84 |  86 |  88 |  90 |  88 |  86 |
|**96** |  56 |  56 |  58 |  61 |  65 |  69 |  73 |  76 |  79 |  82 |  85 |  87 |  89 |  91 |  89 |  87 |
|**100**|  57 |  57 |  59 |  62 |  66 |  70 |  74 |  77 |  80 |  83 |  86 |  88 |  90 |  92 |  90 |  88 |

---

## TunerStudio Copy-Paste Format (Row by Row)

### Row 1 (MAP 16 kPa):
```
28,28,29,30,32,34,36,38,40,42,44,46,48,50,48,46
```

### Row 2 (MAP 26 kPa):
```
29,29,30,31,34,36,38,41,43,45,48,50,52,54,52,50
```

### Row 3 (MAP 30 kPa):
```
30,30,31,32,36,38,41,44,46,49,52,54,56,58,56,54
```

### Row 4 (MAP 36 kPa):
```
32,32,33,35,39,42,45,48,51,54,57,59,61,63,61,59
```

### Row 5 (MAP 40 kPa):
```
34,34,35,37,41,44,48,51,54,57,60,62,64,66,64,62
```

### Row 6 (MAP 46 kPa):
```
36,36,37,40,44,48,52,55,58,61,64,66,68,70,68,66
```

### Row 7 (MAP 50 kPa):
```
38,38,40,43,47,51,55,58,61,64,67,69,71,73,71,69
```

### Row 8 (MAP 56 kPa):
```
42,42,44,47,51,55,59,62,65,68,71,73,75,77,75,73
```

### Row 9 (MAP 60 kPa):
```
45,45,47,50,54,58,62,65,68,71,74,76,78,80,78,76
```

### Row 10 (MAP 66 kPa):
```
48,48,50,53,57,61,65,68,71,74,77,79,81,83,81,79
```

### Row 11 (MAP 70 kPa):
```
50,50,52,55,59,63,67,70,73,76,79,81,83,85,83,81
```

### Row 12 (MAP 76 kPa):
```
52,52,54,57,61,65,69,72,75,78,81,83,85,87,85,83
```

### Row 13 (MAP 86 kPa):
```
54,54,56,59,63,67,71,74,77,80,83,85,87,89,87,85
```

### Row 14 (MAP 90 kPa):
```
55,55,57,60,64,68,72,75,78,81,84,86,88,90,88,86
```

### Row 15 (MAP 96 kPa):
```
56,56,58,61,65,69,73,76,79,82,85,87,89,91,89,87
```

### Row 16 (MAP 100 kPa):
```
57,57,59,62,66,70,74,77,80,83,86,88,90,92,90,88
```

---

## Key Design Points

### 1. Idle Zone (Reduced for IPO Emissions)
- **Area:** RPM 500-1200, MAP 16-50 kPa
- **Values:** 28-43% (was 36-50%)
- **Purpose:** Reduce CO emissions by running leaner at idle
- **Target AFR:** 14.0-14.7 (stoichiometric)

### 2. Cruise Zone (Unchanged)
- **Area:** RPM 1500-3000, MAP 40-60 kPa
- **Values:** 48-68%
- **Purpose:** Fuel economy, smooth operation
- **Target AFR:** 14.7-15.0

### 3. Peak Torque Zone (Unchanged)
- **Area:** RPM 2700-3400, MAP 80-100 kPa
- **Values:** 74-83%
- **Purpose:** Maximum torque at factory spec (130 Nm @ 3000 RPM)
- **Target AFR:** 12.5-13.0 (rich for power)

### 4. Peak Power Zone (Unchanged)
- **Area:** RPM 4800-5200, MAP 90-100 kPa
- **Values:** 88-92%
- **Purpose:** Maximum power at factory spec (75 PS @ 5200 RPM)
- **Target AFR:** 12.5-12.8 (rich for power/safety)

### 5. Over-Rev Zone (Reduced)
- **Area:** RPM 5700-6200, all MAP
- **Values:** Reduced from peak (falloff)
- **Purpose:** Engine protection near redline (6200 RPM)

---

## How to Apply in TunerStudio

### Method 1: Manual Entry
1. Go to **Fuel → VE Table (1)**
2. Click on each cell and enter the value from the table above
3. Press **Burn to ECU** when done

### Method 2: Copy-Paste (If Supported)
1. Go to **Fuel → VE Table (1)**
2. Select all cells (Ctrl+A)
3. Right-click → Paste Values
4. Use the row-by-row format above

### Method 3: Use VE Analyze Live
1. Start engine, let it warm up to 80°C+
2. Enable **VE Analyze Live** in TunerStudio
3. Drive normally for 10-15 minutes
4. Let the auto-tune adjust values based on actual AFR
5. Review and burn to ECU

---

## Important Notes

1. **BACKUP FIRST!** Save your current tune before making changes

2. **Test in Steps:**
   - First, change only the idle zone (MAP 16-50, RPM 500-1200)
   - Test drive to verify no issues
   - Then adjust other zones if needed

3. **Monitor AFR:**
   - Idle should read 14.0-14.7 (not 11.0 like before)
   - WOT should stay at 12.3-13.0 (unchanged)

4. **If Engine Stumbles at Idle:**
   - Increase idle zone values by 2-3 points
   - Problem = too lean, solution = add fuel

5. **WOT Performance:**
   - Should remain excellent (no changes to high load cells)
   - Your datalog showed AFR 12.3 at WOT = perfect!

---

## Version History

| Date | Change |
|------|--------|
| Dec 2025 | Initial table - reduced idle zone 25% for IPO |
| Previous | VE 36-83% range (idle too rich at AFR 11.0) |

---

**File:** `VE_TABLE_RECOMMENDED.md`  
**For:** VW Passat B2 1984 1.6L DT + Speeduino v0.4
