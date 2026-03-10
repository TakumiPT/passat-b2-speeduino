"""
Search old session specifically for injBatRates / battery correction changes.
This is the biggest change between Feb 28 and Mar 5 and likely explains the lean condition.
"""
import os, json, re

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

def extract_text(msg):
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

# Search for ALL mentions of battery correction, injBatRates, brvBins, 
# and also "255" "176" "127" in the context of battery or injector
search_terms = [
    'injBatRates', 'brvBins', 'battery correction', 'batVoltCorrect',
    'bat volt', 'battery volt', 'voltage correction',
    'injector opening', 'dead time',
]

print("\n" + "=" * 80)
print("SEARCHING FOR BATTERY CORRECTION / injBatRates CHANGES")
print("=" * 80)

for i, req in enumerate(requests):
    resp = req.get('response', {})
    resp_text = extract_text(resp)
    user_text = extract_text(req.get('message', ''))
    combined = (resp_text + ' ' + user_text).lower()
    
    found = [t for t in search_terms if t.lower() in combined]
    
    if found:
        print(f"\n{'=' * 60}")
        print(f"Message #{i} — matched: {found}")
        print(f"{'=' * 60}")
        print(f"USER: {user_text[:300]}")
        print(f"---")
        # Show relevant parts of the response
        for term in found:
            # Find context around the term
            pos = resp_text.lower().find(term.lower())
            if pos >= 0:
                start = max(0, pos - 200)
                end = min(len(resp_text), pos + 500)
                context = resp_text[start:end]
                print(f"  Context around '{term}':")
                print(f"  ...{context}...")
                print()

# Also search for the specific values 255, 176, 127 in context of fuel/injector
print("\n" + "=" * 80)
print("SEARCHING FOR values 255/176/127 near fuel/injector/battery context")
print("=" * 80)

for i, req in enumerate(requests):
    resp = req.get('response', {})
    resp_text = extract_text(resp)
    
    # Look for 255 + 176 + 127 in the same message (the specific injBatRates values)
    if '255' in resp_text and '176' in resp_text and '127' in resp_text:
        user_text = extract_text(req.get('message', ''))
        print(f"\n--- Message #{i} contains 255+176+127 ---")
        print(f"USER: {user_text[:200]}")
        # Find context around these numbers
        for val in ['255', '176', '127']:
            pos = resp_text.find(val)
            if pos >= 0:
                start = max(0, pos - 100)
                end = min(len(resp_text), pos + 200)
                print(f"  ...{resp_text[start:end]}...")
        print()

# Search for "110 106 102 100 100 98" - the OLD values
print("\n" + "=" * 80)
print("SEARCHING FOR old values pattern 110/106/102")
print("=" * 80)

for i, req in enumerate(requests):
    resp = req.get('response', {})
    resp_text = extract_text(resp)
    user_text = extract_text(req.get('message', ''))
    combined = resp_text + ' ' + user_text
    
    if '110' in combined and '106' in combined and '102' in combined:
        # Check if these appear close together (within 200 chars)
        for m in re.finditer('110', combined):
            pos = m.start()
            snippet = combined[pos:pos+100]
            if '106' in snippet and '102' in snippet:
                print(f"\n--- Message #{i} has 110/106/102 near each other ---")
                user_text_short = extract_text(req.get('message', ''))
                print(f"USER: {user_text_short[:200]}")
                context_start = max(0, pos - 100)
                context_end = min(len(combined), pos + 300)
                print(f"  ...{combined[context_start:context_end]}...")
                break
