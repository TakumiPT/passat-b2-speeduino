"""
Better MLG parser - try to get clean data
"""
import struct
import os

def read_mlg_properly(filename):
    """
    TunerStudio MLG format parser
    """
    with open(filename, 'rb') as f:
        # Header
        magic = f.read(5)  # MLVLG
        if magic != b'MLVLG':
            print(f"Warning: Not MLVLG format: {magic}")
            return None, None
        
        version = struct.unpack('<H', f.read(2))[0]
        timestamp = struct.unpack('<Q', f.read(8))[0]
        num_fields = struct.unpack('<H', f.read(2))[0]
        
        print(f"MLG File Format")
        print(f"Version: {version}")
        print(f"Fields: {num_fields}")
        
        # Skip to find actual field names
        # Look for recognizable ASCII patterns
        pos = f.tell()
        f.seek(0)
        data = f.read()
        
        # Find field names by looking for null-terminated strings
        fields = []
        i = 15  # Start after header
        
        while len(fields) < num_fields and i < len(data) - 100:
            # Look for sequences that look like field names
            if 32 <= data[i] <= 126:  # Printable ASCII
                name = b''
                j = i
                while j < len(data) and data[j] != 0 and 32 <= data[j] <= 126 and len(name) < 32:
                    name += bytes([data[j]])
                    j += 1
                
                if 2 <= len(name) <= 30:
                    # Check if followed by null padding
                    if j < len(data) and data[j] == 0:
                        # Next 32 bytes might be units
                        unit_start = j + 1
                        while unit_start < len(data) and data[unit_start] == 0:
                            unit_start += 1
                        
                        unit = b''
                        if unit_start < len(data):
                            k = unit_start
                            while k < len(data) and data[k] != 0 and 32 <= data[k] <= 126 and len(unit) < 32:
                                unit += bytes([data[k]])
                                k += 1
                        
                        try:
                            field_name = name.decode('ascii')
                            field_unit = unit.decode('ascii', errors='ignore') if unit else ''
                            
                            # Filter out junk
                            if field_name and not any(c in field_name for c in ['<', '>', '=', '"']):
                                fields.append({'name': field_name, 'unit': field_unit, 'offset': i})
                        except:
                            pass
                
                i = j + 88  # Field definitions are typically 88 bytes
            else:
                i += 1
        
        print(f"\nFound {len(fields)} field definitions:")
        for idx, field in enumerate(fields[:40]):
            print(f"  [{idx:3d}] {field['name']:25s} ({field['unit']})")
        
        if len(fields) > 40:
            print(f"  ... and {len(fields)-40} more")
        
        # Find where data starts - look for consistent 4-byte float patterns
        # Data typically starts after all field definitions
        data_start = fields[-1]['offset'] + 88 if fields else 1000
        
        # Try to find actual data by looking for reasonable float values
        f.seek(data_start)
        
        # Read records - each record is num_fields * 4 bytes (float32)
        record_size = num_fields * 4
        records = []
        
        # Try different starting positions
        for offset_adjust in range(0, 500, 4):
            f.seek(data_start + offset_adjust)
            test_records = []
            
            for _ in range(10):  # Try reading 10 records
                try:
                    record_bytes = f.read(record_size)
                    if len(record_bytes) < record_size:
                        break
                    values = struct.unpack(f'<{num_fields}f', record_bytes)
                    test_records.append(values)
                except:
                    break
            
            # Check if this looks like valid data
            if len(test_records) >= 5:
                # Check if values are reasonable (not NaN, not huge)
                valid = True
                for rec in test_records[:5]:
                    # Check first few values - should be reasonable
                    if any(abs(v) > 1e10 or v != v for v in rec[:10]):  # v != v checks for NaN
                        valid = False
                        break
                
                if valid:
                    print(f"\nFound valid data at offset {data_start + offset_adjust}")
                    # Read all records from this position
                    f.seek(data_start + offset_adjust)
                    while True:
                        try:
                            record_bytes = f.read(record_size)
                            if len(record_bytes) < record_size:
                                break
                            values = struct.unpack(f'<{num_fields}f', record_bytes)
                            records.append(values)
                        except:
                            break
                    break
        
        print(f"Read {len(records)} data records")
        
        return fields, records

