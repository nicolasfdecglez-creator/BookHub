import os


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'superSecretKey123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bookhub.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
