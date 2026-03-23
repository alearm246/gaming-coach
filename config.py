import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Clash Royale
    CLASH_API_KEY = os.getenv('CLASH_API_KEY')