import struct
import csv
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

def parse_mlg_file(filename):
    """
    Parse TunerStudio MLG (MegaLog) binary file
    """
    with open(filename, 'rb') as f:
        data = f.read()
    
    # MLG files typically have a header section
    # Try to find common patterns and extract data
    
    print(f"File size: {len(data)} bytes")
    print(f"\nFirst 200 bytes (hex):")
    print(' '.join(f'{b:02x}' for b in data[:200]))
    
    print(f"\nFirst 200 bytes (attempting ASCII where possible):")
    ascii_preview = ''
    for b in data[:200]:
        if 32 <= b <= 126:
            ascii_preview += chr(b)
        else:
            ascii_preview += f'[{b:02x}]'
    print(ascii_preview)
    
    # Look for header signature
    print("\n" + "="*60)
    print("Searching for header information...")
    print("="*60)
    
    # Try to find text strings in the file (channel names, etc.)
    text_strings = []
    current_string = ''
    for i, b in enumerate(data):
        if 32 <= b <= 126:  # Printable ASCII
            current_string += chr(b)
        else:
            if len(current_string) > 3:
                text_strings.append((i - len(current_string), current_string))
            current_string = ''
    
    print(f"\nFound {len(text_strings)} text strings in file:")
    for pos, string in text_strings[:50]:  # Show first 50
        print(f"  Position {pos}: '{string}'")
    
    return data, text_strings

def analyze_cold_start(data, text_strings):
    """
    Analyze the cold start attempt focusing on:
    - Cranking RPM
    - AFR (Air-Fuel Ratio)
    - Fuel pulse width
    - Priming pulse
    - Engine temperature
    - Battery voltage
    """
    print("\n" + "="*60)
    print("COLD START ANALYSIS")
    print("="*60)
    
    # Look for common TunerStudio channel names
    important_channels = [
        'RPM', 'rpm',
        'AFR', 'afr', 'Lambda',
        'PW', 'pulseWidth', 'Pulse',
        'CLT', 'coolant', 'temp',
        'MAT', 'IAT', 'intake',
        'Battery', 'Vbatt', 'voltage',
        'TPS', 'throttle',
        'Crank',
        'Prime',
        'VE',
    ]
    
    found_channels = []
    for pos, string in text_strings:
        for channel in important_channels:
            if channel.lower() in string.lower():
                found_channels.append((pos, string))
                break
    
    print(f"\nPotentially relevant channels found:")
    for pos, channel in found_channels:
        print(f"  {channel}")
    
    return found_channels

def parse_mlv_binary(filename):
    """
    Parse TunerStudio MLV binary format
    MLVLG format structure
    """
    with open(filename, 'rb') as f:
        # Read header
        magic = f.read(5)  # Should be "MLVLG"
        if magic != b'MLVLG':
            print(f"Warning: Unexpected magic bytes: {magic}")
        
        format_version = struct.unpack('<H', f.read(2))[0]
        timestamp = struct.unpack('<Q', f.read(8))[0]
        
        print(f"\nFile format version: {format_version}")
        print(f"Timestamp: {timestamp}")
        
        # Read field definitions
        num_fields = struct.unpack('<H', f.read(2))[0]
        print(f"Number of fields: {num_fields}")
        
        fields = []
        for i in range(num_fields):
            # Each field has: name (32 bytes), unit (32 bytes), type (4 bytes), etc
            field_data = f.read(88)  # Approximate field definition size
            # Extract field name (first 32 bytes, null-terminated)
            field_name = field_data[:32].split(b'\x00')[0].decode('ascii', errors='ignore')
            if field_name:
                fields.append(field_name)
        
        print(f"\nFields found: {fields[:20]}")  # Show first 20
        
        # Read data records
        record_size = num_fields * 4  # Assuming 4 bytes (float) per field
        data_records = []
        
        try:
            while True:
                record_data = f.read(record_size)
                if len(record_data) < record_size:
                    break
                values = struct.unpack(f'<{num_fields}f', record_data)
                data_records.append(values)
        except:
            pass
        
        print(f"Read {len(data_records)} data records")
        
        return fields, data_records

