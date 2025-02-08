from flask import Flask, render_template, request, jsonify
import csv
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
import RPi.GPIO as GPIO
from threading import Thread
import time

app = Flask(__name__)

# Hardware Setup
PUMP_IRRIGATION = 17
PUMP_DOSER = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_IRRIGATION, GPIO.OUT)
GPIO.setup(PUMP_DOSER, GPIO.OUT)

# Datenmanagement
DATA_FILE = "sensor_data.csv"
CALIB_FILE = "calibration.json"
calibration = {"slope": 0.5, "offset": 0}
current_temp = 25.0
current_ec = 1.2
target_ec = 1.5
schedule = []

# Initialisierung
if os.path.exists(CALIB_FILE):
    with open(CALIB_FILE) as f:
        calibration = json.load(f)

def log_data(temp, ec):
    with open(DATA_FILE, "a") as f:
        f.write(f"{datetime.now().isoformat()},{temp},{ec}\n")

def control_pumps():
    while True:
        # EC-Korrektur
        GPIO.output(PUMP_DOSER, GPIO.HIGH if current_ec < target_ec else GPIO.LOW)
        
        # Zeitplan
        now = datetime.now().strftime("%H:%M")
        active = any(s['start'] <= now <= s['end'] for s in schedule)
        GPIO.output(PUMP_IRRIGATION, GPIO.HIGH if active else GPIO.LOW)
        
        time.sleep(10)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def receive_data():
    global current_temp, current_ec
    try:
        current_temp = float(request.form.get("temp"))
        raw_tds = float(request.form.get("raw_tds"))
        current_ec = raw_tds * calibration["slope"] + calibration["offset"]
        log_data(current_temp, current_ec)
        return "OK"
    except Exception as e:
        return str(e), 400

@app.route("/graph")
def generate_graph():
    try:
        df = pd.read_csv(DATA_FILE, names=["time", "temp", "ec"])
        df["time"] = pd.to_datetime(df["time"])
        df = df[df["time"] > pd.Timestamp.now() - pd.DateOffset(hours=24)]
        
        plt.figure(figsize=(10,4))
        plt.plot(df["time"], df["temp"], label="Temperatur (°C)")
        plt.plot(df["time"], df["ec"], label="EC-Wert")
        plt.legend()
        
        img = BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight")
        plt.close()
        return f"data:image/png;base64,{base64.b64encode(img.getvalue()).decode()}"
    except Exception as e:
        return f"Fehler: {str(e)}"

@app.route("/calibrate", methods=["POST"])
def calibrate():
    try:
        data = request.json
        slope = (data["ec2"] - data["ec1"]) / (data["raw2"] - data["raw1"])
        calibration.update(slope=slope, offset=data["ec1"] - slope * data["raw1"])
        with open(CALIB_FILE, "w") as f:
            json.dump(calibration, f)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route("/schedule", methods=["POST"])
def update_schedule():
    global schedule
    schedule = request.json
    return jsonify(success=True)

@app.route("/get_data")
def get_data():
    return jsonify(
        temp=current_temp,
        ec=current_ec,
        target_ec=target_ec,
        schedule=schedule
    )

if __name__ == "__main__":
    Thread(target=control_pumps).start()
    app.run(host="0.0.0.0", port=5000)
