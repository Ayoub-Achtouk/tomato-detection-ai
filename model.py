import cv2
import numpy as np
from ultralytics import YOLO
import torch
import os
import urllib.request

# Configuration
CONFIDENCE_THRESHOLD = 0.50  # Seuil de confiance comme dans votre code
CLASS_NAME = 'Tomat'  # Nom de la classe à détecter (pomme/tomate)

MODEL_FILE = "best.pt"

MODEL_URL = "https://drive.google.com/uc?export=download&id=1pumwaAfSB3YRi4yIo_b8-C3SapD3dtZR"

def download_model():
    if not os.path.exists(MODEL_FILE):
        print("📥 Téléchargement du modèle...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
        print("✅ Modèle téléchargé")
    else:
        print("✔️ Modèle déjà téléchargé")
def load_model():
    try:
        download_model()  # 👈 important

        model = YOLO(MODEL_FILE)

        print(f"✅ Modèle chargé depuis {MODEL_FILE}")
        print(f"📊 Classes: {model.names}")

        return model

    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        return None

def detect_apples(model, image):
    """
    Détecte les pommes/tomates dans l'image avec YOLO
    Retourne: (detections_list, annotated_image)
    """
    if model is None:
        return get_dummy_detections(image), image
    
    # Faire la prédiction
    results = model.predict(image, conf=CONFIDENCE_THRESHOLD)
    
    detections = []
    
    # Traiter les résultats
    if len(results) > 0:
        # Récupérer les boîtes
        boxes = results[0].boxes
        
        if boxes is not None and len(boxes) > 0:
            # Convertir en CPU si nécessaire
            if torch.is_tensor(boxes.xyxy):
                boxes_xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy()
            else:
                boxes_xyxy = boxes.xyxy
                confs = boxes.conf
                classes = boxes.cls
            
            # Pour chaque détection
            for box, conf, cls in zip(boxes_xyxy, confs, classes):
                x1, y1, x2, y2 = map(int, box)
                class_name = results[0].names[int(cls)]
                
                # Filtrer par nom de classe (si nécessaire)
                if class_name == CLASS_NAME or CLASS_NAME == 'Tomat':
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(conf),
                        'label': class_name,
                        'class_id': int(cls)
                    })
            
            # Annoter l'image avec les détections (comme dans votre code Colab)
            annotated_image = annotate_image(image, results, boxes_xyxy, confs, classes, results[0].names)
            
        else:
            annotated_image = image
    else:
        annotated_image = image
    
    return detections, annotated_image

def annotate_image(image, results, boxes, confs, classes, class_names):
    """
    Annoter l'image avec les boîtes et les labels
    Similaire à votre fonction plot_results
    """
    img = image.copy()
    
    # Couleurs
    box_color = (0, 0, 255)  # Rouge pour les tomates/pommes
    text_bg_color = (255, 255, 255)  # Blanc
    
    # Comptage par classe
    counts = {}
    for cls in classes:
        cls_id = int(cls)
        if cls_id not in counts:
            counts[cls_id] = 1
        else:
            counts[cls_id] += 1
    
    # Dessiner chaque boîte
    for box, conf, cls in zip(boxes, confs, classes):
        x1, y1, x2, y2 = map(int, box)
        class_name = class_names[int(cls)]
        label = f'{class_name} {conf:.2f}'
        
        # Dessiner le rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 4)
        
        # Préparer le texte
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        
        # Dessiner l'arrière-plan du texte
        cv2.rectangle(img, 
                     (x1, y1 - size[1] - 13), 
                     (x1 + size[0], y1), 
                     box_color, 
                     -1)
        
        # Dessiner le texte
        cv2.putText(img, label, (x1, y1 - 10), font, font_scale, text_bg_color, thickness)
    
    # Ajouter le comptage total
    total_count = sum(counts.values())
    text_y = 40
    for class_id, count in counts.items():
        class_name = class_names[class_id]
        count_text = f"Number of {class_name} = {count}"
        cv2.putText(img, count_text, (20, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
        text_y += 40
    
    # Ajouter le titre
    cv2.putText(img, f"Total: {total_count} detections", (20, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    
    return img

def get_dummy_detections(image):
    """
    Génère des détections factices pour les tests (si modèle non chargé)
    """
    height, width = image.shape[:2]
    return [
        {
            'bbox': [int(width*0.2), int(height*0.3), 
                    int(width*0.4), int(height*0.6)],
            'confidence': 0.95,
            'label': 'Tomat',
            'class_id': 0
        },
        {
            'bbox': [int(width*0.6), int(height*0.4), 
                    int(width*0.8), int(height*0.7)],
            'confidence': 0.87,
            'label': 'Tomat',
            'class_id': 0
        }
    ]