def export_to_csv(fields, data_records, output_file):
    """Export parsed data to CSV"""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(data_records)
    print(f"\nData exported to: {output_file}")

def analyze_cold_start_data(fields, data_records):
    """Analyze the actual cold start data"""
    print("\n" + "="*60)
    print("DETAILED COLD START DATA ANALYSIS")
    print("="*60)
    
    # Find indices of important fields
    field_indices = {}
    important_fields = ['RPM', 'Lambda', 'Battery', 'VE', 'Accel Enrich', 
                       'AFR Target', 'PulseWidth', 'TPS', 'CLT', 'MAT']
    
    for i, field in enumerate(fields):
        for imp_field in important_fields:
            if imp_field.lower() in field.lower():
                field_indices[field] = i
                break
    
    print(f"\nKey fields mapped:")
    for field, idx in field_indices.items():
        print(f"  {field}: column {idx}")
    
    if not data_records:
        print("\nNo data records found!")
        return
    
    # Analyze first 50 records (cold start period)
    start_records = min(50, len(data_records))
    print(f"\nAnalyzing first {start_records} records (cold start period):")
    print("-" * 60)
    
    for field, idx in field_indices.items():
        values = [record[idx] for record in data_records[:start_records]]
        print(f"\n{field}:")
        print(f"  Min: {min(values):.2f}")
        print(f"  Max: {max(values):.2f}")
        print(f"  Avg: {sum(values)/len(values):.2f}")
        print(f"  First 10 values: {[f'{v:.1f}' for v in values[:10]]}")
    
    # Create visualization
    create_plots(fields, data_records, field_indices)
    
    # Analysis and diagnosis
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    
    # Check if engine was cranking
    if 'RPM' in [f for f in field_indices.keys() if 'RPM' in f]:
        rpm_field = [f for f in field_indices.keys() if 'RPM' in f][0]
        rpm_idx = field_indices[rpm_field]
        max_rpm = max([record[rpm_idx] for record in data_records[:start_records]])
        
        print(f"\n1. CRANKING RPM:")
        if max_rpm < 50:
            print(f"   ⚠️  WARNING: Max RPM was only {max_rpm:.0f}")
            print("   → Engine may not be cranking properly")
            print("   → Check starter, battery, or sensor")
        elif max_rpm < 200:
            print(f"   ⚠️  WEAK: Max RPM was {max_rpm:.0f}")
            print("   → Cranking is weak, check battery/starter")
        else:
            print(f"   ✓ OK: Max RPM was {max_rpm:.0f} (adequate cranking)")
    
    # Check fuel enrichment
    ae_field = [f for f in field_indices.keys() if 'Accel' in f or 'Enrich' in f]
    if ae_field:
        ae_idx = field_indices[ae_field[0]]
        avg_ae = sum([record[ae_idx] for record in data_records[:start_records]]) / start_records
        print(f"\n2. ACCELERATION ENRICHMENT:")
        print(f"   Average: {avg_ae:.1f}%")
        if avg_ae > 500:
            print("   ⚠️  EXTREMELY HIGH - Engine likely FLOODED!")
            print("   → You increased enrichment 6x - this is too much")
            print("   → Engine has too much fuel to ignite")
        elif avg_ae > 200:
            print("   ⚠️  VERY HIGH - Likely too rich")
    
    # Check AFR/Lambda
    lambda_fields = [f for f in field_indices.keys() if 'Lambda' in f or 'AFR' in f]
    if lambda_fields:
        lambda_idx = field_indices[lambda_fields[0]]
        values = [record[lambda_idx] for record in data_records[:start_records]]
        avg_lambda = sum(values) / len(values)
        print(f"\n3. AIR/FUEL RATIO:")
        print(f"   Average Lambda: {avg_lambda:.3f}")
        if avg_lambda > 2.0 or avg_lambda < 0.5:
            print("   ⚠️  Sensor not reading (engine not running)")
        
    print("\n" + "="*60)
    print("RECOMMENDATION:")
    print("="*60)
    print("Based on 6x priming/crank enrichment increase:")
    print("→ Engine is almost certainly FLOODED with fuel")
    print("→ Too much fuel prevents ignition")
    print("\nTO FIX:")
    print("1. CLEAR THE FLOOD:")
    print("   - Hold throttle wide open (100% TPS)")
    print("   - Crank engine for 10 seconds")
    print("   - This will clear excess fuel")
    print("\n2. REDUCE ENRICHMENT:")
    print("   - Set priming/crank enrichment back to STOCK values")
    print("   - Start with baseline first")
    print("   - Then increase gradually (try 1.2x, 1.5x, max 2x)")
    print("\n3. CHECK SPARK PLUGS:")
    print("   - May be fuel-fouled from flooding")
    print("   - Clean or replace if wet/black")

