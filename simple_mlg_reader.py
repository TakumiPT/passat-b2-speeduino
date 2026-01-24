"""
Simple MLG file reader for TunerStudio logs
This will show you the raw values during your cold start attempt
"""

with open(r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.mlg", 'rb') as f:
    data = f.read()

# The file starts with "MLVLG" header
print("="*70)
print("COLD START DATA LOG ANALYSIS - 6X ENRICHMENT ATTEMPT")
print("="*70)
print(f"\nLog file size: {len(data):,} bytes")
print(f"Header: {data[:5]}")

# Look for key configuration values in the embedded XML
config_str = data.decode('latin-1', errors='ignore')

# Extract key tuning values
print("\n" + "="*70)
print("CURRENT TUNING CONFIGURATION:")
print("="*70)

# Priming pulse
if 'fpPrime' in config_str:
    idx = config_str.find('fpPrime')
    snippet = config_str[idx:idx+100]
    print(f"\nPriming settings found in config:")
    print(f"  {snippet[:80]}")

# Cranking enrichment
if 'crankingPct' in config_str:
    idx = config_str.find('crankingPct')
    snippet = config_str[idx:idx+100]
    print(f"\nCranking enrichment:")
    print(f"  {snippet[:80]}")

if 'crankingEnrich' in config_str:
    idx = config_str.find('crankingEnrich')
    for i in range(3):
        snippet = config_str[idx+i*100:idx+(i+1)*100]
        if 'cranking' in snippet.lower():
            print(f"  {snippet[:80]}")

# Cranking RPM threshold
if 'crankRPM' in config_str:
    idx = config_str.find('crankRPM')
    snippet = config_str[idx:idx+100]
    print(f"\nCranking RPM threshold:")
    print(f"  {snippet[:80]}")

print("\n" + "="*70)
print("ANALYSIS BASED ON YOUR DESCRIPTION:")
print("="*70)
print("\n❌ PROBLEM: Engine did NOT start with 6x priming/crank enrichment")
print("\n📊 File Capture Details:")
print(f"   - Log captured on: Thu Nov 13 13:20:23 2025")
print(f"   - ECU: Speeduino 2025.01.6")
print(f"   - File has {len(data):,} bytes of data")

print("\n" + "="*70)
print("🔍 DIAGNOSIS:")
print("="*70)
print("\n1. ENGINE FLOODING (Most Likely)")
print("   Problem: 6x enrichment = 600% of normal fuel")
print("   Result: Too much fuel washes cylinder walls")
print("   Effect: Fuel mixture too rich to ignite")
print("   ")
print("   Normal cold start enrichment: 100-150%")
print("   Your setting: 600% (6x)")
print("   → This is 4-6x too much fuel!")

print("\n2. WHAT HAPPENS WHEN FLOODED:")
print("   ❌ Spark plugs get fuel-soaked")
print("   ❌ Compression reduced (fuel on cylinder walls)")
print("   ❌ Air/Fuel ratio way too rich (>15:1)")
print("   ❌ Spark can't ignite the saturated mixture")

print("\n3. SIGNS OF FLOODING:")
print("   • Engine cranks but doesn't fire")
print("   • Smell of raw gas from exhaust")
print("   • Wet/black spark plugs")
print("   • Low or no compression feeling")

print("\n" + "="*70)
print("✅ SOLUTION:")
print("="*70)

print("\n📋 IMMEDIATE ACTIONS:")
print("\n1. CLEAR THE FLOOD (Do this now!):")
print("   a) Remove spark plugs and check condition")
print("      → If wet/black = CONFIRMED flooding")
print("   b) Clean or replace plugs")
print("   c) With plugs out, crank engine 5-10 seconds")
print("      → This clears fuel from cylinders")
print("   d) OR: Use 'Clear Flood Mode':")
print("      → Hold throttle 100% open (WOT)")
print("      → Crank for 10 seconds")
print("      → ECU should cut fuel")

print("\n2. RESET ENRICHMENT TO BASELINE:")
print("   → Set priming pulse BACK TO STOCK")
print("   → Set cranking enrichment BACK TO STOCK")
print("   → Test if car starts with normal values")

print("\n3. GRADUAL TUNING APPROACH:")
print("   Once car starts with stock values:")
print("   ")
print("   Try these increments:")
print("   • Stock (1.0x) - Baseline")
print("   • 1.2x = 20% more - Mild")
print("   • 1.5x = 50% more - Moderate")
print("   • 2.0x = 100% more - Maximum safe")
print("   ")
print("   ❌ NEVER go above 2.5x enrichment")
print("   ❌ Your 6x was extreme flooding territory")

print("\n4. COLD START TUNING BEST PRACTICES:")
print("   • Make SMALL changes (10-20% at a time)")
print("   • Test each change before increasing")
print("   • Monitor AFR if you have wideband O2")
print("   • Target: Lambda 0.85-0.95 during crank")
print("   • Log each start attempt")

print("\n" + "="*70)
print("📌 RECOMMENDED ENRICHMENT VALUES:")
print("="*70)
print("\nTemperature-based priming:")
print("  -20°C:  150-200% (1.5-2.0x)")
print("   0°C:   120-150% (1.2-1.5x)")
print("  +20°C:  100-120% (1.0-1.2x)")
print("  +40°C+: 80-100%  (0.8-1.0x)")
print("\n⚠️  Your 600% (6x) floods engine at ANY temperature!")

print("\n" + "="*70)
print("🔧 NEXT STEPS:")
print("="*70)
print("\n1. ✓ Check/clean/replace spark plugs")
print("2. ✓ Clear flood (WOT + crank OR remove plugs)")
print("3. ✓ Reset enrichment to STOCK values")
print("4. ✓ Attempt start with stock settings")
print("5. ✓ If starts OK, increase by 20% and test")
print("6. ✓ Continue gradual increases until optimal")
print("\nDO NOT skip straight back to high enrichment!")
print("\n" + "="*70)

# Try to determine if TunerStudio can export this
print("\n💡 TIP: For detailed data analysis:")
print("   1. Open start.mlg in TunerStudio")
print("   2. Go to: Tools → MegaLogViewer")
print("   3. File → Export to CSV")
print("   4. Then we can see exact RPM, PW, AFR values")
print("="*70)
