# 🏙️ UrbanFix: AI Command Center

Built for the Gemini 3 Pro Vibe Coding Hackathon.

UrbanFix is an end-to-end, AI-powered infrastructure management dashboard that bridges the gap between defect detection and physical repair. It utilizes Gemini's advanced reasoning to process visual telemetry and drive a strict municipal workflow.

## 🚀 Key Features
* **AI Vision Engine:** Processes road imagery, generates bounding boxes, and calculates severity.
* **PWD Material Estimator:** Goes beyond standard detection by analyzing pixel density to automatically calculate Hot Mix Asphalt volume (in tons) and estimate repair budgets.
* **Strict State Machine Workflow:** An automated 8-stage pipeline (`REPORTED` → `AI_ANALYZED` → `SMC_REVIEW` → `DEPT_ASSIGNED` → `CONTRACTOR_ASSIGNED` → `REPAIRED` → `CITIZEN_VERIFIED` → `CLOSED`) driven by a Python Flask backend and immutable SQLite data lake.
* **Geospatial Intelligence:** Live mapping of critical hazard clusters.

## 💻 Tech Stack
* **Backend:** Python, Flask, SQLite3, YOLO
* **Frontend:** HTML, Tailwind CSS, Vanilla JavaScript, Leaflet.js, Chart.js
* **AI/Prompting:** Gemini 3 Pro
