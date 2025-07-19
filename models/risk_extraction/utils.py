import os
import json
import tiktoken
import re
from bs4 import BeautifulSoup

def extract_risk_section(file_path):
    """Extract the 'Item 1A. Risk Factors' section from a 10-K filing."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    # Clean HTML if needed
    soup = BeautifulSoup(raw_text, "html.parser")
    text = soup.get_text(" ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Regex patterns to extract Item 1A
    pattern = r"(Item\s+1A[\.:]?\s+Risk\s+Factors)(.*?)(Item\s+1B[\.:]?\s+|Item\s+2[\.:]?\s+|Item\s+7[\.:]?\s+)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(2).strip()
    else:
        return ""

def chunk_text(text, max_tokens=10000, model_name="gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunks.append(encoding.decode(chunk_tokens))

    return chunks

# 🔹 Load the Gemini risk extraction prompt
def load_prompt_template():
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompts", "risk_extraction_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise Exception(f"❌ Prompt file not found at: {prompt_path}")


# 🔹 Parse the Gemini model's JSON response

def parse_risks_json(raw_response):
    """
    Extract valid JSON list of risks from the Gemini response.
    Gemini sometimes adds extra text or formatting – strip all that out.
    """
    try:
        # First, try parsing as-is
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON array manually
        match = re.search(r"(\[.*?\])", raw_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                raise ValueError(f"❌ Failed to parse cleaned JSON: {e}")
        else:
            raise ValueError("❌ No JSON array found in response.")

# 🔹 Save risk output to a JSON file
def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


