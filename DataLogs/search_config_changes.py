"""
Focused search: Find EXACTLY what config values were changed in the old session.
Compare the Feb 28 restore point with the current MSQ to find all differences.
Also search the session for specific value assignments.
"""
import os, re, json

# PART 1: Compare Feb 28 last restore point with current MSQ
print("=" * 80)
print("PART 1: DIFF between Feb 28 restore point and current MSQ")
print("=" * 80)

feb28_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\restorePoints\Passat2025_2026-02-28_17.14.34.msq"
mar5_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\restorePoints\Passat2025_2026-03-05_21.16.06.msq"
current_file = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\CurrentTune.msq"

def extract_constants(filepath):
    """Extract all <constant> values from MSQ file"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    constants = {}
    # Single-value constants
    for m in re.finditer(r'<constant[^>]*name="([^"]+)"[^>]*>(.*?)</constant>', content, re.DOTALL):
        name = m.group(1)
        value = m.group(2).strip()
        constants[name] = value
    
    return constants

print(f"\nReading Feb 28 restore: {os.path.basename(feb28_file)}")
feb28 = extract_constants(feb28_file)
print(f"  Found {len(feb28)} constants")

print(f"Reading Mar 5 restore: {os.path.basename(mar5_file)}")
mar5 = extract_constants(mar5_file)
print(f"  Found {len(mar5)} constants")

print(f"Reading current tune: {os.path.basename(current_file)}")
current = extract_constants(current_file)
print(f"  Found {len(current)} constants")

# Compare Feb 28 → Mar 5 restore point
print(f"\n{'=' * 80}")
print(f"CHANGES from Feb 28 → Mar 5 restore point:")
print(f"{'=' * 80}")

changes_found = 0
# Critical settings to highlight
critical = {'reqFuel', 'divider', 'nSquirts', 'nCylinders', 'nInjectors', 
            'injOpen', 'injLayout', 'alternate', 'algorithm', 'engineType',
            'hardRevLim', 'SoftRevLim', 'iacAlgorithm', 'iacCLmaxValue',
            'iacStepHome', 'iacMaxSteps', 'dfcoEnabled',
            'injType', 'injCharacteristics'}

for name in sorted(set(list(feb28.keys()) + list(mar5.keys()))):
    v_feb = feb28.get(name, '<MISSING>')
    v_mar = mar5.get(name, '<MISSING>')
    
    if v_feb != v_mar:
        # Skip large tables for now, show value differences
        if len(str(v_feb)) > 200 and len(str(v_mar)) > 200:
            # Check if it's a table that actually changed
            v_feb_clean = ' '.join(v_feb.split())
            v_mar_clean = ' '.join(v_mar.split())
            if v_feb_clean != v_mar_clean:
                tag = " *** CRITICAL ***" if name in critical else ""
                print(f"\n  [{name}]{tag}: TABLE CHANGED")
                # Show first and last few values
                feb_vals = v_feb.split()
                mar_vals = v_mar.split()
                if len(feb_vals) == len(mar_vals):
                    diffs = [(i, feb_vals[i], mar_vals[i]) for i in range(len(feb_vals)) 
                             if feb_vals[i] != mar_vals[i]]
                    print(f"    {len(diffs)} values changed out of {len(feb_vals)}:")
                    for idx, old, new in diffs[:20]:
                        print(f"      Position {idx}: {old} → {new}")
                    if len(diffs) > 20:
                        print(f"      ... and {len(diffs) - 20} more")
                changes_found += 1
        else:
            tag = " *** CRITICAL ***" if name in critical else ""
            print(f"  [{name}]{tag}: {v_feb} → {v_mar}")
            changes_found += 1

print(f"\nTotal changes: {changes_found}")

# Also compare Mar 5 restore → current (in case something changed after)
print(f"\n{'=' * 80}")
print(f"CHANGES from Mar 5 restore → CurrentTune.msq:")
print(f"{'=' * 80}")

changes2 = 0
for name in sorted(set(list(mar5.keys()) + list(current.keys()))):
    v_mar = mar5.get(name, '<MISSING>')
    v_cur = current.get(name, '<MISSING>')
    
    if v_mar != v_cur:
        if len(str(v_mar)) > 200 and len(str(v_cur)) > 200:
            v_mar_clean = ' '.join(v_mar.split())
            v_cur_clean = ' '.join(v_cur.split())
            if v_mar_clean != v_cur_clean:
                tag = " *** CRITICAL ***" if name in critical else ""
                print(f"\n  [{name}]{tag}: TABLE CHANGED")
                mar_vals = v_mar.split()
                cur_vals = v_cur.split()
                if len(mar_vals) == len(cur_vals):
                    diffs = [(i, mar_vals[i], cur_vals[i]) for i in range(len(mar_vals)) 
                             if mar_vals[i] != cur_vals[i]]
                    print(f"    {len(diffs)} values changed out of {len(mar_vals)}:")
                    for idx, old, new in diffs[:20]:
                        print(f"      Position {idx}: {old} → {new}")
                changes2 += 1
        else:
            tag = " *** CRITICAL ***" if name in critical else ""
            print(f"  [{name}]{tag}: {v_mar} → {v_cur}")
            changes2 += 1

print(f"\nTotal changes: {changes2}")

# PART 2: Search old session for the specific changes found
print(f"\n{'=' * 80}")
print(f"PART 2: Search session for AI recommendations about these changes")
print(f"{'=' * 80}")

session_file = os.path.join(
    os.environ['APPDATA'],
    'Code', 'User', 'workspaceStorage',
    '5323181ec9c0e79a376a9c20c4ff0a51',
    'chatSessions',
    '91e9721a-f7ad-4450-a4af-0b181291c495.json'
)

print("Loading session...")
with open(session_file, 'r', encoding='utf-8', errors='replace') as f:
    session = json.loads(f.read())

requests = session.get('requests', [])
print(f"Loaded {len(requests)} messages")

# Search for specific value changes
def extract_text(msg):
    """Extract readable text from message"""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        v = msg.get('value', '') or msg.get('text', '') or msg.get('message', '')
        if isinstance(v, list):
            parts = []
            for item in v:
                if isinstance(item, dict):
                    parts.append(item.get('value', ''))
                else:
                    parts.append(str(item))
            return ' '.join(parts)
        return str(v)
    if isinstance(msg, list):
        parts = []
        for item in msg:
            parts.append(extract_text(item))
        return ' '.join(parts)
    return str(msg)

# Look for specific critical things:
# 1. VE table changes
# 2. reqFuel changes  
# 3. Any "change X to Y" instruction from the AI
# 4. Specific mentions of the Feb 28 fixes

search_terms = {
    'VE table values': r'VE\s+(?:table|values?).*?(?:\d+\s*→\s*\d+|\d+\s*->\s*\d+|\d+\s+to\s+\d+)',
    'reqFuel value': r'reqFuel.*?(?:\d+\.?\d*)',
    'iacCLmax change': r'iacCLmax\w*.*?(?:\d+)',
    'hardRevLim change': r'hardRevLim.*?(?:\d+)',
    'WUE values': r'(?:WUE|wueValues|warmup).*?(?:\d+\s*%|\d+\s*→)',
    'ASE values': r'(?:ASE|asePct|after.start).*?(?:\d+\s*%|\d+\s*→)',
    'injOpen change': r'injOpen.*?(?:\d+\.?\d*)',
    'change setting': r'(?:change|set|update)\s+(?:this|it|the\s+\w+)\s+(?:to|=)\s+[\d"]+',
}

for label, pattern in search_terms.items():
    print(f"\nSearching for: {label}")
    found = 0
    for i, req in enumerate(requests):
        resp = req.get('response', {})
        text = extract_text(resp)
        
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            found += 1
            if found <= 3:
                user_msg = extract_text(req.get('message', ''))
                print(f"  Message #{i}: {matches[:3]}")
                print(f"    User: {user_msg[:100]}")
    
    if found == 0:
        print(f"  No matches found")
    elif found > 3:
        print(f"  ... and {found - 3} more matches")

# PART 3: Focus on messages around Feb 28 - March 5 timeframe
print(f"\n{'=' * 80}")
print(f"PART 3: Messages containing specific config value assignments")
print(f"{'=' * 80}")

# Look for any message that mentions specific numeric assignments to known settings
for i, req in enumerate(requests):
    resp = req.get('response', {})
    text = extract_text(resp)
    user_text = extract_text(req.get('message', ''))
    
    # Find explicit value assignments
    assignments = re.findall(
        r'`?(reqFuel|divider|nSquirts|injOpen|hardRevLim|SoftRevLim|softRevLim|'
        r'iacCLmaxValue|iacStepHome|iacMaxSteps|dfcoEnabled|injCharacteristics|'
        r'injType|alternate|nInjectors|nCylinders|algorithm|injLayout|'
        r'batVoltCorrect|decelAmount)`?\s*(?::|=|→|to|should be|change to)\s*'
        r'[`"]*(\S+?)[`"]*(?:\s|,|\.|\)|$)',
        text, re.IGNORECASE
    )
    
    if assignments:
        print(f"\nMessage #{i}:")
        print(f"  User: {user_text[:120]}")
        print(f"  Assignments: {assignments}")
