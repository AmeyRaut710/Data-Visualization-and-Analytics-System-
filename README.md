# 📊 AI Data Visualization & Analytics System

<p align="center">

![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

</p>

<p align="center">
An <b>Agentic AI-powered Data Visualization and Analytics Platform</b> that automatically profiles, cleans, analyzes, visualizes, and explains datasets using intelligent AI agents.
</p>

---

# 🚀 Live Demo

### 🌐 **Project URL**

**https://data-visualization-and-analytics-sy.vercel.app/**

---

# 📖 Overview

AI Data Visualization & Analytics System is a modern web-based platform designed to simplify data analysis for students, researchers, analysts, and businesses.

Instead of manually cleaning datasets and creating visualizations, users simply upload a dataset and let AI agents perform:

- Data Profiling
- Data Quality Analysis
- Intelligent Data Cleaning
- Automatic Visualization
- AI-Powered Insights
- Interactive Chat with Dataset
- Report Generation

The system processes uploaded datasets entirely **in memory (RAM)** to ensure maximum privacy.

---

# 🔒 Privacy First

✅ CSV, XLS, XLSX and TSV files are processed **only in RAM**

✅ Uploaded datasets are **never permanently stored**

✅ No database is used to save user datasets

✅ MongoDB stores only:

- User preferences
- System logs
- Chat history (optional)

---

# ✨ Features

## 📊 Data Profiling Agent

Automatically detects:

- Dataset dimensions
- Column names
- Data types
- Numerical & categorical columns
- Memory usage
- Summary statistics

---

## 🧹 Data Quality Agent

Detects:

- Missing values
- Duplicate rows
- Empty cells
- Invalid values
- Outliers

Supports multiple algorithms:

- IQR
- Z-Score
- Isolation Forest

---

## 🤖 AI Data Cleaning Agent

Provides intelligent cleaning operations:

- Fill Missing Values
- Drop Missing Values
- Remove Duplicates
- Handle Outliers
- Change Data Types
- Rename Columns
- Delete Columns

---

## 📈 Visualization Agent

Automatically recommends and generates interactive charts.

Supported visualizations include:

- Bar Chart
- Line Chart
- Scatter Plot
- Pie Chart
- Histogram
- Box Plot
- Heatmap
- Correlation Matrix
- Count Plot
- Distribution Plot

Built using:

- Plotly
- Recharts

---

## 💬 AI Chat Assistant

Powered by:

- LangGraph
- LangChain
- Google Gemini

Capabilities:

- Ask questions about datasets
- Explain trends
- Summarize statistics
- Generate insights
- Recommend visualizations

---

## 📄 Report Generation

Export:

- Cleaned CSV
- HTML Reports

Includes:

- Dataset Summary
- Quality Report
- Charts
- AI Insights

---

# 🏗️ System Architecture

```
                User Uploads Dataset
                        │
                        ▼
              Data Profiling Agent
                        │
                        ▼
             Data Quality Assessment
                        │
                        ▼
              AI Cleaning Agent
                        │
                        ▼
            Visualization Generator
                        │
                        ▼
            AI Chat & Insights Agent
                        │
                        ▼
               Export Reports / CSV
```

---

# 🛠 Tech Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Plotly.js
- Recharts
- Axios

---

## Backend

- FastAPI
- Pandas
- NumPy
- Scikit-learn
- LangChain
- LangGraph
- Google Gemini API

---

## Database

MongoDB

Used only for:

- User Preferences
- System Logs
- Session Management

> **Datasets are never stored.**

---

# 📂 Project Structure

```
AI-Data-Visualization-System
│
├── backend
│   ├── app
│   ├── services
│   ├── agents
│   ├── models
│   ├── utils
│   └── main.py
│
├── frontend
│   ├── src
│   ├── pages
│   ├── components
│   ├── hooks
│   └── assets
│
├── docker-compose.yml
├── run_project.bat
├── README.md
└── requirements.txt
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-Data-Visualization-System.git

cd AI-Data-Visualization-System
```

---

## 2. Configure Environment

Create:

```
backend/.env
```

Add:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

---

## 3. Install Dependencies

### Backend

```bash
cd backend

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend

npm install
```

---

## 4. Run Project

### Option 1 — Docker

```bash
docker-compose up --build
```

---

### Option 2 — Windows

Double-click:

```
run_project.bat
```

---

### Option 3 — Manual

Backend

```bash
uvicorn app.main:app --reload
```

Frontend

```bash
npm run dev
```

---

# 📊 Supported File Formats

- CSV
- XLS
- XLSX
- TSV

---

# 🚀 Future Enhancements

- PDF Report Export
- Dashboard Sharing
- Role-based Authentication
- Multi-file Analysis
- Real-time Collaboration
- AutoML Integration
- SQL Dataset Support
- Cloud Storage Connectors
- Explainable AI (SHAP/LIME)
- Multi-Agent Workflow Expansion

---

# 📸 Screenshots

> Add screenshots of:

- Home Page
- Upload Page
- Data Profiling
- Data Cleaning
- Dashboard
- AI Chat
- Report Generation

Example:

```
/screenshots/home.png
/screenshots/dashboard.png
/screenshots/chat.png
```

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository

2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push

```bash
git push origin feature-name
```

5. Create a Pull Request

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Developer

**Amey Raut**

B.Tech Computer Science & Engineering

Data Analytics | AI | Machine Learning | Full Stack Development

---

# ⭐ Support

If you found this project useful, please consider giving it a ⭐ on GitHub.

It helps others discover the project and motivates further development.

---

<p align="center">

<b>Built with ❤️ using React, FastAPI, LangGraph, Google Gemini, and AI Agents.</b>

</p>
