import os
import sys

import numpy as np
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "kathmandu_pm25_raw.csv"
MIN_HOURS = 18      # a day needs at least this many valid hourly readings
OUTLIER_MAX = 500   # readings above this are treated as sensor errors

df = pd.read_csv(path)
df["utc"] = pd.to_datetime(df["utc"], utc=True)
df["local_time"] = df["utc"].dt.tz_convert("Asia/Kathmandu")

print("Rows:", len(df))
print("Negative values (by value):")
print(df.loc[df["value"] < 0, "value"].value_counts().head())

df.loc[df["value"] < 0, "value"] = np.nan
n_out = int((df["value"] > OUTLIER_MAX).sum())
print(f"Readings above {OUTLIER_MAX}: {n_out} (set to missing)")
df.loc[df["value"] > OUTLIER_MAX, "value"] = np.nan
print("Missing after cleaning:", int(df["value"].isna().sum()),
      f"({df['value'].isna().mean():.1%})")


df["date"] = df["local_time"].dt.floor("D").dt.tz_localize(None)
g = df.groupby(["location", "date"])["value"]
daily = g.agg(pm25_mean="mean", valid_hours="count").reset_index()
daily.loc[daily["valid_hours"] < MIN_HOURS, "pm25_mean"] = np.nan


city = (daily.groupby("date")["pm25_mean"].mean()
        .rename("pm25_city").reset_index())
full = pd.date_range(city["date"].min(), city["date"].max(), freq="D")
city = city.set_index("date").reindex(full).rename_axis("date").reset_index()

print("\nDays in span:", len(city))
print("Days with a valid city value:", int(city["pm25_city"].notna().sum()),
      f"({city['pm25_city'].notna().mean():.0%})")
print(city["pm25_city"].describe())

# Longest gaps
isna = city["pm25_city"].isna()
runs = isna.ne(isna.shift()).cumsum()
gaps = city[isna].groupby(runs[isna])["date"].agg(["min", "max", "count"])
print("\nLongest gaps (days):")
print(gaps.sort_values("count", ascending=False).head(5).to_string(index=False))

os.makedirs(os.path.join("data", "processed"), exist_ok=True)
out = os.path.join("data", "processed", "kathmandu_pm25_daily.csv")
city.to_csv(out, index=False)
daily.to_csv(os.path.join("data", "processed", "kathmandu_pm25_daily_by_station.csv"), index=False)
print("\nSaved", out)