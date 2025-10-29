from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
