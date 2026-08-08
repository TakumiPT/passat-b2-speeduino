import csv, os, re
from datetime import datetime

LOGDIR = r"C:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs"

# 1) List all .mlg files newest first
mlgs = sorted([f for f in os.listdir(LOGDIR) if f.endswith('.mlg')], reverse=True)
print("=== .mlg files (newest first, by file mtime) ===")
all_mlgs = sorted([f for f in os.listdir(LOGDIR) if f.endswith('.mlg')],
                  key=lambda f: os.path.getmtime(os.path.join(LOGDIR, f)), reverse=True)
for f in all_mlgs[:10]:
    mt = datetime.fromtimestamp(os.path.getmtime(os.path.join(LOGDIR, f)))
    print(f"  {mt:%Y-%m-%d %H:%M}  {f}")

dated = [f for f in all_mlgs if re.match(r'\d{4}-\d{2}-\d{2}', f)]
dates = [datetime.strptime(re.match(r'(\d{4}-\d{2}-\d{2})', f).group(1), "%Y-%m-%d") for f in dated]
print(f"\nDays since previous log: {(dates[0]-dates[1]).days} days (prev: {dated[1]}, newest: {dated[0]})")

# 2) Load CSV (row0 = names, row1 = units)
csvfile = os.path.join(LOGDIR, "2026-07-26_17.46.26.csv")
with open(csvfile) as fh:
    rows = list(csv.reader(fh, delimiter=';'))
names = rows[0]
data = rows[2:]
n = len(data)
print(f"\nRows: {n}, cols: {len(names)}")

def col(i):
    out = []
    for r in data:
        try: out.append(float(r[i]))
        except: out.append(0.0)
    return out

t   = col(0)   # Time s
rpm = col(2)
kpa = col(3)
tps = col(5)
afr = col(6)   # AFR
iat = col(8)
clt = col(9)
eng = col(10)  # Engine bits: bit0=running?, bit1=crank
gbatt = col(14)  # battery correction %
gwarm = col(15)  # warmup enrich %
pw1 = col(22)
pw2 = col(23)
afrt= col(26)
duty= col(28)
dwell=col(32)
batt= col(34)  # Battery V
sync= col(38)  # Error ID / sync losses? check names
print("name[36..45]:", names[36:46])

print(f"Log duration: {max(t):.1f}s")
print(f"\n=== RPM ===")
print(f"Max RPM: {max(rpm):.0f}")
print(f"Time with RPM>400 (started): {sum(1 for x in rpm if x>400)*0.075:.1f}s" if rpm else 0)
started = any(x > 400 for x in rpm)
print(f"ENGINE STARTED: {started}")

# cranking: rpm > 30
crank_idx = [i for i,x in enumerate(rpm) if x > 30]
if crank_idx:
    t0, t1 = t[crank_idx[0]], t[crank_idx[-1]]
    print(f"\n=== CRANKING ===")
    print(f"Crank window: {t0:.2f}s - {t1:.2f}s  ({t1-t0:.1f}s total)")
    crpm = [rpm[i] for i in crank_idx]
    print(f"Crank RPM avg/max: {sum(crpm)/len(crpm):.0f} / {max(crpm):.0f}")
    print(f"Batt during crank: min {min(batt[i] for i in crank_idx):.2f}V  avg {sum(batt[i] for i in crank_idx)/len(crank_idx):.2f}V")
    print(f"PW1 during crank: avg {sum(pw1[i] for i in crank_idx)/len(crank_idx):.2f} ms  max {max(pw1[i] for i in crank_idx):.2f} ms")
    print(f"AFR during crank: avg {sum(afr[i] for i in crank_idx)/len(crank_idx):.1f}")
    print(f"CLT during crank: {clt[crank_idx[0]]:.0f} -> {clt[crank_idx[-1]]:.0f}")

# RPM trace profile - did it rise and fall?
peak = max(rpm); pki = rpm.index(peak)
print(f"\nRPM peak {peak:.0f} at t={t[pki]:.2f}s")
print(f"RPM at end of log: {rpm[-1]:.0f}")

# sample every ~1.5s
print("\n=== Timeline (t, rpm, kpa, afr, batt, pw1, clt) ===")
step = max(1, int(1.5/0.075))
for i in range(0, n, step):
    print(f"{t[i]:6.2f}  {rpm[i]:5.0f}  {kpa[i]:4.0f}  {afr[i]:6.1f}  {batt[i]:5.2f}  {pw1[i]:6.2f}  {clt[i]:4.0f}")
