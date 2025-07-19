from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
from simulator import run_monte_carlo_simulation

app = Flask(__name__)
CORS(app)

# Adjust this path to your CSV location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../data/reports/GS_treat_risks_for_montecarlo.csv"))

@app.route("/")
def index():
    return "Monte Carlo API is running!"

@app.route("/api/risks", methods=["GET"])
def get_all_risks():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "Risk file not found."}), 404

    df = pd.read_csv(DATA_PATH)
    # Just return array of risks, each object with key "Risk"
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/simulate", methods=["POST"])
def simulate_risk():
    data = request.json
    try:
        risk_name = data["risk"]
        mean = float(data.get("mean", 1_000_000))
        stddev = float(data.get("stddev", 300_000))
        simulations = int(data.get("simulations", 10_000))

        result = run_monte_carlo_simulation(risk_name, mean, stddev, simulations)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
