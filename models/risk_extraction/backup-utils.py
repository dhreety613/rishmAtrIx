
import json

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2)

def load_prompt_template():
    with open("models/risk_extraction/prompt.txt", "r", encoding="utf-8") as f:
        return f.read()
