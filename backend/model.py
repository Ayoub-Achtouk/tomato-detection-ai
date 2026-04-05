import cv2
import numpy as np

def load_model():
    print("⚠️ Mode démo (pas de vrai modèle)")
    return None

def detect_apples(model, image):
    height, width = image.shape[:2]

    detections = [
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

    annotated_image = image.copy()

    for det in detections:
        x1, y1, x2, y2 = det['bbox']

        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(annotated_image, det['label'],
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2)

    return detections, annotated_image
