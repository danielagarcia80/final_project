from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = 'cst205final'  # Required to use sessions securely

# Initialize Flask-Bootstrap
Bootstrap(app)

# Load quizzes from JSON
with open('quizzes.json') as f:
    quizzes = json.load(f)['quizzes']

# User data storage in memory
users = {}

@app.route('/')
def index():
    return render_template('index.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    quiz = quizzes[quiz_id]
    if request.method == 'POST':
        user_answers = [request.form.get(f'answers_{i}') for i in range(len(quiz['questions']))]
        score = sum(1 for i, q in enumerate(quiz['questions']) if user_answers[i] == q['answer'])
        username = session['username']
        if username in users:
            users[username]['scores'].append(score)
            return render_template('result.html', quiz=quiz, score=score, user_answers=user_answers)
        else:
            flash('User not found. Please log in again.')
            return redirect(url_for('login'))
    
    return render_template('quiz.html', quiz=quiz)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if username in users:
            flash('Username already exists')
            return redirect(url_for('register'))
        users[username] = {'password': password, 'scores': []}
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/leaderboard')
def leaderboard():
    unique_scores = {}
    for username, data in users.items():
        if data['scores']:
            unique_scores[username] = max(data['scores'])
    sorted_scores = sorted(unique_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return render_template('leaderboard.html', scores=sorted_scores)

if __name__ == '__main__':
    app.run(debug=True)
