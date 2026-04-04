from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import cv2
import numpy as np
import base64
from werkzeug.utils import secure_filename
import sys

# Ajouter le chemin du backend pour l'import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importez votre modèle
from model import load_model, detect_apples

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # CORS plus permissif

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
if model is not None:
    print("✅ Modèle chargé avec succès!")
else:
    print("⚠️ Modèle non chargé, mode dégradé activé")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return jsonify({
        'message': 'Tomato Detection API',
        'status': 'running',
        'model_loaded': model is not None
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'model_info': 'YOLO Tomato Detector'
    })

@app.route('/api/detect', methods=['POST'])
def detect():
    try:
        print("📨 Requête reçue sur /api/detect")
        
        # Vérifier si c'est un upload de fichier
        if 'image' in request.files:
            file = request.files['image']
            print(f"📁 Fichier reçu: {file.filename}")

            if file.filename == '':
                return jsonify({'error': 'Aucun fichier sélectionné'}), 400

            if not allowed_file(file.filename):
                return jsonify({'error': f'Format non supporté. Utilisez: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

            # Sauvegarder temporairement
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{uuid.uuid4().hex}_{filename}')
            file.save(temp_path)
            
            # Lire l'image
            image = cv2.imread(temp_path)
            
            # Nettoyer
            os.remove(temp_path)
            
            if image is None:
                return jsonify({'error': "Impossible de lire l'image"}), 400

        # Vérifier si c'est du base64
        elif request.json and 'image_base64' in request.json:
            image_data = request.json['image_base64']
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        else:
            return jsonify({'error': 'Aucune image fournie. Envoyez un fichier ou du base64.'}), 400

        # Détection
        print("🔍 Lancement de la détection...")
        detections, annotated_image = detect_apples(model, image)
        print(f"🎯 {len(detections)} détections trouvées")

        # Sauvegarder l'image annotée
        result_filename = f"result_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        cv2.imwrite(result_path, annotated_image)

        # Convertir l'image annotée en base64 pour l'envoyer directement
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'success': True,
            'filename': result_filename,
            'detections': detections,
            'count': len(detections),
            'image_url': f'/uploads/{result_filename}',
            'annotated_base64': annotated_base64
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
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Serveur démarré sur http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
