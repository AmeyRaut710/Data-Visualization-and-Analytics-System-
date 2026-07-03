# AI Data Visualization and Analytics System - Complete Architecture Report

This document provides a comprehensive, step-by-step explanation of the AI Data Visualization and Analytics System. It is designed to serve as a detailed reference for generating a formal project report.

---

## 1. Project Overview
The **AI Data Visualization and Analytics System** is an Agentic AI-powered platform that allows users to upload datasets (CSV, Excel, etc.) and perform intelligent data profiling, cleaning, visualization, and conversational analytics. 

**Key Philosophy (Privacy First):** 
The system operates entirely **in-memory (RAM)**. Datasets are never permanently stored in a database or on disk. Uploaded data exists only during the active user session and is automatically garbage-collected when the session expires or is manually deleted.

---

## 2. Technology Stack
The platform uses a modern, decoupled client-server architecture.

### Frontend
*   **Core Framework:** React.js (v19) via Vite
*   **Styling:** Tailwind CSS (v3), PostCSS
*   **Routing:** React Router DOM (v7)
*   **Data Visualization:** Plotly.js, React-Plotly.js, Recharts
*   **Data Grid:** AG Grid Community & React
*   **Icons:** Lucide React
*   **HTTP Client:** Axios

### Backend
*   **Core Framework:** FastAPI (Python)
*   **Server:** Uvicorn
*   **Data Processing:** Polars (for high-performance in-memory operations) and Pandas (for fallback/AI agent compatibility)
*   **AI / LLM Integration:** LangChain, LangGraph, Google Gemini Pro (`langchain-google-genai`)
*   **Machine Learning:** Scikit-Learn, XGBoost, SHAP, LIME (for advanced analytics and anomaly detection)
*   **Other Utilities:** RapidFuzz, PyArrow, Pydantic, openpyxl (for Excel files), orjson (for fast JSON responses)

---

## 3. System Architecture & Core Modules

The system is split into two independent repositories/folders: `frontend/` and `backend/`.

### 3.1 Backend Architecture (`backend/app/`)
The backend follows a service-oriented and agent-based architecture:

*   **`api/routes.py`**: The main entry point for all frontend requests. It orchestrates the flow between services, session management, and AI agents.
*   **`core/state.py`**: Manages the in-memory `active_sessions` dictionary. Each session maps a unique `session_id` to its respective Polars DataFrame, history (for undo/redo), and metadata caches.
*   **`services/`**:
    *   `data_ingestion.py`: Parses incoming CSV/XLSX files into DataFrames and generates initial overviews.
    *   `data_quality.py`: Evaluates the dataset for missing values, duplicates, and outliers (using algorithms like Isolation Forest or Z-Score).
    *   `data_cleaning.py`: Executes targeted transformations (e.g., dropping columns, filling NaNs, casting types).
    *   `metadata_manager.py`: Highly optimized module that computes boolean masks for the dataset (e.g., where the outliers or empty cells are) and caches them to prevent re-computation.
    *   `export_service.py`: Handles exporting the cleaned dataset back to the user as a CSV/HTML.
*   **`agents/` (The "Agentic AI" Core)**:
    *   `cleaning_agent.py`: Analyzes columns with issues and recommends the best data cleaning strategies.
    *   `visualization_agent.py`: Reviews the dataset schema and generates optimal configurations for Plotly/Recharts charts.
    *   `insight_agent.py`: Generates narrative insights, executive summaries, and health reports based on the statistical profile of the data.
    *   `chat_agent.py`: A conversational agent (RAG/DataFrame Agent) that allows the user to ask plain-text questions about their dataset.
    *   `prediction_agent.py`: Likely handles the Scikit-learn/XGBoost predictive modeling and SHAP/LIME explainability.

### 3.2 Frontend Architecture (`frontend/src/`)
The frontend is a Single Page Application (SPA) structured by features:

*   **`App.jsx`**: Contains the sidebar navigation and routing logic.
*   **`pages/`**:
    *   `UploadPage.jsx`: Drag-and-drop interface for file uploads.
    *   `WorkspacePage.jsx`: Interactive workspace for data cleaning (the core operational hub).
    *   `TablePage.jsx`: A high-performance data grid view utilizing AG-Grid, capable of handling large datasets via backend pagination.
    *   `DashboardPage.jsx`: Provides an overarching view of data health and basic stats.
    *   `VisualizationPage.jsx`: Renders the AI-generated interactive charts.
    *   `InsightPage.jsx`: Displays AI-generated narrative insights.
    *   `ChatPage.jsx`: A ChatGPT-like interface for querying the dataset.
    *   `SettingsPage.jsx`: User preferences (if any).

