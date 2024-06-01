from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app
import os

load_dotenv()

dg_client_key = os.getenv('DG_CLIENT_KEY')
