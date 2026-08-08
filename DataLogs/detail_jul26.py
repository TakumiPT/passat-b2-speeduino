import csv
csvfile = r"C:\Users\User1\Documents\TunerStudioProjects\Passat2025\DataLogs\2026-07-26_17.46.26.csv"
with open(csvfile) as fh:
    rows = list(csv.reader(fh, delimiter=';'))
names = rows[0]; data = rows[2:]
def col(i):
    out=[]
    for r in data:
        try: out.append(float(r[i]))
        except: out.append(0.0)
    return out
t=col(0); rpm=col(2); kpa=col(3); tps=col(5); afr=col(6); clt=col(9)
eng=col(10); pw=col(22); afrt=col(26); duty=col(28); dwell=col(32); batt=col(34)
errn=col(36); errid=col(37); gbat=col(14); gwarm=col(15); gego=col(12); gammae=col(17); ve=col(19)

print("Engine bits unique values:", sorted(set(eng)))
print("Error# unique:", sorted(set(errn)), " ErrorID unique:", sorted(set(errid)))
print("TPS unique:", sorted(set(tps)))
print("Duty max:", max(duty), " Dwell avg running:", sum(dwell)/len(dwell))

# cranking window = eng bit crank? find first rpm>0 to rpm>400
i_crank0 = next(i for i in range(len(rpm)) if rpm[i]>50)
i_start  = next(i for i in range(len(rpm)) if rpm[i]>400)
print(f"\nCrank start t={t[i_crank0]:.2f}s, fired at t={t[i_start]:.2f}s -> cranked {(t[i_start]-t[i_crank0]):.2f}s")
seg=range(i_crank0,i_start)
print(f"During crank: rpm {min(rpm[i] for i in seg):.0f}-{max(rpm[i] for i in seg):.0f}, "
      f"batt min {min(batt[i] for i in seg):.2f}V, PW {sum(pw[i] for i in seg)/len(list(seg)):.2f}ms, "
      f"AFR {sum(afr[i] for i in seg)/len(list(seg)):.1f}, kpa {sum(kpa[i] for i in seg)/len(list(seg)):.0f}")

# running window
i_end = next(i for i in range(i_start,len(rpm)) if rpm[i]<200)
seg=range(i_start,i_end)
print(f"\nRunning t={t[i_start]:.2f}-{t[i_end]:.2f}s ({t[i_end]-t[i_start]:.1f}s): "
      f"rpm avg {sum(rpm[i] for i in seg)/len(list(seg)):.0f}, PW avg {sum(pw[i] for i in seg)/len(list(seg)):.2f}ms, "
      f"duty avg {sum(duty[i] for i in seg)/len(list(seg)):.1f}%, batt avg {sum(batt[i] for i in seg)/len(list(seg)):.2f}V, "
      f"VE {sum(ve[i] for i in seg)/len(list(seg)):.0f}%, gammae {sum(gammae[i] for i in seg)/len(list(seg)):.0f}%")

# AFR during run - oscillation?
afr_run=[afr[i] for i in seg]
print(f"AFR during run: min {min(afr_run):.1f} max {max(afr_run):.1f} (target {afrt[i_start]:.1f})")

# the stall: last 3s before rpm<200
print("\n=== Stall window (t, rpm, kpa, afr, pw, batt, eng, err#) ===")
for i in range(i_end-30, i_end+5):
    print(f"{t[i]:6.2f} {rpm[i]:5.0f} {kpa[i]:4.0f} {afr[i]:6.1f} {pw[i]:6.2f} {batt[i]:5.2f} eng={int(eng[i])} err={int(errn[i])}/{int(errid[i])} gammae={gammae[i]:.0f}")
