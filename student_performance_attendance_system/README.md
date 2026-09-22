# Student Performance & Attendance Management System

## Technology
- Python 3.10+
- Streamlit
- SQLite
- Pandas

## Features
- Dashboard with KPIs
- Student management
- Attendance recording and percentage calculation
- Marks recording and total calculation
- Student profiles
- Performance/attendance charts
- Automatic alerts for low attendance (<75%) or low average mark (<50)
- SQLite database with sample CSE data

## Run
1. Open a terminal in this folder.
2. Create a virtual environment (optional but recommended):
   python -m venv .venv
3. Activate it:
   Windows PowerShell: .venv\Scripts\Activate.ps1
   Windows CMD: .venv\Scripts\activate
   macOS/Linux: source .venv/bin/activate
4. Install dependencies:
   pip install -r requirements.txt
5. Start:
   streamlit run app.py

The browser will open the local Streamlit application. The SQLite database is created automatically as `student_system.db` and populated with sample data on first run.
