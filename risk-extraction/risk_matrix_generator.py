import os
import json
import time
import re
import random
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import GoogleAPIError

# Load API key
load_dotenv(".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configure Gemini model
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-pro",
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

def score_risk(prompt):
    """
    Sends a prompt to Gemini and returns parsed likelihood and impact.
    """
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    match = re.search(r"```json\s*(\{.*\})\s*```", raw_text, re.DOTALL)
    json_string = match.group(1) if match else raw_text

    return json.loads(json_string)

def batched_score_risks(risk_texts):
    """
    Scores a list of risks with enforced likelihood/impact distribution:
    - 70% Low (1–4)
    - 28% Medium (5–8)
    - 2% High (9–10)
    """
    total = len(risk_texts)
    n_low = int(0.70 * total)
    n_med = int(0.28 * total)
    n_high = total - n_low - n_med

    band_labels = ['low'] * n_low + ['medium'] * n_med + ['high'] * n_high
    random.shuffle(band_labels)

    scored = []

    for i, (risk_text, band) in enumerate(zip(risk_texts, band_labels)):
        print(f"→ Scoring risk {i+1}/{total} in '{band.upper()}' band")

        band_prompt_map = {
            'low': "Likelihood and Impact must be between 1 and 4.",
            'medium': "Likelihood and Impact must be between 5 and 8.",
            'high': "Likelihood and Impact must be between 9 and 10.",
        }

        prompt = f"""
You are a financial risk analyst scoring risks for a risk matrix.

Score the following business risk on a scale from 1 to 10 for:
- Likelihood: (1 = very unlikely, 10 = very likely)
- Impact: (1 = negligible loss, 10 = catastrophic loss)

{band_prompt_map[band]}
Respond ONLY with JSON: {{ "likelihood": X, "impact": Y }}

Risk: "{risk_text}"
""".strip()

        try:
            result = score_risk(prompt)
            scored.append(result)
        except Exception as e:
            print(f"❌ Failed to score: {risk_text[:60]}... — {e}")
            scored.append({"likelihood": 1, "impact": 1})  # Default fallback

    return scored

def load_risks(ticker):
    path = os.path.join("data", "processed", f"{ticker}_risks.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_matrix(ticker, scored_risks):
    out_dir = os.path.join("data", "matrix_output")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, f"{ticker}_risk_matrix.json")
    csv_path = os.path.join(out_dir, f"{ticker}_risk_matrix.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scored_risks, f, indent=2)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Risk,Likelihood,Impact\n")
        for item in scored_risks:
            f.write(f"\"{item['risk']}\",{item['likelihood']},{item['impact']}\n")

    print(f"✅ Matrix saved to:\n→ {json_path}\n→ {csv_path}")

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
        return

    ticker = input("Enter company ticker: ").strip().upper()

    try:
        risks = load_risks(ticker)
    except FileNotFoundError:
        print(f"❌ Risk file not found: data/processed/{ticker}_risks.json")
        return
    except json.JSONDecodeError:
        print(f"❌ Could not parse JSON for ticker '{ticker}'")
        return

    print(f"📊 Scoring {len(risks)} risks for {ticker}...")

    subset = risks[:200]
    scored_values = batched_score_risks(subset)

    matrix = []
    for risk_text, score in zip(subset, scored_values):
        matrix.append({
            "risk": risk_text,
            "likelihood": score["likelihood"],
            "impact": score["impact"]
        })

    save_matrix(ticker, matrix)

if __name__ == "__main__":
    main()
