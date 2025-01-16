from flask import Flask, render_template, request
import random  # Nur zur Simulation von Sensordaten

app = Flask(__name__)

# Simulierte Sensordaten
data = {
    "ec": 1.2,
    "ph": 7.0,
    "temperature": 25.0,
    "water_level": 50.0
}

@app.route("/")
def index():
    return render_template("index.html", data=data)

@app.route("/update", methods=["POST"])
def update():
    # Werte anpassen (z. B. Zielwerte setzen)
    data["ec"] = float(request.form.get("ec", data["ec"]))
    data["ph"] = float(request.form.get("ph", data["ph"]))
    data["temperature"] = float(request.form.get("temperature", data["temperature"]))
    data["water_level"] = float(request.form.get("water_level", data["water_level"]))
    return "Werte aktualisiert!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
