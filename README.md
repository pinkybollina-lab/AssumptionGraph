\# AssumptionGraph



\## Enterprise Assumption Intelligence



AssumptionGraph helps organizations capture assumptions across departments, identify inconsistencies, understand dependencies, and explore the downstream impact of potential decisions.



\## Key Features



\- \*\*Assumption Management:\*\* Capture and organize organizational assumptions.

\- \*\*Voice Intelligence:\*\* Extract information from voice input using the configured speech service.

\- \*\*Assumption Graph:\*\* Visualize relationships and dependencies between assumptions.

\- \*\*Findings:\*\* Identify potential contradictions for human review.

\- \*\*Scenario Simulator:\*\* Explore possible changes and their downstream impacts.



\## Technology Stack



\- \*\*Frontend:\*\* React, Vite, React Flow

\- \*\*Backend:\*\* Python, FastAPI, SQLAlchemy

\- \*\*Database:\*\* SQLite for local development; configurable through `DATABASE\_URL`.



\## Project Structure



```text

AssumptionGraph/

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

├── frontend/

│   ├── public/

│   ├── src/

│   └── package.json

├── .gitignore

└── README.md

```



\## Local Setup



\### Backend



Open a terminal in the project folder:



```powershell

cd backend

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

pip install -r requirements.txt

```



Create a local `.env` file using `.env.example` as a template. Configure your own GNANI API credentials if you intend to use the speech service. Never upload actual API keys.



Start the backend:



```powershell

uvicorn app.main:app --reload

```



\- Backend: http://127.0.0.1:8000

\- API documentation: http://127.0.0.1:8000/docs



\### Frontend



Open a second terminal:



```powershell

cd frontend

npm install

npm run dev

```



Open the frontend URL printed by Vite, normally http://localhost:5173.



\## Running Tests



From the backend directory:



```powershell

pytest test\_scenarios.py

```



Additional extraction test scripts are available in the backend directory.



\## Configuration and Security



\- Keep API keys and credentials in a local `.env` file.

\- Do not commit database files, backups, virtual environments, or generated build files.

\- Configure production environment variables and allowed frontend origins before deployment.

\- A fresh local setup creates its own database. The development database is not included in this repository.



\## Project Status



This repository contains the application source code and development tests. Production deployment and production database configuration must be completed separately.

