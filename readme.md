# Flask API - Audio

## Resumen

Esta API es una POC para evaluar el alcance y si es factible utilizando Flask y MongoDB para almacenamiento y recuperacion de archivos de audio.

## Configuración para levantar el proyecto - Python 3.12.0

- Opcional:
  - Generar enviroment: `python -m venv venv`
  - Activar enviroment: `./venv/bin/activate`

- Instalar libs contenidas dentro de requierements.txt: `pip install -r requirements.txt`
- Agregar `.env` con la credenciales de mongo por fuera de `/src`, por ejemplo:
  ```
  MONGO_URI=mongodb+srv://<db_username>:<db_password>@sandbox.np2pkby.mongodb.net/?retryWrites=true&w=majority&appName=<ClusterName>
  ```

## Recursos

Se provee algunos ejemplos para invocar facil desde postman en la colección `FlaskAPI.postman_collection.json`

