"""
Parse the two new MLG files from 2026-03-01 (corrected voltage correction table)
MLG1: 19.05.30 - car started
MLG2: 19.08.45 - car did NOT start

MLVLG binary format:
  5 bytes: "MLVLG"
  2 bytes: version (uint16 BE)  
  8 bytes: timestamp
  2 bytes: info_data_start (uint16 BE)
  2 bytes: data_begin_index (uint16 BE)
  2 bytes: record_length (uint16 BE)
  2 bytes: num_fields (uint16 BE)
  Then field definitions, then data records
"""
import struct
import sys
import os

def parse_mlg(filename):
    """Parse MLVLG format properly"""
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Header
    magic = data[0:5]
    if magic != b'MLVLG':
        print(f"ERROR: Not MLVLG format: {magic}")
        return None, None
    
    # Parse header - big endian
    version = struct.unpack('>H', data[5:7])[0]
    timestamp = struct.unpack('>Q', data[7:15])[0]
    info_data_start = struct.unpack('>H', data[15:17])[0]
    data_begin_idx = struct.unpack('>H', data[17:19])[0]
    record_length = struct.unpack('>H', data[19:21])[0]
    num_fields = struct.unpack('>H', data[21:23])[0]
    
    print(f"  Version: {version}")
    print(f"  Num fields: {num_fields}")
    print(f"  Record length: {record_length} bytes")
    print(f"  Info data start: {info_data_start}")
    print(f"  Data begin index: {data_begin_idx}")
    
    # Parse field definitions starting at offset 23
    # Each field: 1 byte type, 1 byte size, 34 bytes name, 34 bytes units,
    #             4 bytes scale, 4 bytes transform, 1 byte digits, padding
    # Actually the format varies. Let me try the standard MLVLG field def:
    # type(1) + unsigned(1) + name(34) + units(34) + scale(4 float) + transform(4 float) + digits(1) + pad
    # = 79 bytes? Let's compute from record positions
    
    # Field definition size = (data_begin_idx - 23) / num_fields  
    # But info_data_start might indicate where field defs start
    
    field_def_start = 23
    if num_fields > 0:
        field_block_size = data_begin_idx - field_def_start
        field_def_size = field_block_size // num_fields
        print(f"  Field def size: {field_def_size} bytes each")
    else:
        return None, None
    
    fields = []
    pos = field_def_start
    for i in range(num_fields):
        fd = data[pos:pos + field_def_size]
        
        # Standard MLVLG field format:
        # byte 0: type (0=uint8, 1=int8, 2=uint16, 3=int16, 4=int32, 5=int64, 6=float32, 7=float64)
        # byte 1: unsigned flag
        # bytes 2-35: name (null terminated, 34 bytes)
        # bytes 36-69: units (null terminated, 34 bytes)
        # bytes 70-73: scale (float32 BE)
        # bytes 74-77: transform (float32 BE)
        # byte 78: digits
        
        ftype = fd[0]
        
        # Extract name - null terminated string
        name_bytes = fd[2:36]
        name = name_bytes.split(b'\x00')[0].decode('ascii', errors='replace').strip()
        
        # Extract units
        units_bytes = fd[36:70]
        units = units_bytes.split(b'\x00')[0].decode('ascii', errors='replace').strip()
        
        # Scale and transform
        if len(fd) >= 78:
            scale = struct.unpack('>f', fd[70:74])[0]
            transform = struct.unpack('>f', fd[74:78])[0]
            digits = fd[78] if len(fd) > 78 else 0
        else:
            scale = 1.0
            transform = 0.0
            digits = 0
        
        # Type sizes
        type_sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 8, 6: 4, 7: 8}
        type_names = {0: 'U8', 1: 'S8', 2: 'U16', 3: 'S16', 4: 'S32', 5: 'S64', 6: 'F32', 7: 'F64'}
        
        fields.append({
            'name': name,
            'units': units,
            'type': ftype,
            'type_name': type_names.get(ftype, f'?{ftype}'),
            'size': type_sizes.get(ftype, 4),
            'scale': scale,
            'transform': transform,
            'digits': digits
        })
        
        pos += field_def_size
    
    print(f"\n  Fields found:")
    for i, fld in enumerate(fields):
        print(f"    [{i:2d}] {fld['name']:25s} {fld['units']:10s} type={fld['type_name']} scale={fld['scale']:.4f} transform={fld['transform']:.2f}")
    
    # Parse data records
    # Each record starts with a marker byte (0x01) then the field data
    # Record structure: marker(1) + timestamp(2 bytes uint16) + field data
    # Actually in MLVLG, records have: marker byte (1) + data (record_length bytes)
    
    records = []
    pos = data_begin_idx
    
    while pos < len(data):
        # Check for record marker
        marker = data[pos]
        if marker == 0x01:  # Normal data record
            pos += 1
            if pos + record_length > len(data):
                break
            
            record_data = data[pos:pos + record_length]
            
            # Parse each field value from the record
            values = {}
            field_pos = 0
            for fld in fields:
                if field_pos + fld['size'] > len(record_data):
                    break
                
                raw_bytes = record_data[field_pos:field_pos + fld['size']]
                
                if fld['type'] == 0:  # uint8
                    raw = struct.unpack('B', raw_bytes)[0]
                elif fld['type'] == 1:  # int8
                    raw = struct.unpack('b', raw_bytes)[0]
                elif fld['type'] == 2:  # uint16
                    raw = struct.unpack('>H', raw_bytes)[0]
                elif fld['type'] == 3:  # int16
                    raw = struct.unpack('>h', raw_bytes)[0]
                elif fld['type'] == 4:  # int32
                    raw = struct.unpack('>i', raw_bytes)[0]
                elif fld['type'] == 5:  # int64
                    raw = struct.unpack('>q', raw_bytes)[0]
                elif fld['type'] == 6:  # float32
                    raw = struct.unpack('>f', raw_bytes)[0]
                elif fld['type'] == 7:  # float64
                    raw = struct.unpack('>d', raw_bytes)[0]
                else:
                    raw = 0
                
                # Apply scale and transform: value = raw * scale + transform
                value = raw * fld['scale'] + fld['transform']
                values[fld['name']] = value
                
                field_pos += fld['size']
            
            records.append(values)
            pos += record_length
            
        elif marker == 0x02:  # Marker record (text/event)
            pos += 1
            if pos + 2 > len(data):
                break
            text_len = struct.unpack('>H', data[pos:pos+2])[0]
            pos += 2 + text_len
        else:
            # Unknown marker, try to skip
            pos += 1
    
    print(f"\n  Data records: {len(records)}")
    return fields, records


