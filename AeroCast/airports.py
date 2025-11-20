import pandas as pd

# Load the world airport dataset
df = pd.read_csv("airports.csv")

# Keep only valid airports (ignore heliports, closed, missing lat/lon)
df = df[df["type"].isin(["small_airport", "medium_airport", "large_airport"])]
df = df.dropna(subset=["latitude_deg", "longitude_deg"])


df = df[["gps_code", "name", "latitude_deg", "longitude_deg"]]

df = df.rename(columns={
    "gps_code": "icao",
    "name": "name",
    "latitude_deg": "lat",
    "longitude_deg": "lon"
})

# Drop entries with missing ICAO
df = df[df["icao"].notna() & (df["icao"].str.len() == 4)]

# Convert to a list of dictionaries
AIRPORTS = df.to_dict(orient="records")

# Build fast lookup dictionary (e.g., AIRPORT_LOOKUP["EIDW"])
AIRPORT_LOOKUP = {a["icao"]: a for a in AIRPORTS}

# Optional test print
if __name__ == "__main__":
    print(f"Loaded {len(AIRPORTS)} airports.")
    print(AIRPORT_LOOKUP.get("EIDW"))
