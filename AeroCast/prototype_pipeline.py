import pandas as pd
import requests
from shapely.geometry import Polygon, Point
from sklearn.ensemble import RandomForestClassifier


# Airport List (Major Airports)
# These are used to test METAR + SIGMET integration
MAJOR_AIRPORTS = [
    ("EIDW", 53.4213, -6.2701),
    ("EGLL", 51.4700, -0.4543),
    ("EGKK", 51.1537, -0.1821),
    ("LFPG", 49.0097, 2.5479),
    ("EDDF", 50.0379, 8.5622),
    ("EHAM", 52.3105, 4.7683),
    ("LEMD", 40.4893, -3.5676),
    ("LIRF", 41.8003, 12.2389),
    ("LOWW", 48.1103, 16.5697),
    ("ESSA", 59.6498, 17.9237),

    ("KJFK", 40.6413, -73.7781),
    ("KLAX", 33.9416, -118.4085),
    ("KORD", 41.9742, -87.9073),
    ("KATL", 33.6407, -84.4277),
    ("KDFW", 32.8998, -97.0403),
    ("KDEN", 39.8561, -104.6737),
    ("KSFO", 37.6213, -122.3790),
    ("KSEA", 47.4502, -122.3088),

    ("OMDB", 25.2532, 55.3657),
    ("OTHH", 25.2731, 51.6081),
    ("OIIE", 35.4161, 51.1523),

    ("RJTT", 35.5494, 139.7798),
    ("RJAA", 35.7647, 140.3864),
    ("VHHH", 22.3080, 113.9185),
    ("ZBAA", 40.08, 116.5846),
    ("WSSS", 1.3644, 103.9915),
    ("RKSI", 37.4602, 126.4407),
    ("VIDP", 28.5562, 77.1000),

    ("YSSY", -33.9399, 151.1753),
    ("YMML", -37.6733, 144.8433),

    ("SBGR", -23.4356, -46.4731),
    ("SAEZ", -34.8222, -58.5358),

    ("FAOR", -26.1337, 28.2420),
    ("HKJK", -1.3192, 36.9278),
    ("FACT", -33.9648, 18.6017),
    ("FAGG", -29.6107, 30.3785),
    ("DTTA", 36.8510, 10.2272),
    ("LHBP", 47.4369, 19.2550),
]

df_airports = pd.DataFrame(MAJOR_AIRPORTS, columns=["icao", "lat", "lon"])

print("Loaded airport dataset:", len(df_airports), "airports")

def parse_visibility(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if "+" in v:
        return float(v.replace("+", ""))
    return float(v)

def get_metar(icao):
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"
    
    try:
        data = requests.get(url, timeout=4).json()
        if not data:
            return {"icao": icao, "wind": None, "visibility": None, "pressure": None, "lat": None, "lon": None}

        j = data[0]

        return {
            "icao": icao,
            "wind": j.get("wspd"),
            "visibility": parse_visibility(j.get("visib")),
            "pressure": j.get("altim"),
            "lat": j.get("lat"),
            "lon": j.get("lon")
        }
    except Exception as e:
        print("Error fetching METAR for:", icao, e)
        return {"icao": icao, "wind": None, "visibility": None, "pressure": None, "lat": None, "lon": None}


metar_rows = [get_metar(icao) for icao in df_airports["icao"]]
df_metar = pd.DataFrame(metar_rows)

print(df_metar)

url = "https://aviationweather.gov/api/data/isigmet?format=json&hazard=turb"
sigmets = requests.get(url, timeout=4).json()

CRUISE_LOW = 0
CRUISE_HIGH = 40000

turb_polygons = []

for s in sigmets:
    base = s.get("base") or 0
    top = s.get("top") or 60000

    if not (top >= CRUISE_LOW and base <= CRUISE_HIGH):
        continue

    coords = s.get("coords", [])
    if len(coords) > 2:
        poly = Polygon([(c["lon"], c["lat"]) for c in coords])
        turb_polygons.append(poly)

len(turb_polygons)

def airport_in_turb(row):
    point = Point(row["lon"], row["lat"])
    for poly in turb_polygons:
        if poly.contains(point):
            return 1
    return 0

df = df_airports.merge(df_metar, on="icao", how="left")

# Prefer METAR lat/lon if provided
df["lat"] = df["lat_y"].fillna(df["lat_x"])
df["lon"] = df["lon_y"].fillna(df["lon_x"])

df = df.drop(columns=["lat_x", "lat_y", "lon_x", "lon_y"])

df["label"] = df.apply(airport_in_turb, axis=1)

X = df[["wind", "visibility", "pressure"]]
y = df["label"]

model = RandomForestClassifier()
model.fit(X, y)

print(model.predict(X))