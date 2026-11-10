# AssumptionGraph
### Enterprise Assumption Intelligence

<p align="center">
  Turning scattered organizational assumptions into actionable intelligence.
</p>

<p align="center">
  <a href="https://assumption-graph.vercel.app">Live Application</a> •
  <a href="https://assumptiongraph.onrender.com/docs">API Documentation</a>
</p>

---

## Overview

Organizations make critical decisions based on assumptions shared across departments, meetings, conversations, and documents. However, these assumptions are often scattered and disconnected, making it difficult to identify inconsistencies, understand dependencies, and anticipate potential business impacts.

**AssumptionGraph** is an Enterprise Assumption Intelligence platform that helps organizations capture, organize, visualize, and analyze assumptions in one centralized system.

It connects organizational assumptions, highlights potential inconsistencies for human review, and enables teams to explore possible scenarios before making important decisions.

## Key Features

### 1. Centralized Dashboard
Provides an overview of recorded assumptions, dependencies, findings, and saved scenarios.

### 2. Assumption Management
Capture, organize, and maintain organizational assumptions with structured information such as department, type, confidence, and status.

### 3. Voice Intelligence – Powered by Gnani AI
Integrates **Gnani AI's Prisma Speech-to-Text API** to convert voice recordings into text. This helps capture spoken organizational knowledge and supports structured assumption creation.

### 4. Interactive Assumption Graph
Visualizes recorded assumptions and their relationships, helping users understand connections across organizational information.

### 5. Findings and Inconsistency Detection
Highlights potential inconsistencies between recorded assumptions so that teams can investigate and review them.

### 6. Scenario Simulator
Allows users to explore possible changes and understand their potential downstream business impacts.

## How It Works

1. **Capture:** Record organizational assumptions through structured inputs or voice recordings.
2. **Transcribe:** Use Gnani AI Speech-to-Text to convert audio into text.
3. **Organize:** Store assumptions with relevant organizational details.
4. **Visualize:** Explore recorded assumptions and their relationships through an interactive graph.
5. **Review:** Identify potential inconsistencies through findings.
6. **Simulate:** Explore possible changes and their downstream impacts.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite |
| Graph Visualization | React Flow |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Graph Processing | NetworkX |
| Voice AI | Gnani AI Prisma Speech-to-Text API |
| Deployment | Vercel, Render |

## System Architecture

```text
             USER
               |
               v
       React + Vite Frontend
               |
               v
         FastAPI Backend
               |
       +-------+--------+
       |       |        |
       v       v        v
  PostgreSQL  NetworkX  Gnani AI
  Database    Graph     Speech-to-Text
       |       |        |
       +-------+--------+
               |
               v
     Assumption Intelligence
               |
       +-------+--------+
       |       |        |
       v       v        v
     Graph  Findings  Scenarios
```

## Project Structure

```text
AssumptionGraph/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
│
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- PostgreSQL (for PostgreSQL-based configuration)
- Gnani AI API credentials (for voice transcription)

### 1. Clone the Repository

```bash
git clone https://github.com/pinkybollina-lab/AssumptionGraph.git
cd AssumptionGraph
```

### 2. Backend Setup

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a template. Configure the database connection and Gnani AI credentials as required.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open a second terminal:

```bash
cd frontend

npm install

npm run dev
```

Open the local URL provided by Vite, normally:

`http://localhost:5173`

## Running Tests

From the backend directory:

```bash
pytest
```

The backend test suite covers API functionality, role-based dashboards, submission workflows, database constraints, and related application behavior.

## Deployment

The application is deployed using:

- **Frontend:** Vercel
- **Backend:** Render
- **Database:** Render PostgreSQL

Access the deployed application:

**Live Application:** https://assumption-graph.vercel.app

**Backend API Documentation:** https://assumptiongraph.onrender.com/docs

## Security and Configuration

- Store API keys and credentials in environment variables.
- Never commit `.env` files or expose private API credentials.
- Use `.env.example` as a configuration template.
- Configure production CORS origins appropriately.
- Do not commit database backups, virtual environments, or generated build files.

## Expected Impact

AssumptionGraph aims to help organizations:

- Improve visibility into organizational assumptions.
- Identify potential inconsistencies earlier.
- Understand relationships between decisions and assumptions.
- Explore possible business impacts before taking action.
- Make better-informed, data-driven decisions.

## Team

**Bollina Kranthi**  
**Rayvanth**

Built as part of **The Great Indian AI Internship Challenge**, integrating Gnani AI voice technology.

---

<p align="center">
  AssumptionGraph – Understand What Your Organization Believes.
  
  Identify What Might Conflict. Explore What Happens Next.
</p>

