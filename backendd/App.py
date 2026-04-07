from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import cv2
import numpy as np
import base64
from werkzeug.utils import secure_filename

from model import load_model, detect_apples, process_video_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("🚀 Chargement du modèle YOLO...")
model = load_model()
print("✅ Modèle chargé avec succès!" if model is not None else "❌ Échec du chargement du modèle")


def allowed_image_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def allowed_video_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None,
        "model_info": "YOLO Tomato Detector"
    })


@app.route("/api/detect", methods=["POST"])
def detect():
    try:
        image = None

        if "image" in request.files:
            file = request.files["image"]

            if file.filename == "":
                return jsonify({"error": "Aucun fichier sélectionné"}), 400

            if not allowed_image_file(file.filename):
                return jsonify({"error": "Format d'image non supporté"}), 400

            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"temp_{uuid.uuid4().hex}_{filename}")
            file.save(temp_path)

            image = cv2.imread(temp_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

        elif request.is_json and request.json and "image_base64" in request.json:
            image_data = request.json["image_base64"]

            if "base64," in image_data:
                image_data = image_data.split("base64,", 1)[1]

            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        else:
            return jsonify({"error": "Aucune image fournie"}), 400

        if image is None:
            return jsonify({"error": "Impossible de lire l'image"}), 400

        detections, annotated_image = detect_apples(model, image)

        result_filename = f"{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(app.config["UPLOAD_FOLDER"], result_filename)
        cv2.imwrite(result_path, annotated_image)

        return jsonify({
            "success": True,
            "filename": result_filename,
            "detections": detections,
            "count": len(detections),
            "image_url": f"/uploads/{result_filename}"
        })

    except Exception as e:
        print(f"❌ Erreur image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/detect-video", methods=["POST"])
def detect_video():
    try:
        if "video" not in request.files:
            return jsonify({"error": "Aucune vidéo fournie"}), 400

        file = request.files["video"]

        if file.filename == "":
            return jsonify({"error": "Aucune vidéo sélectionnée"}), 400

        if not allowed_video_file(file.filename):
            return jsonify({"error": "Format de vidéo non supporté"}), 400

        input_filename = secure_filename(file.filename)
        input_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            f"input_{uuid.uuid4().hex}_{input_filename}"
        )

        output_filename = f"output_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_filename)

        file.save(input_path)

        success, result = process_video_file(model, input_path, output_path)

        if os.path.exists(input_path):
            os.remove(input_path)

        if not success:
            if os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({"error": result}), 400

        return jsonify({
            "success": True,
            "message": "Vidéo traitée avec succès",
            "video_url": f"/uploads/{output_filename}",
            "total_frames": result["total_frames"],
            "total_detections": result["total_detections"]
        })

    except Exception as e:
        print(f"❌ Erreur vidéo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