def analyze_data(fields, records):
    """Analyze the start data"""
    if not records or not fields:
        print("No data to analyze")
        return
    
    print("\n" + "="*70)
    print("DATA ANALYSIS")
    print("="*70)
    
    # Map key fields
    field_map = {}
    for i, field in enumerate(fields):
        name_lower = field['name'].lower()
        if 'rpm' in name_lower and 'map' not in name_lower:
            field_map['rpm'] = i
        elif 'pw' in name_lower and len(field['name']) < 5:
            field_map['pw'] = i
        elif 'lambda' in name_lower:
            field_map['lambda'] = i
        elif 'afr' in name_lower and 'target' not in name_lower:
            field_map['afr'] = i
        elif 'battery' in name_lower or 'vbatt' in name_lower:
            field_map['battery'] = i
        elif 'tps' in name_lower:
            field_map['tps'] = i
        elif 'clt' in name_lower or 'coolant' in name_lower:
            field_map['clt'] = i
        elif 'time' in name_lower and i < 5:
            field_map['time'] = i
        elif 'accel' in name_lower or 'ae' in name_lower:
            field_map['ae'] = i
        elif field['name'] == 'VE':
            field_map['ve'] = i
    
    print("\nMapped fields:")
    for key, idx in field_map.items():
        print(f"  {key:10s}: [{idx:3d}] {fields[idx]['name']} ({fields[idx]['unit']})")
    
    # Show first 30 records
    print("\n" + "="*70)
    print("FIRST 30 SAMPLES:")
    print("="*70)
    
    # Print header
    header = "Sample |"
    for key in ['time', 'rpm', 'pw', 'lambda', 'battery', 'tps', 'clt']:
        if key in field_map:
            header += f" {fields[field_map[key]]['name'][:10]:>10s} |"
    print(header)
    print("-"*len(header))
    
    for i in range(min(30, len(records))):
        row = f"{i:6d} |"
        for key in ['time', 'rpm', 'pw', 'lambda', 'battery', 'tps', 'clt']:
            if key in field_map:
                val = records[i][field_map[key]]
                if key == 'time':
                    row += f" {val:10.2f} |"
                elif key == 'rpm':
                    row += f" {val:10.0f} |"
                elif key in ['pw', 'lambda', 'battery']:
                    row += f" {val:10.2f} |"
                else:
                    row += f" {val:10.1f} |"
        print(row)
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS (All samples):")
    print("="*70)
    
    for key in ['rpm', 'pw', 'lambda', 'battery', 'tps', 'clt', 'ae', 've']:
        if key in field_map:
            idx = field_map[key]
            values = [r[idx] for r in records]
            
            print(f"\n{fields[idx]['name']} ({fields[idx]['unit']}):")
            print(f"  Min:     {min(values):10.2f}")
            print(f"  Max:     {max(values):10.2f}")
            print(f"  Average: {sum(values)/len(values):10.2f}")
            
            # Special notes
            if key == 'rpm':
                max_rpm = max(values)
                print(f"  Peak RPM: {max_rpm:.0f}")
                if max_rpm > 600:
                    print(f"  → Engine STARTED and ran!")
                elif max_rpm > 250:
                    print(f"  → Engine cranked at ~{max_rpm:.0f} RPM")
                else:
                    print(f"  → Low RPM detected")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    mlg_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\start.mlg"
    
    print("="*70)
    print("TunerStudio MLG Parser")
    print("="*70)
    
    fields, records = read_mlg_properly(mlg_file)
    
    if fields and records:
        analyze_data(fields, records)
