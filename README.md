GWAcalculator

A simple Flask application for students to post updates and manage academic grades using the Philippine GWA system.

Features:
- Register/login with session-based authentication
- Facebook-like feed with posts, reactions, comments (vanilla JS)
- Foldable sidebar with departments and courses (starts with COTE)
- Academic panel to enter subject grades and compute weighted GWA
- SQLite backend with SQLAlchemy models

Run locally:
1. python -m venv venv
2. venv\Scripts\activate
3. pip install -r requirements.txt
4. python init_db.py    # creates SQLite DB and seeds COTE
5. python app.py

Open http://127.0.0.1:5000/ in your browser.