def analyze_mlg(filename, label, fields, records):
    """Analyze cranking and running data"""
    print(f"\n{'='*75}")
    print(f"  ANALYSIS: {label}")
    print(f"  File: {os.path.basename(filename)}")  
    print(f"  Records: {len(records)}")
    print(f"{'='*75}")
    
    if not records:
        print("  NO DATA!")
        return
    
    # Find key field names (they may vary)
    key_fields = {}
    for fld in fields:
        n = fld['name'].lower()
        if n == 'rpm' or (n == 'rpm' and 'map' not in n):
            key_fields['RPM'] = fld['name']
        elif 'time' in n and 'time' == n[:4]:
            key_fields['Time'] = fld['name']
        elif n == 'pw' or n == 'pw1':
            key_fields['PW'] = fld['name']
        elif n == 'afr' and 'target' not in n:
            key_fields['AFR'] = fld['name']
        elif 'battery' in n and 'v' in n:
            key_fields['BattV'] = fld['name']
        elif n == 'clt' or 'coolant' in n:
            key_fields['CLT'] = fld['name']
        elif n == 'engine':
            key_fields['Engine'] = fld['name']
        elif n == 'tps':
            key_fields['TPS'] = fld['name']
        elif n == 'map' and 'rpm' not in n:
            key_fields['MAP'] = fld['name']
        elif n == 'duty cycle' or n == 'dutycycle':
            key_fields['Duty'] = fld['name']
        elif 'gbattery' in n or n == 'gbattery':
            key_fields['Gbatt'] = fld['name']
        elif 'gwarm' in n or n == 'gwarm':
            key_fields['Gwarm'] = fld['name']
        elif 'gammae' in n or n == 'gammae':
            key_fields['Gammae'] = fld['name']
        elif n == 'secl':
            key_fields['SecL'] = fld['name']
        elif 'accel' in n and 'enrich' in n:
            key_fields['AE'] = fld['name']
        elif n == 've current' or n == 'vecurrent' or n == 've_current':
            key_fields['VE'] = fld['name']
        elif n == 'lambda' and 'target' not in n:
            key_fields['Lambda'] = fld['name']
    
    # Try alternative field name matching
    all_names = [f['name'] for f in fields]
    for name in all_names:
        nl = name.lower().replace(' ', '').replace('_', '')
        if 'rpm' == nl and 'RPM' not in key_fields:
            key_fields['RPM'] = name
        elif nl == 'pw' and 'PW' not in key_fields:
            key_fields['PW'] = name
        elif nl == 'batteryv' and 'BattV' not in key_fields:
            key_fields['BattV'] = name
        elif nl == 'dutycycle' and 'Duty' not in key_fields:
            key_fields['Duty'] = name
        elif nl == 'vecurrent' and 'VE' not in key_fields:
            key_fields['VE'] = name
    
    print(f"\n  Mapped fields: {key_fields}")
    
    # Get RPM field
    rpm_key = key_fields.get('RPM')
    if not rpm_key:
        print("  ERROR: Cannot find RPM field!")
        # Try first few records to see what fields exist
        if records:
            print(f"  Available fields: {list(records[0].keys())[:20]}")
        return
    
    # Classify records
    cranking = []  # RPM > 0 and < 500
    running = []   # RPM >= 500
    idle_off = []  # RPM = 0
    
    for r in records:
        rpm = r.get(rpm_key, 0)
        if rpm == 0:
            idle_off.append(r)
        elif rpm < 500:
            cranking.append(r)
        else:
            running.append(r)
    
    print(f"\n  Record classification:")
    print(f"    Key off/0 RPM: {len(idle_off)}")
    print(f"    Cranking (<500 RPM): {len(cranking)}")
    print(f"    Running (>=500 RPM): {len(running)}")
    
    # Helper to get field value safely
    def get(record, key):
        field_name = key_fields.get(key)
        if field_name and field_name in record:
            return record[field_name]
        return None
    
    def stats(records_list, key):
        vals = [get(r, key) for r in records_list if get(r, key) is not None]
        if not vals:
            return None
        return {'min': min(vals), 'max': max(vals), 'avg': sum(vals)/len(vals), 'n': len(vals)}
    
    # ---- CRANKING ANALYSIS ----
    if cranking:
        print(f"\n  --- CRANKING DATA ---")
        for k in ['RPM', 'BattV', 'PW', 'AFR', 'CLT', 'Duty', 'Gbatt', 'Gwarm', 'Gammae', 'TPS', 'MAP', 'Engine']:
            s = stats(cranking, k)
            if s:
                print(f"    {k:10s}: min={s['min']:8.1f}  avg={s['avg']:8.1f}  max={s['max']:8.1f}  (n={s['n']})")
        
        # PW vs Voltage during cranking
        print(f"\n    PW vs Battery Voltage during cranking:")
        print(f"    {'Voltage':>10} | {'Samples':>7} | {'Avg PW':>8} | {'Avg AFR':>8} | {'Avg RPM':>8} | {'Avg Duty':>9}")
        print(f"    {'-'*65}")
        
        for lo, hi in [(7.0,8.0),(8.0,8.5),(8.5,9.0),(9.0,9.5),(9.5,10.0),(10.0,10.5),(10.5,11.0),(11.0,12.0)]:
            band = [r for r in cranking if get(r,'BattV') is not None and lo <= get(r,'BattV') < hi]
            if band:
                avg_pw = sum(get(r,'PW') for r in band if get(r,'PW')) / max(1,len([r for r in band if get(r,'PW')]))
                avg_afr = sum(get(r,'AFR') for r in band if get(r,'AFR')) / max(1,len([r for r in band if get(r,'AFR')]))
                avg_rpm = sum(get(r,'RPM') for r in band if get(r,'RPM')) / max(1,len([r for r in band if get(r,'RPM')]))
                avg_duty = sum(get(r,'Duty') for r in band if get(r,'Duty')) / max(1,len([r for r in band if get(r,'Duty')]))
                print(f"    {lo:.1f}-{hi:.1f}V | {len(band):>7} | {avg_pw:>7.3f} | {avg_afr:>7.1f} | {avg_rpm:>7.0f} | {avg_duty:>8.1f}%")
    
    # ---- RUNNING ANALYSIS ----
    if running:
        print(f"\n  --- RUNNING DATA ---")
        for k in ['RPM', 'BattV', 'PW', 'AFR', 'CLT', 'Duty', 'Gbatt', 'MAP', 'TPS']:
            s = stats(running, k)
            if s:
                print(f"    {k:10s}: min={s['min']:8.1f}  avg={s['avg']:8.1f}  max={s['max']:8.1f}  (n={s['n']})")
        
        # Check AFR quality during running
        afr_vals = [get(r, 'AFR') for r in running if get(r, 'AFR') is not None]
        if afr_vals:
            stoich_band = [a for a in afr_vals if 14.0 <= a <= 15.5]
            rich = [a for a in afr_vals if a < 14.0]
            lean = [a for a in afr_vals if a > 15.5]
            print(f"\n    AFR Distribution (running):")
            print(f"      Rich (< 14.0):      {len(rich):>5} ({100*len(rich)/len(afr_vals):.1f}%)")
            print(f"      Stoich (14.0-15.5):  {len(stoich_band):>5} ({100*len(stoich_band)/len(afr_vals):.1f}%)")
            print(f"      Lean (> 15.5):       {len(lean):>5} ({100*len(lean)/len(afr_vals):.1f}%)")
    
    # ---- TIMELINE (first 50 samples) ----
    print(f"\n  --- FIRST 50 SAMPLES ---")
    header_keys = ['Time', 'RPM', 'BattV', 'PW', 'AFR', 'CLT', 'Duty', 'Engine']
    avail = [k for k in header_keys if k in key_fields]
    print(f"    {'#':>4} |", end="")
    for k in avail:
        print(f" {k:>8} |", end="")
    print()
    print(f"    {'-'*75}")
    
    for i, r in enumerate(records[:50]):
        print(f"    {i:>4} |", end="")
        for k in avail:
            v = get(r, k)
            if v is not None:
                if k == 'RPM':
                    print(f" {v:>8.0f} |", end="")
                elif k == 'Engine':
                    print(f" {v:>8.0f} |", end="")
                else:
                    print(f" {v:>8.2f} |", end="")
            else:
                print(f" {'N/A':>8} |", end="")
        print()
    
    if len(records) > 50:
        print(f"    ... ({len(records) - 50} more records)")
    
    return cranking, running


