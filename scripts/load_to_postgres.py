
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
user = os.environ["POSTGRES_USER"]
pw = os.environ["POSTGRES_PASSWORD"]
db = os.environ["POSTGRES_DB"]
engine = create_engine(f"postgresql+psycopg://{user}:{pw}@127.0.0.1:5433/{db}")

raw = pd.read_csv("kathmandu_pm25_raw.csv", parse_dates=["utc"])
raw = raw[["locationId", "location", "utc", "value", "unit", "latitude", "longitude"]]
raw = raw.rename(columns={"locationId": "location_id"})
daily = pd.read_csv(os.path.join("data", "processed", "kathmandu_pm25_daily.csv"),
                    parse_dates=["date"])

with engine.begin() as con:
    for schema in ("raw", "staging", "mart"):
        con.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    con.execute(text("DROP VIEW IF EXISTS staging.pm25_hourly_clean"))

raw.to_sql("pm25_hourly", engine, schema="raw", if_exists="replace",
           index=False, chunksize=5000, method="multi")
daily.to_sql("pm25_daily", engine, schema="mart", if_exists="replace", index=False)

with engine.begin() as con:
    con.execute(text("""
        CREATE VIEW staging.pm25_hourly_clean AS
        SELECT location, utc,
               CASE WHEN value < 0 OR value > 500 THEN NULL ELSE value END AS pm25
        FROM raw.pm25_hourly
    """))

with engine.connect() as con:
    print("raw.pm25_hourly rows:", con.execute(text("SELECT count(*) FROM raw.pm25_hourly")).scalar())
    print("staging valid readings:", con.execute(text("SELECT count(pm25) FROM staging.pm25_hourly_clean")).scalar())
    print("mart.pm25_daily rows:", con.execute(text("SELECT count(*) FROM mart.pm25_daily")).scalar())
    print("mart days with value:", con.execute(text("SELECT count(pm25_city) FROM mart.pm25_daily")).scalar())