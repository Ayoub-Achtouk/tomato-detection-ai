import os
import cv2
import numpy as np
from ultralytics import YOLO
import torch

CONFIDENCE_THRESHOLD = 0.50
CLASS_NAME = "Tomat"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "best.pt"))


def load_model():
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Modèle introuvable: {MODEL_PATH}")
            return None

        model = YOLO(MODEL_PATH)
        print(f"✅ Modèle chargé depuis {MODEL_PATH}")
        print(f"📊 Classes: {model.names}")
        return model

    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        return None


def detect_apples(model, image):
    if model is None:
        return get_dummy_detections(image), image

    results = model.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
    detections = []
    annotated_image = image.copy()

    if len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
        return detections, annotated_image

    boxes = results[0].boxes

    if torch.is_tensor(boxes.xyxy):
        boxes_xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy()
    else:
        boxes_xyxy = np.array(boxes.xyxy)
        confs = np.array(boxes.conf)
        classes = np.array(boxes.cls)

    filtered_boxes = []
    filtered_confs = []
    filtered_classes = []

    for box, conf, cls in zip(boxes_xyxy, confs, classes):
        x1, y1, x2, y2 = map(int, box)
        class_name = results[0].names[int(cls)]

        if CLASS_NAME is None or class_name == CLASS_NAME:
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": float(conf),
                "label": class_name,
                "class_id": int(cls)
            })
            filtered_boxes.append([x1, y1, x2, y2])
            filtered_confs.append(float(conf))
            filtered_classes.append(int(cls))

    if filtered_boxes:
        annotated_image = annotate_image(
            image,
            np.array(filtered_boxes),
            np.array(filtered_confs),
            np.array(filtered_classes),
            results[0].names
        )

    return detections, annotated_image


def annotate_image(image, boxes, confs, classes, class_names):
    img = image.copy()
    box_color = (0, 0, 255)
    text_bg_color = (255, 255, 255)

    counts = {}
    for cls in classes:
        cls_id = int(cls)
        counts[cls_id] = counts.get(cls_id, 0) + 1

    for box, conf, cls in zip(boxes, confs, classes):
        x1, y1, x2, y2 = map(int, box)
        class_name = class_names[int(cls)]
        label = f"{class_name} {conf:.2f}"

        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]

        text_y1 = max(0, y1 - text_size[1] - 10)
        text_y2 = y1
        cv2.rectangle(img, (x1, text_y1), (x1 + text_size[0] + 8, text_y2), box_color, -1)
        cv2.putText(img, label, (x1 + 4, max(15, y1 - 6)), font, font_scale, text_bg_color, thickness)

    text_y = 30
    total_count = sum(counts.values())

    for class_id, count in counts.items():
        class_name = class_names[class_id]
        count_text = f"Number of {class_name} = {count}"
        cv2.putText(img, count_text, (20, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        text_y += 35

    cv2.putText(
        img,
        f"Total: {total_count} detections",
        (20, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2
    )

    return img


def process_video_file(model, input_path, output_path):
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        return False, "Impossible de lire la vidéo"

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        return False, "Impossible de créer la vidéo de sortie"

    total_frames = 0
    total_detections = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            detections, annotated_frame = detect_apples(model, frame)
            total_detections += len(detections)
            total_frames += 1

            out.write(annotated_frame)

    except Exception as e:
        cap.release()
        out.release()
        return False, f"Erreur pendant le traitement vidéo: {str(e)}"

    cap.release()
    out.release()

    return True, {
        "total_frames": total_frames,
        "total_detections": total_detections
    }


def get_dummy_detections(image):
    height, width = image.shape[:2]
    return [
        {
            "bbox": [int(width * 0.2), int(height * 0.3), int(width * 0.4), int(height * 0.6)],
            "confidence": 0.95,
            "label": "Tomat",
            "class_id": 0
        },
        {
            "bbox": [int(width * 0.6), int(height * 0.4), int(width * 0.8), int(height * 0.7)],
            "confidence": 0.87,
            "label": "Tomat",
            "class_id": 0
        }
    ]
