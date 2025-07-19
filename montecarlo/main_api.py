# models/montecarlo/main_api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import time
import uuid
import sqlite3
from simulator import run_monte_carlo_simulation
from risk_extraction.final import extract_risks_from_ticker
from risk_matrix_generator import generate_matrix
from prepare_3T_from_ticker import get_montecarlo_list

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# Init DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    ticker TEXT
)
""")
conn.commit()
conn.close()

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    ticker = data.get("ticker")

    if not username or not password or not ticker:
        return jsonify({"error": "Missing fields"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        c.execute("INSERT INTO users (id, username, password, ticker) VALUES (?, ?, ?, ?)",
                  (user_id, username, password, ticker))
        conn.commit()
        return jsonify({"message": "User registered successfully."})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists."}), 400
    finally:
        conn.close()

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT ticker FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()

    if result:
        return jsonify({"ticker": result[0]})
    else:
        return jsonify({"error": "Invalid credentials."}), 401

@app.route("/process_ticker", methods=["POST"])
def process_ticker():
    data = request.json
    ticker = data.get("ticker")

    try:
        extract_risks_from_ticker(ticker)
        generate_matrix(ticker)
        risks = get_montecarlo_list(ticker)
        return jsonify({"risks": risks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/simulate", methods=["POST"])
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
