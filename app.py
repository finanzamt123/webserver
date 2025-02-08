from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
from threading import Thread
import time
import json
import os

app = Flask(__name__)

# GPIO-Pins
PUMP_IRRIGATION = 17  # Bewässerungspumpe
PUMP_DOSER = 18       # Dosierpumpe

# Globale Variablen
current_temp = 25.0
current_ec = 1.2
target_ec = 1.5
schedule = []
calibration = {"slope": 0.5, "offset": 0}
CALIB_FILE = "calibration.json"

# Lade Kalibrierung
if os.path.exists(CALIB_FILE):
    with open(CALIB_FILE, "r") as f:
        calibration = json.load(f)

# GPIO initialisieren
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_IRRIGATION, GPIO.OUT)
GPIO.setup(PUMP_DOSER, GPIO.OUT)

def control_pumps():
    while True:
        # EC-Korrektur
        if current_ec < target_ec:
            GPIO.output(PUMP_DOSER, GPIO.HIGH)
        else:
            GPIO.output(PUMP_DOSER, GPIO.LOW)

        # Zeitplan für Bewässerung
        current_time = time.strftime("%H:%M")
        for entry in schedule:
            if entry['start'] <= current_time <= entry['end']:
                GPIO.output(PUMP_IRRIGATION, GPIO.HIGH)
                break
        else:
            GPIO.output(PUMP_IRRIGATION, GPIO.LOW)
        time.sleep(10)

@app.route("/")
def index():
    return render_template("index.html", 
        temp=current_temp, 
        ec=current_ec, 
        target_ec=target_ec, 
        schedule=schedule
    )

@app.route("/data", methods=["POST"])
def data():
    global current_temp, current_ec
    try:
        raw_tds = float(request.form.get("raw_tds"))
        temp = float(request.form.get("temp"))
        current_ec = (raw_tds * calibration["slope"]) + calibration["offset"]
        current_temp = temp
        return "OK"
    except Exception as e:
        print(f"Fehler: {e}")
        return "Fehler", 400

@app.route("/get_sensor_data")
def get_sensor_data():
    return jsonify(temp=current_temp, ec=current_ec)

@app.route("/set_ec", methods=["POST"])
def set_ec():
    global target_ec
    target_ec = float(request.form.get("target_ec"))
    return "EC aktualisiert"

@app.route("/set_schedule", methods=["POST"])
def set_schedule():
    global schedule
    schedule = json.loads(request.form.get("schedule_entries"))
    return "Zeitplan aktualisiert"

@app.route("/calibrate_ec", methods=["POST"])
def calibrate_ec():
    global calibration
    try:
        raw1 = float(request.form.get("raw1"))
        ec1 = float(request.form.get("ec1"))
        raw2 = float(request.form.get("raw2"))
        ec2 = float(request.form.get("ec2"))
        slope = (ec2 - ec1) / (raw2 - raw1)
        offset = ec1 - (slope * raw1)
        calibration = {"slope": slope, "offset": offset}
        with open(CALIB_FILE, "w") as f:
            json.dump(calibration, f)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

if __name__ == "__main__":
    Thread(target=control_pumps).start()
    app.run(host="0.0.0.0", port=5000)
