import subprocess
import tempfile
from flask import jsonify, request, send_file
from bson import ObjectId
from dotenv import load_dotenv
import io
import os
import openai
# from openai import OpenAI

import base64

# Cargar las variables del archivo .env
load_dotenv()

openai.api_key = os.getenv('openai.api_key')
# client = OpenAI(
#   api_key=os.environ['OPENAI_API_KEY']  # this is also the default, it can be omitted
# )

def upload_audio(_mongod, _gridfs):
    try:
        # Obtener el JSON completo del request
        data = request.get_json()

        # Validar la estructura del JSON
        if 'data' not in data or 'audioBase64' not in data['data']:
            return jsonify({'error': 'Falta el campo "audioBase64" en "data"'}), 400

        if 'metadata' not in data or not all(k in data['metadata'] for k in ['mimetype', 'extension', 'filename']):
            return jsonify({'error': 'Falta información en el campo "metadata"'}), 400

        # Extraer el audio y decodificar el Base64 a binario
        audio_base64 = data['data']['audioBase64']
        audio_data = base64.b64decode(audio_base64)

        # Extraer los metadatos del audio
        mimetype = data['metadata']['mimetype']
        extension = data['metadata']['extension']
        filename = data['metadata']['filename']
        size = data['metadata'].get('size')  # Tamaño es opcional
        size_unit = data['metadata'].get('sizeUnit')  # Unidad opcional

        # Crear un nombre de archivo completo
        full_filename = f"{filename}.{extension}"

        # Subir el archivo a GridFS
        file_id = _gridfs.put(audio_data, filename=full_filename, content_type=mimetype)

        # Responder con el ID del archivo subido y los metadatos
        return jsonify({
            'message': 'Archivo subido correctamente',
            'file_id': str(file_id),
            'metadata': {
                'filename': full_filename,
                'mimetype': mimetype,
                'size': size,
                'sizeUnit': size_unit
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_audio_from_gridfs(file_id, _gridfs):
    try:
        # Intenta encontrar el archivo en GridFS
        file_data = _gridfs.find_one({"_id": ObjectId(file_id)})

        if not file_data:
            return None, 'Archivo no encontrado'

        # Recuperar el archivo
        file_binary = _gridfs.get(file_data._id).read()
        mimetype = file_data.content_type
        filename = file_data.filename

        return file_binary, mimetype, filename

    except Exception as e:
        return None, str(e)

# def get_audio_file(file_id, _gridfs):
#     try:
#         # Intenta encontrar el archivo en GridFS
#         file_data = _gridfs.find_one({"_id": ObjectId(file_id)})

#         if not file_data:
#             return jsonify({'error': 'Archivo no encontrado'}), 404

#         # Recuperar el archivo y enviarlo
#         output = _gridfs.get(file_data._id).read()
#         return send_file(io.BytesIO(output), mimetype=file_data.content_type, as_attachment=True, download_name=file_data.filename)

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

def get_audio_file(file_id, _gridfs):
    try:
        file_binary, mimetype, filename = get_audio_from_gridfs(file_id, _gridfs)

        if file_binary is None:
            return jsonify({'error': mimetype}), 404  # mimetype contiene el mensaje de error

        # Verifica que el mimetype sea correcto para un archivo de audio
        if not mimetype.startswith('audio/'):
            return jsonify({'error': 'El archivo recuperado no es de tipo audio'}), 400

        # Enviar el archivo recuperado como descarga
        return send_file(io.BytesIO(file_binary), mimetype=mimetype, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_unique_temp_file(suffix=".wav"):
    """
    Crea un archivo temporal con un nombre único y devuelve el nombre del archivo.
    El archivo no se eliminará automáticamente al cerrar para permitir su manipulación posterior.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()  # Cerramos el archivo para poder usarlo en otros procesos
    return temp_file.name


def generate_report_from_transcript(transcript_text):
    """
    Función que toma una transcripción y la envía a la API de OpenAI para formatearla en un reporte.

    :param transcript_text: Texto de la transcripción obtenida de Whisper.
    :return: Reporte formateado.
    """
    # Instrucciones y transcripción para enviar a ChatGPT
    messages = [
        {"role": "system", "content": "Eres un asistente que formatea transcripciones en un reporte médico estructurado."},
        {"role": "user", "content": f"""
        Por favor, genera un reporte médico estructurado a partir de la siguiente transcripción. Usa el siguiente formato:
        Título: [El título general del reporte]
        Subtítulo 1: [Descripción breve]
        Texto: [Cuerpo de la sección]
        Subtítulo 2: [Descripción breve]
        Texto: [Cuerpo de la sección]
        Conclusión: [Descripción breve]
        Texto: [Conclusión]

        Transcripción:
        {transcript_text}
        """}
    ]
    try:
        # Llamada a la API de OpenAI para generar el reporte
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": "Eres un asistente que da formato técnico a reportes médico."},
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0
        )

        # Obtener el reporte formateado desde la respuesta
        formatted_report = response.choices[0].message.content

        # Retornar el reporte formateado
        return jsonify({'formatted_report': formatted_report}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_audioConsultaToWhisper_service(file_id, _gridfs):
    try:
        # Intenta encontrar el archivo en GridFS
        file_data = _gridfs.find_one({"_id": ObjectId(file_id)})

        if not file_data:
            return jsonify({'error': 'Archivo no encontrado'}), 404

        # Recuperar el archivo en formato binario
        file_binary = _gridfs.get(file_data._id).read()

        # Crear archivos temporales con nombres únicos
        temp_file_path = create_unique_temp_file(suffix=".wav")
        converted_file_path = create_unique_temp_file(suffix=".wav")

        # # Guardar el archivo temporalmente
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        #     temp_file.write(file_binary)
        #     temp_file.flush()

        # Guardar el archivo binario en el archivo temporal
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(file_binary)

        # Convertir el archivo a formato .wav usando ffmpeg
        # converted_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        subprocess.run(['ffmpeg', '-y', '-i', temp_file_path, converted_file_path], check=True)

        # Ahora enviamos el archivo convertido a Whisper para transcripción
        with open(converted_file_path, 'rb') as audio_file:
            transcription  = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        # La transcripción se obtiene accediendo al atributo "text"
        transcript_text = transcription.text

              # Eliminar los archivos temporales
        os.remove(temp_file_path)
        os.remove(converted_file_path)

        # return jsonify({'transcription': transcript_text}), 200
        return generate_report_from_transcript(transcript_text)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
