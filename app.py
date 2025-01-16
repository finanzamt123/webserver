from flask import Flask, render_template, request, jsonify
import glob
import time

app = Flask(__name__)

# DS18B20 Initialisierung
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]
device_file = device_folder + '/w1_slave'

# Sensordaten und Zielwerte
data = {
    "ec": 1.2,  # Beispielwert für elektrische Leitfähigkeit
    "ph": 7.0,  # Beispielwert für pH
    "temperature": 25.0,  # Standardtemperatur, wird überschrieben
    "water_level": 50.0  # Beispielwert für Wasserstand
}


def read_temp():
    """
    Liest die Temperatur vom DS18B20-Sensor aus.
    """
    with open(device_file, 'r') as f:
        lines = f.readlines()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = f.readlines()
    temp_pos = lines[1].find('t=')
    if temp_pos != -1:
        temp_c = float(lines[1][temp_pos + 2:]) / 1000.0
        return temp_c
    return None


@app.route("/")
def index():
    """
    Startseite mit Anzeige der aktuellen Werte.
    """
    return render_template("index.html")


@app.route("/data")
def get_data():
    """
    API-Route, die die aktuellen Werte als JSON zurückgibt.
    """
    # Aktualisiere die Temperatur mit dem DS18B20-Wert
    data["temperature"] = read_temp()
    return jsonify(data)


@app.route("/update", methods=["POST"])
def update():
    """
    Aktualisiert die Zielwerte für EC, pH und Wasserstand.
    """
    try:
        data["ec"] = float(request.form.get("ec", data["ec"]))
        data["ph"] = float(request.form.get("ph", data["ph"]))
        data["water_level"] = float(request.form.get("water_level", data["water_level"]))
    except ValueError:
        # Falls fehlerhafte Werte übermittelt werden, bleiben die alten Werte erhalten.
        pass
    return "Werte aktualisiert!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
