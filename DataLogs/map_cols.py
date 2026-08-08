import csv
csvfile = r"C:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\2026-07-26_17.46.26.csv"
with open(csvfile) as fh:
    rows = list(csv.reader(fh, delimiter=';'))
units, data = rows[0], rows[1:]
# print each column: index, unit, first value, value at t~12s (running), min, max
run_i = min(range(len(data)), key=lambda i: abs(float(data[i][0])-12.0))
for i in range(len(units)):
    vals = []
    for r in data:
        try: vals.append(float(r[i]))
        except: pass
    if vals:
        print(f"{i:3d} [{units[i]:6s}] first={vals[0]:10.3f} running={vals[run_i]:10.3f} min={min(vals):10.3f} max={max(vals):10.3f}")
