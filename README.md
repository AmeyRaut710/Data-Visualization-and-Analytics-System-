# AI Data Visualization System

An Agentic AI-powered Data Visualization and Analytics Platform. 
**Privacy First:** Uploaded CSV, XLS, XLSX, TSV files are strictly processed in-memory (RAM) and never saved to a database or disk permanently. 

## Features
- **Data Profiling:** Automatic metadata inference.
- **Data Quality Assessment:** Missing values, duplicates, outliers (IQR, Z-Score, Isolation Forest).
- **Data Cleaning Agent:** Interactive filling, dropping, and type casting.
- **Visualization Agent:** Auto-generated Plotly/Recharts.
- **AI Insights & Chat Assistant:** Powered by LangGraph and Gemini.
- **Export System:** CSV and HTML reports.

## Setup Instructions

1. Rename `.env.example` to `backend/.env` and add your `GEMINI_API_KEY`.
2. Run the application:
   - **Using Docker:** `docker-compose up --build`
   - **Using Batch Script (Windows):** Double-click `run_project.bat`

## Architecture
- **Frontend:** React + Vite + TailwindCSS + Plotly.js
- **Backend:** FastAPI + Pandas + LangChain + Scikit-Learn
- **Database:** MongoDB (Used strictly for user preferences and system logs. No datasets are stored).
