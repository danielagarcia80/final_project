from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = 'cst205final'  # Required to use sessions securely
# flask --app quiz_main --debug run
# Initialize Flask-Bootstrap
Bootstrap(app)

# Load quizzes from JSON
with open('quizzes.json') as f:
    quizzes = json.load(f)['quizzes']

# User data storage in memory
users = {}

# Main route and main page where all quizzes are displayed
@app.route('/')
def index():
    return render_template('index.html', quizzes=quizzes)

# Go to the specific quiz chosen by user
@app.route('/quiz/<quiz_title>', methods=['GET'])
def quiz(quiz_title):
    if 'username' not in session:
        return redirect(url_for('login'))

    selected_quiz = next((quiz for quiz in quizzes if quiz['title'] == quiz_title), None)
    return render_template('quiz.html', quiz=selected_quiz)

# Show the results of the score once the user completed a quiz 
@app.route('/results', methods=['POST'])
def results():
    quiz_title = request.form.get('title')
    selected_quiz = next((quiz for quiz in quizzes if quiz['title'] == quiz_title), None)
    
    total_questions = len(selected_quiz['questions'])
    correct_answers = 0
    
    # Add up the score depending how many questions were correct
    for question in selected_quiz['questions']:
        selected_answer = request.form.get(f'question_{question["id"]}')
        if selected_answer and question['options'][selected_answer]:
            correct_answers += 1
    
    username = session['username']
    if username in users:
        users[username]['scores'].append(correct_answers)
    else:
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))
    
    return render_template('result.html', total_questions=total_questions, correct_answers=correct_answers)

# User login that checks for incorrect username or passwords
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

# Log out user by removing from session
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Registers a user if they don't have a log in already
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

# Display the leaderboard with top 5 users based on their highest scores
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
