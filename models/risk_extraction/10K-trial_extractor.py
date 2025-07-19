import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
from sec_edgar_downloader import Downloader

from models.risk_extraction.utils import (
    chunk_text, load_prompt_template, parse_risks_json, save_json
)

# Load environment variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

COMPANY_DIR = "data/processed"
FILING_ROOT = "sec-edgar-filings"

def ensure_filings_exist(ticker, attempts=1, max_attempts=3):
    """Check if full-submission.txt exists, else download 10-Ks (max 3 attempts)."""
    base_dir = os.path.join(FILING_ROOT, ticker, "10-K")

    # Check for existing full-submission.txt files
    if os.path.exists(base_dir):
        files = []
        for subdir in os.listdir(base_dir):
            path = os.path.join(base_dir, subdir, "full-submission.txt")
            if os.path.isfile(path):
                files.append(path)
        if files:
            return files

    # Retry logic
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

    # Try again after downloading
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
    company_ticker = input("Enter the company ticker (e.g., AAPL): ").upper()
    print(f"🔍 Searching filings for: {company_ticker}")

    filings = ensure_filings_exist(company_ticker)
    if not filings:
        print("❌ No filings found or downloaded. Exiting.")
        return

    all_text = ""
    for file_path in filings:
        print(f"📄 Processing: {file_path}")
        all_text += extract_text_from_filing(file_path)

    if not all_text.strip():
        print("⚠️ Extracted text is empty. Exiting.")
        return

    chunks = chunk_text(all_text)
    all_risks = []

    print("🧠 Extracting risks with Gemini...")
    for i, chunk in enumerate(chunks):
        print(f"→ Chunk {i+1}/{len(chunks)}")
        try:
            raw = extract_risks_with_gemini(chunk)
            risks = parse_risks_json(raw)
            all_risks.extend(risks)
        except Exception as e:
            print(f"⚠️ Error in chunk {i+1}: {e}")

    os.makedirs(COMPANY_DIR, exist_ok=True)
    out_path = os.path.join(COMPANY_DIR, f"{company_ticker}_risks.json")
    save_json(all_risks, out_path)

    print(f"✅ Saved {len(all_risks)} risks to: {out_path}")

if __name__ == "__main__":
    run_risk_pipeline()
