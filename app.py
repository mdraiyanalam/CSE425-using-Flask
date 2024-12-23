from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import datetime

from flask import render_template, redirect, url_for, session

DB_PATH = 'Child_learning_shell.db'

# Helper functions
def init_db():
    """Initialize the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT CHECK(role IN ('student', 'parent', 'teacher')),
                email TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                subject TEXT,
                challenge_type TEXT,
                difficulty TEXT,
                score REAL,
                date DATETIME,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        ''')
        conn.commit()

def generate_math_challenge(difficulty):
    """Generate a dynamic math challenge."""
    num_range = range(1, 20) if difficulty == 'easy' else range(20, 50)
    a, b = random.choice(num_range), random.choice(num_range)
    operation = random.choice(['+', '-', '*', '/'])
    if operation == '/':
        while b == 0:  # Avoid division by zero
            b = random.choice(num_range)
    challenge = f"What is {a} {operation} {b}?"
    answer = eval(f"{a}{operation}{b}")
    return challenge, round(answer, 2)

def generate_science_challenge():
    """Generate a dynamic science challenge."""
    questions = [
        ("What planet is known as the Red Planet?", "Mars"),
        ("What is the chemical symbol for water?", "H2O"),
        ("What gas do plants primarily use for photosynthesis?", "Carbon dioxide")
    ]
    return random.choice(questions)

# Flask App Creation
def create_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'

    # Database initialization function
    def init_db():
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Create table if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_scores (
                username TEXT PRIMARY KEY,
                total_score INTEGER
            );
        ''')

        conn.commit()
        conn.close()

    # Call init_db() to ensure the table exists when the app starts
    # Initialize the database
    init_db()

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            role = request.form['role']

            hashed_password = generate_password_hash(password)

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO users (username, password, role, email)
                        VALUES (?, ?, ?, ?)
                    ''', (username, hashed_password, role, email))
                    conn.commit()
                    flash("Registration successful! Please log in.", "success")
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    flash("Username already exists. Please try again.", "danger")

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user and check_password_hash(user[1], password):
                    session['user'] = user[0]
                    flash("Logged in successfully!", "success")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid credentials. Please try again.", "danger")

        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if 'user' not in session:
            return redirect(url_for('login'))
        return render_template('dashboard.html', username=session['user'])

    @app.route('/challenge/<subject>')
    def challenge(subject):
        if 'user' not in session:
            return redirect(url_for('login'))
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT challenge_type, difficulty, score FROM challenges WHERE subject = ?", (subject,)
            )
            challenges = cursor.fetchall()
        return render_template('challenge.html', subject=subject, challenges=challenges)

    @app.route('/game', methods=['GET', 'POST'])
    def game():
        game_type = request.args.get('type')
        if not game_type:
            return "Game type is required.", 400

        if game_type == 'math_puzzle':
            if request.method == 'POST':
                user_answer = request.form.get('answer')
                correct_answer = session.get('correct_answer')

                if user_answer and correct_answer:
                    if float(user_answer) == float(correct_answer):
                        message = "Correct!"
                    else:
                        message = f"Incorrect! The correct answer was {correct_answer}."
                    return render_template('math_puzzle.html', message=message)

            a, b = random.randint(1, 10), random.randint(1, 10)
            operation = random.choice(['+', '-', '*', '/'])
            question = f"What is {a} {operation} {b}?"
            # Calculate the correct answer and cast it to float
            correct_answer = float(eval(f"{a}{operation}{b}"))

            session['correct_answer'] = round(correct_answer, 2)
            return render_template('math_puzzle.html', question=question)

        elif game_type == 'periodic_table_explorer':
            if request.method == 'POST':
                user_answer = request.form.get('answer').strip().lower()
                correct_answer = session.get('element_name')

                if user_answer == correct_answer.lower():
                    message = "Correct!"
                else:
                    message = f"Incorrect! The correct answer was {correct_answer}."
                return render_template('periodic_table_explorer.html', message=message)

            periodic_table = [
                {'symbol': 'H', 'name': 'Hydrogen', 'atomic_number': 1},
                {'symbol': 'He', 'name': 'Helium', 'atomic_number': 2},
                {'symbol': 'Li', 'name': 'Lithium', 'atomic_number': 3},
            ]
            element = random.choice(periodic_table)
            session['element_name'] = element['name']
            clue = f"This element has the symbol '{element['symbol']}' and atomic number {element['atomic_number']}."
            return render_template('periodic_table_explorer.html', clue=clue)

        elif game_type == 'science':
            return render_template('periodic_table_explorer.html', clue=clue)

        else:
            return "Invalid game type.", 404
        
    @app.route('/leaderboard')
    def leaderboard():
        if 'user' not in session:
            return redirect(url_for('login'))
        
        # Connect to the SQLite database (adjust the path to your actual database file)
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Query to get leaderboard data (username and total_score)
        cursor.execute('SELECT username, total_score FROM user_scores ORDER BY total_score DESC LIMIT 10')
        leaderboard_data = cursor.fetchall()

        # Close the connection
        conn.close()

        return render_template('leaderboard.html', leaderboard=leaderboard_data)
    
    @app.route('/memory', methods=['GET', 'POST'])
    def memory():
        # Initialize the memory key in session if it's not already set
        if 'memory' not in session:
            session['memory'] = 0  # Default value is 0

        memory_value = session.get('memory', 0)
        result = None

        if request.method == 'POST':
            value = request.form.get('value')
            operation = request.form.get('operation')

            if operation == 'm+':
                if value:
                    session['memory'] += float(value)  # Add value to memory
                    flash(f"Value {value} added to memory!", "success")
                else:
                    flash("Please enter a value to store in memory.", "danger")
            elif operation == 'mr':
                result = session.get('memory', 0)  # Recall memory
                flash("Recalled memory value!", "info")
            elif operation == 'mc':
                session['memory'] = 0  # Clear memory
                flash("Memory cleared!", "info")
            else:
                flash("Invalid operation.", "danger")

        # Render the memory page with current value and result (if any)
        return render_template('memory.html', memory_value=session.get('memory', 0), result=result)

    @app.route('/advanced_math', methods=['GET', 'POST'])
    def advanced_math():
        result = None
        error_message = None

        if request.method == 'POST':
            try:
                # Get the operation and values from the form
                operation = request.form.get('operation')
                x = float(request.form.get('x'))  # The first number
                y = float(request.form.get('y')) if request.form.get('y') else None  # The second number, optional for square root

                if operation == 'power':  # x^y
                    result = x ** y
                elif operation == 'square_root':  # sqrt(x)
                    if x < 0:
                        error_message = "Cannot take the square root of a negative number."
                    else:
                        result = x ** 0.5  # Square root of x
                elif operation == 'modulus':  # x % y
                    result = x % y
                else:
                    error_message = "Invalid operation."

            except ValueError:
                error_message = "Please enter valid numeric values."

        return render_template('advanced_math.html', result=result, error_message=error_message)


    @app.route('/progress')
    def progress():
        if 'user' not in session:
            return redirect(url_for('login'))
        # Example progress data (replace with actual logic)
        progress_data = {
            "Math": 75,
            "Science": 50,
            "English": 90
        }
        return render_template('progress.html', progress=progress_data)

    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user' not in session:
            return redirect(url_for('login'))

        # Retrieve profile data
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, role FROM users WHERE username = ?', (session['user'],))
            user = cursor.fetchone()

        profile_data = {
            "username": user[0],
            "email": user[1],
            "role": user[2]
        }

        if request.method == 'POST':
            # Process form data
            email = request.form['email']
            role = request.form['role']

            # Update the database
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET email = ?, role = ? WHERE username = ?
                ''', (email, role, session['user']))
                conn.commit()

            # Update profile data for the current session
            profile_data['email'] = email
            profile_data['role'] = role

            # Pass a success message to the template
            flash("Profile updated successfully!", "success")

        return render_template('profile.html', profile=profile_data)
    
    @app.route('/unit_conversion', methods=['GET', 'POST'])
    def unit_conversion():
        if 'user' not in session:
            return redirect(url_for('login'))
        
        conversion_result = None

        if request.method == 'POST':
            # Retrieve form data
            conversion_type = request.form.get('conversion_type')
            value = float(request.form.get('value'))

            # Perform conversion
            if conversion_type == 'meters_to_kilometers':
                conversion_result = f"{value} meters = {value / 1000} kilometers"
            elif conversion_type == 'kilometers_to_meters':
                conversion_result = f"{value} kilometers = {value * 1000} meters"
            elif conversion_type == 'grams_to_kilograms':
                conversion_result = f"{value} grams = {value / 1000} kilograms"
            elif conversion_type == 'kilograms_to_grams':
                conversion_result = f"{value} kilograms = {value * 1000} grams"

        return render_template('unit_conversion.html', conversion_result=conversion_result)

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash("Logged out successfully!", "info")
        return redirect(url_for('home'))

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
