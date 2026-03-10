"""Check AFR readings across ALL datalogs to find when sensor stopped working"""
import csv
import os

datalog_dir = '.'
csv_files = sorted([f for f in os.listdir(datalog_dir) if f.endswith('.csv') and f.startswith('20')])

print(f"{'Date':>22} {'Samples':>8} {'AFR Avg':>8} {'AFR Min':>8} {'AFR Max':>8} {'Pegged19+':>10} {'Normal':>10} {'Status':>12}")
print("-" * 100)

for fname in csv_files:
    try:
        with open(fname, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            headers = reader.fieldnames
            
            # Find AFR column
            afr_col = None
            for h in headers:
                if h.strip() == 'AFR':
                    afr_col = h
                    break
            if not afr_col:
                for h in headers:
                    if 'AFR' in h and 'Target' not in h:
                        afr_col = h
                        break
            
            if not afr_col:
                print(f"  {fname:>22}  -- no AFR column --")
                continue
            
            # Find RPM column
            rpm_col = None
            for h in headers:
                if h.strip() == 'RPM':
                    rpm_col = h
                    break
            
            afr_vals = []
            for row in reader:
                try:
                    rpm = float(row[rpm_col]) if rpm_col else 999
                    afr = float(row[afr_col])
                    if rpm > 400:  # engine running
                        afr_vals.append(afr)
                except:
                    pass
            
            if not afr_vals:
                print(f"  {fname:>22}  -- no running data --")
                continue
            
            avg = sum(afr_vals) / len(afr_vals)
            mn = min(afr_vals)
            mx = max(afr_vals)
            pegged = sum(1 for a in afr_vals if a >= 19.5)
            normal = sum(1 for a in afr_vals if 10 < a < 19)
            pegged_pct = pegged / len(afr_vals) * 100
            normal_pct = normal / len(afr_vals) * 100
            
            if normal_pct > 50:
                status = "WORKING"
            elif pegged_pct > 80:
                status = "DEAD"
            else:
                status = "PARTIAL"
            
            print(f"  {fname:>22} {len(afr_vals):>8} {avg:>8.1f} {mn:>8.1f} {mx:>8.1f} {pegged_pct:>9.1f}% {normal_pct:>9.1f}% {status:>12}")
    
    except Exception as e:
        print(f"  {fname:>22}  ERROR: {e}")
