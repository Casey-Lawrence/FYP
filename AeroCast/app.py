from flask import Flask, render_template, request
import requests
import os
from airports import AIRPORTS, AIRPORT_LOOKUP

app = Flask(__name__)

AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY")

def get_airport_name(icao):
    info = AIRPORT_LOOKUP.get(icao)
    if info:
        return info["name"]
    return icao

def interpret_metar(metar):
    metar = metar.upper()
    summary = []

    # Wind
    if "G" in metar:
        summary.append("gusty winds")
    elif "KT" in metar:
        summary.append("steady winds")

    # Clouds
    if "BKN" in metar or "OVC" in metar:
        summary.append("mostly cloudy skies")
    elif "SCT" in metar or "FEW" in metar:
        summary.append("partly cloudy skies")
    else:
        summary.append("clear conditions")

    # weather
    if "SHRA" in metar or "RA" in metar:
        summary.append("with some rain showers")
    if "BR" in metar or "FG" in metar:
        summary.append("and reduced visibility")
    if "TS" in metar or "CB" in metar:
        summary.append("and possible thunderstorms")

    return " ".join(summary).capitalize() + "."

@app.route("/", methods=["GET", "POST"])
def home():
    data = None

    if request.method == "POST":
        flight = request.form.get("flight").strip().upper()

        try:
            #AviationStack lookup
            flight_url = f"http://api.aviationstack.com/v1/flights?access_key={AVIATIONSTACK_KEY}&flight_iata={flight}"
            fdata = requests.get(flight_url, timeout=10).json()

            dep_icao = arr_icao = airline = route = status = None
            source = None
            lat = lon = None

            if fdata.get("data"):
                flight_info = fdata["data"][0]
                dep_icao = flight_info["departure"].get("icao")
                arr_icao = flight_info["arrival"].get("icao")
                airline = flight_info["airline"]["name"]
                dep_name = get_airport_name(dep_icao)
                arr_name = get_airport_name(arr_icao)
                route = f"{dep_name} ({dep_icao}) -> {arr_name} ({arr_icao})"
                status = flight_info.get("flight_status", "unknown").capitalize()
                
            else:
                data = {"error": f"No flight found for {flight}."}
                return render_template("index.html", data=data)

            # Fetch METAR data from NOAA
            metar_dep = requests.get(
                f"https://aviationweather.gov/api/data/metar?ids={dep_icao}&format=raw&hours=3"
            ).text.strip()
            metar_arr = requests.get(
                f"https://aviationweather.gov/api/data/metar?ids={arr_icao}&format=raw&hours=3"
            ).text.strip()

            combined = metar_dep + metar_arr

            # --- Simple turbulence risk logic ---
            risk = "Smooth"
            if any(x in combined for x in ["BKN", "OVC", "SHRA", "CB", "BR", "RA"]):
                risk = "Light"
            if any(x in combined for x in ["TS", "MOD", "G", "+SHRA"]):
                risk = "Moderate"
            if any(x in combined for x in ["SEV", "SQ", "+TS", "FC"]):
                risk = "Severe"

            calming = None
            if risk in ["Moderate", "Severe"]:
                calming = (
                    "Turbulence can feel uncomfortable but is rarely dangerous. "
                    "Fasten your seatbelt and take slow, deep breaths. "
                    "Aircraft are designed to handle these conditions safely."
                )

            dep_summary = interpret_metar(metar_dep)
            arr_summary = interpret_metar(metar_arr)

            data = {
                "flight": flight,
                "airline": airline,
                "route": route,
                "status": status,
                "source": source,
                "risk": risk,
                "calming": calming,
                "dep_summary": dep_summary,
                "arr_summary": arr_summary,
            }

        except Exception as e:
            data = {"error": str(e)}

    return render_template("index.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)