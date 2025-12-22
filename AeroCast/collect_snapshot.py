import csv
import os
import sys
import traceback
from datetime import datetime
import requests
from shapely.geometry import Point, Polygon

DATA_DIR = r"C:\Users\casey\OneDrive - Technological University Dublin\AeroCastData"
CSV_FILE = os.path.join(DATA_DIR, "aerocast_dataset.csv")
RUN_LOG = os.path.join(DATA_DIR, "task_run.log")
ERROR_LOG = os.path.join(DATA_DIR, "task_error.log")

OPENSKY_API = "https://opensky-network.org/api/states/all"
METAR_API = "https://aviationweather.gov/api/data/metar"
SIGMET_API = "https://aviationweather.gov/api/data/sigmet"

BBOX = {"lamin": 35, "lamax": 60, "lomin": -15, "lomax": 30}

def log(msg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z - {msg}\n")

def fetch_flights():
    r = requests.get(OPENSKY_API, params=BBOX, timeout=20)
    r.raise_for_status()
    return r.json().get("states", [])

def fetch_metar(lat, lon):
    r = requests.get(
        METAR_API,
        params={"lat": lat, "lon": lon, "radius": 50, "format": "json"},
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    return data[0]["rawOb"] if data else None

def fetch_sigmet_polygons():
    r = requests.get(SIGMET_API, params={"format": "json"}, timeout=20)
    r.raise_for_status()
    polygons = []
    for s in r.json():
        coords = s.get("coords")
        if coords and len(coords) >= 3:
            polygons.append(
                Polygon([(c["lon"], c["lat"]) for c in coords])
            )
    return polygons

def inside_sigmet(lat, lon, polygons):
    p = Point(lon, lat)
    return any(poly.contains(p) for poly in polygons)

def main():
    log("Run started")
    flights = fetch_flights()
    sigmets = fetch_sigmet_polygons()

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        if not file_exists:
            w.writerow([
                "timestamp",
                "icao24",
                "callsign",
                "lat",
                "lon",
                "altitude",
                "velocity",
                "metar",
                "sigmet_flag"
            ])

        for s in flights:
            if s[5] is None or s[6] is None:
                continue

            metar = None
            try:
                metar = fetch_metar(s[6], s[5])
            except:
                pass

            sigmet_flag = int(inside_sigmet(s[6], s[5], sigmets))

            w.writerow([
                datetime.utcnow().isoformat() + "Z",
                s[0],
                (s[1] or "").strip(),
                s[6],
                s[5],
                s[7],
                s[9],
                metar,
                sigmet_flag
            ])

    log("Run finished")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        sys.exit(1)
