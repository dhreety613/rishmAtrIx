import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
import numpy as np

from sec_edgar_downloader import Downloader
from models.risk_extraction.utils import (
    chunk_text, load_prompt_template, parse_risks_json, save_json
)

# 🌱 Setup
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

COMPANY_DIR = "data/processed"
FILING_ROOT = "sec-edgar-filings"


def ensure_filings_exist(ticker, attempts=1, max_attempts=3):
    base_dir = os.path.join(FILING_ROOT, ticker, "10-K")

    # Check for full-submission.txt
    if os.path.exists(base_dir):
        files = []
        for subdir in os.listdir(base_dir):
            path = os.path.join(base_dir, subdir, "full-submission.txt")
            if os.path.isfile(path):
                files.append(path)
        if files:
            return files

    if attempts > max_attempts:
        print(f"❌ Failed to find or download filings after {max_attempts} attempts. Aborting.")
        return []

    print(f"📥 No existing filings found. Downloading for {ticker}... (Attempt {attempts}/{max_attempts})")
    try:
        dl = Downloader("MyCompany", "youremail@example.com")
        dl.get("10-K", ticker, limit=3)
    except Exception as e:
        print(f"❌ Error during download: {e}")
        return []

    return ensure_filings_exist(ticker, attempts + 1, max_attempts)


def extract_text_from_filing(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    return soup.get_text()


def extract_risks_with_gemini(text_chunk):
    prompt_template = load_prompt_template()
    filled_prompt = prompt_template.replace("{FILING_TEXT}", text_chunk[:4000])
    response = model.generate_content(filled_prompt)
    return response.text


def run_risk_pipeline():
    ticker = input("Enter the company ticker (e.g., AAPL): ").upper()
    print(f"🔍 Searching filings for: {ticker}")

    filings = ensure_filings_exist(ticker)
    if not filings:
        print("❌ No filings found or downloaded. Exiting.")
        return

    full_text = ""
    for file_path in filings:
        print(f"📄 Processing: {file_path}")
        full_text += extract_text_from_filing(file_path)

    if not full_text.strip():
        print("⚠️ Extracted text is empty. Exiting.")
        return

    # Chunk full 10-K text
    chunks = chunk_text(full_text)
    print(f"🧠 Total chunks: {len(chunks)}")

    # Select 50 evenly spaced chunks
    selected_chunks = [chunks[i] for i in np.linspace(0, len(chunks)-1, 50, dtype=int)]
    all_risks = []

    print("🧠 Extracting risks with Gemini...")
    for i, chunk in enumerate(selected_chunks):
        print(f"→ Chunk {i+1}/50")
        try:
            raw = extract_risks_with_gemini(chunk)
            risks = parse_risks_json(raw)
            all_risks.extend(risks)
        except Exception as e:
            print(f"⚠️ Error in chunk {i+1}: {e}")

    os.makedirs(COMPANY_DIR, exist_ok=True)
    out_path = os.path.join(COMPANY_DIR, f"{ticker}_risks.json")
    save_json(all_risks, out_path)

    print(f"✅ Saved {len(all_risks)} risks to: {out_path}")


if __name__ == "__main__":
    run_risk_pipeline()
