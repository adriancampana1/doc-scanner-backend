from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

CORS(app)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

if __name__ == '__main__':
    app.run()

from app import routes