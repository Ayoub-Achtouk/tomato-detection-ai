from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import send_from_directory
import os
import uuid
import cv2
import numpy as np
from PIL import Image
import io
import base64
from werkzeug.utils import secure_filename
import json

# Importez votre modèle
from model import load_model, detect_apples

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Créer le dossier uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Charger le modèle YOLO
print("🚀 Chargement du modèle YOLO...")
model = load_model()
print("✅ Modèle chargé avec succès!")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok', 
        'model_loaded': model is not None,
        'model_info': 'YOLO Apple Detector'
    })

@app.route('/api/detect', methods=['POST'])
def detect():
    """
    Endpoint pour la détection avec YOLO
    """
    try:
        # Vérifier si c'est un upload de fichier
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'Aucun fichier sélectionné'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Format de fichier non supporté'}), 400
            
            # Sauvegarder temporairement l'image
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{filename}')
            file.save(temp_path)
            
            # Lire l'image avec OpenCV
            image = cv2.imread(temp_path)
            
            # Supprimer le fichier temporaire
            os.remove(temp_path)
            
        # Vérifier si c'est du base64
        elif 'image_base64' in request.json:
            image_data = request.json['image_base64']
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
        else:
            return jsonify({'error': 'Aucune image fournie'}), 400
        
        if image is None:
            return jsonify({'error': 'Impossible de lire l\'image'}), 400
        
        # Détecter les pommes
        detections, annotated_image = detect_apples(model, image)
        
        # Sauvegarder l'image annotée
        result_filename = f"{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        cv2.imwrite(result_path, annotated_image)
        
        return jsonify({
            'success': True,
            'filename': result_filename,
            'detections': detections,
            'count': len(detections),
            'image_url': f'/uploads/{result_filename}'
        })
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)