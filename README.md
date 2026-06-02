# 🚨 CrisisSwarm — Multi-Agent Disaster Response

[![Streamlit App](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://mircosoft-crisisswarm-n6uhmu7uk2wnesmxddv6dq.streamlit.app)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Groq Llama 3.3](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange?style=for-the-badge)](https://console.groq.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Microsoft Build AI Hackathon 2026** — *Theme 05: Agent Swarms*
>
> "Eight specialized AI agents coordinate disaster response in real-time — each with a dedicated role, shared situational awareness, a verification layer, and human-in-the-loop approval before alerts are broadcast."

---

## 🚀 Live Demo

Watch the swarm coordinate in real-time:
👉 **[CrisisSwarm Operations Dashboard](https://mircosoft-crisisswarm-n6uhmu7uk2wnesmxddv6dq.streamlit.app)**

*Select a scenario → click **ACTIVATE SWARM** → monitor live execution, maps, and reports.*

---

## 📖 How It Works

A single dispatcher cannot safely triage, allocate, route, and broadcast under intense pressure. **CrisisSwarm** solves this by deploying 8 specialized agents sharing a single situational context:

1. **Structured parsing**: Incident details are parsed to extract affected zones, hazards, and hospital locations.
2. **Sequential reasoning**: Each specialist agent handles one part of the problem, passing structured JSON outputs to downstream agents.
3. **Self-Correction & Verification**: The Verifier agent cross-checks all planning outputs, ensuring consistency and safety, returning a confidence score.
4. **Human-in-the-Loop**: A checkpoint halts the pipeline before broadcasting alerts, allowing operators to review routing, triage, and communications.
5. **Real-time inference**: Powered by **Groq Llama 3.3 70B** for sub-second agent processing and instant operational updates.

---

## ✨ Features

- **Shared Situation Parsing**: Disaster types, hazards, blocked roads, and critical resources parsed instantly by LLaMA 3.3.
- **8 Specialized Swarm Agents**: Situation, Commander, Triage, Resource, Routing, Comms, Verifier, and Reporter.
- **Automated Verification**: Verifier agent assesses overall plans, detects contradictions, flags errors, and issues a final confidence score (0-100).
- **Human-in-the-Loop Checkpoint**: Secure operator approval UI for validation of triage and routing paths prior to alerting.
- **Dual Groq Key Rotation**: Infinite, circular fallback mechanism that automatically switches API keys on rate-limits (`429`).
- **Pre-Configured & Custom Scenarios**: 5 default disaster scenarios (Earthquake in Mumbai, Hurricane in Florida, Flood in Tokyo, Earthquake in Turkey, Cyclone in Chennai) plus custom text scenario input.
- **Interactive Geospatial Visualizations**: Dynamic Pydeck map showing zones colored by severity, coordinates, routing overlays, and ETA tooltips.
- **Azure Maps & Fallbacks**: Utilizes Azure Maps Route API for real street route distances and travel times, falling back to Haversine routing if no key is configured.
- **Format Exporting**: Download detailed Executive Situation Reports (SitRep) in PDF and raw JSON format.
- **Docker-Ready**: Packaged with multi-platform Docker configuration for seamless team setup.

---

## 🏗️ Architecture Flow

```text
Scenario Text
↓
[Situation Parser] — extracts zones, hazards, blocked roads
↓
[Commander + Triage] — task assignments + per-zone casualties
↓
[Resource] — ambulances, medical teams, shelters, supplies
↓
[Routing] — ETAs, deployment order, road status
↓
⚠️  HUMAN APPROVAL CHECKPOINT
↓
[Comms] — responder, hospital, public alerts
↓
[Verifier] — cross-checks ALL outputs, flags issues
↓
[Analysis] — cross-agent synthesis, recommended actions
↓
[Reporter] — executive SitRep
↓
[Dashboard] — map, transcript, PDF/JSON export
```

### Swarm Agents Summary

| Agent | File | Primary Responsibility |
| :--- | :--- | :--- |
| **Situation** | `core/situation.py` | Parses incident details, zones, hazards, and coordinates. |
| **Commander** | `agents/commander.py` | Sets mission-critical tasks and prioritizes operational zones. |
| **Triage** | `agents/triage.py` | Classifies casualties (Critical/Serious/Minor) per zone. |
| **Resource** | `agents/resource.py` | Allocates medical teams, emergency vehicles, and supplies. |
| **Routing** | `agents/routing.py` | Determines route order, travel times, and ETAs (Azure Route API). |
| **Comms** | `agents/comms.py` | Formulates targeted responder, hospital, and public warnings. |
| **Verifier** | `agents/verifier.py` | Cross-checks compliance, conflicts, and issues a confidence score. |
| **Reporter** | `agents/reporter.py` | Synthesizes an executive-level PDF and text Situation Report. |

---

## 🛠️ Tech Stack

- **Groq API (Llama 3.3 70B)**: Real-time agent reasoning & sub-second response times.
- **OpenAI Python SDK**: Compatible Groq client interface.
- **Streamlit**: Dashboard and real-time step visualization.
- **Pydeck**: 3D interactive map component.
- **Azure Maps Route API**: Real-world route calculations.
- **ReportLab**: High-fidelity PDF generation.
- **Docker & Docker Compose**: Deployment packaging.
- **Python 3.11 - 3.13**: Application runtime.

---

## 📂 Project Structure

```text
crisisswarm/
├── agents/
│   ├── __init__.py
│   ├── commander.py   # Task assignments and zone priority
│   ├── triage.py      # Per-zone casualties classification
│   ├── resource.py    # Resource allocation
│   ├── routing.py     # Azure Maps + haversine routing
│   ├── comms.py       # Alert broadcasting (responder, hospital, public)
│   ├── verifier.py    # Cross-agent verification & confidence scoring
│   └── reporter.py    # SitRep generation
├── core/
│   ├── __init__.py
│   ├── agent_llm.py   # Low-level LLM helper
│   ├── analysis.py    # Operational analysis and recommended actions
│   ├── context.py     # SwarmContext structure
│   ├── groq_client.py # Dual key rotation & API integration
│   ├── scenario.py    # Scenarios data and coordinator mappings
│   ├── situation.py   # Situation parser & initial incident analysis
│   └── swarm.py       # Orchestration pipeline
├── dashboard/
│   ├── __init__.py
│   └── app.py         # Streamlit UI dashboard
├── config.py          # Configuration settings loader
├── docker-compose.yml # Docker Compose setup
├── Dockerfile         # Docker container definition
├── requirements.txt   # Python requirements list
└── .env.example       # Template for configuration keys
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Groq API Key ([Get one here](https://console.groq.com/keys))

### Installation & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/tejaspatel2255/Mircosoft-crisisswarm.git
   cd Mircosoft-crisisswarm
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and enter your credentials:
   - `GROQ_API_KEY`: Primary key.
   - `GROQ_API_KEY_2` (Optional): Backup key for seamless rotation under heavy traffic.
   - `AZURE_MAPS_KEY` (Optional): Azure Maps API subscription key.

4. **Verify Groq connection**
   ```bash
   python -c "from core.groq_client import verify_connection; print(verify_connection())"
   ```

5. **Start Streamlit Dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```
   Open your browser to `http://localhost:8501`.

---

## 🐳 Docker Deployment

To spin up the containerized application without local Python installation requirements:

```bash
docker-compose up --build
```

Access the application at `http://localhost:8501`.

---

## ⚙️ Environment Variables

| Variable | Required | Description | Default |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | **Yes** | Primary Groq API Key | - |
| `GROQ_API_KEY_2` | No | Backup key (rotated automatically on 429) | - |
| `GROQ_MODEL` | No | Model model for reasoning | `llama-3.3-70b-versatile` |
| `AZURE_MAPS_KEY` | No | Route calculation (haversine calculation fallback) | - |
| `STREAMLIT_PORT` | No | Internal port for Streamlit | `8501` |
| `SERVICE_NAME` | No | Service display name | `CrisisSwarm` |

---

## 👥 Team & Authors

- **Tejas Patel** — Lead AI Architect, Swarm Orchestration, Groq integration, and Streamlit Dashboard.

---

## 📄 License

This project is licensed under the MIT License.