def create_plots(fields, data_records, field_indices):
    """Create visualization plots of key parameters"""
    if not field_indices:
        return
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('Cold Start Analysis - 6x Enrichment Attempt', fontsize=14, fontweight='bold')
    
    records_to_plot = min(100, len(data_records))
    x_axis = list(range(records_to_plot))
    
    # Plot 1: RPM
    rpm_fields = [f for f in field_indices.keys() if 'RPM' in f and 'MAP' not in f]
    if rpm_fields:
        rpm_idx = field_indices[rpm_fields[0]]
        rpm_values = [data_records[i][rpm_idx] for i in range(records_to_plot)]
        axes[0].plot(x_axis, rpm_values, 'b-', linewidth=2, label='RPM')
        axes[0].axhline(y=300, color='g', linestyle='--', label='Target Crank RPM')
        axes[0].set_ylabel('RPM', fontsize=12, fontweight='bold')
        axes[0].set_title('Engine Speed During Crank Attempt')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Lambda/AFR
    lambda_fields = [f for f in field_indices.keys() if 'Lambda' in f]
    if lambda_fields:
        lambda_idx = field_indices[lambda_fields[0]]
        lambda_values = [data_records[i][lambda_idx] for i in range(records_to_plot)]
        axes[1].plot(x_axis, lambda_values, 'r-', linewidth=2, label='Lambda')
        axes[1].axhline(y=1.0, color='g', linestyle='--', label='Stoich (1.0)')
        axes[1].set_ylabel('Lambda', fontsize=12, fontweight='bold')
        axes[1].set_title('Air/Fuel Ratio')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Battery Voltage
    battery_fields = [f for f in field_indices.keys() if 'Battery' in f]
    if battery_fields:
        batt_idx = field_indices[battery_fields[0]]
        batt_values = [data_records[i][batt_idx] for i in range(records_to_plot)]
        axes[2].plot(x_axis, batt_values, 'orange', linewidth=2, label='Battery V')
        axes[2].axhline(y=10.0, color='r', linestyle='--', label='Min Safe (10V)')
        axes[2].set_ylabel('Voltage', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Sample Number', fontsize=12)
        axes[2].set_title('Battery Voltage During Crank')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = 'cold_start_analysis.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")

if __name__ == "__main__":
    mlg_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.mlg"
    
    print("TunerStudio MLG Cold Start Analysis")
    print("="*60)
    print(f"Analyzing: {mlg_file}")
    print("="*60)
    
    try:
        fields, data_records = parse_mlv_binary(mlg_file)
        
        # Export to CSV
        csv_file = mlg_file.replace('.mlg', '_export.csv')
        export_to_csv(fields, data_records, csv_file)
        
        # Detailed analysis
        analyze_cold_start_data(fields, data_records)
        
    except Exception as e:
        print(f"\nError during binary parsing: {e}")
        print("Attempting alternative parsing method...")
        data, text_strings = parse_mlg_file(mlg_file)
        found_channels = analyze_cold_start(data, text_strings)
