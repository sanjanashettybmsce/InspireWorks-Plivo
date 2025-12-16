import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ivr_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Plivo
    PLIVO_AUTH_ID = os.environ.get('PLIVO_AUTH_ID')
    PLIVO_AUTH_TOKEN = os.environ.get('PLIVO_AUTH_TOKEN')
    PLIVO_FROM_NUMBER = os.environ.get('PLIVO_FROM_NUMBER', '14692463987')
    
    # Test Numbers
    ENGLISH_AGENT_NUMBER = '14692463990'
    SPANISH_AGENT_NUMBER = '918031274121'
