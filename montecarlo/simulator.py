import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def run_monte_carlo_simulation(risk_name, mean, stddev, simulations=10000):
    losses = np.random.normal(loc=mean, scale=stddev, size=simulations)

    min_loss = round(np.min(losses), 2)
    max_loss = round(np.max(losses), 2)
    avg_loss = round(np.mean(losses), 2)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(losses, bins=50, color="#004080", alpha=0.7)
    ax.axvline(avg_loss, color='gold', linestyle='--', label=f'Avg: ${avg_loss:,.0f}')
    ax.set_title(f"Simulated Loss Distribution for\n{risk_name}")
    ax.set_xlabel("Loss ($)")
    ax.set_ylabel("Frequency")
    ax.legend()

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    encoded_plot = base64.b64encode(buffer.read()).decode('utf-8')

    return {
        "risk": risk_name,
        "min_loss": min_loss,
        "max_loss": max_loss,
        "avg_loss": avg_loss,
        "graph_base64": encoded_plot
    }

def run_simulation_for_all_risks(csv_path, base_mean=1_000_000, base_stddev=300_000, custom_inputs=None):
    df = pd.read_csv(csv_path)
    results = []

    for i, row in df.iterrows():
        risk_text = row["Risk"]
        if custom_inputs and risk_text in custom_inputs:
            mean, stddev = custom_inputs[risk_text]
        else:
            mean, stddev = base_mean, base_stddev

        result = run_monte_carlo_simulation(risk_text, mean, stddev)
        results.append(result)

    return results
