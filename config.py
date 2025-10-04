import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://cloud.sz3dp.com')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
