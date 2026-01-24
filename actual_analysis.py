"""
Actual MLG Log Analysis - What Really Happened
"""
import struct

def parse_mlg_header(filename):
    """Parse the MLG file structure properly"""
    with open(filename, 'rb') as f:
        # Read header
        magic = f.read(5)  # MLVLG
        version = struct.unpack('<H', f.read(2))[0]
        timestamp = struct.unpack('<Q', f.read(8))[0]
        
        # Number of fields
        num_fields_bytes = f.read(2)
        num_fields = struct.unpack('<H', num_fields_bytes)[0]
        
        print(f"Magic: {magic}")
        print(f"Version: {version}")
        print(f"Number of fields: {num_fields}")
        
        # Read field definitions
        fields = []
        field_start = f.tell()
        
        # Each field definition is 88 bytes
        for i in range(num_fields):
            field_def = f.read(88)
            # Name is first 32 bytes
            name = field_def[:32].rstrip(b'\x00').decode('ascii', errors='ignore')
            # Unit is next 32 bytes
            unit = field_def[32:64].rstrip(b'\x00').decode('ascii', errors='ignore')
            fields.append({'name': name, 'unit': unit})
        
        data_start = f.tell()
        
        # Read all data
        f.seek(0)
        all_data = f.read()
        
        # Find where actual numeric data starts (after field definitions)
        # Data records are 4 bytes per field (float32)
        record_size = num_fields * 4
        
        # Read records
        f.seek(data_start)
        records = []
        
        while True:
            record_bytes = f.read(record_size)
            if len(record_bytes) < record_size:
                break
            try:
                values = struct.unpack(f'<{num_fields}f', record_bytes)
                records.append(values)
            except:
                break
        
        return fields, records

def analyze_start_log(fields, records):
    """Analyze what actually happened during the start"""
    print("\n" + "="*70)
    print("ACTUAL START LOG ANALYSIS")
    print("="*70)
    
    print(f"\nTotal records captured: {len(records)}")
    print(f"\nFields in log ({len(fields)} total):")
    for i, field in enumerate(fields[:30]):  # Show first 30
        print(f"  [{i}] {field['name']:30s} ({field['unit']})")
    
    if len(fields) > 30:
        print(f"  ... and {len(fields)-30} more fields")
    
    # Find key indices
    key_fields = {}
    search_terms = {
        'time': ['Time', 'time'],
        'rpm': ['RPM', 'rpm'],
        'pw': ['PulseWidth', 'pulsewidth', 'PW'],
        'lambda': ['Lambda', 'lambda', 'AFR'],
        'battery': ['Battery', 'Vbatt'],
        'tps': ['TPS', 'throttle'],
        'clt': ['CLT', 'coolant'],
        'mat': ['MAT', 'IAT'],
        've': ['VE'],
        'accel': ['Accel', 'AE'],
    }
    
    for key, search_list in search_terms.items():
        for i, field in enumerate(fields):
            for term in search_list:
                if term.lower() in field['name'].lower():
                    key_fields[key] = {'index': i, 'name': field['name'], 'unit': field['unit']}
                    break
            if key in key_fields:
                break
    
    print("\n" + "="*70)
    print("KEY PARAMETERS FOUND:")
    print("="*70)
    for key, info in key_fields.items():
        print(f"{key.upper():15s}: [{info['index']}] {info['name']} ({info['unit']})")
    
    if not records:
        print("\nNo data records found!")
        return
    
    # Analyze the data
    print("\n" + "="*70)
    print("START SEQUENCE ANALYSIS:")
    print("="*70)
    
    # Show sample size
    samples_to_show = min(20, len(records))
    print(f"\nShowing first {samples_to_show} samples:")
    print("-"*70)
    
    # Print header
    header = "Sample"
    for key in ['time', 'rpm', 'pw', 'lambda', 'battery', 'tps', 've']:
        if key in key_fields:
            header += f" | {key_fields[key]['name'][:12]:>12s}"
    print(header)
    print("-"*70)
    
    # Print data
    for i in range(samples_to_show):
        row = f"{i:6d}"
        for key in ['time', 'rpm', 'pw', 'lambda', 'battery', 'tps', 've']:
            if key in key_fields:
                idx = key_fields[key]['index']
                value = records[i][idx]
                # Format based on expected range
                if key == 'time':
                    row += f" | {value:12.3f}"
                elif key == 'rpm':
                    row += f" | {value:12.0f}"
                elif key == 'pw':
                    row += f" | {value:12.2f}"
                elif key == 'lambda':
                    row += f" | {value:12.3f}"
                elif key == 'battery':
                    row += f" | {value:12.2f}"
                elif key == 'tps':
                    row += f" | {value:12.1f}"
                else:
                    row += f" | {value:12.2f}"
        print(row)
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS (Full Log):")
    print("="*70)
    
    for key in ['rpm', 'pw', 'lambda', 'battery', 'tps', 've', 'clt', 'mat']:
        if key in key_fields:
            idx = key_fields[key]['index']
            values = [r[idx] for r in records]
            # Filter out obvious bad values
            clean_values = [v for v in values if abs(v) < 1e6]
            
            if clean_values:
                print(f"\n{key_fields[key]['name']}:")
                print(f"  Min:     {min(clean_values):10.2f} {key_fields[key]['unit']}")
                print(f"  Max:     {max(clean_values):10.2f} {key_fields[key]['unit']}")
                print(f"  Average: {sum(clean_values)/len(clean_values):10.2f} {key_fields[key]['unit']}")
                
                # Special analysis for RPM
                if key == 'rpm':
                    max_rpm = max(clean_values)
                    if max_rpm > 500:
                        print(f"  → Engine STARTED! Reached {max_rpm:.0f} RPM")
                    elif max_rpm > 200:
                        print(f"  → Engine was CRANKING at {max_rpm:.0f} RPM")
                    else:
                        print(f"  → Low RPM: {max_rpm:.0f} RPM")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    mlg_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.mlg"
    
    print("="*70)
    print("TUNERSTUDIO MLG FILE ANALYSIS")
    print("="*70)
    print(f"File: {mlg_file}")
    
    try:
        fields, records = parse_mlg_header(mlg_file)
        analyze_start_log(fields, records)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
