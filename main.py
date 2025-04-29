from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database setup
DATABASE = 'cybercheck.db'

# Checklist items
CHECKLIST_ITEMS = [
    "Use strong, unique passwords",
    "Enable two-factor authentication",
    "Keep your software updated",
    "Backup important data regularly",
    "Use a VPN when on public Wi-Fi",
    "Be cautious of phishing emails",
    "Install antivirus and keep it updated"
]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

with app.app_context():
    def init_db():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER,
                total INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

def get_feedback(score, total):
    percentage = score / total
    if percentage >= 0.8:
        return "Excellent! You're following most security best practices.", "excellent"
    elif percentage >= 0.5:
        return "Good start, but there's room for improvement.", "good"
    else:
        return "Your security needs attention.", "poor"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/checklist', methods=['GET', 'POST'])
def checklist():
    if request.method == 'POST':
        completed = request.form.getlist('item')
        score = len(completed)
        total = len(CHECKLIST_ITEMS)
        feedback, score_class = get_feedback(score, total)

        db = get_db()
        db.execute("INSERT INTO results (score, total) VALUES (?, ?)", (score, total))
        db.commit()

        return render_template('results.html',
                               score=score,
                               total=total,
                               feedback=feedback,
                               score_class=score_class)

    return render_template('checklist.html', checklist_items=CHECKLIST_ITEMS)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/progress-data')
def progress_data():
    db = get_db()
    results = db.execute('''
        SELECT score, strftime('%Y-%m-%d', timestamp) as date 
        FROM results 
        ORDER BY timestamp
    ''').fetchall()

    scores = [row['score'] for row in results]
    dates = [row['date'] for row in results]

    return jsonify({
        'scores': scores,
        'dates': dates,
        'total': len(CHECKLIST_ITEMS)
    })

@app.route('/password-checker')
def password_checker():
    return render_template('password.html')

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    with app.app_context():
        init_db()  # <-- manually call init_db before running the app
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
