from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import os
from pymongo import MongoClient
import gridfs

# Importar las rutas
from routes.audio_uploader_router import audio_uploader_service, init_audio_uploader_service
from routes.ping_router import ping_service

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/audioConsulta/*": {"origins": "http://localhost:4200"}})

uri = os.getenv('MONGO_URI')
mongo_client = MongoClient(uri)
_mongod = mongo_client['AudioData']
_gridfs = gridfs.GridFS(_mongod)

# Inicializar el servicio de carga de audio
init_audio_uploader_service(_mongod, _gridfs)

# Registrar las rutas
app.register_blueprint(audio_uploader_service, url_prefix='/api/audio')
app.register_blueprint(ping_service, url_prefix='/api/ping')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=4000)
