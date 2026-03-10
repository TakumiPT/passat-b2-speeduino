"""
Get the full text of session message #86 (injBatRates recommendation)
and search for ALL messages that recommended specific injBatRates values.
"""
import os, json

session_file = os.path.join(
    os.environ['APPDATA'],
    'Code', 'User', 'workspaceStorage',
    '5323181ec9c0e79a376a9c20c4ff0a51',
    'chatSessions',
    '91e9721a-f7ad-4450-a4af-0b181291c495.json'
)

with open(session_file, 'r', encoding='utf-8', errors='replace') as f:
    session = json.loads(f.read())

requests = session.get('requests', [])

def extract_all_text(msg, depth=0):
    if depth > 5:
        return ''
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        parts = []
        for key in ['value', 'text', 'message', 'content']:
            v = msg.get(key)
            if v:
                parts.append(extract_all_text(v, depth+1))
        return ' '.join(parts)
    if isinstance(msg, list):
        return ' '.join(extract_all_text(item, depth+1) for item in msg)
    return ''

# Message #86 - the injBatRates recommendation
print("=" * 80)
print("MESSAGE #86 — Full AI response about injBatRates")
print("=" * 80)
req = requests[86]
user_text = extract_all_text(req.get('message', ''))
resp_text = extract_all_text(req.get('response', {}))
print(f"USER: {user_text[:300]}")
print(f"\nAI RESPONSE (relevant parts):")
# Find the part about battery correction / injBatRates
import re
# Find all occurrences of voltage/percent context
for m in re.finditer(r'(?:Voltage|Percent|battery|correction|injBat|110|106|102|135|115|105|255|176|127).{0,500}', resp_text, re.IGNORECASE):
    snippet = m.group()
    if any(x in snippet for x in ['110', '106', '102', '135', '255', 'Percent', 'Battery']):
        print(f"\n...{snippet}...")
        print()

# Also search ALL messages for "255" + "176" + "127" together OR "135" + "115" + "105"
print("\n" + "=" * 80)
print("ALL MESSAGES recommending injBatRates values")
print("=" * 80)

for i, req in enumerate(requests):
    resp_text = extract_all_text(req.get('response', {}))
    user_text = extract_all_text(req.get('message', ''))
    
    # Check for the specific value sets
    has_new = all(v in resp_text for v in ['255', '176', '127'])
    has_mid = all(v in resp_text for v in ['135', '115', '105'])
    has_old = '110' in resp_text and '106' in resp_text and '102' in resp_text
    
    if has_new or has_mid:
        print(f"\nMessage #{i}: {'has 255/176/127' if has_new else ''} {'has 135/115/105' if has_mid else ''}")
        print(f"  USER: {user_text[:200]}")
        # Find the relevant context
        for pattern in [r'(?:Voltage|Percent|Battery|inject).*?(?:255|176|127|135|115|105).{0,300}',
                        r'(?:255|176|127|135|115|105).*?(?:Voltage|Percent|Battery|inject).{0,200}']:
            matches = re.findall(pattern, resp_text, re.IGNORECASE | re.DOTALL)
            for m in matches[:2]:
                print(f"  CONTEXT: ...{m[:300]}...")

# Check when the values actually changed - look at ALL restore points
print("\n" + "=" * 80)
print("injBatRates in ALL restore points (chronological)")
print("=" * 80)

import glob
restore_dir = r"c:\Users\User1\Documents\TunerStudioProjects\Passat2025\restorePoints"
msq_files = sorted(glob.glob(os.path.join(restore_dir, "*.msq")))

for msq in msq_files[-10:]:  # last 10
    with open(msq, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    m = re.search(r'<constant[^>]*name="injBatRates"[^>]*>(.*?)</constant>', content, re.DOTALL)
    if m:
        vals = m.group(1).strip().replace('\n', ' ')
        vals = ' '.join(vals.split())
        basename = os.path.basename(msq)
        print(f"  {basename}: [{vals}]")
