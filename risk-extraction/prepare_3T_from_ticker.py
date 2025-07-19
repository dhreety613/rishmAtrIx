import pandas as pd
import os
import json

# Step 1: Input
ticker = input("Enter ticker symbol (e.g., AAPL): ").strip().upper()

# Step 2: Paths
input_json = f"data/matrix_output/{ticker}_risk_matrix.json"
output_csv = f"data/reports/{ticker}_3T_risks.csv"
output_treat_csv = f"data/reports/{ticker}_treat_risks_for_montecarlo.csv"

# Step 3: Check file exists
if not os.path.exists(input_json):
    print(f"❌ File not found: {input_json}")
    exit()

# Step 4: Load JSON data
with open(input_json, 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Step 5: Clean + Score
df.columns = df.columns.str.strip().str.lower()
df['risk_score'] = df['likelihood'] * df['impact']

# Step 6: Classify
def classify_risk(score):
    if score >= 65:
        return 'Transfer'
    elif score >= 40:
        return 'Treat'
    else:
        return 'Tolerate'

df['action'] = df['risk_score'].apply(classify_risk)

# Step 7: Save full matrix with actions
os.makedirs("data/reports", exist_ok=True)
df.to_csv(output_csv, index=False)

# Step 8: Save Treat-only risks for Monte Carlo
df[df['action'] == 'Treat'].to_csv(output_treat_csv, index=False)

# Step 9: Print summary
print("\n✅ 3T report generated:")
print(f"- Full matrix: {output_csv}")
print(f"- Treat risks (for Monte Carlo): {output_treat_csv}")
print("\n📊 Risk counts:")
print(df['action'].value_counts())
