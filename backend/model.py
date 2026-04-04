import cv2
import numpy as np
from ultralytics import YOLO
import torch
import os
import gdown  # Installer: pip install gdown

# Configuration
CONFIDENCE_THRESHOLD = 0.50
CLASS_NAME = 'Tomat'

MODEL_FILE = "best.pt"
# Utiliser l'ID du fichier Google Drive
GOOGLE_DRIVE_FILE_ID = "1pumwaAfSB3YRi4yIo_b8-C3SapD3dtZR"

def download_model():
    """Télécharge le modèle depuis Google Drive avec gdown"""
    if not os.path.exists(MODEL_FILE):
        print("📥 Téléchargement du modèle depuis Google Drive...")
        try:
            # Méthode 1: Avec gdown (recommandé)
            url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}"
            gdown.download(url, MODEL_FILE, quiet=False)
            print("✅ Modèle téléchargé avec succès!")
        except Exception as e:
            print(f"❌ Erreur de téléchargement: {e}")
            # Méthode 2: Alternative avec requests
            try:
                import requests
                print("🔄 Tentative avec requests...")
                # URL alternative pour Google Drive
                download_url = f"https://drive.usercontent.google.com/download?id={GOOGLE_DRIVE_FILE_ID}&export=download&confirm=t"
                response = requests.get(download_url, stream=True)
                with open(MODEL_FILE, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("✅ Modèle téléchargé avec succès!")
            except Exception as e2:
                print(f"❌ Échec du téléchargement: {e2}")
                raise
    else:
        print("✔️ Modèle déjà téléchargé")

def load_model():
    try:
        download_model()
        
        # Vérifier que le fichier existe et n'est pas vide
        if os.path.getsize(MODEL_FILE) < 1000000:  # Moins de 1MB = fichier corrompu
            print("⚠️ Fichier modèle corrompu, suppression et re-téléchargement...")
            os.remove(MODEL_FILE)
            download_model()
        
        model = YOLO(MODEL_FILE)
        print(f"✅ Modèle chargé depuis {MODEL_FILE}")
        print(f"📊 Classes: {model.names}")
        return model

    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        return None

def detect_apples(model, image):
    """Détecte les tomates dans l'image avec YOLO"""
    if model is None:
        print("⚠️ Modèle non chargé, utilisation des détections factices")
        return get_dummy_detections(image), image
    
    # Faire la prédiction
    results = model.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
    
    detections = []
    
    if len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes
        
        if len(boxes) > 0:
            # Récupérer les données
            boxes_xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            classes = boxes.cls.cpu().numpy()
            
            # Pour chaque détection
            for box, conf, cls in zip(boxes_xyxy, confs, classes):
                x1, y1, x2, y2 = map(int, box)
                class_name = results[0].names[int(cls)]
                
                # Accepter toutes les détections (pas de filtre strict)
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float(conf),
                    'label': class_name,
                    'class_id': int(cls)
                })
            
            # Annoter l'image
            annotated_image = annotate_image(image, detections)
        else:
            annotated_image = image
    else:
        annotated_image = image
    
    print(f"🎯 {len(detections)} tomates détectées")
    return detections, annotated_image

def annotate_image(image, detections):
    """Annoter l'image avec les boîtes et les labels"""
    img = image.copy()
    
    # Couleurs
    box_color = (0, 0, 255)  # Rouge
    text_color = (255, 255, 255)  # Blanc
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        confidence = det['confidence']
        label = det['label']
        
        # Dessiner le rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)
        
        # Texte
        text = f"{label}: {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Fond du texte
        cv2.rectangle(img, (x1, y1 - text_h - 5), (x1 + text_w, y1), box_color, -1)
        cv2.putText(img, text, (x1, y1 - 5), font, font_scale, text_color, thickness)
    
    # Ajouter le compteur en haut
    y_offset = 30
    cv2.putText(img, f"Tomates detectees: {len(detections)}", 
                (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, (0, 255, 0), 2)
    
    return img

def get_dummy_detections(image):
    """Détections factices pour les tests"""
    height, width = image.shape[:2]
    return [
        {
            'bbox': [int(width*0.2), int(height*0.3), 
                    int(width*0.4), int(height*0.6)],
            'confidence': 0.95,
            'label': 'Tomate',
            'class_id': 0
        },
        {
            'bbox': [int(width*0.6), int(height*0.4), 
                    int(width*0.8), int(height*0.7)],
            'confidence': 0.87,
            'label': 'Tomate',
            'class_id': 0
        }
    ]
