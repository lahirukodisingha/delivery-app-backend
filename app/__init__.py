from flask import Flask
from pymongo import MongoClient
from flask_cors import CORS
import os
from dotenv import load_dotenv

# .env ෆයිල් එකේ තියෙන දත්ත කියවන්න
load_dotenv()

app = Flask(__name__)
# Frontend එකෙන් එන requests වලට ඉඩ දෙන්න CORS දානවා
CORS(app) 

# MongoDB එකට කනෙක්ට් වීම
client = MongoClient(os.getenv("MONGO_URI"))
db = client.delivery_db # Database එකේ නම 'delivery_db'