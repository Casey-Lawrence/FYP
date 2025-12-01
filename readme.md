# AeroCast Casey Edwards Lawrence

## Overview
AeroCast is a web application that retrieves live flight and weather data to provide basic turbulence insights for passengers.
This interim version demonstrates core functionality including flight lookup, METAR interpretation and route visualisation.

## Contents
This folder contains:
- Flask application (app.py)
- Airport lookup utilities (airports.py, airports.csv)
- HTML templates and CSS
- A prototype data exploration script (prototype_pipeline.py)
- Requirements file

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Add your AviationStack API key to a .env file.
A free key can be obtained at: https://aviationstack.com
(Free tier has very limited coverage.)
3. Run main application: `python app.py`

## Project Structure
AeroCast/
├── app.py                # Main application
├── airports.py           # Airport data loader
├── airports.csv          # Airport dataset
├── prototype_pipeline.py # Experimental script (not used by app)
├── templates/
│   ├── index.html
│   └── sigmets.html
├── static/
│   └── style.css
└── requirements.txt


## Dependencies
- Python 3.9+

## Contact
If you have any questions please send me an email. 
c22485436@mytudublin.ie