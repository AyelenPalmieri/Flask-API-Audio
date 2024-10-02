from flask import Blueprint

from services.audio_uploader_service import upload_audio, get_audio_file, send_audioConsultaToWhisper_service

audio_uploader_service = Blueprint('audio_uploader_service', __name__)


def init_audio_uploader_service(db, fs):
    @audio_uploader_service.route('/upload', methods=['POST'])
    def upload_audio_route():
        return upload_audio(db, fs)

    @audio_uploader_service.route('/file/<file_id>', methods=['GET'])
    def retrieve_audio_file(file_id):
        return get_audio_file(file_id, fs)

    @audio_uploader_service.route('/transcribe/<file_id>', methods=['POST'])
    def send_audioConsultaToWhisper(file_id):
        return send_audioConsultaToWhisper_service(file_id, fs)
