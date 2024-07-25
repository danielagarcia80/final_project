from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap4
from werkzeug.security import generate_password_hash, check_password_hash
import requests, random, json, pprint

app = Flask(__name__)
app.secret_key = 'cst205final'  # Required to use sessions securely
# flask --app quiz_main --debug run
# Initialize Flask-Bootstrap
Bootstrap4(app)

# User data storage in memory
users = {}

@app.route('/', methods=['GET'])
def index():
    categories = ("Music", "Sports and Leisure", "Film and TV", "Arts and Literature", "History",
                  "Society and Culture", "Science", "Geography", "Food and Drink", "General Knowledge")
    return render_template('index.html', quiz_data = categories)


@app.route('/quiz/<quiz_title>', methods=['GET'])
def quiz(quiz_title):
    if 'username' not in session:
        return redirect(url_for('login'))
    quizzes_file = load_json()
    questions = quizzes_file[quiz_title]
    if len(questions) >= 2:
        final_questions = random.sample(questions, 2)
    else:
        final_questions = questions
    count = 10 - len(final_questions)
    remaining_questions = get_data(quiz_title, count)
    finished_questions = GetImages(remaining_questions)
    final_questions = final_questions + finished_questions

    return render_template('quiz.html', quiz=final_questions)


@app.route('/results', methods=['POST'])
def results():
    quiz_title = request.form.get('title')
    quizzes_file = load_json()
    selected_quiz = next((quiz for quiz in quizzes_file if quiz['title'] == quiz_title), None)
    
    total_questions = len(selected_quiz['questions'])
    correct_answers = 0
    
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


# Load quizzes from JSON
def load_json():    
    with open('quizzes.json') as f:
        quizzes = json.load(f)['quizzes']
    return quizzes

# gets questions from trivia api
def get_data(search_term, limit):
    ApiKeyAuth = 'ApiKeyAuth'
    url = 'https://the-trivia-api.com/v2/questions'
    categories = request.args.get('categories', search_term)
    headers = {
        'X-API-Key': ApiKeyAuth
    }
    params = {
        'categories': categories,
        'limit': limit
    }
    
    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        return (data)
    except:
        print('please try again')
# gets images for questions if available
def GetImages(questions):
    API_key = '90dGU9XIi9x7RkSKXUGzP1XNOkPgptIC2icAlDeLc90'
    endpoint = 'https://api.unsplash.com/search/photos'
    headers = {
        'Accept-Version': 'v1',
        'Authorization': f'Client-ID {API_key}'
    }
    for question in questions:
        search_term = question['correctAnswer']
        print(f"Searching for: {search_term}")
        params = {
            'query': search_term, 
            'per_page': 1
        }
        try:
            r = requests.get(endpoint, headers=headers, params=params)
            data = r.json()
            if data['results']:
                image_url = data['results'][0]['urls']['regular']
                question['image'] = image_url
            else:
                question['image'] = None 
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image for {search_term}: {e}")
            question['image'] = None
    return questions

if __name__ == '__main__':
    app.run(debug=True)
