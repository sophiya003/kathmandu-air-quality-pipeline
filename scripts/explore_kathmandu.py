import sys
 
import pandas as pd
 
paths = sys.argv[1:]
if not paths:
    sys.exit("Give at least one CSV path.")
 
df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
df["utc"] = pd.to_datetime(df["utc"], errors="coerce", utc=True)
 
print("Total rows:", len(df))
print("Columns:", list(df.columns))
print("Locations:", df["location"].unique())
print("Parameters:\n", df["parameter"].value_counts())
 
pm = df[df["parameter"].str.lower() == "pm25"].copy()
print("\n--- PM2.5 ---")
print("Rows:", len(pm))
print("Date range:", pm["utc"].min(), "->", pm["utc"].max())
print("Null timestamps:", int(pm["utc"].isna().sum()))
print("Negative values:", int((pm["value"] < 0).sum()))
print("Value summary:\n", pm["value"].describe())
 
for loc, g in pm.groupby("location"):
    g = g.dropna(subset=["utc"])
    days = g["utc"].dt.floor("D").nunique()
    span = (g["utc"].max() - g["utc"].min()).days + 1
    print(f"\n{loc}: {len(g)} rows, {days} days with data of {span} in span "
          f"({days / span:.0%} coverage), units: {g['unit'].unique()}")
 
pm.to_csv("kathmandu_pm25_raw.csv", index=False)
print("\nSaved kathmandu_pm25_raw.csv")
 

