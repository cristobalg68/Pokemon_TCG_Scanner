import cv2
import numpy as np
import imagehash
from PIL import Image, ImageTk
import pandas as pd
import tkinter as tk

def read_frame(camera, size):
    ret, frame = camera.read()

    if not ret:
        print("Failed to read frame from the webcam")
        return None

    resized_frame = cv2.resize(frame, (size, size))
    return resized_frame

def read_image(path_image, size):
    img = cv2.imread(path_image)
    img = cv2.resize(img, (size, size))
    return img

def process_detections(detections):
    if detections.masks is None:
        return []
    return [
        {
            'bbox': bbox.cpu().numpy().astype(int),
            'segmentation': seg,
            'mask': mask.cpu().numpy()
        }
        for mask, seg, bbox in zip(detections.masks.data, detections.masks.xy, detections.boxes.xywh)
    ]

def mask_to_card(image, detections):
    for det in detections:
        mask = (det['mask'].astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            epsilon = 0.1 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                center = np.mean(approx, axis=0)
                corners = np.array(sorted(approx, key=lambda x: np.arctan2(x[0][1] - center[0][1], x[0][0] - center[0][0])))
                width = np.linalg.norm(corners[0] - corners[1])
                height = np.linalg.norm(corners[1] - corners[2])
                dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
                M = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
                card = cv2.warpPerspective(image, M, (int(width), int(height)))
                if width > height:
                    card = cv2.rotate(card, cv2.ROTATE_90_CLOCKWISE)
                det['card_image'] = cv2.flip(cv2.resize(card, (320, 444)), 1)
                break

def hash_image(img, hash_size):
    pil_img = Image.fromarray(img).convert('RGB')
    return f'{imagehash.dhash(pil_img, hash_size)}{imagehash.phash(pil_img, hash_size)}'

def hash_cards(detections, hash_size):
    for det in detections:
        if 'card_image' in det:
            det['hash'] = hash_image(det['card_image'], hash_size)
            flipped = cv2.rotate(det['card_image'], cv2.ROTATE_180)
            det['hash_flipped'] = hash_image(flipped, hash_size)

def hamming_distance(h1, h2):
    return sum(a != b for a, b in zip(h1, h2))

def find_match(h, df, threshold=14*6.8):
    df['similarity'] = df['hash'].apply(lambda x: hamming_distance(x, h))
    min_row = df.loc[df['similarity'].idxmin()]
    if min_row['similarity'] < threshold:
        return f"{min_row['Name']} {min_row['Set_Name']} {min_row['Local_ID']}", min_row['similarity']
    return None, None

def match_hashes(detections, df):
    for det in detections:
        if 'hash' in det:
            match1, sim1 = find_match(det['hash'], df)
            match2, sim2 = find_match(det['hash_flipped'], df)
            if match1 and (not match2 or sim1 <= sim2):
                det['match'] = match1
            elif match2:
                det['match'] = match2

def draw_boxes_and_segmentation(image, x, y, w, h, segmentation, bbox=False):
    if bbox:
        cv2.rectangle(image, (x - int(w/2), y - int(h/2)), (x + int(w/2), y + int(h/2)), (0, 255, 0), 2)
    overlay = image.copy()
    cv2.polylines(image, [segmentation], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.fillPoly(overlay, [segmentation], color=(0, 0, 255))
    cv2.addWeighted(overlay, 0.2, image, 0.8, 0, dst=image)

def draw(image, detections):
    for detection in detections:
        x, y, w, h = detection["bbox"]
        segmentation = np.array(detection["segmentation"]).reshape(-1, 2).astype(np.int32)
        draw_boxes_and_segmentation(image, x, y, w, h, segmentation)

def draw_t(image, tracker):
    for id in tracker['matches']:
        x, y, w, h = tracker['matches'][id]["bbox"]
        segmentation = np.array(tracker['matches'][id]["segmentation"]).reshape(-1, 2).astype(np.int32)
        draw_boxes_and_segmentation(image, x, y, w, h, segmentation)

def show_image(image, container):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(image)
    img_tk = ImageTk.PhotoImage(img_pil)

    label = tk.Label(container, image=img_tk, bg="black")
    label.image = img_tk
    label.pack(expand=True)

def show_video(image, video_label):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(image)
    img_tk = ImageTk.PhotoImage(image=img_pil)

    video_label.imgtk = img_tk
    video_label.config(image=img_tk)

def calcular_iou(bbox1, bbox2):
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    xA = max(x1_1, x1_2)
    yA = max(y1_1, y1_2)
    xB = min(x2_1, x2_2)
    yB = min(y2_1, y2_2)

    inter_ancho = max(0, xB - xA)
    inter_alto = max(0, yB - yA)
    inter_area = inter_ancho * inter_alto

    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0.0

    iou = inter_area / union_area
    return iou

def track_objects(detections, tracked_matches, threshold):
    new_detections = []
    new_matches = {}
    for detection in detections:
        x, y, w, h = detection["bbox"]
        x1_2 = x - int(w/2)
        y1_2 = y - int(h/2) 
        x2_2 = x + int(w/2)
        y2_2 = y + int(h/2)
        for key in tracked_matches['matches']:
            x, y, w, h = tracked_matches['matches'][key]["bbox"]
            x1_1 = x - int(w/2) 
            y1_1 = y - int(h/2) 
            x2_1 = x + int(w/2)
            y2_1 = y + int(h/2)
            iou = calcular_iou([x1_1, y1_1, x2_1, y2_1], [x1_2, y1_2, x2_2, y2_2])
            if iou > threshold:
                new_matches[key] = tracked_matches['matches'][key]
                detection['match'] = True
        if 'match' not in detection.keys():
            new_detections.append(detection)
            id = str(tracked_matches['last_id'])
            new_matches[id] = {}
            new_matches[id]["bbox"] = detection["bbox"]
            new_matches[id]["segmentation"] = detection["segmentation"]
            tracked_matches['last_id'] += 1
                
    detections = new_detections
    tracked_matches['matches'] = new_matches