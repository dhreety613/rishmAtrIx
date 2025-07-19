import os
import json
import time
import re # Import the regular expression module
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # Import for safety settings
from google.api_core.exceptions import GoogleAPIError # Import specific API error for handling

# Load API key from room.env file
load_dotenv(".env")
# Configure the generative AI model with the loaded API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini Pro model for content generation
# Add safety settings to potentially reduce instances of blocked responses
# IMPORTANT CHANGE: Changed model name from "gemini-pro" to "gemini-1.0-pro"
# The previous error "404 models/gemini-pro is not found" suggests that
# "gemini-pro" might not be directly available or correctly mapped in the v1beta API for generateContent.
# "gemini-1.0-pro" is a more explicit and generally available model name for text generation.
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro",  # or "models/gemini-1.0-pro"
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

def score_risk(risk_text):
    """
    Scores a given business risk on likelihood and impact using the Gemini Pro model.
    Expects a JSON response from the model and handles potential formatting issues.
    """
    prompt = f"""
You are a financial risk expert.

Score the following business risk on two axes:
- Likelihood: from 1 (very unlikely) to 10 (very likely)
- Impact: from 1 (negligible) to 10 (catastrophic)

Respond ONLY with a JSON object like:
{{ "likelihood": 7, "impact": 8 }}

Risk: "{risk_text}"
"""
    raw_text = "" # Initialize raw_text to ensure it's always defined for error messages
    json_string = "" # Initialize json_string for error messages
    response = None # Initialize response to None

    try:
        # Generate content from the model based on the prompt
        response = model.generate_content(prompt)
        
        # --- NEW DEBUGGING PRINTS ---
        print(f"DEBUG: Full Gemini API response object: {response}")
        if response.prompt_feedback:
            print(f"DEBUG: Prompt Feedback: {response.prompt_feedback}")
        if response.candidates:
            print(f"DEBUG: Candidates available: {len(response.candidates)}")
        # --- END NEW DEBUGGING PRINTS ---

        # Check if the response has any candidates (i.e., if content was generated or blocked)
        if not response.candidates:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else 'N/A'
            print(f"🚫 Gemini response had no candidates. Blocked reason: {block_reason}.")
            raise ValueError(f"Gemini response was empty or blocked. Reason: {block_reason}. Full response: {response}")

        # Get the raw text response and strip leading/trailing whitespace
        # Safely access .text attribute, as it might not exist if content is not text
        raw_text = response.text.strip() if hasattr(response, 'text') and response.text is not None else ""
        print("🔍 Raw Gemini output:", repr(raw_text))  # Debug: show the exact raw output

        # Explicitly check if raw_text is empty right after stripping
        if not raw_text:
            raise ValueError("Gemini returned an empty string for the risk score. This indicates no content was generated, or content was not text.")

        # Attempt to extract JSON from markdown code block if present (e.g., ```json{...}```)
        # This makes the parsing more resilient to variations in model output.
        match = re.search(r"```json\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if match:
            json_string = match.group(1)
            print("✨ Extracted JSON from markdown:", repr(json_string)) # Debug: show extracted JSON
        else:
            # If no markdown block is found, assume the raw text is the JSON string
            json_string = raw_text
            print("✨ Using raw text as JSON:", repr(json_string)) # Debug: confirm raw text is used

        # Check if the extracted JSON string is empty (could happen if regex failed on non-markdown empty string)
        if not json_string:
            raise ValueError("Empty or unparseable response from Gemini after extraction attempt. The extracted JSON string was empty.")
            
        # Parse the JSON string into a Python dictionary
        parsed = json.loads(json_string)
        
        # Validate that both 'likelihood' and 'impact' keys are present in the parsed JSON
        if "likelihood" in parsed and "impact" in parsed:
            return parsed
        else:
            # Raise an error if expected keys are missing
            raise ValueError(f"Missing 'likelihood' or 'impact' keys in parsed JSON: {parsed}. Full raw response: '{raw_text}'")
            
    except json.JSONDecodeError as e:
        # Catch JSON parsing errors specifically and provide detailed debug info
        raise ValueError(f"Failed to parse JSON from Gemini response. "
                         f"Raw text received: '{raw_text}', "
                         f"Attempted JSON string: '{json_string}'. "
                         f"Error: {e}")
    except GoogleAPIError as e:
        # Catch Google API specific errors (e.g., invalid API key, quota issues, network)
        print(f"🚨 Google API Error: {e}")
        raise RuntimeError(f"Scoring failed due to Google API error: {e}")
    except Exception as e:
        # Catch any other unexpected errors during the scoring process
        # Print the full response object for more context if an error occurs
        print(f"🚨 An unexpected error occurred during API call or processing: {e}")
        if response: # Only print if response object was successfully assigned
            print(f"Full Gemini response object: {response}")
        else:
            print("Gemini response object was not available (error likely occurred during API call itself, e.g., network issue).")
        raise RuntimeError(f"Scoring failed due to an unexpected error: {e}")

def safe_score_risk(risk_text, retries=2, delay=2):
    """
    Attempts to score a risk with multiple retries in case of transient failures.
    """
    for attempt in range(retries + 1):
        try:
            return score_risk(risk_text)
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed for: {risk_text[:60]}... ({e})")
            if attempt < retries:
                time.sleep(delay) # Wait before retrying
    return None # Return None if all retries fail

def load_risks(ticker):
    """
    Loads risk data from a JSON file based on the company ticker.
    """
    path = os.path.join("data", "processed", f"{ticker}_risks.json")
    # Ensure the directory exists before trying to open the file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_matrix(ticker, scored_risks):
    """
    Saves the scored risks into JSON and CSV formats.
    """
    out_dir = os.path.join("data", "matrix_output")
    os.makedirs(out_dir, exist_ok=True) # Ensure output directory exists

    json_path = os.path.join(out_dir, f"{ticker}_risk_matrix.json")
    csv_path = os.path.join(out_dir, f"{ticker}_risk_matrix.csv")

    # Save to JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scored_risks, f, indent=2)

    # Save to CSV file
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Risk,Likelihood,Impact\n") # Write CSV header
        for item in scored_risks:
            # Enclose risk text in quotes to handle commas within the text
            f.write(f"\"{item['risk']}\",{item['likelihood']},{item['impact']}\n")

    print(f"✅ Matrix saved to:\n→ {json_path}\n→ {csv_path}")

def main():
    """
    Main function to run the risk scoring process.
    """
    # Check if the API key is loaded
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in room.env file.")
        print("Please ensure 'room.env' exists in the same directory as this script,")
        print("and contains a line like: GEMINI_API_KEY=\"YOUR_ACTUAL_API_KEY_HERE\"")
        return # Exit if API key is missing

    # Prompt user for company ticker
    ticker = input("Enter company ticker: ").strip().upper()
    
    try:
        # Load risks for the given ticker
        risks = load_risks(ticker)
    except FileNotFoundError:
        print(f"❌ Error: Risk file not found for ticker '{ticker}'. "
              "Please ensure 'data/processed/{ticker}_risks.json' exists.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from 'data/processed/{ticker}_risks.json'. "
              "Please check the file's content.")
        return

    print(f"📊 Scoring {len(risks)} risks for {ticker}...")
    matrix = []

    # Iterate through risks and score them (capped at 200 to manage API usage)
    for i, risk_text in enumerate(risks[:200]):
        print(f"→ [{i+1}/{len(risks)}] Attempting to score: {risk_text[:60]}...")
        score = safe_score_risk(risk_text)
        if score:
            matrix.append({
                "risk": risk_text,
                "likelihood": score["likelihood"],
                "impact": score["impact"]
            })
            print(f"✅ [{i+1}/{len(risks)}] Successfully scored risk.") # Debug after success
        else:
            print(f"❌ [{i+1}/{len(risks)}] Skipping risk due to persistent scoring failure.") # Debug after failure

    # Save the final risk matrix
    save_matrix(ticker, matrix)

if __name__ == "__main__":
    main()
