import os
import phonenumbers
from phonenumbers import geocoder, carrier
from opencage.geocoder import OpenCageGeocode
import folium
from flask import Flask, request, render_template, jsonify, send_from_directory

app = Flask(__name__)
API_KEY = os.environ['key']

# Dossier pour stocker les cartes générées
MAPS_DIR = "maps"
os.makedirs(MAPS_DIR, exist_ok=True)

def geolocate_phone_number(phone_number, api_key):
    phone_number_obj = phonenumbers.parse(phone_number)

    # Localisation de base
    location = geocoder.description_for_number(phone_number_obj, "en")

    # Opérateur téléphonique
    operator = carrier.name_for_number(phone_number_obj, "en")

    # Géolocalisation via OpenCage
    geocoder_obj = OpenCageGeocode(api_key)
    results = geocoder_obj.geocode(location)

    if results and len(results):
        latitude = results[0]['geometry']['lat']
        longitude = results[0]['geometry']['lng']
        return {
            "latitude": latitude,
            "longitude": longitude,
            "location": location,
            "operator": operator,
            "full_results": results
        }
    else:
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/locate", methods=["POST"])
def locate():
    phone_number = request.form.get("phone_number")
    if not phone_number:
        return render_template("error.html", message="Phone number is required!")

    result = geolocate_phone_number(phone_number, API_KEY)
    if result:
        # Création de la carte avec Folium
        map_filename = f"{phone_number.replace('+', '')}.html"
        map_path = os.path.join(MAPS_DIR, map_filename)
        map_location = folium.Map(location=[result["latitude"], result["longitude"]], zoom_start=9)
        folium.Marker([result["latitude"], result["longitude"]], popup=result["location"]).add_to(map_location)
        map_location.save(map_path)

        return render_template(
            "results.html",
            phone_number=phone_number,
            latitude=result["latitude"],
            longitude=result["longitude"],
            location=result["location"],
            operator=result["operator"],
            map_url=f"/maps/{map_filename}"
        )
    else:
        return render_template("error.html", message="Location not found!")

@app.route("/maps/<filename>")
def maps(filename):
    return send_from_directory(MAPS_DIR, filename)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
