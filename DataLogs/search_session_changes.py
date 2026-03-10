"""
Search the old frozen session (210MB JSON) for any config change recommendations
made by the AI. We want to know every setting the AI told the user to change.
"""
import os, re, json

session_file = os.path.join(
    os.environ['APPDATA'],
    'Code', 'User', 'workspaceStorage',
    '5323181ec9c0e79a376a9c20c4ff0a51',
    'chatSessions',
    '91e9721a-f7ad-4450-a4af-0b181291c495.json'
)

print(f"Session file: {session_file}")
print(f"Size: {os.path.getsize(session_file) / 1e6:.1f} MB")

# Read the entire file 
print("Loading session file...")
with open(session_file, 'r', encoding='utf-8', errors='replace') as f:
    data = f.read()

print(f"Loaded {len(data)} chars")

# Parse as JSON to get structured messages
print("Parsing JSON...")
try:
    session = json.loads(data)
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    # Try to find the requests array
    print("Trying to extract requests...")
    session = None

# Navigate to the messages
if session:
    # TunerStudio session format varies - explore structure
    if isinstance(session, dict):
        print(f"Top-level keys: {list(session.keys())[:20]}")
        requests = session.get('requests', session.get('messages', []))
        if not requests and 'data' in session:
            requests = session['data'].get('requests', [])
    elif isinstance(session, list):
        requests = session
    else:
        requests = []
    
    print(f"Found {len(requests)} requests/messages")
    
    # Search for config change recommendations in assistant messages
    # Keywords that indicate settings changes
    change_keywords = [
        'reqFuel', 'divider', 'nSquirts', 'nCylinders', 'nInjectors',
        'injOpen', 'injLayout', 'alternate', 'algorithm',
        'veTable', 'VE table', 'VE Table',
        'iacCLmax', 'iacStepHome', 'iacMaxSteps',
        'hardRevLim', 'SoftRevLim', 'softRevLim',
        'wueValues', 'WUE', 'warmup enrichment',
        'asePct', 'ASE', 'after start',
        'dfco', 'DFCO',
        'injBatRates', 'brvBins', 'battery correction',
        'accelEnrich', 'acceleration enrichment',
        'change to', 'set to', 'change from', 'should be',
        'TunerStudio',
    ]
    
    config_changes = []
    
    for i, req in enumerate(requests):
        if isinstance(req, dict):
            # Get the response/assistant message
            response = req.get('response', {})
            if isinstance(response, dict):
                msg_parts = response.get('value', '') or response.get('message', '') or ''
                if isinstance(msg_parts, list):
                    msg_text = ' '.join(str(p) for p in msg_parts)
                else:
                    msg_text = str(msg_parts)
            elif isinstance(response, str):
                msg_text = response
            else:
                msg_text = str(response)
            
            # Also check user message for context
            user_msg = req.get('message', '')
            if isinstance(user_msg, dict):
                user_msg = user_msg.get('text', '') or user_msg.get('value', '') or ''
            
            # Search for config-related content
            found_keywords = []
            for kw in change_keywords:
                if kw.lower() in msg_text.lower() or kw.lower() in str(user_msg).lower():
                    found_keywords.append(kw)
            
            # Look specifically for "change X to Y" or "set X to Y" patterns
            change_patterns = re.findall(
                r'(?:change|set|adjust|modify|update|correct)\s+\w+\s+(?:to|=|→)\s+\S+',
                msg_text, re.IGNORECASE
            )
            
            value_patterns = re.findall(
                r'(reqFuel|divider|nSquirts|nCylinders|nInjectors|injOpen|injLayout|'
                r'iacCLmaxValue|iacStepHome|iacMaxSteps|hardRevLim|softRevLim|SoftRevLim|'
                r'dfcoEnabled|alternate|algorithm|injBatRates|brvBins)'
                r'\s*[:=→]\s*(\S+)',
                msg_text, re.IGNORECASE
            )
            
            if found_keywords and (change_patterns or value_patterns):
                config_changes.append({
                    'msg_idx': i,
                    'keywords': found_keywords,
                    'change_patterns': change_patterns[:5],
                    'value_patterns': value_patterns[:10],
                    'user_msg_preview': str(user_msg)[:200],
                    'response_preview': msg_text[:500] if msg_text else '',
                })
    
    print(f"\nFound {len(config_changes)} messages with config change recommendations")
    print("=" * 80)
    
    for idx, change in enumerate(config_changes):
        print(f"\n--- Config Change #{idx+1} (message {change['msg_idx']}) ---")
        print(f"Keywords: {', '.join(change['keywords'])}")
        if change['value_patterns']:
            print(f"Value assignments: {change['value_patterns']}")
        if change['change_patterns']:
            print(f"Change patterns: {change['change_patterns']}")
        print(f"User said: {change['user_msg_preview']}")
        print(f"AI response: {change['response_preview'][:300]}...")
        print()

else:
    # Fallback: search raw text
    print("Falling back to raw text search...")
    
    # Search for specific MSQ setting changes
    patterns_to_find = [
        (r'reqFuel["\s]*(?::|=|to)\s*[\d.]+', 'reqFuel setting'),
        (r'divider["\s]*(?::|=|to)\s*[\d.]+', 'divider setting'),
        (r'nSquirts["\s]*(?::|=|to)\s*[\d.]+', 'nSquirts setting'),
        (r'injOpen["\s]*(?::|=|to)\s*[\d.]+', 'injOpen setting'),
        (r'hardRevLim["\s]*(?::|=|to)\s*[\d.]+', 'hardRevLim setting'),
        (r'iacCLmax\w*["\s]*(?::|=|to)\s*[\d.]+', 'iacCLmax setting'),
    ]
    
    for pattern, label in patterns_to_find:
        matches = re.findall(pattern, data, re.IGNORECASE)
        if matches:
            unique = list(set(matches))
            print(f"\n{label}: {unique[:10]}")