# =====================================================================
# MAIN
# =====================================================================

print("=" * 75)
print("  PARSING 2026-03-01 MLG FILES (CORRECTED VOLTAGE CORRECTION)")
print("=" * 75)

mlg_files = [
    ("DataLogs/2026-03-01_19.05.30.mlg", "MLG1 - CAR STARTED"),
    ("DataLogs/2026-03-01_19.08.45.mlg", "MLG2 - CAR DID NOT START"),
]

results = {}
for mlg_file, label in mlg_files:
    if not os.path.exists(mlg_file):
        # Try from DataLogs dir
        alt = os.path.basename(mlg_file)
        if os.path.exists(alt):
            mlg_file = alt
        else:
            print(f"\n  FILE NOT FOUND: {mlg_file}")
            continue
    
    print(f"\n{'='*75}")
    print(f"  PARSING: {label}")
    print(f"  File: {mlg_file} ({os.path.getsize(mlg_file):,} bytes)")
    print(f"{'='*75}")
    
    fields, records = parse_mlg(mlg_file)
    
    if fields and records:
        result = analyze_mlg(mlg_file, label, fields, records)
        results[label] = result
    else:
        print(f"  FAILED TO PARSE: {mlg_file}")
        if fields:
            print(f"  Fields found: {len(fields)}, Records: {len(records) if records else 0}")


# =====================================================================
# COMPARISON
# =====================================================================
print(f"\n\n{'='*75}")
print("  COMPARISON: STARTED vs DID NOT START")
print(f"{'='*75}")

if len(results) == 2:
    labels = list(results.keys())
    for label in labels:
        if results[label]:
            cranking, running = results[label]
            print(f"\n  {label}:")
            print(f"    Cranking samples: {len(cranking) if cranking else 0}")
            print(f"    Running samples:  {len(running) if running else 0}")
else:
    print("  Could not compare - not all files parsed successfully.")
    print("  Check field names and file paths.")