---

## 4. Step-by-Step System Flow (How it Works)

### Step 1: Data Ingestion & Session Creation
1. The user drags and drops a dataset on the `UploadPage`.
2. The file is sent via a `POST /api/upload` request.
3. **Backend (`routes.py`)**:
    * The file is read into memory as a `polars.DataFrame`.
    * A unique `session_id` (UUID) is generated.
    * A session object is created in `core.state.active_sessions`. This object stores the raw DataFrame, a history stack (for Undo/Redo operations), and a history pointer.
    * `MetadataManager.compute_all_masks` is called to pre-calculate where anomalies (missing data, outliers) exist.
    * An overview (row count, column count, memory usage) is returned to the frontend.

### Step 2: Data Quality Assessment
1. The frontend requests `GET /api/quality/{session_id}`.
2. **Backend**:
    * `DataQualityService` uses the pre-computed masks to generate a detailed report (missing values %, outlier detection, duplicate count).
    * `InsightAgent` consumes this technical report and generates a natural language "AI Health Report" describing the dataset's condition.

### Step 3: Interactive Data Cleaning
1. In the `WorkspacePage`, the user selects an issue (e.g., "Missing Values" in the "Age" column).
2. The user can ask for AI recommendations (`POST /api/clean/{session_id}/recommend`), which triggers the `CleaningAgent`.
3. The user applies a cleaning action (e.g., Fill with Mean) via `POST /api/clean/{session_id}/apply`.
4. **Backend**:
    * `DataCleaningService` applies the transformation.
    * The new DataFrame state is appended to the session's `history` list.
    * The `history_pointer` moves forward. This enables O(1) Undo/Redo capabilities by just shifting the pointer and accessing previous DataFrame states in RAM.
    * `MetadataManager` smartly updates the anomaly masks rather than recomputing the whole dataset.

### Step 4: AI Visualizations & Insights
1. **Visualizations**: The user navigates to the `VisualizationPage`. The frontend calls `GET /api/visualizations/{session_id}`. The `VisualizationAgent` samples the dataset, determines the best chart types (scatter, bar, distribution), and returns JSON configurations that React-Plotly renders.
2. **Insights**: The `InsightPage` calls `GET /api/insights/{session_id}`. The `InsightAgent` runs statistical correlation tests and uses the LLM to write a comprehensive executive summary.

### Step 5: Conversational Analytics (Chat)
1. The user types a question in the `ChatPage` (e.g., "What is the average sales in Q3?").
2. The request goes to `POST /api/chat/{session_id}`.
3. **Backend**: `ChatAgent` uses LangChain's DataFrame Agent (or similar LangGraph flow). It converts the user's natural language into Python/Polars code, executes it against the in-memory DataFrame securely, and returns a natural language answer to the user.

### Step 6: Export & Garbage Collection
1. The user exports the cleaned data via `GET /api/export/{session_id}/csv`.
2. To prevent memory leaks, `sweep_expired_sessions()` runs on new uploads, iterating through `active_sessions` and deleting any session inactive for more than 1 hour. Python's `gc.collect()` is explicitly called to free RAM.

---

## 5. Key Technical Highlights for the Report

1.  **Polars over Pandas**: By using Polars for core operations, the backend achieves multi-threaded, highly parallelized data processing, making the API significantly faster and memory-efficient compared to traditional Pandas backends.
2.  **O(1) Undo/Redo Architecture**: The history is maintained as a list of DataFrame references in memory. Because Polars utilizes Arrow memory layouts (copy-on-write), keeping historical states consumes minimal additional RAM, allowing instant undo/redo.
3.  **Smart Metadata Caching**: Instead of scanning the dataset every time the user requests the Table View or Quality Report, anomaly coordinates (row/col indices of nulls, outliers) are computed once and cached.
4.  **Multi-Agent Orchestration**: The system doesn't rely on a single massive LLM prompt. It delegates specific tasks (Cleaning, Visualization, Chat, Insight) to specialized Agents (using LangGraph/LangChain), improving accuracy and reducing hallucinations.
5.  **Secure LLM Execution**: When the Chat Agent writes code to query the dataset, it runs against a secure in-memory sandbox (the active session's DataFrame), entirely isolated from the host OS and without database access.
