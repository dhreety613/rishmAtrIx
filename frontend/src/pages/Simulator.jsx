import React, { useEffect, useState } from "react";
import "../App.css";

function App() {
  const [risks, setRisks] = useState([]);
  const [selectedRisks, setSelectedRisks] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch risk data on component mount
  useEffect(() => {
    fetch("http://localhost:5000/api/risks")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRisks(data);
        } else {
          alert("Unexpected API response");
        }
      })
      .catch(() => alert("Failed to load risk list"));
  }, []);

  // Toggle selection for a single risk
  const toggleRiskSelection = (riskName) => {
    setSelectedRisks((prev) =>
      prev.includes(riskName)
        ? prev.filter((r) => r !== riskName)
        : [...prev, riskName]
    );
  };

  // Run simulations
  const fetchSimulations = async () => {
    if (selectedRisks.length === 0) {
      alert("Please select at least one risk.");
      return;
    }

    setLoading(true);
    const allResults = [];

    for (const riskName of selectedRisks) {
      try {
        const res = await fetch("http://localhost:5000/api/simulate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            risk: riskName,
            mean: 1000000,
            stddev: 300000,
            simulations: 10000,
          }),
        });

        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || "Simulation failed");
        }

        const data = await res.json();
        allResults.push(data);
      } catch (error) {
        alert(`Simulation failed for risk "${riskName}": ${error.message}`);
      }
    }

    setResults(allResults);
    setLoading(false);
  };

  return (
    <div className="app-container">
      <h1>Monte Carlo Risk Simulator</h1>

      <div className="risk-selection">
        <h3>Select Risks to Simulate:</h3>
        <div className="risk-list">
          {risks.length === 0 && <p>Loading risks...</p>}
          {risks.map((risk, idx) => (
            <label key={idx} style={{ display: "block", cursor: "pointer" }}>
              <input
                type="checkbox"
                value={risk.risk}
                checked={selectedRisks.includes(risk.risk)}
                onChange={() => toggleRiskSelection(risk.risk)}
              />
              {" "}
              {risk.risk}
            </label>
          ))}
        </div>
      </div>

      <button onClick={fetchSimulations} disabled={loading}>
        {loading ? "Simulating..." : "Run Simulation"}
      </button>

      <div className="results">
        {results.map((risk, idx) => (
          <div key={idx} className="risk-card">
            <h3>{risk.risk}</h3>
            <p><strong>Min Loss:</strong> ${risk.min_loss.toLocaleString()}</p>
            <p><strong>Max Loss:</strong> ${risk.max_loss.toLocaleString()}</p>
            <p><strong>Avg Loss:</strong> ${risk.avg_loss.toLocaleString()}</p>
            <img
              src={`data:image/png;base64,${risk.graph_base64}`}
              alt={`Distribution for ${risk.risk}`}
              style={{ maxWidth: "100%", height: "auto" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
