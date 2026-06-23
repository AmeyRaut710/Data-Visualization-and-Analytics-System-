# 📊 AI Data Visualization System

[![Live Demo](https://img.shields.io/badge/Demo-Live-brightgreen.svg)](https://data-visualization-and-analytics-system-5kqje197n.vercel.app)
[![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

**AI Data Visualization System** is an Agentic AI-powered Data Visualization and Analytics Platform. 

🔒 **Privacy First:** Uploaded CSV, XLS, XLSX, and TSV files are strictly processed **in-memory (RAM)** and are **never saved to a database or disk permanently**.

---

## 🚀 Live Deployment

- **Main Application:** [https://data-visualization-and-analytics-sy.vercel.app](https://data-visualization-and-analytics-sy.vercel.app)
- **Alternate Link:** [https://data-visualization-and-analytics-system-5kqje197n.vercel.app](https://data-visualization-and-analytics-system-5kqje197n.vercel.app)

---

## ✨ Features

- **Data Profiling:** Automatic metadata inference to understand dataset structures instantly.
- **Data Quality Assessment:** Robust detection for missing values, duplicates, and outliers (using IQR, Z-Score, and Isolation Forest algorithms).
- **Data Cleaning Agent:** Interactive filling, dropping, and type casting functionality powered by AI.
- **Visualization Agent:** Auto-generated interactive charts using Plotly and Recharts.
- **AI Insights & Chat Assistant:** Ask questions about your data! Powered by LangGraph and Google Gemini.
- **Export System:** Export cleaned datasets as CSV or generate comprehensive HTML reports.

---

## 🏗 Architecture

The platform follows a modern decoupled architecture:

- **Frontend:** React + Vite + TailwindCSS + Plotly.js
- **Backend:** FastAPI + Pandas + LangChain + Scikit-Learn
- **Database:** MongoDB *(Note: Used strictly for user preferences and system logs. No datasets are stored!)*

---

## 💻 Setup Instructions

To run the application locally, follow these steps:

1. **Environment Configuration:**
   Rename `.env.example` to `backend/.env` and add your Gemini API Key:
   ```env
   GEMINI_API_KEY="your-api-key-here"
   ```

2. **Run the Application:**
   Choose one of the following methods to start both frontend and backend:
   
   - **Using Docker:**
     ```bash
     docker-compose up --build
     ```
   
   - **Using Batch Script (Windows):**
     Double-click `run_project.bat` from your file explorer.

---

*Built with ❤️ for Data Analysts & Engineers.*
