# RiskMatrix Project

## 📂 Project Structure & Flow

### `models/risk_extraction/`
- **`final.py`**  
  Downloads the SEC EDGAR filings for the user-specified ticker. It processes the 10-K document in 50-chunk segments and extracts risk-related content.  
  Extracted risks are saved into the `data/` folder.

- **`risk_matrix_generator.py`**  
  Takes the extracted risks and assigns **impact** and **likelihood** values, generating a **risk matrix** for the given ticker.

- **`prepare_3T_from_ticker.py`**  
  Consumes the risk matrix and prepares:
  - `3T reports`
  - `montecarlo CSV` used for simulation

---

### `montecarlo/`
- **`simulator.py`**  
  Performs Monte Carlo simulation on the risk data provided, using statistical sampling and analysis methods.

- **`main_api.py`** (Flask backend)  
  Handles API routes for:
  - User authentication (`/signup`, `/signin`)
  - Running the full risk extraction and matrix generation pipeline based on the ticker
  - Serving risks and simulation results

---

### `frontend/` (React Frontend)
- Structured under `src/pages/` with:
  - `SignUp.jsx`
  - `SignIn.jsx`
  - `Loading.jsx` (initiates backend pipeline)
  - `Simulator.jsx`

- **✅ `Simulator.jsx`**  
  A fully functional page that:
  - Loads risks from the backend via `api.py` (`/api/risks`)
  - Performs Monte Carlo simulation per risk using `/api/simulate`
  - Displays individual risk outcomes dynamically

> The frontend is under development but synced with the backend. `Simulator.jsx` can be run independently to test the simulation flow via `api.py`.

---

## 🛠 Status: In Progress
End-to-end flow from signup to simulation is being actively built and refined.
