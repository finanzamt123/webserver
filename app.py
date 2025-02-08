from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from threading import Thread
import time
import json

app = Flask(__name__)

# GPIO-Pins
PUMP_IRRIGATION = 17  # Bewässerungspumpe
PUMP_DOSER = 18       # Dosierpumpe

# Globale Variablen
current_temp = 25.0
current_ec = 1.2
target_ec = 1.5
schedule = []  # Liste der Bewässerungszeiten (als Dictionary: {'start': 'HH:MM', 'end': 'HH:MM'})

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
    return render_template("index.html", temp=current_temp, ec=current_ec, target_ec=target_ec, schedule=schedule)

@app.route("/data", methods=["POST"])
def data():
    global current_temp, current_ec
    current_temp = float(request.form.get("temp"))
    current_ec = float(request.form.get("ec"))
    return "OK"

@app.route("/set_ec", methods=["POST"])
def set_ec():
    global target_ec
    target_ec = float(request.form.get("target_ec"))
    return "EC aktualisiert"

@app.route("/set_schedule", methods=["POST"])
def set_schedule():
    global schedule
    schedule_entries = request.form.get("schedule_entries")
    if schedule_entries:
        schedule = json.loads(schedule_entries)
    else:
        schedule = []
    return "Zeitplan aktualisiert"

if __name__ == "__main__":
    Thread(target=control_pumps).start()
    app.run(host="0.0.0.0", port=5000)
