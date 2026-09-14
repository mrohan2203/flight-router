# ✈️ Flight Router: Autonomous ATC Agent

![React](https://img.shields.io/badge/React_Three_Fiber-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-F37626?style=for-the-badge&logo=xgboost&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

An autonomous, 3D Air Traffic Control (ATC) radar simulation powered by real-time ADSB telemetry. This project utilizes a dual AI architecture: **LangGraph (Llama 3.1)** for dynamic conflict resolution and an **XGBoost** predictive classifier acting as a deterministic safety gatekeeper.

## ✨ Core Features

*   **Real-Time 3D Radar:** Renders live, globally scaled telemetry across major hubs (LHR, JFK, SIN, MAA, DXB) using React Three Fiber and WebSockets. Filters out ground noise to focus on active airspace.
*   **LLM Orchestration:** An autonomous LangGraph agent uses Llama 3.1 to analyze airspace state and issue deterministic tool calls (Descent Clearances, Lateral Diversions).
*   **Deterministic ML Gatekeeper:** An XGBoost model trained on synthetic wake turbulence and separation minimums evaluates all LLM commands. If the LLM hallucinates an unsafe vector, the gatekeeper blocks the command and logs a system override.
*   **Zero-Latency Synthetic Radio:** Translates raw JSON resolution commands into natural ATC English, broadcasted instantly using the browser's native Web Speech API.
*   **Automated Analytics:** Accumulates asynchronous session metrics in the background and generates downloadable PDF shift reports using FPDF.

## 🧠 System Architecture

1.  **Ingestion:** FastAPI background threads poll the ADSB.lol API, map global coordinates via equirectangular projection, and filter non-airborne targets.
2.  **Detection:** XGBoost evaluates proximity and wake turbulence categories across all active flight pairs.
3.  **Resolution:** LangGraph prompts Llama 3.1 with active conflicts to generate ATC tool-call solutions.
4.  **Validation:** The Gatekeeper Node cross-references the LLM's output against the XGBoost predictions.
5.  **Execution:** Approved commands are pushed via WebSockets to the React frontend, updating target visual states and triggering synthetic audio.

## 🚀 Local Installation

### Prerequisites
*   Node.js & npm
*   Python 3.12+
*   [Ollama](https://ollama.ai/) running locally with the Llama 3.1 model (`ollama run llama3.1`)
*   *(macOS only)* OpenMP runtime for XGBoost: `brew install libomp`

### 1. Backend Setup
Navigate to the backend directory, set up your virtual environment, and train the local safety model before starting the server.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate synthetic training data and serialize the XGBoost model
python train_wake_model.py

# Start the FastAPI WebSocket server
uvicorn main:app --reload

### 2. Frontend Setup
In a new terminal window, navigate to the frontend directory and start the Vite development server.

```bash
cd frontend
npm install
npm run dev
```

## 🎮 Usage

*   **Select Airspace:** Use the dropdown in the ATC Agent Log panel to switch between global airport sectors.
*   **Target Inspector:** Click on any 3D aircraft cone to view its live telemetry, callsign, and wake category.
*   **Monitor Agent Logs:** Watch the UI for red XGBoost System Alerts, and listen for the synthetic radio broadcasts when the LLM successfully resolves a conflict.
*   **Export Analytics:** Click `[ Generate Shift Report ]` to download a PDF breakdown of session traffic and time-stamped conflict logs.

## 🐳 Docker Deployment

The Python backend is containerized for cloud deployment (AWS App Runner / Azure Container Apps). 

```bash
# Build the image
docker build -t flight-router-backend .

# Run locally to test containerization
docker run -p 8000:8000 flight-router-backend
```
*Note: Ensure the cloud provider is configured with a minimum instance count of `1` to prevent serverless scale-to-zero cold starts from dropping the continuous WebSocket loop.*
