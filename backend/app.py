from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from model import load_model, detect_apples

import os
import uuid
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Créer le dossier uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modèle non chargé au démarrage
print("🚀 API démarrée, modèle non encore chargé")
model = None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return jsonify({
        "message": "Tomato Detection API",
        "status": "running",
        "model_loaded": model is not None
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None,
        "model_info": "YOLO Tomato Detector"
    })


@app.route("/api/detect", methods=["POST"])
def detect():
    global model

    try:
        print("📨 Requête reçue sur /api/detect")

        image = None

        # Cas 1 : image envoyée comme fichier
        if "image" in request.files:
            file = request.files["image"]
            print(f"📁 Fichier reçu : {file.filename}")

            if file.filename == "":
                return jsonify({"error": "Aucun fichier sélectionné"}), 400

            if not allowed_file(file.filename):
                return jsonify({
                    "error": f"Format non supporté. Utilisez : {', '.join(ALLOWED_EXTENSIONS)}"
                }), 400

            filename = secure_filename(file.filename)
            temp_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                f"temp_{uuid.uuid4().hex}_{filename}"
            )

            file.save(temp_path)
            image = cv2.imread(temp_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            if image is None:
                return jsonify({"error": "Impossible de lire l'image"}), 400

        # Cas 2 : image envoyée en base64
        elif request.is_json and request.json and "image_base64" in request.json:
            image_data = request.json["image_base64"]

            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]

            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                return jsonify({"error": "Impossible de décoder l'image base64"}), 400

        else:
            return jsonify({
                "error": "Aucune image fournie. Envoyez un fichier ou du base64."
            }), 400

        # Charger le modèle seulement à la première requête
        if model is None:
            print("📦 Chargement du modèle à la première requête...")
            model = load_model()

            if model is None:
                return jsonify({
                    "error": "Le modèle n'a pas pu être chargé."
                }), 500

        print("🔍 Lancement de la détection...")
        detections, annotated_image = detect_apples(model, image)
        print(f"🎯 {len(detections)} détections trouvées")

        # Sauvegarder l'image annotée
        result_filename = f"result_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(app.config["UPLOAD_FOLDER"], result_filename)
        cv2.imwrite(result_path, annotated_image)

        # Convertir l'image annotée en base64
        success, buffer = cv2.imencode(".jpg", annotated_image)
        if not success:
            return jsonify({"error": "Erreur lors de l'encodage de l'image résultat"}), 500

        annotated_base64 = base64.b64encode(buffer).decode("utf-8")

        return jsonify({
            "success": True,
            "filename": result_filename,
            "detections": detections,
            "count": len(detections),
            "image_url": f"/uploads/{result_filename}",
            "annotated_base64": annotated_base64
        })

    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
@app.route("/ping")
def ping():
    return "pong", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Serveur démarré sur http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
