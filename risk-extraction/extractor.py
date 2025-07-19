import os
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv
from models.risk_extraction.utils import save_json, load_prompt_template

# Load .env for API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_news_headlines(company_name):
    query = company_name.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}"
    feed = feedparser.parse(url)
    headlines = [entry.title for entry in feed.entries]
    return headlines[:15]

def generate_risk_prompt(company_name, headlines):
    prompt_template = load_prompt_template()
    headline_text = "\n".join(f"- {title}" for title in headlines)
    return prompt_template.replace("{COMPANY_NAME}", company_name).replace("{HEADLINES}", headline_text)

def get_risks_from_gemini(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def extract_risks_for_company(company_name):
    print(f"📡 Fetching news for: {company_name}")
    headlines = fetch_news_headlines(company_name)

    if not headlines:
        print("❌ No headlines found. Try a different company name.")
        return

    prompt = generate_risk_prompt(company_name, headlines)
    print("🧠 Sending to Gemini...")
    risks = get_risks_from_gemini(prompt)

    output_path = f"data/processed/{company_name.replace(' ', '_')}_news_risks.json"
    os.makedirs("data/processed", exist_ok=True)
    save_json(risks, output_path)

    print(f"\n✅ Saved extracted risks to: {output_path}")
    print("\n🛡️ Risk Output Preview:\n")
    print(risks)

if __name__ == "__main__":
    company = input("Enter company name: ")
    extract_risks_for_company(company)
