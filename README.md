# AI Data Analyst Agent

This is a comprehensive full-stack application built to serve as an AI-powered Data Analyst. Users can upload datasets (CSV/Excel), and the AI will automatically clean the data, perform Exploratory Data Analysis (EDA), detect anomalies, generate visualizations, and provide business insights.

## Features (Resume-Worthy)
*   **Authentication**: JWT-based user login and role-based access.
*   **Agentic Workflow**: Uses LangGraph to orchestrate a multi-step data analysis pipeline.
*   **Natural Language Querying**: Talk to your data using a LangChain Pandas agent.
*   **Dashboard**: A responsive Next.js frontend with Shadcn UI for managing datasets and viewing chat history.
*   **Security**: Basic prompt injection defenses and secure API endpoints.
*   **Evaluation & Auditing**: Tracks latency, estimates cost, and maintains audit logs for every query and upload.

## Tech Stack
*   **Frontend**: Next.js, Tailwind CSS, Shadcn UI, Recharts
*   **Backend**: FastAPI, SQLAlchemy, LangChain, LangGraph
*   **Database**: SQLite (Configured to be easily swapped for PostgreSQL via DATABASE_URL)
*   **LLM Provider**: Gemini 2.5 Pro (via Google GenAI)

## How to Run

### Using Docker Compose (Recommended)
1.  Ensure you have Docker installed.
2.  Set your API key in `docker-compose.yml` or export it: `export GOOGLE_API_KEY=your_key`
3.  Run the application:
    ```bash
    docker-compose up --build
    ```
4.  Access the frontend at `http://localhost:3000` and backend docs at `http://localhost:8000/docs`.

### Running Locally without Docker
#### Backend
1.  Navigate to `/backend`: `cd backend`
2.  Create and activate a virtual environment: `python -m venv venv` and `source venv/bin/activate` (or `.\venv\Scripts\activate` on Windows).
3.  Install dependencies: `pip install -r requirements.txt`
4.  Copy `.env.example` to `.env` and set your `GOOGLE_API_KEY`.
5.  Start the server: `uvicorn main:app --reload`

#### Frontend
1.  Navigate to `/frontend`: `cd frontend`
2.  Install dependencies: `npm install`
3.  Start the dev server: `npm run dev`

## Deployment
This project is configured to be easily deployed to services like Render, Vercel, or a VPS using the provided Dockerfiles and `docker-compose.yml`.
