"""Quick hex dump of first bytes of MLG file to understand format"""
import struct, sys

files = [
    "DataLogs/2026-03-01_19.05.30.mlg",
    "DataLogs/2026-03-01_19.08.45.mlg",
]

for fname in files:
    with open(fname, 'rb') as f:
        data = f.read(1000)
    
    print(f"\n{'='*70}")
    print(f"FILE: {fname} ({len(data)} bytes shown)")
    print(f"{'='*70}")
    
    # Show first 200 bytes as hex + ascii
    for offset in range(0, min(500, len(data)), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[offset:offset+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[offset:offset+16])
        print(f"  {offset:04x}: {hex_part:<48s}  {ascii_part}")
    
    # Parse header candidates
    print(f"\n  Magic: {data[0:5]}")
    
    # Try both endianness for header fields
    print(f"\n  --- LITTLE ENDIAN ---")
    print(f"  Bytes 5-6 (version?):     {struct.unpack('<H', data[5:7])[0]}")
    print(f"  Bytes 7-14 (timestamp?):  {struct.unpack('<Q', data[7:15])[0]}")
    print(f"  Bytes 15-16:              {struct.unpack('<H', data[15:17])[0]}")
    print(f"  Bytes 17-18:              {struct.unpack('<H', data[17:19])[0]}")
    print(f"  Bytes 19-20:              {struct.unpack('<H', data[19:21])[0]}")
    print(f"  Bytes 21-22:              {struct.unpack('<H', data[21:23])[0]}")
    
    print(f"\n  --- BIG ENDIAN ---")
    print(f"  Bytes 5-6 (version?):     {struct.unpack('>H', data[5:7])[0]}")
    print(f"  Bytes 7-14 (timestamp?):  {struct.unpack('>Q', data[7:15])[0]}")
    print(f"  Bytes 15-16:              {struct.unpack('>H', data[15:17])[0]}")
    print(f"  Bytes 17-18:              {struct.unpack('>H', data[17:19])[0]}")
    print(f"  Bytes 19-20:              {struct.unpack('>H', data[19:21])[0]}")
    print(f"  Bytes 21-22:              {struct.unpack('>H', data[21:23])[0]}")
    
    # Look for field names (search for common TunerStudio field names)
    search_terms = [b'RPM', b'PW', b'Time', b'Battery', b'TPS', b'CLT', b'Lambda', b'AFR']
    full_data = open(fname, 'rb').read()
    for term in search_terms:
        pos = full_data.find(term)
        if pos >= 0:
            context = full_data[max(0,pos-4):pos+40]
            ascii_ctx = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in context)
            print(f"  Found '{term.decode()}' at offset {pos}: {ascii_ctx}")
